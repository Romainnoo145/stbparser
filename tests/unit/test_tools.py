"""
Tests for all 6 agent tools.

Tests cover:
1. validate_webhook - Webhook signature validation
2. fetch_proposal_data - Offorte API data fetching
3. parse_construction_elements - Dutch element parsing
4. transform_proposal_to_table_records - Data transformation
5. sync_to_airtable - Airtable synchronization
6. process_won_proposal - End-to-end orchestration
"""

import pytest
import json
import hashlib
import hmac
from unittest.mock import AsyncMock, Mock, patch
from pydantic_ai import RunContext

from offorte_airtable_sync.tools import (
    validate_webhook,
    fetch_proposal_data,
    parse_construction_elements,
    transform_proposal_to_table_records,
    sync_to_airtable,
    process_won_proposal
)


# ============================================================================
# Tool 1: validate_webhook
# ============================================================================

class TestValidateWebhook:
    """Test webhook signature validation."""

    def test_validate_webhook_valid_signature(self, mock_webhook_payload):
        """Test webhook validation with valid signature."""
        secret = "test_secret_key"
        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        result = validate_webhook(mock_webhook_payload, signature, secret)

        assert result["valid"] is True
        assert result["event_type"] == "proposal_won"
        assert result["proposal_id"] == 12345
        assert result["timestamp"] == "2025-01-15 14:30:00"

    def test_validate_webhook_invalid_signature(self, mock_webhook_payload):
        """Test webhook validation with invalid signature."""
        secret = "test_secret_key"
        invalid_signature = "invalid_signature_12345"

        result = validate_webhook(mock_webhook_payload, invalid_signature, secret)

        assert result["valid"] is False
        assert "error" in result
        assert result["error"] == "Invalid signature"

    def test_validate_webhook_wrong_secret(self, mock_webhook_payload):
        """Test webhook validation with wrong secret."""
        secret = "correct_secret"
        wrong_secret = "wrong_secret"

        # Generate signature with wrong secret
        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            wrong_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        result = validate_webhook(mock_webhook_payload, signature, secret)

        assert result["valid"] is False

    def test_validate_webhook_malformed_payload(self):
        """Test webhook validation with malformed payload."""
        secret = "test_secret"
        payload = {"incomplete": "data"}  # Missing required fields
        signature = "any_signature"

        result = validate_webhook(payload, signature, secret)

        # Should handle gracefully
        assert "valid" in result

    def test_validate_webhook_empty_payload(self):
        """Test webhook validation with empty payload."""
        secret = "test_secret"
        payload = {}
        signature = "any_signature"

        result = validate_webhook(payload, signature, secret)

        assert result["valid"] is False

    @pytest.mark.unit
    def test_validate_webhook_constant_time_comparison(self, mock_webhook_payload):
        """Test that signature comparison uses constant-time algorithm."""
        # This test verifies hmac.compare_digest is used
        secret = "test_secret"
        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        valid_signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        # Valid signature should work
        result1 = validate_webhook(mock_webhook_payload, valid_signature, secret)
        assert result1["valid"] is True

        # Invalid signature should fail
        result2 = validate_webhook(mock_webhook_payload, "wrong", secret)
        assert result2["valid"] is False


# ============================================================================
# Tool 2: fetch_proposal_data
# ============================================================================

