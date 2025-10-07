"""Transformation modules for Offorte to Airtable sync."""

from .offorte_to_airtable import (
    transform_proposal_to_all_records,
    transform_proposal_to_klantenportaal,
    extract_specs_from_html,
    determine_element_type
)

__all__ = [
    'transform_proposal_to_all_records',
    'transform_proposal_to_klantenportaal',
    'extract_specs_from_html',
    'determine_element_type'
]
