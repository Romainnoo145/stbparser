"""
Transformation functions for STB-ADMINISTRATIE tables.

These functions transform Offorte proposals to Inmeetplanning, Projecten, and Facturatie records.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta


def transform_proposal_to_inmeetplanning(proposal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform proposal to Inmeetplanning record (STB-ADMINISTRATIE).

    Creates planning record for measurement/installation scheduling.

    Args:
        proposal_data: Complete proposal from Offorte

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
    content = proposal_data.get('content', {})
    pricetables = content.get('pricetables', []) if content else proposal_data.get('pricetables', [])
    num_elements = len(pricetables)

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

    # Create summary (first 5 elements)
    element_types = []
    for pt in pricetables[:5]:  # First 5
        title = pt.get('title', 'Element')
        element_types.append(title)

    elements_summary = ", ".join(element_types)
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
