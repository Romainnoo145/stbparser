"""
Transformation functions for STB-ADMINISTRATIE tables.

These functions transform Offorte proposals to Inmeetplanning, Projecten, and Facturatie records.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from backend.transformers.specs_parser import extract_product_name_clean


def transform_proposal_to_inmeetplanning(
    proposal_data: Dict[str, Any],
    elementen_overzicht: List[Dict[str, Any]] = None,
    hoofdproduct_specs: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Transform proposal to Inmeetplanning record (STB-ADMINISTRATIE).

    Creates planning record for measurement/installation scheduling.

    Args:
        proposal_data: Complete proposal from Offorte
        elementen_overzicht: List of element records (optional, for better data)
        hoofdproduct_specs: List of hoofdproduct specificaties (optional, for locaties)

    Returns:
        Inmeetplanning record dict
    """
    proposal_id = str(proposal_data.get('id', ''))

    # Customer info
    customer = proposal_data.get('customer') or proposal_data.get('contact', {})
    customer_name = customer.get('company_name', '') or customer.get('name', '') or customer.get('fullname', '')

    # Address
    street = customer.get('street', '')
    zipcode = customer.get('zipcode', '')
    city = customer.get('city', '')
    state = customer.get('state', '')

    # Pricing
    won_at = proposal_data.get('won_at')
    total_incl = float(proposal_data.get('price_total_original', 0) or 0)

    # Count elements
    if elementen_overzicht:
        num_elements = len(elementen_overzicht)
    else:
        content = proposal_data.get('content', {})
        pricetables = content.get('pricetables', []) if content else proposal_data.get('pricetables', [])
        num_elements = len(pricetables)

    # Calculate estimated hours for measurement
    # Base: 15 minutes per element (middle of 10-20 range)
    # Add extra time for doors (more complex) and upper floors
    estimated_minutes = 0
    has_upper_floor = False

    if elementen_overzicht:
        for element in elementen_overzicht:
            element_type = element.get('Hoofdproduct Type', '')

            # Base time per element
            if 'deur' in element_type.lower():
                estimated_minutes += 20  # Doors take longer
            else:
                estimated_minutes += 15  # Windows average time

        # Check for upper floors in locaties
        if hoofdproduct_specs:
            for spec in hoofdproduct_specs:
                locatie = spec.get('Locatie', '').lower()
                if any(floor in locatie for floor in ['eerste verdieping', 'tweede verdieping', 'zolder']):
                    has_upper_floor = True
                    break

        # Add 20% extra time if there are upper floors (ladder needed)
        if has_upper_floor:
            estimated_minutes = int(estimated_minutes * 1.2)
    else:
        # Fallback: 15 min per element
        estimated_minutes = num_elements * 15

    # Convert to hours and round to nearest 0.5
    estimated_hours = estimated_minutes / 60
    # Round to nearest 0.5 (e.g., 1.2 -> 1.0, 1.3 -> 1.5, 1.8 -> 2.0)
    estimated_hours = round(estimated_hours * 2) / 2

    # Create elements overview (list of all element names)
    elementen_overview_text = ""
    if elementen_overzicht:
        element_lines = []
        for i, elem in enumerate(elementen_overzicht, 1):
            naam = elem.get('Hoofdproduct Naam', 'Element')
            element_type = elem.get('Hoofdproduct Type', '')
            element_lines.append(f"{i}. {naam} ({element_type})")
        elementen_overview_text = "\n".join(element_lines)

    # Extract unique locaties
    locaties_text = ""
    if hoofdproduct_specs:
        unique_locaties = set()
        for spec in hoofdproduct_specs:
            locatie = spec.get('Locatie', '').strip()
            if locatie and locatie.lower() != 'n.v.t':
                unique_locaties.add(locatie)

        if unique_locaties:
            locaties_text = "\n".join(sorted(unique_locaties))

    return {
        "Opdrachtnummer": proposal_id,
        "Klantnaam": customer_name,
        "Klant & Stad": f"{customer_name}, {city}" if city else customer_name,
        "Telefoon": customer.get('phone', ''),
        "E-mail": customer.get('email', ''),
        "Volledig Adres": street,
        "Postcode": zipcode,
        "Stad": city,
        "Provincie": state,
        "Opdracht verkocht op": won_at.split('T')[0] if won_at else None,
        "Total Amount Incl BTW": total_incl,
        "Aantal Elementen": num_elements,
        "Elementen": num_elements,  # Number field (not text)
        "Elementen Overzicht": elementen_overview_text if elementen_overview_text else None,
        "Locaties": locaties_text if locaties_text else None,
        "Uren": estimated_hours,
        "Projectstatus": "Te Plannen",  # Valid: Te Plannen, Gepland, Voltooid, Geannuleerd
        "Start Inmeetplanning Trigger": True,  # Trigger for automation
    }


