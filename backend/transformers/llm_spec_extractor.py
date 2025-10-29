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
  "locatie": "Location/room if mentioned, else 'N.v.t'",

  "glas_type": "One of: Triple, HR++, HR+++, Veiligheidsglas, Dubbelglas, Anders, or 'N.v.t'",
  "glas_detail": "Glass details/description or 'N.v.t'",

  "kleur_kozijn": "Frame color (RAL code or description) or 'N.v.t'",
  "kleur_binnen": "Inside color or 'N.v.t'",
  "kleur_buiten": "Outside color or 'N.v.t'",

  "draairichting": "Links, Rechts, or 'N.v.t' (for doors)",

  "deurbeslag_binnen": "Inside door hardware or 'N.v.t'",
  "deurbeslag_buiten": "Outside door hardware or 'N.v.t'",
  "staafgreep_specificatie": "Bar handle specs (e.g. 'RVS P45 30x600mm') or 'N.v.t'",
  "scharnieren_type": "Hinge type or 'N.v.t'",
  "type_cilinder": "Cylinder type or 'N.v.t'",
  "cilinder_gelijksluitend": "Ja if cylinders are 'gelijksluitend', else 'N.v.t'",

  "soort_onderdorpel": "Threshold type (e.g. 'Hardstenen onderdorpel') or 'N.v.t'",
  "brievenbus": "Ja if mailbox mentioned, else 'N.v.t'",
  "afwatering": "Drainage info or 'N.v.t'",
  "binnenafwerking": "Interior finish or 'N.v.t'",

  "extra_opties": "List all extra options, surcharges (meerprijs), special features. Join with newlines. Use 'N.v.t' if none."
}}

RULES:
- Extract dimensions from patterns like (1234x5678mm) or (1234x5678)
- For "glas_type", ONLY use one of these exact values: Triple, HR++, HR+++, Veiligheidsglas, Dubbelglas, Anders
- For boolean-like fields (cilinder_gelijksluitend, brievenbus), return "Ja" if mentioned, else "N.v.t"
- For colors: look for RAL codes, color names in subproducts with "Meerprijs afwijkende kleur"
- For hardware: look for "beslag", "greep", "cilinder", "hang- en sluitwerk"
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