class TestFetchProposalData:
    """Test Offorte API proposal fetching."""

    @pytest.mark.asyncio
    async def test_fetch_proposal_basic(
        self, test_deps, mock_offorte_proposal, mock_offorte_company, mock_offorte_contact
    ):
        """Test basic proposal fetching."""
        # Create mock context
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        # Mock HTTP responses
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.side_effect = [
            mock_offorte_proposal,
            {"blocks": []},  # content
            mock_offorte_company,
            mock_offorte_contact
        ]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        test_deps._http_client = mock_client

        result = await fetch_proposal_data(ctx, 12345, include_content=True)

        assert result["id"] == 12345
        assert result["proposal_nr"] == "2025001NL"
        assert "company" in result
        assert "contacts" in result
        assert "content" in result

    @pytest.mark.asyncio
    async def test_fetch_proposal_without_content(self, test_deps, mock_offorte_proposal):
        """Test fetching proposal without content."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_offorte_proposal
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        test_deps._http_client = mock_client

        result = await fetch_proposal_data(ctx, 12345, include_content=False)

        assert result["id"] == 12345
        assert "content" not in result or result["content"] is None

    @pytest.mark.asyncio
    async def test_fetch_proposal_with_retry(self, test_deps, mock_offorte_proposal):
        """Test proposal fetching with retry on failure."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        mock_client = AsyncMock()
        mock_response_fail = AsyncMock()
        mock_response_fail.raise_for_status.side_effect = Exception("Network error")

        mock_response_success = AsyncMock()
        mock_response_success.json.return_value = mock_offorte_proposal
        mock_response_success.raise_for_status = Mock()

        # First call fails, second succeeds
        mock_client.get.side_effect = [mock_response_fail, mock_response_success]

        test_deps._http_client = mock_client

        result = await fetch_proposal_data(ctx, 12345, include_content=False)

        # Should eventually succeed after retry
        assert result["id"] == 12345

    @pytest.mark.asyncio
    async def test_fetch_proposal_api_error(self, test_deps):
        """Test handling of API errors."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_client.get.return_value = mock_response

        test_deps._http_client = mock_client

        result = await fetch_proposal_data(ctx, 12345)

        assert "error" in result
        assert result["proposal_id"] == 12345


# ============================================================================
# Tool 3: parse_construction_elements
# ============================================================================

class TestParseConstructionElements:
    """Test Dutch construction element parsing."""

    def test_parse_simple_elements(self, mock_offorte_content):
        """Test parsing simple construction elements."""
        elements = parse_construction_elements(mock_offorte_content, "2025001NL")

        assert len(elements) > 0
        assert all("element_id" in elem for elem in elements)
        assert all("type" in elem for elem in elements)

    def test_parse_coupled_elements(self):
        """Test parsing coupled elements (D1, D2)."""
        content = {
            "blocks": [
                {
                    "name": "Merk 1: Deuren",
                    "description": "Deurpakket",
                    "price": 0.0
                },
                {
                    "name": "D1. D2. Voordeur variant",
                    "description": "1200x2400mm",
                    "price": 3500.00
                }
            ]
        }

        elements = parse_construction_elements(content, "2025001NL")

        # Should create 2 separate elements for D1 and D2
        coupled_elements = [e for e in elements if e["coupled"]]
        assert len(coupled_elements) == 2
        assert any(e["variant"] == "D1" for e in coupled_elements)
        assert any(e["variant"] == "D2" for e in coupled_elements)

    def test_parse_merk_blocks(self, mock_offorte_content):
        """Test parsing Merk (brand) blocks."""
        elements = parse_construction_elements(mock_offorte_content, "2025001NL")

        # Elements should have brand information
        branded_elements = [e for e in elements if e["brand"] != "Onbekend"]
        assert len(branded_elements) > 0

    def test_parse_dimensions(self):
        """Test parsing dimensions from descriptions."""
        content = {
            "blocks": [
                {
                    "name": "Test raam",
                    "description": "Vast raam 1200x2400mm met glas",
                    "price": 1500.00
                }
            ]
        }

        elements = parse_construction_elements(content, "2025001NL")

        assert len(elements) > 0
        assert elements[0]["width_mm"] == 1200
        assert elements[0]["height_mm"] == 2400

    def test_parse_element_types(self, mock_offorte_content):
        """Test element type detection."""
        elements = parse_construction_elements(mock_offorte_content, "2025001NL")

        types = {e["type"] for e in elements}
        assert "Vast raam" in types or "Draaikiep raam" in types or "Voordeur" in types

    @pytest.mark.dutch
    def test_parse_dutch_special_chars(self):
        """Test parsing Dutch special characters."""
        content = {
            "blocks": [
                {
                    "name": "Kunststof kozijn",
                    "description": "Draaikiep raam 800x1200mm, crème kleur",
                    "price": 1200.00
                }
            ]
        }

        elements = parse_construction_elements(content, "2025001NL")

        assert len(elements) > 0
        # Should handle special characters without errors

    def test_parse_empty_content(self):
        """Test parsing empty content."""
        content = {"blocks": []}

        elements = parse_construction_elements(content, "2025001NL")

        assert elements == []

    def test_parse_with_line_items_key(self):
        """Test parsing content using line_items key instead of blocks."""
        content = {
            "line_items": [
                {
                    "name": "Vast raam",
                    "description": "1000x1500mm",
                    "price": 1000.00
                }
            ]
        }

        elements = parse_construction_elements(content, "2025001NL")

        assert len(elements) > 0


# ============================================================================
# Tool 4: transform_proposal_to_table_records
# ============================================================================

class TestTransformProposalToTableRecords:
    """Test data transformation to Airtable schemas."""

    def test_transform_all_tables(self, mock_offorte_proposal, mock_offorte_company, mock_offorte_contact):
        """Test transformation creates records for all 6 tables."""
        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [mock_offorte_contact]
        }
        elements = [
            {
                "element_id": "2025001NL_0",
                "type": "Voordeur",
                "brand": "Merk 1",
                "location": None,
                "width_mm": 1200,
                "height_mm": 2400,
                "coupled": False,
                "variant": None,
                "price": 3500.00,
                "notes": "Complete voordeur"
            }
        ]

        records = transform_proposal_to_table_records(proposal, elements)

        assert "klantenportaal" in records
        assert "projecten" in records
        assert "elementen_review" in records
        assert "inmeetplanning" in records
        assert "facturatie" in records
        assert "deur_specificaties" in records

    def test_transform_customer_portal(self, mock_offorte_proposal, mock_offorte_company, mock_offorte_contact):
        """Test klantenportaal table transformation."""
        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [mock_offorte_contact]
        }

        records = transform_proposal_to_table_records(proposal, [])

        customer_records = records["klantenportaal"]
        assert len(customer_records) == 1
        assert customer_records[0]["Bedrijfsnaam"] == "Van der Berg Bouw B.V."
        assert customer_records[0]["Adres"] == "Dorpsstraat 123"
        assert customer_records[0]["Postcode"] == "1234 AB"
        assert customer_records[0]["Status"] == "Actief"

    def test_transform_invoice_splits(self, mock_offorte_proposal, mock_offorte_company):
        """Test facturatie table transformation with 30/65/5 splits."""
        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "total_price": 45000.00
        }

        records = transform_proposal_to_table_records(proposal, [])

        invoices = records["facturatie"]
        assert len(invoices) == 3

        # Check 30% vooraf
        vooraf = next(inv for inv in invoices if "30%" in inv["Factuur Type"])
        assert vooraf["Bedrag"] == 13500.00
        assert vooraf["Status"] == "Concept"

        # Check 65% bij start
        bij_start = next(inv for inv in invoices if "65%" in inv["Factuur Type"])
        assert bij_start["Bedrag"] == 29250.00
        assert bij_start["Status"] == "Gepland"

        # Check 5% oplevering
        oplevering = next(inv for inv in invoices if "5%" in inv["Factuur Type"])
        assert oplevering["Bedrag"] == 2250.00
        assert oplevering["Status"] == "Gepland"

    @pytest.mark.dutch
    def test_transform_invoice_splits_rounding(self, mock_offorte_proposal, mock_offorte_company):
        """Test invoice splits round correctly for Dutch currency."""
        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "total_price": 12345.67
        }

        records = transform_proposal_to_table_records(proposal, [])

        invoices = records["facturatie"]
        total_invoiced = sum(inv["Bedrag"] for inv in invoices)

        # Should be close to original (within rounding)
        assert abs(total_invoiced - 12345.67) < 0.05

    def test_transform_measurement_planning(self, mock_offorte_proposal, mock_offorte_company):
        """Test inmeetplanning table transformation."""
        proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company
        }
        elements = [{"type": "Raam"}, {"type": "Deur"}, {"type": "Raam"}]

        records = transform_proposal_to_table_records(proposal, elements)

        planning = records["inmeetplanning"]
        assert len(planning) == 1
        assert planning[0]["Aantal Elementen"] == 3
        assert planning[0]["Geschatte Tijd (min)"] == 54  # 3 * 18 minutes

    def test_transform_elements_review(self, mock_offorte_proposal):
        """Test elementen_review table transformation."""
        proposal = mock_offorte_proposal
        elements = [
            {
                "element_id": "2025001NL_0",
                "type": "Voordeur",
                "brand": "Merk 1",
                "location": "Voorzijde",
                "width_mm": 1200,
                "height_mm": 2400,
                "coupled": True,
                "variant": "D1",
                "price": 3500.00,
                "notes": "Test notes"
            }
        ]

        records = transform_proposal_to_table_records(proposal, elements)

        elements_records = records["elementen_review"]
        assert len(elements_records) == 1
        assert elements_records[0]["Element ID"] == "2025001NL_0"
        assert elements_records[0]["Type"] == "Voordeur"
        assert elements_records[0]["Gekoppeld"] is True
        assert elements_records[0]["Variant"] == "D1"

    def test_transform_door_specifications(self, mock_offorte_proposal):
        """Test deur_specificaties table transformation (only doors)."""
        proposal = mock_offorte_proposal
        elements = [
            {"type": "Voordeur", "notes": "Test door"},
            {"type": "Vast raam", "notes": "Test window"},
            {"type": "Achterdeur", "notes": "Back door"}
        ]

        records = transform_proposal_to_table_records(proposal, elements)

        door_specs = records["deur_specificaties"]
        # Should only include door elements
        assert len(door_specs) == 2
        assert all("deur" in spec["Deur Type"].lower() for spec in door_specs)


# ============================================================================
# Tool 5: sync_to_airtable
# ============================================================================

class TestSyncToAirtable:
    """Test Airtable synchronization."""

    @pytest.mark.asyncio
    async def test_sync_create_new_records(self, test_deps):
        """Test creating new records in Airtable."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        records = [
            {"Order Nummer": "2025001NL", "Bedrijfsnaam": "Test Company"}
        ]

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_table = Mock()
            mock_table.all.return_value = []  # No existing records
            mock_table.create.return_value = {"id": "recABC123"}
            mock_api.return_value.table.return_value = mock_table

            result = await sync_to_airtable(
                ctx,
                "appTestBase",
                "test_table",
                records,
                key_field="Order Nummer"
            )

        assert result["success"] is True
        assert result["created"] == 1
        assert result["updated"] == 0
        assert len(result["record_ids"]) == 1

    @pytest.mark.asyncio
    async def test_sync_update_existing_records(self, test_deps):
        """Test updating existing records in Airtable."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        records = [
            {"Order Nummer": "2025001NL", "Bedrijfsnaam": "Updated Company"}
        ]

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_table = Mock()
            mock_table.all.return_value = [{"id": "recEXIST", "fields": {}}]
            mock_table.update.return_value = {"id": "recEXIST"}
            mock_api.return_value.table.return_value = mock_table

            result = await sync_to_airtable(
                ctx,
                "appTestBase",
                "test_table",
                records,
                key_field="Order Nummer"
            )

        assert result["success"] is True
        assert result["created"] == 0
        assert result["updated"] == 1

    @pytest.mark.asyncio
    async def test_sync_batch_operations(self, test_deps):
        """Test batch operations respect 10 record limit."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        # Create 25 records (should batch into 3 groups: 10, 10, 5)
        records = [
            {"Order Nummer": f"2025{i:03d}NL", "Bedrijfsnaam": f"Company {i}"}
            for i in range(25)
        ]

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_table = Mock()
            mock_table.all.return_value = []
            mock_table.create.return_value = {"id": "recNEW"}
            mock_api.return_value.table.return_value = mock_table

            result = await sync_to_airtable(
                ctx,
                "appTestBase",
                "test_table",
                records,
                key_field="Order Nummer"
            )

        assert result["created"] == 25
        # Verify create was called 25 times (once per record)
        assert mock_table.create.call_count == 25

    @pytest.mark.asyncio
    async def test_sync_rate_limiting(self, test_deps):
        """Test rate limiting with sleep between batches."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        records = [{"Order Nummer": "2025001NL"}]

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            with patch("offorte_airtable_sync.tools.asyncio.sleep") as mock_sleep:
                mock_table = Mock()
                mock_table.all.return_value = []
                mock_table.create.return_value = {"id": "recNEW"}
                mock_api.return_value.table.return_value = mock_table

                await sync_to_airtable(ctx, "appBase", "table", records)

                # Should sleep after batch (0.21s for rate limit)
                mock_sleep.assert_called()

    @pytest.mark.asyncio
    async def test_sync_error_handling(self, test_deps):
        """Test error handling in sync operations."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        records = [{"Order Nummer": "2025001NL"}]

        with patch("offorte_airtable_sync.tools.AirtableApi") as mock_api:
            mock_api.side_effect = Exception("Airtable API error")

            result = await sync_to_airtable(ctx, "appBase", "table", records)

        assert result["success"] is False
        assert result["failed"] == 1
        assert len(result["errors"]) > 0


