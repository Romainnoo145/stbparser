"""
LLM-based spec extraction for Offorte pricetables.

Uses OpenAI GPT-4 to extract structured specs from HTML content with high accuracy.
Handles variations in HTML structure, Dutch language, and product-specific fields.
"""

import json
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import openai
from loguru import logger

from backend.core.settings import settings


class LLMSpecExtractor:
    """Extract specs from Offorte pricetables using LLM."""

    def __init__(self):
        """Initialize LLM extractor with OpenAI client."""
        self.client = openai.OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model

    def extract_specs_from_pricetable(
        self,
        pricetable: Dict[str, Any],
        element_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract all specs from a pricetable using LLM.

        Args:
            pricetable: Pricetable dict with 'rows' list
            element_type: Optional hint about element type (Deur, Raam, etc.)

        Returns:
            Dict with extracted specs matching Airtable field names
        """
        rows = pricetable.get('rows', [])
        if not rows:
            logger.warning("Empty pricetable, no specs to extract")
            return {}

        # Collect all HTML content from pricetable
        main_row = rows[0]
        main_html = main_row.get('content', '')

        # Also include subproduct rows (they contain color, glass, hardware info)
        subproduct_html = []
        for row in rows[1:]:
            content = row.get('content', '')
            if content:
                subproduct_html.append(content)

        # Convert HTML to readable text for LLM
        main_text = self._html_to_text(main_html)
        subproduct_text = "\n".join([self._html_to_text(html) for html in subproduct_html])

        # Build prompt
        prompt = self._build_extraction_prompt(main_text, subproduct_text, element_type)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting structured data from Dutch construction proposals. Extract specs accurately and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,  # Deterministic output
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            specs = json.loads(content)

            logger.info(f"LLM extracted {len(specs)} spec fields")
            logger.debug(f"Extracted specs: {specs}")

            return specs

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return {}

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean readable text."""
        soup = BeautifulSoup(html, 'html.parser')

        # Get text but preserve structure
        lines = []
        for element in soup.find_all(['p', 'li', 'em']):
            text = element.get_text(strip=True)
            if text:
                lines.append(text)

        return '\n'.join(lines) if lines else soup.get_text(strip=True)

    def _build_extraction_prompt(
        self,
        main_text: str,
        subproduct_text: str,
        element_type: Optional[str]
    ) -> str:
        """Build prompt for LLM spec extraction."""

        type_hint = f"\n\nHint: This is a {element_type} product." if element_type else ""

        return f"""Extract specs from this Dutch construction product description.

MAIN PRODUCT:
{main_text}

SUBPRODUCTS (colors, glass, hardware, options):
{subproduct_text}
{type_hint}

Extract the following fields (return JSON). Use "N.v.t" if a field is not mentioned or not applicable:

{{
  "product_name": "Clean product name without dimensions",
  "geoffreerde_afmetingen": "Full dimension string like '2450x1760 mm' or 'N.v.t'",
  "breedte": numeric width in mm or null,
  "hoogte": numeric height in mm or null,
  "locatie": "Location/placement description. Look for: Floor + position (e.g. 'begane grond voorgevel', 'eerste verdieping achtergevel', 'begane grond zijgevel'), room names (e.g. 'Slaapkamer', 'Woonkamer', 'Zolder'), or 'Plaats:' text. Use 'N.v.t' only if truly not mentioned.",

  "glas_type": "One of: Triple, HR++, HR+++, Veiligheidsglas, Dubbelglas, Anders, or 'N.v.t'",

  "kleur_kozijn_binnen": "Inside frame color (RAL code or description) or 'N.v.t'",
  "kleur_vleugel_binnen": "Inside sash/wing color (RAL code or description) or 'N.v.t'",
  "kleur_kozijn_buiten": "Outside frame color (RAL code or description) or 'N.v.t'",
  "kleur_vleugel_buiten": "Outside sash/wing color (RAL code or description) or 'N.v.t'",
  "kleur_binnenafwerking": "Interior finish color or type or 'N.v.t'",
  "kleur_afstandhouders": "Spacer color - ONLY use 'Aluminium' or 'Zwart'. Default is 'Aluminium' unless specifically mentioned as 'Zwart' or 'N.v.t'",

  "model_deurpaneel": "Door panel model name or type (e.g. 'Paneeldeur', 'Vlakke deur') or 'N.v.t'",
  "type_profiel_kozijn": "Frame/profile type (e.g. 'Kunststof', 'Aluminium', 'Hout', 'Verdiept kunststof') or 'N.v.t'",

  "draairichting": "Links, Rechts, or 'N.v.t' (for doors, from inside view)",

  "kleur_deurbeslag_binnen": "Color of inside door hardware or 'N.v.t'",
  "kleur_deurbeslag_buiten": "Color of outside door hardware or 'N.v.t'",
  "soort_staafgreep": "Bar handle type/specs (e.g. 'RVS P45 30x600mm') or 'N.v.t'",
  "kleur_scharnieren": "Hinge color or 'N.v.t'",
  "type_cilinder": "Cylinder type (e.g. 'Gelijksluitende cilinders') or 'N.v.t'",
  "cilinder_gelijksluitend": "Ja if cylinders are 'gelijksluitend', else 'N.v.t'",

  "soort_dorpel": "Threshold type (e.g. 'Hardstenen dorpel', 'Aluminium dorpel') or 'N.v.t'",
  "brievenbus": "Ja if mailbox mentioned, else 'N.v.t'",
  "afwatering": "Drainage info or 'N.v.t'",

  "extra_opties": "List all extra options, surcharges (meerprijs), special features. Join with newlines. Use 'N.v.t' if none.",
  "opmerkingen": "Additional notes or special remarks for internal team or 'N.v.t'",

  "korting_bedrag": "Total discount amount in euros (numeric). Look for 'korting', 'totaal minbedrag', 'discount', negative prices. If no discount mentioned, use 0."
}}

RULES:
- Extract dimensions from patterns like (1234x5678mm) or (1234x5678)
- For "locatie": Look for floor+position patterns ('begane grond voorgevel', 'eerste verdieping achtergevel', 'begane grond zijgevel'), room names ('Slaapkamer', 'Woonkamer', 'Badkamer', 'Zolder', 'Garage'), or 'Plaats:' text. Often appears after dimensions.
- For "glas_type", ONLY use one of these exact values: Triple, HR++, HR+++, Veiligheidsglas, Dubbelglas, Anders
- For boolean-like fields (cilinder_gelijksluitend, brievenbus), return "Ja" if mentioned, else "N.v.t"
- For colors: Distinguish between kozijn (frame) and vleugel (sash/wing). Look for RAL codes, color names in subproducts with "Meerprijs afwijkende kleur"
- For hardware: look for "beslag", "greep", "cilinder", "hang- en sluitwerk", "scharnieren"
- If a field is not mentioned or not applicable to this product type, use "N.v.t"
- Return ONLY valid JSON, no markdown or extra text
"""


# Singleton instance
_extractor = None


def get_llm_extractor() -> LLMSpecExtractor:
    """Get or create LLM extractor singleton."""
    global _extractor
    if _extractor is None:
        _extractor = LLMSpecExtractor()
    return _extractor


def extract_specs_with_llm(
    pricetable: Dict[str, Any],
    element_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to extract specs using LLM.

    Args:
        pricetable: Pricetable dict with 'rows' list
        element_type: Optional hint about element type

    Returns:
        Dict with extracted specs
    """
    extractor = get_llm_extractor()
    return extractor.extract_specs_from_pricetable(pricetable, element_type)
