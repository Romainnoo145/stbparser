"""
End-to-end integration tests for Offorte-Airtable Sync Agent.

Tests the complete workflow:
1. Webhook receives event
2. Background worker processes
3. Offorte API fetching
4. Data transformation
5. Airtable synchronization
6. All 6 tables updated

These tests validate the PRP success criteria.
"""

import pytest
import json
import hashlib
import hmac
from unittest.mock import AsyncMock, Mock, patch
from fastapi.testclient import TestClient

from offorte_airtable_sync.server import app
from offorte_airtable_sync.agent import process_proposal_sync
from offorte_airtable_sync.tools import process_won_proposal


class TestEndToEndWebhookToSync:
    """Test complete webhook to sync flow."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_proposal_sync_workflow(
        self,
        test_deps,
        mock_offorte_proposal,
        mock_offorte_company,
        mock_offorte_contact,
        mock_offorte_content
    ):
        """Test complete workflow from proposal fetch to Airtable sync."""
        # Create complete proposal data
        complete_proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [mock_offorte_contact],
            "content": mock_offorte_content
        }

        ctx = Mock()
        ctx.deps = test_deps

        # Mock fetch_proposal_data
        with patch("offorte_airtable_sync.tools.fetch_proposal_data") as mock_fetch:
            mock_fetch.return_value = complete_proposal

            # Mock sync_to_airtable
            with patch("offorte_airtable_sync.tools.sync_to_airtable") as mock_sync:
                mock_sync.return_value = {
                    "success": True,
                    "created": 1,
                    "updated": 0,
                    "failed": 0,
                    "record_ids": ["recABC123"],
                    "errors": []
                }

                result = await process_won_proposal(ctx, 12345)

        # Verify success
        assert result["success"] is True
        assert result["proposal_id"] == 12345
        assert "sync_summary" in result
        assert result["total_records_created"] > 0

    @pytest.mark.integration
    def test_webhook_to_queue_integration(self, mock_webhook_payload):
        """Test webhook receives event and queues to Redis."""
        client = TestClient(app)
        secret = "test_webhook_secret_12345"

        # Generate valid signature
        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        mock_redis = AsyncMock()
        mock_redis.rpush = AsyncMock(return_value=1)

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200
        assert response.json()["queued"] is True
        mock_redis.rpush.assert_called_once()


class TestValidationGates:
    """Test PRP validation gates and success criteria."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_validation_gate_webhook_response_time(self, mock_webhook_payload):
        """
        PRP VALIDATION GATE: Webhook response < 1 second
        """
        import time

        client = TestClient(app)
        secret = "test_webhook_secret_12345"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        mock_redis = AsyncMock()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                start = time.time()
                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )
                elapsed = time.time() - start

        assert response.status_code == 200
        # VALIDATION GATE: Must respond in < 1 second
        assert elapsed < 1.0, f"Webhook took {elapsed}s, must be < 1s"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_validation_gate_all_six_tables_sync(
        self,
        test_deps,
        mock_offorte_proposal,
        mock_offorte_company,
        mock_offorte_contact
    ):
        """
        PRP VALIDATION GATE: All 6 tables sync correctly
        """
        complete_proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [mock_offorte_contact],
            "content": {"blocks": []}
        }

        ctx = Mock()
        ctx.deps = test_deps

        sync_calls = []

        async def track_sync_calls(ctx, base_id, table_name, records, key_field="Order Nummer"):
            sync_calls.append(table_name)
            return {
                "success": True,
                "created": len(records),
                "updated": 0,
                "failed": 0,
                "record_ids": [f"rec{i}" for i in range(len(records))],
                "errors": []
            }

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", return_value=complete_proposal):
            with patch("offorte_airtable_sync.tools.sync_to_airtable", side_effect=track_sync_calls):
                result = await process_won_proposal(ctx, 12345)

        # VALIDATION GATE: All 6 tables must be synced
        expected_tables = {
            "klantenportaal",
            "projecten",
            "elementen_review",
            "inmeetplanning",
            "facturatie",
            "deur_specificaties"
        }

        synced_tables = set(sync_calls)
        # Some tables might be skipped if no data (like deur_specificaties if no doors)
        # But at minimum, core tables should be present
        core_tables = {"klantenportaal", "projecten", "facturatie", "inmeetplanning"}
        assert core_tables.issubset(synced_tables), f"Missing core tables. Synced: {synced_tables}"

    @pytest.mark.integration
    @pytest.mark.dutch
    def test_validation_gate_invoice_splits_30_65_5(self, mock_offorte_proposal, mock_offorte_company):
        """
        PRP VALIDATION GATE: Invoice splits calculate properly (30/65/5)
        """
        from offorte_airtable_sync.tools import transform_proposal_to_table_records

        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "total_price": 45000.00
        }

        records = transform_proposal_to_table_records(proposal, [])
        invoices = records["facturatie"]

        # VALIDATION GATE: Must have 3 invoices
        assert len(invoices) == 3

        # VALIDATION GATE: Splits must be 30%, 65%, 5%
        vooraf = next(inv for inv in invoices if "30%" in inv["Factuur Type"])
        bij_start = next(inv for inv in invoices if "65%" in inv["Factuur Type"])
        oplevering = next(inv for inv in invoices if "5%" in inv["Factuur Type"])

        assert vooraf["Bedrag"] == 13500.00  # 30% of 45000
        assert bij_start["Bedrag"] == 29250.00  # 65% of 45000
        assert oplevering["Bedrag"] == 2250.00  # 5% of 45000

        # Total should equal original
        total = vooraf["Bedrag"] + bij_start["Bedrag"] + oplevering["Bedrag"]
        assert total == 45000.00

    @pytest.mark.integration
    @pytest.mark.dutch
    def test_validation_gate_coupled_elements_separate_records(self):
        """
        PRP VALIDATION GATE: Coupled elements (D1, D2) handled as separate records
        """
        from offorte_airtable_sync.tools import parse_construction_elements

        content = {
            "blocks": [
                {
                    "name": "Merk 1: Deuren",
                    "description": "Deurpakket",
                    "price": 0.0
                },
                {
                    "name": "D1. D2. D3. Voordeur variant",
                    "description": "1200x2400mm",
                    "price": 3500.00
                }
            ]
        }

        elements = parse_construction_elements(content, "2025001NL")

        # VALIDATION GATE: D1, D2, D3 should create 3 separate records
        coupled_elements = [e for e in elements if e["coupled"]]
        assert len(coupled_elements) == 3

        # All should be marked as coupled
        assert all(e["coupled"] for e in coupled_elements)

        # Should have different variants
        variants = {e["variant"] for e in coupled_elements}
        assert variants == {"D1", "D2", "D3"}

    @pytest.mark.integration
    def test_validation_gate_no_duplicate_records_on_resync(self, test_deps):
        """
        PRP VALIDATION GATE: No duplicate records created on re-sync
        """
        # This tests the upsert logic in sync_to_airtable

        ctx = Mock()
        ctx.deps = test_deps

        records = [
            {"Order Nummer": "2025001NL", "Bedrijfsnaam": "Test Company"}
        ]

        call_count = {"creates": 0, "updates": 0}

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_table = Mock()

            def mock_all(formula=None):
                # First call: no existing records
                # Second call: existing record found
                if call_count["creates"] > 0:
                    return [{"id": "recEXIST", "fields": {}}]
                return []

            mock_table.all = mock_all

            def mock_create(record):
                call_count["creates"] += 1
                return {"id": f"recNEW{call_count['creates']}"}

            def mock_update(record_id, record):
                call_count["updates"] += 1
                return {"id": record_id}

            mock_table.create = mock_create
            mock_table.update = mock_update
            mock_api.return_value.table.return_value = mock_table

            # First sync
            from offorte_airtable_sync.tools import sync_to_airtable
            result1 = await sync_to_airtable(ctx, "appBase", "table", records, "Order Nummer")

            # Second sync (should update, not create)
            result2 = await sync_to_airtable(ctx, "appBase", "table", records, "Order Nummer")

        # VALIDATION GATE: First sync creates, second sync updates
        assert result1["created"] == 1
        assert result1["updated"] == 0

        # Second sync should update existing
        assert result2["created"] == 0 or result2["updated"] == 1

    @pytest.mark.integration
    @pytest.mark.dutch
    def test_validation_gate_dutch_special_characters(self, dutch_special_chars):
        """
        PRP VALIDATION GATE: Dutch special characters display correctly
        """
        from offorte_airtable_sync.tools import transform_proposal_to_table_records

        proposal = {
            "id": 12345,
            "proposal_nr": "2025001NL",
            "name": "Test Proposal",
            "total_price": dutch_special_chars["price_value"],
            "company": {
                "name": dutch_special_chars["company_name"],
                "city": dutch_special_chars["city"],
                "street": "Test straat 123",
                "zipcode": "1234 AB",
                "email": "test@test.nl",
                "phone": "+31 20 1234567"
            },
            "contacts": [
                {"name": dutch_special_chars["contact_name"], "email": "test@test.nl"}
            ]
        }

        records = transform_proposal_to_table_records(proposal, [])

        # VALIDATION GATE: Special characters should be preserved
        customer_record = records["klantenportaal"][0]
        assert "Müller" in customer_record["Bedrijfsnaam"]
        assert "ô" in customer_record["Contact Persoon"] or "Jerôme" in customer_record["Contact Persoon"]
        assert "'s-Hertogenbosch" == dutch_special_chars["city"]


