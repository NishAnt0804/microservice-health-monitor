"""Unit tests for Notification Service."""

import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthCheck:
    """Tests for the /api/notifications/health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/api/notifications/health")
        assert response.status_code == 200

    def test_health_returns_correct_service_name(self, client):
        response = client.get("/api/notifications/health")
        data = response.get_json()
        assert data["service"] == "notification-service"
        assert data["status"] == "healthy"

    def test_health_contains_required_fields(self, client):
        response = client.get("/api/notifications/health")
        data = response.get_json()
        required_fields = ["service", "status", "version", "uptime_seconds", "timestamp", "checks"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestSendNotification:
    """Tests for the POST /api/notifications/send endpoint."""

    def test_send_notification_success(self, client):
        response = client.post(
            "/api/notifications/send",
            json={
                "recipient": "user@example.com",
                "message": "Test notification",
                "channel": "email",
            },
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "sent"
        assert data["channel"] == "email"

    def test_send_notification_default_channel(self, client):
        response = client.post(
            "/api/notifications/send",
            json={"recipient": "user@example.com", "message": "Test"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["channel"] == "email"

    def test_send_notification_missing_fields(self, client):
        response = client.post(
            "/api/notifications/send",
            json={"recipient": "user@example.com"},
        )
        assert response.status_code == 400

    def test_send_notification_invalid_channel(self, client):
        response = client.post(
            "/api/notifications/send",
            json={
                "recipient": "user@example.com",
                "message": "Test",
                "channel": "pigeon",
            },
        )
        assert response.status_code == 400


class TestListNotifications:
    """Tests for the GET /api/notifications endpoint."""

    def test_list_notifications_returns_200(self, client):
        response = client.get("/api/notifications")
        assert response.status_code == 200
        data = response.get_json()
        assert "notifications" in data


class TestNotificationStats:
    """Tests for the GET /api/notifications/stats endpoint."""

    def test_stats_returns_200(self, client):
        response = client.get("/api/notifications/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_sent" in data
        assert "by_channel" in data
        assert "by_priority" in data


class TestRequestTracing:
    """Tests for request ID middleware."""

    def test_response_contains_request_id(self, client):
        response = client.get("/api/notifications/health")
        assert "X-Request-ID" in response.headers

    def test_custom_request_id_is_preserved(self, client):
        custom_id = "notif-trace-67890"
        response = client.get(
            "/api/notifications/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["X-Request-ID"] == custom_id