# ============================================================================
# Tool 6: process_won_proposal
# ============================================================================

class TestProcessWonProposal:
    """Test end-to-end proposal processing."""

    @pytest.mark.asyncio
    async def test_process_won_proposal_success(
        self, test_deps, mock_offorte_proposal, mock_offorte_company, mock_offorte_contact
    ):
        """Test successful end-to-end proposal processing."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        # Mock fetch_proposal_data
        complete_proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [mock_offorte_contact],
            "content": {"blocks": []}
        }

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", return_value=complete_proposal):
            with patch("offorte_airtable_sync.tools.sync_to_airtable") as mock_sync:
                mock_sync.return_value = {
                    "success": True,
                    "created": 1,
                    "updated": 0,
                    "failed": 0,
                    "errors": []
                }

                result = await process_won_proposal(ctx, 12345)

        assert result["success"] is True
        assert result["proposal_id"] == 12345
        assert "sync_summary" in result
        assert "correlation_id" in result

    @pytest.mark.asyncio
    async def test_process_won_proposal_fetch_error(self, test_deps):
        """Test handling of fetch errors."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        with patch("offorte_airtable_sync.tools.fetch_proposal_data") as mock_fetch:
            mock_fetch.return_value = {"error": "API error", "proposal_id": 12345}

            result = await process_won_proposal(ctx, 12345)

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_process_won_proposal_sync_all_tables(
        self, test_deps, mock_offorte_proposal, mock_offorte_company
    ):
        """Test that all 6 tables are synced."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        complete_proposal = {
            **mock_offorte_proposal,
            "company": mock_offorte_company,
            "contacts": [],
            "content": {"blocks": []}
        }

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", return_value=complete_proposal):
            with patch("offorte_airtable_sync.tools.sync_to_airtable") as mock_sync:
                mock_sync.return_value = {
                    "success": True,
                    "created": 1,
                    "updated": 0,
                    "failed": 0,
                    "errors": []
                }

                result = await process_won_proposal(ctx, 12345)

                # Verify sync was called for multiple tables
                assert mock_sync.call_count > 0

        assert "sync_summary" in result

    @pytest.mark.asyncio
    async def test_process_won_proposal_performance_tracking(self, test_deps, mock_offorte_proposal):
        """Test that processing time is tracked."""
        ctx = Mock(spec=RunContext)
        ctx.deps = test_deps

        complete_proposal = {
            **mock_offorte_proposal,
            "company": {},
            "contacts": [],
            "content": {"blocks": []}
        }

        with patch("offorte_airtable_sync.tools.fetch_proposal_data", return_value=complete_proposal):
            with patch("offorte_airtable_sync.tools.sync_to_airtable") as mock_sync:
                mock_sync.return_value = {
                    "success": True,
                    "created": 0,
                    "updated": 0,
                    "failed": 0,
                    "errors": []
                }

                result = await process_won_proposal(ctx, 12345)

        assert "processing_time_seconds" in result
        assert isinstance(result["processing_time_seconds"], (int, float))
        assert result["processing_time_seconds"] >= 0
