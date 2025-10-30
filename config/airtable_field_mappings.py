"""
Airtable field mappings configuration - COMPLETE 3-BASE STRUCTURE

This file contains all field name mappings for:
- STB-SALES base (5 tables)
- STB-ADMINISTRATIE base (3 tables)

Update this file when Airtable table structures change - no code changes needed.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class TableConfig:
    """Configuration for a single Airtable table."""
    name: str
    base_type: str  # 'sales', 'administratie', or 'productie'
    airtable_base_id: str  # Which Airtable base (from settings)
    key_field: str  # Field used for upsert operations
    fields: Dict[str, str]  # Maps internal field names to Airtable field names


# =============================================================================
# STB-SALES BASE - FIELD MAPPINGS
# =============================================================================

# Table 1: Klantenportaal (10 velden)
KLANTENPORTAAL_FIELDS = {
    "opdrachtnummer": "Opdrachtnummer",
    "klantnaam": "Klantnaam",
    "adres": "Adres",
    "telefoon": "Telefoon",
    "email": "E-mail",
    "totaalprijs_excl_btw": "Totaalprijs Excl BTW",
    "totaalprijs_incl_btw": "Totaalprijs Incl BTW",
    "offerte_elementen_overzicht": "Offerte Elementen Overzicht",
    "verkoop_notities": "Verkoop Notities",
    # "aangemaakt_op" - createdTime field (automatic)
}

# Table 2: Elementen Overzicht (21 velden)
ELEMENTEN_OVERZICHT_FIELDS = {
    # Identificatie
    "opdrachtnummer": "Opdrachtnummer",
    "element_id": "Element ID",
    "klantnaam": "Klantnaam",

    # Hoofdproduct
    "hoofdproduct_type": "Hoofdproduct Type",
    "hoofdproduct_naam": "Hoofdproduct Naam",
    "hoofdproduct_prijs_excl_btw": "Hoofdproduct Prijs Excl BTW",
    "hoofdproduct_aantal": "Hoofdproduct Aantal",

    # Subproducten Summary
    "subproducten_aantal": "Subproducten Aantal",
    "subproducten_totaal_excl_btw": "Subproducten Totaal Excl BTW",

    # Prijzen
    "element_subtotaal_excl_btw": "Element Subtotaal Excl BTW",
    "element_korting": "Element Korting",
    "element_totaal_excl_btw": "Element Totaal Excl BTW",
    "element_btw_bedrag": "Element BTW Bedrag",
    "element_btw_percentage": "Element BTW Percentage",
    "element_totaal_incl_btw": "Element Totaal Incl BTW",

    # Nacalculatie Summary (rollups/formulas)
    "kostprijs_totaal": "Kostprijs Totaal",
    "marge_euro": "Marge Euro",
    "marge_percentage": "Marge Percentage",

    # Review
    "review_datum": "Review Datum",
    "review_door": "Review Door",
    "verkoop_notities": "Verkoop Notities",
}

# Table 3: Hoofdproduct Specificaties (32 velden)
HOOFDPRODUCT_SPECIFICATIES_FIELDS = {
    # Identificatie
    "element_id_ref": "Element ID Ref",
    "opdrachtnummer": "Opdrachtnummer",
    "klantnaam": "Klantnaam",

    # Context
    "element_type": "Element Type",
    "element_naam": "Element Naam",
    "locatie": "Locatie",

    # Afmetingen
    "geoffreerde_afmetingen": "Geoffreerde Afmetingen",
    "breedte_mm": "Breedte (mm)",
    "hoogte_mm": "Hoogte (mm)",

    # Glas
    "glas_type": "Glas Type",
    "glas_detail": "Glas Detail",

    # Kleur/Afwerking
    "kleur_kozijn": "Kleur Kozijn",
    "kleur_binnen": "Kleur Binnen",
    "kleur_buiten": "Kleur Buiten",
    "afwerking_type": "Afwerking Type",

    # Deur Specifiek
    "model_deur": "Model Deur",
    "type_profiel_kozijn": "Type Profiel/Kozijn",
    "draairichting": "Draairichting",

    # Beslag/Hardware
    "deurbeslag_binnen": "Deurbeslag Binnen",
    "deurbeslag_buiten": "Deurbeslag Buiten",
    "staafgreep_specificatie": "Staafgreep Specificatie",
    "scharnieren_type": "Scharnieren Type",
    "type_cilinder": "Type Cilinder",
    "cilinder_gelijksluitend": "Cilinder Gelijksluitend",

    # Dorpel/Onderdelen
    "soort_onderdorpel": "Soort Onderdorpel",
    "brievenbus": "Brievenbus",
    "afwatering": "Afwatering",

    # Overig
    "binnenafwerking": "Binnenafwerking",
    "extra_opties": "Extra Opties",

    # Review
    "verkoop_review_status": "Verkoop Review Status",
    "opmerkingen_voor_binnendienst": "Opmerkingen voor Binnendienst",
}

# Table 4: Subproducten (16 velden - verkoop data only)
SUBPRODUCTEN_FIELDS = {
    # Unique ID
    "subproduct_id": "Subproduct ID",

    # Identificatie
    "element_id_ref": "Element ID Ref",
    "opdrachtnummer": "Opdrachtnummer",
    "klantnaam": "Klantnaam",
    "element_type": "Element Type",

    # Subproduct Info
    "subproduct_type": "Subproduct Type",
    "subproduct_naam": "Subproduct Naam",
    "subproduct_beschrijving": "Subproduct Beschrijving",
    "subproduct_categorie": "Subproduct Categorie",
    "bron": "Bron",

    # Prijzen (verkoop)
    "prijs_per_stuk_excl_btw": "Prijs Per Stuk (Excl BTW)",
    "aantal": "Aantal",
    "verkoopprijs_totaal_excl_btw": "Verkoopprijs totaal (Excl BTW)",

    # Offorte Meta
    "product_id": "Product ID",
    "sku": "SKU",
}

# Table 5: Subproducten Kostprijzen (11 velden - kostprijs data only)
SUBPRODUCTEN_KOSTPRIJZEN_FIELDS = {
    # Identificatie
    "subproduct_id_ref": "Subproduct ID Ref",  # Link to Subproducten
    "opdrachtnummer": "Opdrachtnummer",  # Lookup
    "klantnaam": "Klantnaam",  # Lookup
    "subproduct_naam": "Subproduct Naam",  # Lookup

    # Kostprijs
    "kostprijs_per_stuk": "Kostprijs Per Stuk (Excl BTW)",
    "kostprijs_totaal": "Kostprijs Totaal (Excl BTW)",  # Formula in Airtable
    "marge_euro": "Marge (Euro)",  # Formula in Airtable
    "marge_percentage": "Marge (%)",  # Formula in Airtable

    # Metadata
    "leverancier": "Leverancier",
    "status": "Status",
    "notities": "Notities",
}

# Table 6: Nacalculatie (24 velden)
NACALCULATIE_FIELDS = {
    # Identificatie
    "element_id_ref": "Element ID Ref",
    "opdrachtnummer": "Opdrachtnummer",
    "klantnaam": "Klantnaam",
    "element_type": "Element Type",

    # Verkoop Samenvatting
    "hoofdproduct_verkoop": "Hoofdproduct Verkoop",
    "subproducten_verkoop": "Subproducten Verkoop",
    "totaal_verkoop_excl_btw": "Totaal Verkoop Excl BTW",
    "totaal_verkoop_incl_btw": "Totaal Verkoop Incl BTW",
    "verkoop_datum": "Verkoop Datum",

    # Kostprijs Breakdown
    "hoofdproduct_kostprijs": "Hoofdproduct Kostprijs",
    "materiaal_kostprijs": "Materiaal Kostprijs",
    "arbeid_kostprijs": "Arbeid Kostprijs",
    "transport_kosten": "Transport Kosten",
    "overige_kosten": "Overige Kosten",
    # Note: "Kostprijs Hoofdproduct (Excl BTW)" and "Kostprijs Subproduct (Excl BTW)" are lookup/formula fields in Airtable
    "totale_kostprijs": "Totale Kostprijs",

    # Marge Analyse
    "bruto_marge_euro": "Bruto Marge Euro",
    "bruto_marge_percentage": "Bruto Marge Percentage",
    "marge_categorie": "Marge Categorie",
    "marge_opmerking": "Marge Opmerking",

    # Review
    "nacalculatie_door": "Nacalculatie Door",
    "nacalculatie_datum": "Nacalculatie Datum",
    "goedgekeurd_door": "Goedgekeurd Door",
}


# =============================================================================
# STB-ADMINISTRATIE BASE - FIELD MAPPINGS
# =============================================================================

# Table 1: Facturatie (12 velden) - BESTAAND
FACTURATIE_FIELDS = {
    "factuur_id": "Factuur ID",
    "opdrachtnummer": "Opdrachtnummer",
    "type_factuur": "Type Factuur",
    "bedrag": "Bedrag",
    "status": "Status",
    "verstuurd_op": "Verstuurd op",
    "vervaldatum": "Vervaldatum",
    "klant": "Klant",
    "email": "Email",
    "telefoon": "Telefoon",
    "adres": "Adres",
    "factuurtitel": "Factuurtitel",
}

# Table 2: Inmeetplanning (23 velden) - BESTAAND
INMEETPLANNING_FIELDS = {
    "opdrachtnummer": "Opdrachtnummer",
    "klant_en_stad": "Klant & Stad",
    "telefoon": "Telefoon",
    "elementen": "Elementen",
    "uren": "Uren",
    "waarde": "Waarde",
    "projectstatus": "Projectstatus",
    "klantnaam": "Klantnaam",
    "email": "E-mail",
    "volledig_adres": "Volledig Adres",
    "stad": "Stad",
    "postcode": "Postcode",
    "provincie": "Provincie",
    "opdracht_verkocht_op": "Opdracht verkocht op",
    "total_amount_incl_btw": "Total Amount Incl BTW",
    "aantal_elementen": "Aantal Elementen",
    "elementen_overzicht": "Elementen Overzicht",
    "locaties": "Locaties",
    "geschatte_uren": "Geschatte Uren",
    "planning_notities": "Planning Notities",
    "uiterlijke_montagedatum": "Uiterlijke montagedatum",
    "inmeetdatum": "Inmeetdatum",
    "start_inmeetplanning_trigger": "Start Inmeetplanning Trigger",
}

# Table 3: Projecten (28 velden) - NIEUW
PROJECTEN_FIELDS = {
    # Identificatie
    "opdrachtnummer": "Opdrachtnummer",
    "klantnaam": "Klantnaam",
    "project_status": "Project Status",

    # Klant Info
    "volledig_adres": "Volledig Adres",
    "postcode": "Postcode",
    "stad": "Stad",
    "telefoon": "Telefoon",
    "email": "Email",

    # Sales Context
    "totaal_verkoopprijs_excl_btw": "Totaal Verkoopprijs Excl BTW",
    "totaal_verkoopprijs_incl_btw": "Totaal Verkoopprijs Incl BTW",
    "aantal_elementen": "Aantal Elementen",
    "elementen_samenvatting": "Elementen Samenvatting",
    "verkoop_review_status": "Verkoop Review Status",
    "verkoop_notities": "Verkoop Notities",

    # Facturatie (lookups)
    "factuur_30_status": "Factuur 30% Status",
    "factuur_65_status": "Factuur 65% Status",
    "factuur_5_status": "Factuur 5% Status",

    # Inmeet (lookups)
    "inmeet_status": "Inmeet Status",
    "inmeetdatum": "Inmeetdatum",
    "toegewezen_inmeter": "Toegewezen Inmeter",
    "inmeet_notities": "Inmeet Notities",
    "inmeet_voltooid": "Inmeet Voltooid",

    # Productie (sync from STB-PRODUCTIE)
    "productie_status": "Productie Status",
    "verwachte_leverdatum": "Verwachte Leverdatum",
    "montage_datum": "Montage Datum",
    "productie_notities": "Productie Notities",
}


# =============================================================================
# TABLE CONFIGURATIONS
# =============================================================================

TABLE_CONFIGS: Dict[str, TableConfig] = {
    # STB-SALES (app9mz6mT0zk8XRGm)
    "klantenportaal": TableConfig(
        name="Klantenportaal",  # Actual Airtable table name
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",  # settings attribute name
        key_field="Opdrachtnummer",
        fields=KLANTENPORTAAL_FIELDS
    ),
    "elementen_overzicht": TableConfig(
        name="Elementen Overzicht",
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",
        key_field="Element ID",
        fields=ELEMENTEN_OVERZICHT_FIELDS
    ),
    "hoofdproduct_specificaties": TableConfig(
        name="Hoofdproduct Specificaties",
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",
        key_field="Element ID Ref",
        fields=HOOFDPRODUCT_SPECIFICATIES_FIELDS
    ),
    "subproducten": TableConfig(
        name="Subproducten",
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",
        key_field="Subproduct ID",  # Unique ID per subproduct
        fields=SUBPRODUCTEN_FIELDS
    ),
    "subproducten_kostprijzen": TableConfig(
        name="Subproducten Kostprijzen",
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",
        key_field="Subproduct ID Ref",  # Links to Subproducten
        fields=SUBPRODUCTEN_KOSTPRIJZEN_FIELDS
    ),
    "nacalculatie": TableConfig(
        name="Nacalculatie",
        base_type="sales",
        airtable_base_id="airtable_base_stb_sales",
        key_field="Element ID Ref",
        fields=NACALCULATIE_FIELDS
    ),

    # STB-ADMINISTRATIE (appuXCPmvIwowH78k)
    "facturatie": TableConfig(
        name="Facturatie",
        base_type="administratie",
        airtable_base_id="airtable_base_stb_administratie",
        key_field="Factuur ID",
        fields=FACTURATIE_FIELDS
    ),
    "inmeetplanning": TableConfig(
        name="Inmeetplanning",
        base_type="administratie",
        airtable_base_id="airtable_base_stb_administratie",
        key_field="Opdrachtnummer",
        fields=INMEETPLANNING_FIELDS
    ),
    "projecten": TableConfig(
        name="Projecten",
        base_type="administratie",
        airtable_base_id="airtable_base_stb_administratie",
        key_field="Opdrachtnummer",
        fields=PROJECTEN_FIELDS
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_table_config(table_name: str) -> Optional[TableConfig]:
    """Get configuration for a specific table."""
    return TABLE_CONFIGS.get(table_name)


def get_field_name(table_name: str, internal_name: str) -> Optional[str]:
    """
    Get Airtable field name for an internal field name.

    Args:
        table_name: Name of the table
        internal_name: Internal field name used in code

    Returns:
        Airtable field name or None if not found
    """
    config = get_table_config(table_name)
    if not config:
        return None
    return config.fields.get(internal_name)


def get_all_field_names(table_name: str) -> List[str]:
    """Get all Airtable field names for a table."""
    config = get_table_config(table_name)
    if not config:
        return []
    return list(config.fields.values())


def get_base_id_setting_name(table_name: str) -> Optional[str]:
    """Get the settings attribute name for a table's base ID."""
    config = get_table_config(table_name)
    if not config:
        return None
    return config.airtable_base_id


def get_key_field(table_name: str) -> Optional[str]:
    """Get the key field used for upserts in a table."""
    config = get_table_config(table_name)
    if not config:
        return None
    return config.key_field


def get_tables_by_base(base_type: str) -> List[str]:
    """Get all table names for a specific base type."""
    return [
        name for name, config in TABLE_CONFIGS.items()
        if config.base_type == base_type
    ]


# =============================================================================
# VALIDATION
# =============================================================================

def validate_field_mappings() -> Dict[str, List[str]]:
    """
    Validate that all table configurations are complete.

    Returns:
        Dictionary of errors per table (empty dict if no errors)
    """
    errors = {}

    for table_name, config in TABLE_CONFIGS.items():
        table_errors = []

        if not config.key_field:
            table_errors.append("Missing key_field")

        if config.base_type not in ['sales', 'administratie', 'productie']:
            table_errors.append(f"Invalid base_type: {config.base_type}")

        if not config.fields:
            table_errors.append("No fields defined")

        if not config.airtable_base_id:
            table_errors.append("Missing airtable_base_id")

        if table_errors:
            errors[table_name] = table_errors

    return errors
