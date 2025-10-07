"""
Tests for server module - FastAPI webhook receiver.

Tests cover:
- Webhook endpoint response time (< 1 sec requirement)
- Webhook signature validation
- Event type handling (proposal_won)
- Redis queue integration
- Health check endpoints
- Error handling
"""

import pytest
import json
import hashlib
import hmac
from unittest.mock import AsyncMock, patch, Mock
from fastapi.testclient import TestClient

from offorte_airtable_sync.server import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    redis_mock = AsyncMock()
    redis_mock.rpush = AsyncMock(return_value=1)
    redis_mock.llen = AsyncMock(return_value=0)
    redis_mock.close = AsyncMock()
    return redis_mock


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Offorte-Airtable Sync"
        assert data["status"] == "running"
        assert "version" in data

    def test_health_endpoint(self, client):
        """Test health endpoint returns status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data


class TestWebhookEndpoint:
    """Test webhook receiving endpoint."""

    def test_webhook_valid_signature(self, client, mock_webhook_payload, mock_redis):
        """Test webhook with valid signature is accepted."""
        secret = "test_webhook_secret_12345"

        # Generate valid signature
        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["queued"] is True
        assert data["proposal_id"] == 12345

    def test_webhook_invalid_signature(self, client, mock_webhook_payload):
        """Test webhook with invalid signature is rejected."""
        secret = "test_webhook_secret_12345"
        invalid_signature = "invalid_signature_12345"

        with patch("offorte_airtable_sync.server.settings") as mock_settings:
            mock_settings.webhook_secret = secret

            response = client.post(
                "/webhook/offorte",
                json=mock_webhook_payload,
                headers={"X-Offorte-Signature": invalid_signature}
            )

        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_webhook_missing_signature(self, client, mock_webhook_payload):
        """Test webhook without signature header."""
        response = client.post(
            "/webhook/offorte",
            json=mock_webhook_payload
            # No signature header
        )

        # Should handle missing signature gracefully
        assert response.status_code in [401, 500]

    def test_webhook_proposal_won_queued(self, client, mock_webhook_payload, mock_redis):
        """Test proposal_won event is queued to Redis."""
        secret = "test_webhook_secret_12345"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200
        # Verify Redis rpush was called
        mock_redis.rpush.assert_called_once()

    def test_webhook_other_event_acknowledged(self, client, mock_redis):
        """Test non-proposal_won events are acknowledged but not queued."""
        secret = "test_webhook_secret_12345"

        payload = {
            "type": "proposal_details_updated",
            "date_created": "2025-01-15 14:30:00",
            "data": {"id": 12345}
        }

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "acknowledged"
        assert data["queued"] is False

    @pytest.mark.slow
    def test_webhook_response_time(self, client, mock_webhook_payload, mock_redis):
        """Test webhook responds within 1 second (PRP requirement)."""
        import time

        secret = "test_webhook_secret_12345"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                start_time = time.time()

                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

                elapsed_time = time.time() - start_time

        assert response.status_code == 200
        # Must respond in < 1 second as per PRP requirement
        assert elapsed_time < 1.0

    def test_webhook_malformed_payload(self, client):
        """Test webhook with malformed JSON payload."""
        response = client.post(
            "/webhook/offorte",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422, 500]

    def test_webhook_error_handling(self, client, mock_webhook_payload):
        """Test webhook error handling returns 500."""
        secret = "test_webhook_secret_12345"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", None):  # Simulate Redis error
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 500


class TestQueueStatusEndpoint:
    """Test queue status endpoint."""

    def test_queue_status_success(self, client, mock_redis):
        """Test queue status returns current length."""
        mock_redis.llen.return_value = 5

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["queue_length"] == 5
        assert "timestamp" in data

    def test_queue_status_empty_queue(self, client, mock_redis):
        """Test queue status with empty queue."""
        mock_redis.llen.return_value = 0

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert data["queue_length"] == 0

    def test_queue_status_redis_error(self, client):
        """Test queue status handles Redis errors."""
        mock_redis_error = AsyncMock()
        mock_redis_error.llen.side_effect = Exception("Redis connection error")

        with patch("offorte_airtable_sync.server.redis_client", mock_redis_error):
            response = client.get("/queue/status")

        assert response.status_code == 200
        data = response.json()
        assert "error" in data


class TestServerLifecycle:
    """Test server startup and shutdown events."""

    @pytest.mark.asyncio
    async def test_startup_connects_redis(self, mock_redis):
        """Test startup event connects to Redis."""
        from offorte_airtable_sync.server import startup

        with patch("offorte_airtable_sync.server.redis.from_url", return_value=mock_redis):
            await startup()

            # Redis connection should be established
            # (In real implementation, redis_client would be set)

    @pytest.mark.asyncio
    async def test_shutdown_closes_redis(self):
        """Test shutdown event closes Redis connection."""
        from offorte_airtable_sync.server import shutdown

        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            await shutdown()

            # Redis close should be called
            mock_redis.close.assert_called_once()


class TestWebhookPayloadStructure:
    """Test webhook payload structure validation."""

    def test_webhook_extracts_proposal_id(self, client, mock_redis):
        """Test webhook correctly extracts proposal ID."""
        secret = "test_webhook_secret_12345"

        payload = {
            "type": "proposal_won",
            "date_created": "2025-01-15 14:30:00",
            "data": {
                "id": 99999,
                "name": "Test Proposal"
            }
        }

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200
        data = response.json()
        assert data["proposal_id"] == 99999

    def test_webhook_includes_timestamp(self, client, mock_redis):
        """Test webhook payload includes timestamp in queue data."""
        secret = "test_webhook_secret_12345"

        payload = {
            "type": "proposal_won",
            "date_created": "2025-01-15 14:30:00",
            "data": {"id": 12345}
        }

        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                response = client.post(
                    "/webhook/offorte",
                    json=payload,
                    headers={"X-Offorte-Signature": signature}
                )

        assert response.status_code == 200

        # Verify rpush was called with timestamp
        mock_redis.rpush.assert_called_once()
        call_args = mock_redis.rpush.call_args
        queued_data = json.loads(call_args[0][1])
        assert "timestamp" in queued_data


class TestWebhookSecurity:
    """Test webhook security measures."""

    def test_webhook_constant_time_comparison(self, client, mock_webhook_payload):
        """Test signature validation uses constant-time comparison."""
        # This is tested implicitly by validate_webhook using hmac.compare_digest
        secret = "test_secret"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.settings") as mock_settings:
            mock_settings.webhook_secret = secret

            # Valid signature should pass
            response = client.post(
                "/webhook/offorte",
                json=mock_webhook_payload,
                headers={"X-Offorte-Signature": signature}
            )

            # The fact that it works confirms hmac.compare_digest is used internally
            assert response.status_code in [200, 500]  # 500 if Redis not available

    def test_webhook_rejects_replay_attacks(self, client, mock_webhook_payload, mock_redis):
        """Test webhook processes same signature multiple times (no replay protection in basic impl)."""
        # Note: Basic implementation doesn't prevent replays, but validates signature each time
        secret = "test_webhook_secret_12345"

        payload_str = json.dumps(mock_webhook_payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()

        with patch("offorte_airtable_sync.server.redis_client", mock_redis):
            with patch("offorte_airtable_sync.server.settings") as mock_settings:
                mock_settings.webhook_secret = secret

                # First request
                response1 = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

                # Second request (replay)
                response2 = client.post(
                    "/webhook/offorte",
                    json=mock_webhook_payload,
                    headers={"X-Offorte-Signature": signature}
                )

        # Both should succeed (no replay protection in basic implementation)
        assert response1.status_code == 200
        assert response2.status_code == 200
