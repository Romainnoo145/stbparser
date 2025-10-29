"""
Enhanced parser for extracting specs from Offorte pricetables.

Handles flexible product structures:
- Parses afmetingen from product titles (e.g., "Product (1234x5678mm)")
- Extracts color specs from subproducts with <em> tags
- Detects glass, motor, and other options from subproducts
"""

import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from loguru import logger


def extract_dimensions_from_text(text: str) -> Dict[str, int]:
    """
    Extract dimensions in format (1234x5678mm) or (1234x5678) from text.

    Args:
        text: Product name or description

    Returns:
        Dict with 'breedte' and 'hoogte' in mm, or empty dict
    """
    # Match patterns like (2450x1760mm) or (2450x1760)
    pattern = r'\((\d+)\s*x\s*(\d+)\s*(?:mm)?\)'
    match = re.search(pattern, text)

    if match:
        return {
            'breedte': int(match.group(1)),
            'hoogte': int(match.group(2))
        }

    return {}


def extract_product_name_clean(html_content: str) -> str:
    """
    Extract clean product name from HTML, removing dimensions.

    Args:
        html_content: HTML with product name

    Returns:
        Clean product name without dimensions
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(strip=True)

    # Remove dimensions pattern (1234x5678mm)
    text = re.sub(r'\s*\(\d+\s*x\s*\d+\s*(?:mm)?\)\s*', '', text)

    return text.strip()


def extract_specs_from_html_items(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract specs from <li> items in HTML (common Offorte pattern).

    Args:
        soup: BeautifulSoup object

    Returns:
        Dict with extracted specs
    """
    specs = {}

    # Get all <li> items (usually contain detailed specs)
    li_items = soup.find_all('li')

    for li in li_items:
        text = li.get_text(strip=True).lower()

        # Onderdorpel
        if 'onderdorpel' in text:
            specs['soort_onderdorpel'] = li.get_text(strip=True)

        # Cilinders
        if 'cilinder' in text:
            if 'gelijksluitend' in text:
                specs['cilinder_gelijksluitend'] = 'Ja'
                specs['type_cilinder'] = li.get_text(strip=True)
            else:
                specs['type_cilinder'] = li.get_text(strip=True)

        # Beslag / Hang- en sluitwerk
        if any(word in text for word in ['beslag', 'greep', 'staafgreep', 'knop', 'hang-', 'sluitwerk', 'sluiting']):
            if 'staafgreep' in text:
                specs['staafgreep_specificatie'] = li.get_text(strip=True)
            elif 'binnen' in text:
                specs['deurbeslag_binnen'] = li.get_text(strip=True)
            elif 'buiten' in text:
                specs['deurbeslag_buiten'] = li.get_text(strip=True)
            else:
                # General beslag info → can go to Extra Opties
                if 'extra_opties' not in specs:
                    specs['extra_opties'] = []
                specs['extra_opties'].append(li.get_text(strip=True))

        # Scharnieren
        if 'scharnier' in text:
            specs['scharnieren_type'] = li.get_text(strip=True)

        # Brievenbus
        if 'brievenbus' in text:
            specs['brievenbus'] = 'Ja'

        # Afwatering
        if 'afwatering' in text or 'waterslag' in text:
            specs['afwatering'] = li.get_text(strip=True)

        # Binnenafwerking
        if 'afwerking' in text or 'paneel' in text:
            specs['binnenafwerking'] = li.get_text(strip=True)

        # Veiligheidsglas
        if 'veiligheidsglas' in text:
            specs['glas_type'] = 'Veiligheidsglas'
            if not specs.get('glas_detail'):
                specs['glas_detail'] = li.get_text(strip=True)

    return specs