def transform_proposal_to_project(proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform proposal to Project record (STB-ADMINISTRATIE).

    Creates master project record for tracking across all stages.

    Args:
        proposal_data: Complete proposal from Offorte

    Returns:
        Project record dict
    """
    proposal_id = str(proposal_data.get('id', ''))

    # Customer info
    customer = proposal_data.get('customer') or proposal_data.get('contact', {})
    customer_name = customer.get('company_name', '') or customer.get('name', '') or customer.get('fullname', '')

    # Address
    street = customer.get('street', '')
    zipcode = customer.get('zipcode', '')
    city = customer.get('city', '')

    full_address = f"{street}, {zipcode} {city}" if all([street, zipcode, city]) else street

    # Pricing
    total_incl = float(proposal_data.get('price_total_original', 0) or 0)
    # Estimate excl BTW (rough calculation, actual is in elements)
    total_excl = total_incl / 1.21 if total_incl else 0

    # Count elements
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', []) if content else proposal_data.get('pricetables', [])
    num_elements = len(pricetables)

    # Create summary (first 5 elements) - extract clean product names
    element_names = []
    for pt in pricetables[:5]:  # First 5
        rows = pt.get('rows', [])
        if rows:
            html_content = rows[0].get('content', '')
            product_name = extract_product_name_clean(html_content)
            element_names.append(product_name)
        else:
            element_names.append('Element')

    elements_summary = ", ".join(element_names)
    if len(pricetables) > 5:
        elements_summary += f" (+{len(pricetables) - 5} meer)"

    return {
        "Opdrachtnummer": proposal_id,
        "Klantnaam": customer_name,
        "Project Status": "Verkocht",  # Valid: Verkocht, Facturatie, Inmeet Planning, Inmeet Voltooid, In Productie, Voltooid
        "Volledig Adres": full_address,
        "Postcode": zipcode,
        "Stad": city,
        "Telefoon": customer.get('phone', ''),
        "Email": customer.get('email', ''),
        "Totaal Verkoopprijs Excl BTW": round(total_excl, 2),
        "Totaal Verkoopprijs Incl BTW": total_incl,
        "Aantal Elementen": num_elements,
        "Elementen Samenvatting": elements_summary,
        "Verkoop Review Status": "In Review",  # Valid: In Review, Goedgekeurd, Afgekeurd
    }


def transform_proposal_to_facturatie(proposal_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Transform proposal to Facturatie records (STB-ADMINISTRATIE).

    Creates 3 invoice records based on STB payment schedule:
    - 30% Vooraf (upfront payment)
    - 65% Bij Start (at project start)
    - 5% Oplevering (at delivery)

    Args:
        proposal_data: Complete proposal from Offorte

    Returns:
        List of 3 Facturatie records
    """
    proposal_id = str(proposal_data.get('id', ''))

    # Customer info
    customer = proposal_data.get('customer') or proposal_data.get('contact', {})
    customer_name = customer.get('company_name', '') or customer.get('name', '') or customer.get('fullname', '')

    # Address
    street = customer.get('street', '')
    zipcode = customer.get('zipcode', '')
    city = customer.get('city', '')
    full_address = f"{street}, {zipcode} {city}" if all([street, zipcode, city]) else street

    # Pricing
    total_incl = float(proposal_data.get('price_total_original', 0) or 0)

    # Create 3 invoices based on payment schedule
    invoices = []

    # 1. 30% Vooraf
    invoices.append({
        "Factuur ID": f"{proposal_id}-F1",
        "Opdrachtnummer": proposal_id,
        "Type Factuur": "30% Vooraf",
        "Bedrag": round(total_incl * 0.30, 2),
        "Status": "Concept",  # Valid: Concept, Verstuurd, Betaald, Herinnering, Achterstallig
        "Klant": customer_name,
        "Email": customer.get('email', ''),
        "Telefoon": customer.get('phone', ''),
        "Adres": full_address,
        "Factuurtitel": f"Vooruitbetaling 30% - Opdracht {proposal_id}",
    })

    # 2. 65% Bij Start
    invoices.append({
        "Factuur ID": f"{proposal_id}-F2",
        "Opdrachtnummer": proposal_id,
        "Type Factuur": "65% Bij Start",
        "Bedrag": round(total_incl * 0.65, 2),
        "Status": "Concept",
        "Klant": customer_name,
        "Email": customer.get('email', ''),
        "Telefoon": customer.get('phone', ''),
        "Adres": full_address,
        "Factuurtitel": f"Start Opdracht 65% - Opdracht {proposal_id}",
    })

    # 3. 5% Oplevering
    invoices.append({
        "Factuur ID": f"{proposal_id}-F3",
        "Opdrachtnummer": proposal_id,
        "Type Factuur": "5% Oplevering",
        "Bedrag": round(total_incl * 0.05, 2),
        "Status": "Concept",
        "Klant": customer_name,
        "Email": customer.get('email', ''),
        "Telefoon": customer.get('phone', ''),
        "Adres": full_address,
        "Factuurtitel": f"Eindafrekening 5% - Opdracht {proposal_id}",
    })

    return invoices
