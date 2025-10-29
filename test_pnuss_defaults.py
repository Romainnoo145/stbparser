#!/usr/bin/env python3
"""Test P. Nuss proposal with tech spec defaults."""

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


def test_pnuss_proposal():
    """Test with P. Nuss proposal data."""
    test_file = Path("/tmp/offorte_320457_test.json")

    if not test_file.exists():
        logger.error(f"Test file not found: {test_file}")
        return

    with open(test_file) as f:
        proposal_data = json.load(f)

    logger.info(f"Testing proposal: {proposal_data.get('name')}")

    # Transform proposal
    records = transform_proposal_to_all_records(proposal_data)

    # Check element specificaties
    specs = records['element_specificaties']

    logger.info(f"\n{'='*80}")
    logger.info(f"P. NUSS PROPOSAL - Tech Spec Defaults Check")
    logger.info(f"{'='*80}\n")

    # Summary counters
    total_elements = len(specs)
    defaults_applied = 0
    missing_defaults = 0

    for idx, spec in enumerate(specs, 1):
        element_name = spec.get('Element Naam', 'N.v.t')
        element_type = spec.get('Element Type', 'N.v.t')

        glas = spec.get('Glas Type', 'N.v.t')
        profiel = spec.get('Type Profiel/Kozijn', 'N.v.t')
        kozijn_binnen = spec.get('Kleur Kozijn Binnen', 'N.v.t')
        kozijn_buiten = spec.get('Kleur Kozijn Buiten', 'N.v.t')

        logger.info(f"Element {idx}: {element_name} ({element_type})")
        logger.info(f"  Glas Type: {glas}")
        logger.info(f"  Type Profiel: {profiel}")
        logger.info(f"  Kozijn Binnen: {kozijn_binnen}")
        logger.info(f"  Kozijn Buiten: {kozijn_buiten}")

        # Check if defaults were properly applied
        has_defaults = True
        issues = []

        if glas == 'N.v.t':
            has_defaults = False
            issues.append("Glas Type")

        if profiel == 'N.v.t':
            has_defaults = False
            issues.append("Type Profiel")

        if kozijn_binnen == 'N.v.t':
            has_defaults = False
            issues.append("Kleur Kozijn Binnen")

        if kozijn_buiten == 'N.v.t':
            has_defaults = False
            issues.append("Kleur Kozijn Buiten")

        if has_defaults:
            logger.success(f"  ✓ All defaults applied")
            defaults_applied += 1
        else:
            logger.warning(f"  ⚠️  Missing: {', '.join(issues)}")
            missing_defaults += 1

        logger.info("")

    # Print summary
    logger.info(f"{'='*80}")
    logger.info(f"SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total Elements: {total_elements}")
    logger.info(f"✓ With Defaults: {defaults_applied} ({defaults_applied/total_elements*100:.0f}%)")
    logger.info(f"⚠️  Missing Defaults: {missing_defaults} ({missing_defaults/total_elements*100:.0f}%)")


if __name__ == "__main__":
    test_pnuss_proposal()