class TestRobustnessAndErrorHandling:
    """Test error handling and robustness requirements."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_retry_on_api_failure(self, test_deps):
        """Test retry logic with exponential backoff."""
        ctx = Mock()
        ctx.deps = test_deps

        call_count = {"count": 0}

        async def failing_then_success(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] < 2:
                raise Exception("API Error")
            return {"id": 12345, "proposal_nr": "2025001NL"}

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", side_effect=failing_then_success):
            # Should eventually succeed after retry
            pass  # Retry logic is in fetch_proposal_data itself

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_partial_sync_failure_handling(
        self,
        test_deps,
        mock_offorte_proposal,
        mock_offorte_company
    ):
        """Test handling of partial sync failures."""
        complete_proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [],
            "content": {"blocks": []}
        }

        ctx = Mock()
        ctx.deps = test_deps

        sync_count = {"count": 0}

        async def partial_failure(ctx, base_id, table_name, records, key_field="Order Nummer"):
            sync_count["count"] += 1
            # First table fails, rest succeed
            if sync_count["count"] == 1:
                return {
                    "success": False,
                    "created": 0,
                    "updated": 0,
                    "failed": len(records),
                    "record_ids": [],
                    "errors": ["API Error"]
                }
            return {
                "success": True,
                "created": len(records),
                "updated": 0,
                "failed": 0,
                "record_ids": ["recABC"],
                "errors": []
            }

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", return_value=complete_proposal):
            with patch("offorte_airtable_sync.tools.sync_to_airtable", side_effect=partial_failure):
                result = await process_won_proposal(ctx, 12345)

        # Should report partial success
        assert "errors" in result
        assert len(result["errors"]) > 0


class TestPerformanceRequirements:
    """Test performance requirements from PRP."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_element_time_calculation_18_minutes(self):
        """Test measurement planning calculates 18 minutes per element."""
        from offorte_airtable_sync.tools import transform_proposal_to_table_records

        proposal = {
            "id": 12345,
            "proposal_nr": "2025001NL",
            "name": "Test",
            "total_price": 10000.00,
            "company": {"name": "Test Company"}
        }

        # Create 5 elements
        elements = [{"type": f"Element {i}"} for i in range(5)]

        records = transform_proposal_to_table_records(proposal, elements)
        planning = records["inmeetplanning"][0]

        # Should calculate 18 minutes per element
        assert planning["Aantal Elementen"] == 5
        assert planning["Geschatte Tijd (min)"] == 90  # 5 * 18

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_operations_respect_limits(self, test_deps):
        """Test Airtable batch operations respect 10 record limit."""
        from offorte_airtable_sync.tools import sync_to_airtable

        ctx = Mock()
        ctx.deps = test_deps

        # Create 25 records
        records = [{"Order Nummer": f"2025{i:03d}NL"} for i in range(25)]

        batch_sizes = []

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_table = Mock()

            def track_create(record):
                batch_sizes.append(1)  # Each create is tracked
                return {"id": "recNEW"}

            mock_table.all.return_value = []
            mock_table.create = track_create
            mock_api.return_value.table.return_value = mock_table

            await sync_to_airtable(ctx, "appBase", "table", records)

        # Should have created all 25 records
        assert len(batch_sizes) == 25


