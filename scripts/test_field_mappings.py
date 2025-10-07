#!/usr/bin/env python3
"""Test the Airtable field mappings configuration."""

from config.airtable_field_mappings import TABLE_CONFIGS, validate_field_mappings

errors = validate_field_mappings()
print('Validation:', 'PASSED' if not errors else errors)
print('Tables configured:', len(TABLE_CONFIGS))

for name, cfg in TABLE_CONFIGS.items():
    print(f'  - {name}: {len(cfg.fields)} fields, key={cfg.key_field}, base={cfg.base_type}')