def extract_specs_from_pricetable(pricetable: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all specs from a pricetable by analyzing all rows.

    This handles:
    - Main product (first row): dimensions, type, AND detailed specs from <li> items
    - Subproducts: colors, glass, motors, options

    Args:
        pricetable: Pricetable dict with 'rows' list

    Returns:
        Dict with extracted specs
    """
    rows = pricetable.get('rows', [])
    if not rows:
        return {}

    specs = {}

    # Parse main product (first row)
    main_row = rows[0]
    main_html = main_row.get('content', '')
    main_soup = BeautifulSoup(main_html, 'html.parser')

    # Extract product name (just the first <p>, not all text)
    first_p = main_soup.find('p')
    if first_p:
        product_name_text = first_p.get_text(strip=True)
        # Remove dimensions pattern
        product_name_text = re.sub(r'\s*\(\d+\s*x\s*\d+\s*(?:mm)?\)\s*', '', product_name_text)
        specs['product_name'] = product_name_text

    # Extract dimensions from product name/content
    dimensions = extract_dimensions_from_text(main_html)
    if dimensions:
        specs['breedte'] = dimensions['breedte']
        specs['hoogte'] = dimensions['hoogte']
        specs['geoffreerde_afmetingen'] = f"{dimensions['breedte']}x{dimensions['hoogte']} mm"

    # Extract detailed specs from <li> items in main product
    main_specs = extract_specs_from_html_items(main_soup)
    specs.update(main_specs)

    # Parse subproducts for additional specs
    for row in rows[1:]:
        html = row.get('content', '')
        soup = BeautifulSoup(html, 'html.parser')

        # Get all text content
        all_text = soup.get_text(strip=True).lower()

        # Get title (first <p>)
        title_p = soup.find('p')
        title = title_p.get_text(strip=True).lower() if title_p else ''

        # Get emphasized details (<em> tags)
        em_tags = soup.find_all('em')
        em_texts = [em.get_text(strip=True) for em in em_tags]

        # === KLEUR DETECTIE ===
        if 'kleur' in title or 'ral' in title:
            # Binnen kleur
            if 'binnen' in title:
                if em_texts:
                    specs['kleur_binnen'] = ', '.join(em_texts)
            # Buiten kleur
            elif 'buiten' in title:
                if em_texts:
                    specs['kleur_buiten'] = ', '.join(em_texts)
            # Algemene kozijn kleur
            else:
                if em_texts:
                    specs['kleur_kozijn'] = ', '.join(em_texts)

        # === GLAS DETECTIE ===
        if 'glas' in all_text or 'beglazing' in all_text or 'hr++' in all_text or 'triple' in all_text:
            glas_info = ' - '.join(em_texts) if em_texts else title
            specs['glas_detail'] = glas_info

            # Determine glass type (must match Airtable singleSelect choices)
            # Choices: Triple, HR++, HR+++, Veiligheidsglas, Dubbelglas, Anders
            if 'hr+++' in all_text:
                specs['glas_type'] = 'HR+++'
            elif 'triple' in all_text:
                specs['glas_type'] = 'Triple'
            elif 'hr++' in all_text:
                specs['glas_type'] = 'HR++'
            elif 'veiligheid' in all_text:
                specs['glas_type'] = 'Veiligheidsglas'
            elif 'dubbel' in all_text:
                specs['glas_type'] = 'Dubbelglas'

        # === MOTOR DETECTIE (voor rolluiken) ===
        if 'motor' in all_text or 'elektrisch' in all_text or 'solar' in all_text:
            motor_info = ' - '.join(em_texts) if em_texts else title
            if 'extra_opties' not in specs:
                specs['extra_opties'] = []
            specs['extra_opties'].append(motor_info)

        # === DRAAIRICHTING ===
        if 'draairichting' in all_text or 'openslaand' in all_text:
            if 'links' in all_text:
                specs['draairichting'] = 'Links'
            elif 'rechts' in all_text:
                specs['draairichting'] = 'Rechts'

        # === HORDEUR ===
        # Note: Hordeur info is captured in subproducten, not element specs
        # No need to add a boolean flag here - "Heeft Hordeuren" is not an Airtable field

        # === ALGEMENE OPTIES ===
        if any(keyword in all_text for keyword in ['meerprijs', 'optie', 'afstandsbediening', 'box']):
            if 'extra_opties' not in specs:
                specs['extra_opties'] = []
            option_text = title_p.get_text(strip=True) if title_p else ''
            if em_texts:
                option_text += ' - ' + ', '.join(em_texts)
            specs['extra_opties'].append(option_text)

    # Join extra options into string
    if 'extra_opties' in specs:
        specs['extra_opties'] = '\n'.join(specs['extra_opties'])

    logger.debug(f"Extracted specs: {specs}")
    return specs


def determine_element_type_enhanced(product_name: str, all_content: str = '') -> str:
    """
    Determine element type with enhanced detection.

    Maps to valid Airtable Element Type options based on CSV export.
    Note: "Rolluik" is NOT a valid option, maps to "Overig".

    Args:
        product_name: Main product name
        all_content: Additional content to analyze

    Returns:
        One of: Deur, Raam, Kozijn, Schuifpui, Vouwwand, Overig
    """
    combined = (product_name + " " + all_content).lower()

    # Check for specific types
    # Note: Rolluiken are mapped to Overig since that's not a valid Airtable option
    if 'deur' in combined:
        return 'Deur'
    elif 'raam' in combined:
        return 'Raam'
    elif 'schuif' in combined:
        return 'Schuifpui'
    elif 'vouw' in combined:
        return 'Vouwwand'
    elif 'kozijn' in combined:
        return 'Kozijn'
    else:
        # Rolluiken, screens, and other types → Overig
        return 'Overig'
