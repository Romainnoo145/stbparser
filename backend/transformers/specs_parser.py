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


def extract_specs_from_pricetable(pricetable: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract all specs from a pricetable by analyzing all rows.

    This handles:
    - Main product (first row): dimensions, type
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

    # Extract product name and dimensions
    specs['product_name'] = extract_product_name_clean(main_html)
    dimensions = extract_dimensions_from_text(main_html)
    if dimensions:
        specs['breedte'] = dimensions['breedte']
        specs['hoogte'] = dimensions['hoogte']
        specs['geoffreerde_afmetingen'] = f"{dimensions['breedte']}x{dimensions['hoogte']} mm"

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

            # Determine glass type
            if 'hr+++' in all_text or 'triple' in all_text:
                specs['glas_type'] = 'HR+++ Triple'
            elif 'hr++' in all_text:
                specs['glas_type'] = 'HR++'
            elif 'hr+' in all_text:
                specs['glas_type'] = 'HR+'

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
        if 'hordeur' in all_text:
            specs['heeft_hordeuren'] = True

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
    Determine element type with enhanced detection including rolluiken.

    Args:
        product_name: Main product name
        all_content: Additional content to analyze

    Returns:
        One of: Deur, Raam, Kozijn, Schuifpui, Vouwwand, Rolluik, Overig
    """
    combined = (product_name + " " + all_content).lower()

    # Check for specific types
    if 'rolluik' in combined or 'screen' in combined:
        return 'Rolluik'
    elif 'deur' in combined:
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
        return 'Overig'
