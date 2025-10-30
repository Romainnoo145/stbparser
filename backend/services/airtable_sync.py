"""
Airtable sync service for pushing records to Airtable tables.

Handles upsert operations based on key fields defined in field mappings.
"""

from typing import Dict, List, Any, Optional
import requests
from loguru import logger

from backend.core.settings import settings
from config.airtable_field_mappings import get_table_config, get_base_id_setting_name


class AirtableSync:
    """Service for syncing data to Airtable."""

    def __init__(self):
        """Initialize Airtable sync service."""
        self.api_key = settings.airtable_api_key
        self.base_url = "https://api.airtable.com/v0"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Load base IDs from settings
        self.bases = {
            "sales": settings.airtable_base_stb_sales,
            "administratie": settings.airtable_base_stb_administratie,
            "productie": settings.airtable_base_stb_productie
        }

    def _get_base_id(self, table_name: str) -> Optional[str]:
        """Get base ID for a table."""
        config = get_table_config(table_name)
        if not config:
            logger.error(f"Unknown table: {table_name}")
            return None

        return self.bases.get(config.base_type)

    def _get_table_name(self, internal_name: str) -> Optional[str]:
        """Get actual Airtable table name from internal name."""
        config = get_table_config(internal_name)
        if not config:
            return None
        return config.name

    def _find_record(self, base_id: str, table_name: str, key_field: str, key_value: str) -> Optional[str]:
        """
        Find existing record by key field.

        Args:
            base_id: Airtable base ID
            table_name: Table name
            key_field: Field to search on
            key_value: Value to find

        Returns:
            Record ID if found, None otherwise
        """
        url = f"{self.base_url}/{base_id}/{table_name}"

        # Build filter formula
        filter_formula = f"{{{key_field}}}='{key_value}'"

        params = {
            "filterByFormula": filter_formula,
            "maxRecords": 1
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()

            records = response.json().get('records', [])
            if records:
                return records[0]['id']

            return None

        except Exception as e:
            logger.error(f"Error finding record in {table_name}: {e}")
            return None

    def _clean_record_data(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean record data before sending to Airtable.

        - Remove empty strings (causes issues with singleSelect fields)
        - Remove None values
        - Convert "N.v.t" to "N.v.t." for singleSelect fields that require it

        Args:
            record_data: Raw record data

        Returns:
            Cleaned record data
        """
        # Fields that use "N.v.t." (with period) in Airtable
        nvt_with_period_fields = {
            'Locatie',
            'Cilinder Gelijksluitend',
            'Brievenbus'
        }

        cleaned = {}
        for key, value in record_data.items():
            # Skip empty strings and None values
            if value == "" or value is None:
                continue

            # Convert "N.v.t" to "N.v.t." for specific singleSelect fields
            if key in nvt_with_period_fields and value == "N.v.t":
                cleaned[key] = "N.v.t."
            else:
                cleaned[key] = value

        return cleaned

    def upsert_record(
        self,
        table_internal_name: str,
        record_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Upsert a single record to Airtable.

        If a record with the same key field value exists, update it.
        Otherwise, create a new record.

        Args:
            table_internal_name: Internal table name (e.g., 'klantenportaal')
            record_data: Dictionary of field values

        Returns:
            Record ID if successful, None otherwise
        """
        config = get_table_config(table_internal_name)
        if not config:
            logger.error(f"Unknown table: {table_internal_name}")
            return None

        base_id = self._get_base_id(table_internal_name)
        table_name = config.name
        key_field = config.key_field

        # Clean the record data
        record_data = self._clean_record_data(record_data)

        if not base_id:
            logger.error(f"Could not determine base ID for {table_internal_name}")
            return None

        # Check if key field exists in data
        if key_field not in record_data:
            logger.error(f"Record data missing key field '{key_field}' for {table_internal_name}")
            return None

        key_value = str(record_data[key_field])

        # Find existing record
        existing_id = self._find_record(base_id, table_name, key_field, key_value)

        url = f"{self.base_url}/{base_id}/{table_name}"

        try:
            if existing_id:
                # Update existing record
                url = f"{url}/{existing_id}"
                payload = {"fields": record_data}
                response = requests.patch(url, headers=self.headers, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Updated record in {table_name}: {key_field}={key_value}")
                return existing_id
            else:
                # Create new record
                payload = {"fields": record_data}
                response = requests.post(url, headers=self.headers, json=payload, timeout=10)
                response.raise_for_status()
                record_id = response.json().get('id')
                logger.info(f"Created record in {table_name}: {key_field}={key_value}")
                return record_id

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error upserting to {table_name}: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Response: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            else:
                logger.error("No response available")
            logger.error(f"Record data: {record_data}")
            return None
        except Exception as e:
            logger.error(f"Error upserting to {table_name}: {e}")
            return None

    def create_record(
        self,
        table_internal_name: str,
        record_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Create a new record in Airtable without checking for existing records.

        Use this for tables where multiple records can have the same key field value,
        like Subproducten where multiple subproducts share the same Element ID Ref.

        Args:
            table_internal_name: Internal table name (e.g., 'subproducten')
            record_data: Dictionary of field values

        Returns:
            Record ID if successful, None otherwise
        """
        config = get_table_config(table_internal_name)
        if not config:
            logger.error(f"Unknown table: {table_internal_name}")
            return None

        base_id = self._get_base_id(table_internal_name)
        table_name = config.name

        # Clean the record data
        record_data = self._clean_record_data(record_data)

        if not base_id:
            logger.error(f"Could not determine base ID for {table_internal_name}")
            return None

        url = f"{self.base_url}/{base_id}/{table_name}"

        try:
            # Always create new record
            payload = {"fields": record_data}
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            record_id = response.json().get('id')

            # Log with subproduct name for clarity
            identifier = record_data.get('Subproduct Naam', record_data.get('Element ID Ref', 'Unknown'))
            logger.info(f"Created record in {table_name}: {identifier}")
            return record_id

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error creating record in {table_name}: {e}")
            if e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Response: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text}")
            else:
                logger.error("No response available")
            logger.error(f"Record data: {record_data}")
            return None
        except Exception as e:
            logger.error(f"Error creating record in {table_name}: {e}")
            return None

    def upsert_records(
        self,
        table_internal_name: str,
        records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Upsert multiple records to a table.

        For Subproducten: Always creates new records (no upsert check)
        For other tables: Upserts based on key field

        Args:
            table_internal_name: Internal table name
            records: List of record dictionaries

        Returns:
            Dictionary with 'created' and 'updated' counts
        """
        stats = {"created": 0, "updated": 0, "failed": 0}

        # Special handling for Subproducten - always create, never update
        # Multiple subproducts can share the same Element ID Ref
        if table_internal_name == 'subproducten':
            for record in records:
                result = self.create_record(table_internal_name, record)
                if result:
                    stats["created"] += 1
                else:
                    stats["failed"] += 1

            logger.info(
                f"Batch create to {table_internal_name}: "
                f"{stats['created']} created, {stats['failed']} failed"
            )
        else:
            # Normal upsert logic for other tables
            for record in records:
                result = self.upsert_record(table_internal_name, record)
                if result:
                    stats["created"] += 1
                else:
                    stats["failed"] += 1

            logger.info(
                f"Batch upsert to {table_internal_name}: "
                f"{stats['created']} succeeded, {stats['failed']} failed"
            )

        return stats

    def sync_proposal_records(self, all_records: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, int]]:
        """
        Sync all records from a transformed proposal to Airtable.

        Args:
            all_records: Dictionary with keys matching table names, values are lists of records

        Returns:
            Dictionary of stats per table
        """
        results = {}

        # Sync in order:
        # STB-SALES: Klantenportaal -> Elements -> Specs -> Subproducten -> Nacalculatie
        # STB-ADMINISTRATIE: Inmeetplanning -> Projecten -> Facturatie
        sync_order = [
            "klantenportaal",
            "elementen_overzicht",
            "hoofdproduct_specificaties",
            "subproducten",
            "nacalculatie",
            "inmeetplanning",
            "projecten",
            "facturatie",
        ]

        for table_name in sync_order:
            records = all_records.get(table_name, [])
            if not records:
                logger.info(f"No records to sync for {table_name}")
                continue

            logger.info(f"Syncing {len(records)} records to {table_name}...")
            stats = self.upsert_records(table_name, records)
            results[table_name] = stats

        return results
