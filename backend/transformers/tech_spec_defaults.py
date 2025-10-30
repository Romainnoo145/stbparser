"""
Apply default technical specifications from the standard tech spec sheet.

These are the standard values that apply to ALL elements unless overridden
by specific options in the Offorte proposal (e.g., "Triple glas" meerprijs).
"""

from typing import Dict, Any


# Default technical specifications for STB projects
DEFAULT_TECH_SPECS = {
    # Glass
    "glas_type": "HR++",  # Standard unless "Triple", "HR+++", etc. specified

    # Profile
    "type_profiel_kozijn": "Verdiept kunststof",

    # Standard colors (from tech spec sheet)
    "kleur_kozijn_binnen": "Wit Massa",
    "kleur_vleugel_binnen": "Wit Massa",
    "kleur_kozijn_buiten": "Antraciet Houtnerfstructuur (AP40)",
    "kleur_vleugel_buiten": "Antraciet Houtnerfstructuur (AP40)",
    "kleur_binnenafwerking": "Wit Massa",
    "kleur_afstandhouders": "Aluminium",  # Standard spacer color (Aluminium or Zwart)
}


def apply_tech_spec_defaults(specs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply default technical specifications for fields that are N.v.t.

    These defaults come from the standard technical specification sheet
    that applies to all STB projects unless overridden by specific options.

    Args:
        specs: Extracted specs from LLM (may contain N.v.t values)

    Returns:
        Specs with defaults applied where N.v.t was found
    """
    enhanced_specs = specs.copy()

    # Apply defaults only if field is N.v.t (not extracted from proposal)
    for field, default_value in DEFAULT_TECH_SPECS.items():
        if specs.get(field) == "N.v.t" or not specs.get(field):
            enhanced_specs[field] = default_value

    # Special handling: If dimensions exist but geoffreerde_afmetingen is N.v.t
    breedte = specs.get('breedte')
    hoogte = specs.get('hoogte')
    afmetingen = specs.get('geoffreerde_afmetingen')

    if (afmetingen == "N.v.t" or not afmetingen) and breedte and hoogte:
        enhanced_specs['geoffreerde_afmetingen'] = f"{breedte}x{hoogte} mm"

    return enhanced_specs


def check_for_overrides(specs: Dict[str, Any], extra_opties: str) -> Dict[str, Any]:
    """
    Check extra options for overrides to default specs.

    For example, if "Triple glas" is mentioned in extra options,
    override the default HR++ glass type.

    Args:
        specs: Specs with defaults applied
        extra_opties: String with extra options from proposal

    Returns:
        Specs with overrides applied
    """
    if not extra_opties or extra_opties == "N.v.t":
        return specs

    enhanced_specs = specs.copy()
    extra_lower = extra_opties.lower()

    # Override glass type if specific type mentioned in options
    if "triple" in extra_lower and specs.get('glas_type') == "HR++":
        enhanced_specs['glas_type'] = "Triple"
    elif "hr+++" in extra_lower and specs.get('glas_type') == "HR++":
        enhanced_specs['glas_type'] = "HR+++"
    elif "veiligheidsglas" in extra_lower and specs.get('glas_type') == "HR++":
        enhanced_specs['glas_type'] = "Veiligheidsglas"

    # Check for alternative profile mentions
    if "houtlookverbinding" in extra_lower or "hvl" in extra_lower:
        if "verdiept kunststof" in specs.get('type_profiel_kozijn', '').lower():
            enhanced_specs['type_profiel_kozijn'] = "Verdiept kunststof met houtlookverbinding"

    return enhanced_specs