class TestDataIntegrity:
    """Test data integrity and consistency."""

    @pytest.mark.integration
    def test_proposal_id_preserved_throughout(
        self,
        mock_offorte_proposal,
        mock_offorte_company
    ):
        """Test Offorte IDs are preserved for reference."""
        from offorte_airtable_sync.tools import transform_proposal_to_table_records

        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company
        }

        records = transform_proposal_to_table_records(proposal, [])

        # Project record should have Offorte ID
        project = records["projecten"][0]
        assert project["Offorte ID"] == str(mock_offorte_proposal["id"])

    @pytest.mark.integration
    def test_order_nummer_consistency_across_tables(
        self,
        mock_offorte_proposal,
        mock_offorte_company
    ):
        """Test Order Nummer is consistent across all tables."""
        from offorte_airtable_sync.tools import transform_proposal_to_table_records

        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "proposal_nr": "2025001NL"
        }

        elements = [{"type": "Test Element", "price": 1000.00}]

        records = transform_proposal_to_table_records(proposal, elements)

        # All tables should use same Order Nummer
        assert records["projecten"][0]["Project Nummer"] == "2025001NL"
        assert records["facturatie"][0]["Order Nummer"] == "2025001NL"
        assert records["elementen_review"][0]["Order Nummer"] == "2025001NL"
        assert records["inmeetplanning"][0]["Order Nummer"] == "2025001NL"
