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
    element_index: int
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
    element_discount = float(pricetable.get('discount_value', 0))
    element_total_excl = element_subtotal - element_discount

    # Calculate BTW (21% is default in NL)
    # Note: Airtable percent field expects 0-1 range, not 0-100
    btw_percentage = 0.21  # 21% as decimal for Airtable
    element_btw = element_total_excl * btw_percentage
    element_total_incl = element_total_excl + element_btw

    # Check for hordeuren
    heeft_hordeuren = specs.get('heeft_hordeuren', False) or any(
        'hordeur' in row.get('product_name', '').lower()
        for row in rows[1:]
    )

    return {
        "Opdrachtnummer": proposal_id,
        "Element ID": element_id,
        "Element Volgnummer": element_index + 1,
        "Klantnaam": customer_name,
        "Status": "Nieuw",

        # Hoofdproduct
        "Hoofdproduct Type": element_type,
        "Hoofdproduct Naam": product_name,
        "Hoofdproduct Beschrijving": description,
        "Hoofdproduct Prijs Excl BTW": main_price,
        "Hoofdproduct Aantal": main_quantity,

        # Subproducten Summary
        "Subproducten Count": subproduct_count,
        "Subproducten Totaal Excl BTW": subproduct_total,
        "Heeft Hordeuren": heeft_hordeuren,

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
    Transform pricetable into Element Specificaties record with enhanced parsing.

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

    # Extract ALL specs from entire pricetable (main + subproducts)
    specs = extract_specs_from_pricetable(pricetable)

    main_row = rows[0]
    html_content = main_row.get('content', '')

    # Get product name from specs or fallback to main row
    product_name = specs.get('product_name', '')
    if not product_name:
        product_name = main_row.get('product_name', '')
        if not product_name:
            product_name = extract_product_name_clean(html_content)

    # Determine element type using enhanced detection
    element_type = determine_element_type_enhanced(product_name, html_content)

    # Extract dimensions with proper formatting
    afmetingen = specs.get('geoffreerde_afmetingen', '')
    breedte = specs.get('breedte')
    hoogte = specs.get('hoogte')

    # Build dimensions string if we have structured data
    if not afmetingen and breedte and hoogte:
        afmetingen = f"{breedte}x{hoogte} mm"

    return {
        "Element ID Ref": element_id,
        "Opdrachtnummer": proposal_id,
        "Klantnaam": customer_name,

        # Context
        "Element Type": element_type,
        "Element Naam": product_name,
        "Locatie": "",  # Not available in Offorte

        # Afmetingen
        "Geoffreerde Afmetingen": afmetingen,
        "Breedte": breedte,
        "Hoogte": hoogte,

        # Glas
        "Glas Type": specs.get('glas_type', ''),
        "Glas Detail": specs.get('glas_detail', ''),

        # Kleur
        "Kleur Kozijn": specs.get('kleur_kozijn', ''),
        "Kleur Binnen": specs.get('kleur_binnen', ''),
        "Kleur Buiten": specs.get('kleur_buiten', ''),

        # Deur
        "Draairichting": specs.get('draairichting', ''),

        # Extra Options
        "Extra Opties": specs.get('extra_opties', ''),

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
    rows = pricetable.get('rows', [])
    if len(rows) <= 1:
        return []  # No subproducten

    subproducten = []

    # Skip first row (that's the hoofdproduct)
    for row in rows[1:]:
        product_name = row.get('product_name', '')
        description = row.get('description', '')
        price = float(row.get('price', 0))
        quantity = int(row.get('quantity', 1))
        subtotal = price * quantity

        # Determine subproduct type/category
        # Don't default to "Standaard" - let Airtable handle empty values
        category = None
        if 'hordeur' in product_name.lower():
            category = "Hordeur"
        elif 'glas' in product_name.lower():
            category = "Glas"
        elif 'beslag' in product_name.lower():
            category = "Beslag"

        subproducten.append({
            "Element ID Ref": element_id,
            "Opdrachtnummer": proposal_id,
            "Klantnaam": customer_name,
            "Element Type": element_type,

            # Subproduct Info
            "Subproduct Type": category,
            "Subproduct Naam": product_name,
            "Subproduct Beschrijving": description,
            "Subproduct Categorie": category,
            "Bron": "Offorte",

            # Prijzen
            "Prijs Per Stuk Excl BTW": price,
            "Aantal": quantity,
            "Subtotaal Excl BTW": subtotal,

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

        # Kostprijs (to be filled manually later in Airtable)
        "Kostprijs Status": None,
    }


def transform_proposal_to_all_records(proposal_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform complete Offorte proposal into all required Airtable records.

    This is the main transformation function that creates records for all 5 STB-SALES tables.

    Args:
        proposal_data: Complete proposal data from Offorte API

    Returns:
        Dictionary with keys: klantenportaal, elementen_overzicht, element_specificaties,
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

    # 2-5. Per pricetable: Element, Specs, Subproducten, Nacalculatie
    elementen_overzicht = []
    element_specificaties = []
    subproducten = []
    nacalculatie = []

    for idx, pricetable in enumerate(pricetables):
        # Element record
        element = transform_pricetable_to_element(
            pricetable, proposal_id, customer_name, idx
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
            element_specificaties.append(specs)

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
        f"{len(element_specificaties)} specs, "
        f"{len(subproducten)} subproducten, "
        f"{len(nacalculatie)} nacalculatie records"
    )

    # 6. Inmeetplanning (STB-ADMINISTRATIE) - 1 record per proposal
    from backend.transformers.administratie_transforms import transform_proposal_to_inmeetplanning
    inmeetplanning = [transform_proposal_to_inmeetplanning(proposal_data)]

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
        "element_specificaties": element_specificaties,
        "subproducten": subproducten,
        "nacalculatie": nacalculatie,
        "inmeetplanning": inmeetplanning,
        "projecten": projecten,
        "facturatie": facturatie,
    }
