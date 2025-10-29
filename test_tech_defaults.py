#!/usr/bin/env python3
"""Test technical specification defaults application."""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.transformers.offorte_to_airtable import transform_proposal_to_all_records
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")


def test_with_location_data():
    """Test with location test data."""
    test_file = Path("/tmp/offorte_test_with_location.json")

    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return

    with open(test_file) as f:
        proposal_data = json.load(f)

    logger.info(f"Testing proposal: {proposal_data.get('name')}")

    # Transform proposal
    records = transform_proposal_to_all_records(proposal_data)

    # Check element specificaties for default values
    specs = records['element_specificaties']

    logger.info(f"\n{'='*80}")
    logger.info(f"ELEMENT SPECIFICATIES - Checking Tech Spec Defaults")
    logger.info(f"{'='*80}\n")

    for idx, spec in enumerate(specs, 1):
        element_name = spec.get('Element Naam', 'N.v.t')
        element_type = spec.get('Element Type', 'N.v.t')
        locatie = spec.get('Locatie', 'N.v.t')

        logger.info(f"Element {idx}: {element_name} ({element_type})")
        logger.info(f"  Locatie: {locatie}")
        logger.info(f"  Glas Type: {spec.get('Glas Type', 'N.v.t')}")
        logger.info(f"  Type Profiel: {spec.get('Type Profiel/Kozijn', 'N.v.t')}")
        logger.info(f"  Kleur Kozijn Binnen: {spec.get('Kleur Kozijn Binnen', 'N.v.t')}")
        logger.info(f"  Kleur Kozijn Buiten: {spec.get('Kleur Kozijn Buiten', 'N.v.t')}")
        logger.info(f"  Kleur Vleugel Binnen: {spec.get('Kleur Vleugel Binnen', 'N.v.t')}")
        logger.info(f"  Kleur Vleugel Buiten: {spec.get('Kleur Vleugel Buiten', 'N.v.t')}")
        logger.info(f"  Kleur Binnenafwerking: {spec.get('Kleur Binnenafwerking', 'N.v.t')}")
        logger.info("")

        # Check if defaults were applied
        glas = spec.get('Glas Type', '')
        profiel = spec.get('Type Profiel/Kozijn', '')

        if glas == 'N.v.t' or profiel == 'N.v.t':
            logger.warning(f"⚠️  Defaults NOT applied for {element_name}")
        else:
            logger.success(f"✓ Defaults applied for {element_name}")


if __name__ == "__main__":
    test_with_location_data()
