"""
Transform Offorte proposal data into Airtable records.

Key Transformation Strategy:
- 1 Offorte Pricetable = 1 Element (in Elementen Overzicht)
- Main row in pricetable = Hoofdproduct (first row)
- Additional rows in pricetable = Subproducten (separate records)
- HTML content parsed for Element Specificaties
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger

# Import enhanced parser functions
from backend.transformers.specs_parser import (
    extract_specs_from_pricetable,
    extract_dimensions_from_text,
    extract_product_name_clean,
    determine_element_type_enhanced
)
# Import LLM-based extractor for high-precision spec extraction
from backend.transformers.llm_spec_extractor import extract_specs_with_llm
# Import technical specification defaults
from backend.transformers.tech_spec_defaults import apply_tech_spec_defaults, check_for_overrides


def transform_proposal_to_klantenportaal(proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Offorte proposal to Klantenportaal record.

    Args:
        proposal_data: Full proposal data from Offorte API

    Returns:
        Dictionary ready for Airtable Klantenportaal table
    """
    # Extract customer info (handle webhook 'contact' vs API 'customer')
    customer = proposal_data.get('customer') or proposal_data.get('contact', {})

    # Build address (handle different field names in webhook vs API)
    street = customer.get('street_and_number') or customer.get('street', '')
    zipcode = customer.get('zip_code') or customer.get('zipcode', '')
    city = customer.get('city', '')

    address_parts = [street, zipcode, city]
    full_address = ', '.join([p for p in address_parts if p])

    # Get pricing (webhook has different structure)
    pricing = proposal_data.get('pricing', {})

    # Try API format first
    total_excl = pricing.get('total_without_discount', 0)
    total_incl = pricing.get('total_including_vat', 0)

    # If not found, try webhook format
    if not total_incl:
        price_total_str = proposal_data.get('price_total_original', '0')
        try:
            total_incl = float(price_total_str)
            # Estimate excl BTW (assuming 21% BTW)
            total_excl = total_incl / 1.21
        except (ValueError, TypeError):
            total_incl = 0
            total_excl = 0

    # Build elements overview (handle webhook vs API pricetables location)
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', []) if content else proposal_data.get('pricetables', [])
    elements_summary = f"{len(pricetables)} element(en)"

    return {
        "Opdrachtnummer": str(proposal_data.get('id', '')),
        "Klantnaam": customer.get('company_name', '') or customer.get('name', '') or customer.get('fullname', ''),
        "Adres": full_address,
        "Telefoon": customer.get('phone', ''),
        "E-mail": customer.get('email', ''),
        "Totaalprijs Excl BTW": total_excl,
        "Totaalprijs Incl BTW": total_incl,
        "Offerte Elementen Overzicht": elements_summary,
        "Verkoop Notities": f"Geïmporteerd uit Offorte op {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    }


def transform_pricetable_to_element(
    pricetable: Dict[str, Any],
    proposal_id: str,
    customer_name: str,
    element_index: int,
    discount_percentage: float = 0
) -> Dict[str, Any]:
    """
    Transform a single Offorte pricetable into an Element record.

    The first row becomes the hoofdproduct, additional rows become subproducten.

    Args:
        pricetable: Pricetable data from Offorte
        proposal_id: Proposal ID (opdrachtnummer)
        customer_name: Customer name
        element_index: Sequential index for this element (0-based)

    Returns:
        Dictionary for Elementen Overzicht table
    """
    rows = pricetable.get('rows', [])
    if not rows:
        logger.warning(f"Pricetable has no rows: {pricetable.get('id')}")
        return {}

    # First row = hoofdproduct
    main_row = rows[0]

    # Generate Element ID: {proposal_id}-E{element_index+1}
    element_id = f"{proposal_id}-E{element_index + 1}"

    # Extract specs from ENTIRE pricetable (main + subproducts)
    specs = extract_specs_from_pricetable(pricetable)

    # Extract product name and dimensions from main row
    html_content = main_row.get('content', '')
    product_name = specs.get('product_name', '')

    # If no product name extracted, fall back to original method
    if not product_name:
        product_name = main_row.get('product_name', '')
        if not product_name:
            product_name = extract_product_name_clean(html_content)

    # Determine element type using enhanced detection
    element_type = determine_element_type_enhanced(product_name, html_content)

    # Get description from specs or main row
    description = main_row.get('description', '')

    # Calculate pricing
    main_price = float(main_row.get('price', 0))
    main_quantity = int(main_row.get('quantity', 1))
    main_subtotal = main_price * main_quantity

    # Count subproducten (rows beyond first)
    subproduct_count = len(rows) - 1
    subproduct_total = sum(
        float(row.get('price', 0)) * int(row.get('quantity', 1))
        for row in rows[1:]
    )

    # Element totals
    element_subtotal = main_subtotal + subproduct_total

    # Apply proportional discount based on overall proposal discount percentage
    element_discount = element_subtotal * (discount_percentage / 100)
    element_total_excl = element_subtotal - element_discount

    # Calculate BTW (21% is default in NL)
    # Note: Airtable percent field expects decimal (0.21 for 21%)
    btw_percentage = 0.21  # 21% as decimal for Airtable
    element_btw = element_total_excl * btw_percentage  # Calculate actual BTW amount
    element_total_incl = element_total_excl + element_btw

    return {
        "Opdrachtnummer": proposal_id,
        "Element ID": element_id,
        "Klantnaam": customer_name,

        # Hoofdproduct
        "Hoofdproduct Type": element_type,
        "Hoofdproduct Naam": product_name,
        "Hoofdproduct Prijs Excl BTW": main_price,
        "Hoofdproduct Aantal": main_quantity,

        # Subproducten Summary
        "Subproducten Aantal": subproduct_count,
        "Subproducten Totaal Excl BTW": subproduct_total,

        # Prijzen
        "Element Subtotaal Excl BTW": element_subtotal,
        "Element Korting": element_discount,
        "Element Totaal Excl BTW": element_total_excl,
        "Element BTW Bedrag": element_btw,
        "Element BTW Percentage": btw_percentage,
        "Element Totaal Incl BTW": element_total_incl,
    }


def transform_pricetable_to_specs(
    pricetable: Dict[str, Any],
    element_id: str,
    proposal_id: str,
    customer_name: str
) -> Dict[str, Any]:
    """
    Transform pricetable into Element Specificaties record with LLM-based extraction.

    Uses OpenAI GPT-4 for high-precision spec extraction from Offorte HTML.
    Handles variations in HTML structure, Dutch language, and product-specific fields.

    Args:
        pricetable: Pricetable data from Offorte
        element_id: Generated element ID
        proposal_id: Proposal ID
        customer_name: Customer name

    Returns:
        Dictionary for Element Specificaties table
    """
    rows = pricetable.get('rows', [])
    if not rows:
        return {}

    main_row = rows[0]
    html_content = main_row.get('content', '')

    # First, determine element type using pattern-based detection (fast)
    product_name = extract_product_name_clean(html_content)
    element_type = determine_element_type_enhanced(product_name, html_content)

    # Extract ALL specs using LLM (high precision)
    logger.info(f"Using LLM to extract specs for {element_type}: {product_name}")
    specs = extract_specs_with_llm(pricetable, element_type)

    # Apply default technical specifications for N.v.t fields
    specs = apply_tech_spec_defaults(specs)

    # Check for overrides in extra options (e.g., Triple glas overrides HR++ default)
    specs = check_for_overrides(specs, specs.get('extra_opties', ''))

    # Use LLM-extracted product name if available
    if specs.get('product_name'):
        product_name = specs['product_name']

    # Extract dimensions from LLM response
    afmetingen = specs.get('geoffreerde_afmetingen', 'N.v.t')
    breedte = specs.get('breedte')
    hoogte = specs.get('hoogte')

    # Helper to get value or N.v.t
    def get_or_nvt(field_name: str) -> str:
        """Get spec value or 'N.v.t' if empty/missing."""
        value = specs.get(field_name)
        if value and str(value).strip() and str(value).lower() != 'null':
            return str(value)
        return "N.v.t"

    return {
        "Element ID Ref": element_id,
        "Opdrachtnummer": proposal_id,
        "Klantnaam": customer_name,

        # Context
        "Element Type": element_type,
        "Element Naam": product_name,
        "Locatie": get_or_nvt('locatie'),

        # Afmetingen
        "Geoffreerde Afmetingen (BxH)": afmetingen if afmetingen != 'N.v.t' else "N.v.t",

        # Profiel & Glas
        "Type Profiel/Kozijn": get_or_nvt('type_profiel_kozijn'),
        "Type Glas": get_or_nvt('glas_type'),

        # Kleur - Split fields for kozijn and vleugel
        "Kleur Kozijn Binnen": get_or_nvt('kleur_kozijn_binnen'),
        "Kleur Vleugel Binnen": get_or_nvt('kleur_vleugel_binnen'),
        "Kleur Kozijn Buiten": get_or_nvt('kleur_kozijn_buiten'),
        "Kleur Vleugel Buiten": get_or_nvt('kleur_vleugel_buiten'),
        "Kleur Binnenafwerking": get_or_nvt('kleur_binnenafwerking'),
        "Kleur Afstandhouders": get_or_nvt('kleur_afstandhouders'),

        # Product specifiek
        "Model Deurpaneel": get_or_nvt('model_deurpaneel'),

        # Deur specifiek
        "Draairichting (binnenaanzicht)": get_or_nvt('draairichting'),

        # Beslag/Hardware - New field names with colors
        "Kleur Deurbeslag Binnen": get_or_nvt('kleur_deurbeslag_binnen'),
        "Kleur Deurbeslag Buiten": get_or_nvt('kleur_deurbeslag_buiten'),
        "Soort Staafgreep": get_or_nvt('soort_staafgreep'),
        "Kleur Scharnieren": get_or_nvt('kleur_scharnieren'),
        "Type Cilinder": get_or_nvt('type_cilinder'),
        "Cilinder Gelijksluitend": get_or_nvt('cilinder_gelijksluitend'),

        # Dorpel/Onderdelen
        "Soort Dorpel": get_or_nvt('soort_dorpel'),
        "Brievenbus": get_or_nvt('brievenbus'),
        "Afwatering": get_or_nvt('afwatering'),

        # Extra Options & Opmerkingen
        "Extra Opties": get_or_nvt('extra_opties'),
        "Opmerkingen voor Binnendienst": get_or_nvt('opmerkingen'),

        # Review
        "Verkoop Review Status": "In Review",
    }


def transform_pricetable_rows_to_subproducten(
    pricetable: Dict[str, Any],
    element_id: str,
    proposal_id: str,
    customer_name: str,
    element_type: str
) -> List[Dict[str, Any]]:
    """
    Transform pricetable rows (excluding first) into Subproducten records.

    Args:
        pricetable: Pricetable data from Offorte
        element_id: Generated element ID
        proposal_id: Proposal ID
        customer_name: Customer name
        element_type: Element type (Deur, Raam, etc.)

    Returns:
        List of dictionaries for Subproducten table
    """
    from bs4 import BeautifulSoup

    rows = pricetable.get('rows', [])
    if len(rows) <= 1:
        return []  # No subproducten

    subproducten = []

    # Skip first row (that's the hoofdproduct)
    for idx, row in enumerate(rows[1:], start=1):
        # Parse HTML content from Offorte API
        html_content = row.get('content', '')
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract product name from first <p> tag
        first_p = soup.find('p')
        product_name = first_p.get_text(strip=True) if first_p else 'N.v.t'

        # Description: any additional text or <li> items
        description = ''
        li_items = soup.find_all('li')
        if li_items:
            description = '\n'.join([li.get_text(strip=True) for li in li_items])

        # Skip unselected optional products (checkboxes not checked)
        # selectable=True means it's an optional add-on
        # user_selected=True means the customer checked the box
        if row.get('selectable') and not row.get('user_selected'):
            continue

        price = float(row.get('price', 0))
        quantity = int(row.get('quantity', 1))
        subtotal = price * quantity

        # Skip meaningless rows: €0 with quantity 0, or N.v.t with €0
        if subtotal == 0 and quantity == 0:
            continue
        if product_name.lower() in ['n.v.t', 'n.v.t.', 'nvt'] and price == 0:
            continue

        # Generate unique Subproduct ID: element_id-S1, element_id-S2, etc.
        subproduct_id = f"{element_id}-S{idx}"

        # Determine subproduct category and type
        # Subproduct Categorie: what kind of product (Kleur, Glas, Beslag, Hordeur, etc.)
        # Subproduct Type: pricing nature (Meerprijs, Optie, Accessoire, Korting)
        product_lower = product_name.lower()
        description_lower = description.lower()
        combined_text = f"{product_lower} {description_lower}"

        # Determine category with improved keyword matching
        if any(word in combined_text for word in ['kleur', 'ral', 'afwijkend', 'coating']):
            category = "Kleur"
        elif any(word in combined_text for word in ['glas', 'beglazing', 'glazen', 'melkglas', 'gezandstraald']):
            category = "Glas"
        elif any(word in combined_text for word in ['beslag', 'greep', 'cilinder', 'knop', 'staafgreep', 'deurgreep', 'sluitwerk', 'hang-']):
            category = "Beslag"
        elif 'hordeur' in combined_text:
            category = "Hordeur"
        elif any(word in combined_text for word in ['dorpel', 'onderdorpel']):
            category = "Dorpel"
        elif any(word in combined_text for word in ['ventilatie', 'rooster']):
            category = "Ventilatie"
        elif any(word in combined_text for word in ['brievenbus', 'kozijnverbreding', 'demonteren', 'monteren']):
            category = "Accessoire"
        else:
            category = "Anders"

        # Determine type (most Offorte items are meerprijs/options)
        subproduct_type = "Meerprijs"  # Default
        if 'korting' in combined_text or 'afprijzing' in combined_text or price < 0:
            subproduct_type = "Korting"
        elif 'optie' in combined_text or 'extra' in combined_text:
            subproduct_type = "Optie"
        elif 'accessoire' in combined_text or 'brievenbus' in combined_text or 'demonteren' in combined_text:
            subproduct_type = "Accessoire"

        subproducten.append({
            # Links
            "Element ID Ref": element_id,
            "Opdrachtnummer": proposal_id,
            "Klantnaam": customer_name,
            "Element Type": element_type,

            # Subproduct Info
            "Subproduct Type": subproduct_type,  # Meerprijs, Optie, Accessoire, Korting
            "Subproduct Naam": product_name,
            "Subproduct Beschrijving": description if description else None,
            "Subproduct Categorie": category,  # Kleur, Glas, Beslag, etc.
            "Bron": "Offorte",

            # Prijzen
            "Prijs Per Stuk (Excl BTW)": price,
            "Aantal": quantity,
            "Verkoopprijs totaal (Excl BTW)": subtotal,

            # Offorte Meta
            "Product ID": str(row.get('product_id', '')),
            "SKU": row.get('sku', ''),
        })

    return subproducten


def transform_element_to_nacalculatie(
    element_data: Dict[str, Any],
    proposal_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create Nacalculatie record from element data.

    Initially, cost prices are empty - to be filled manually later.

    Args:
        element_data: Element record (from Elementen Overzicht)
        proposal_date: Date proposal was won

    Returns:
        Dictionary for Nacalculatie table
    """
    return {
        "Element ID Ref": element_data.get("Element ID"),
        "Opdrachtnummer": element_data.get("Opdrachtnummer"),
        "Klantnaam": element_data.get("Klantnaam"),
        "Element Type": element_data.get("Hoofdproduct Type"),

        # Verkoop Samenvatting (from element)
        "Hoofdproduct Verkoop": element_data.get("Hoofdproduct Prijs Excl BTW", 0),
        "Subproducten Verkoop": element_data.get("Subproducten Totaal Excl BTW", 0),
        "Totaal Verkoop Excl BTW": element_data.get("Element Totaal Excl BTW", 0),
        "Totaal Verkoop Incl BTW": element_data.get("Element Totaal Incl BTW", 0),
        "Verkoop Datum": proposal_date or datetime.now().strftime('%Y-%m-%d'),

        # Kostprijs fields (to be filled manually later in Airtable)
    }


def transform_proposal_to_all_records(proposal_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform complete Offorte proposal into all required Airtable records.

    This is the main transformation function that creates records for all 5 STB-SALES tables.

    Args:
        proposal_data: Complete proposal data from Offorte API

    Returns:
        Dictionary with keys: klantenportaal, elementen_overzicht, hoofdproduct_specificaties,
        subproducten, nacalculatie - each containing list of records
    """
    proposal_id = str(proposal_data.get('id', ''))

    # Handle both webhook payload (data.contact) and API response (data.customer)
    customer = proposal_data.get('customer') or proposal_data.get('contact', {})
    customer_name = customer.get('company_name', '') or customer.get('name', '') or customer.get('fullname', '')

    # Handle both webhook payload (data.content.pricetables) and API response (data.pricetables)
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', []) if content else proposal_data.get('pricetables', [])

    # Get proposal date
    proposal_date = proposal_data.get('won_at') or proposal_data.get('created_at')
    if proposal_date:
        # Convert to date string if needed
        proposal_date = proposal_date.split('T')[0] if 'T' in proposal_date else proposal_date

    logger.info(f"Transforming proposal {proposal_id} with {len(pricetables)} pricetables")

    # 1. Klantenportaal (1 record per proposal)
    klantenportaal = [transform_proposal_to_klantenportaal(proposal_data)]

    # FIRST PASS: Extract specs and calculate total discount
    total_subtotal = 0
    total_discount = 0
    pricetable_subtotals = []

    for idx, pricetable in enumerate(pricetables):
        rows = pricetable.get('rows', [])
        if not rows:
            pricetable_subtotals.append(0)
            continue

        # Calculate element subtotal
        main_row = rows[0]
        main_price = float(main_row.get('price', 0))
        main_quantity = int(main_row.get('quantity', 1))
        main_subtotal = main_price * main_quantity

        subproduct_total = sum(
            float(row.get('price', 0)) * int(row.get('quantity', 1))
            for row in rows[1:]
        )

        element_subtotal = main_subtotal + subproduct_total
        pricetable_subtotals.append(element_subtotal)
        total_subtotal += element_subtotal

        # Extract discount from LLM specs
        specs = extract_specs_from_pricetable(pricetable)
        korting_bedrag = float(specs.get('korting_bedrag', 0))
        total_discount += korting_bedrag

    # Calculate discount percentage
    discount_percentage = (total_discount / total_subtotal * 100) if total_subtotal > 0 else 0
    logger.info(f"Total discount: €{total_discount:.2f} on subtotal €{total_subtotal:.2f} = {discount_percentage:.2f}%")

    # 2-5. Per pricetable: Element, Specs, Subproducten, Nacalculatie
    elementen_overzicht = []
    hoofdproduct_specificaties = []
    subproducten = []
    nacalculatie = []

    for idx, pricetable in enumerate(pricetables):
        # Element record
        element = transform_pricetable_to_element(
            pricetable, proposal_id, customer_name, idx, discount_percentage
        )
        if not element:
            continue

        element_id = element['Element ID']
        element_type = element['Hoofdproduct Type']
        elementen_overzicht.append(element)

        # Specificaties record
        specs = transform_pricetable_to_specs(
            pricetable, element_id, proposal_id, customer_name
        )
        if specs:
            hoofdproduct_specificaties.append(specs)

        # Subproducten records (0-N per element)
        subs = transform_pricetable_rows_to_subproducten(
            pricetable, element_id, proposal_id, customer_name, element_type
        )
        subproducten.extend(subs)

        # Nacalculatie record
        nacalc = transform_element_to_nacalculatie(element, proposal_date)
        nacalculatie.append(nacalc)

    logger.info(
        f"Created {len(elementen_overzicht)} elements, "
        f"{len(hoofdproduct_specificaties)} specs, "
        f"{len(subproducten)} subproducten, "
        f"{len(nacalculatie)} nacalculatie records"
    )

    # 6. Inmeetplanning (STB-ADMINISTRATIE) - 1 record per proposal
    from backend.transformers.administratie_transforms import transform_proposal_to_inmeetplanning
    inmeetplanning = [transform_proposal_to_inmeetplanning(
        proposal_data,
        elementen_overzicht=elementen_overzicht,
        hoofdproduct_specs=hoofdproduct_specificaties
    )]

    # 7. Projecten (STB-ADMINISTRATIE) - 1 record per proposal
    from backend.transformers.administratie_transforms import transform_proposal_to_project
    projecten = [transform_proposal_to_project(proposal_data)]

    # 8. Facturatie (STB-ADMINISTRATIE) - 3 records per proposal (30%, 65%, 5%)
    from backend.transformers.administratie_transforms import transform_proposal_to_facturatie
    facturatie = transform_proposal_to_facturatie(proposal_data)

    logger.info(
        f"Created {len(inmeetplanning)} inmeetplanning, {len(projecten)} project, "
        f"{len(facturatie)} facturatie records"
    )

    return {
        "klantenportaal": klantenportaal,
        "elementen_overzicht": elementen_overzicht,
        "hoofdproduct_specificaties": hoofdproduct_specificaties,
        "subproducten": subproducten,
        "nacalculatie": nacalculatie,
        "inmeetplanning": inmeetplanning,
        "projecten": projecten,
        "facturatie": facturatie,
    }
