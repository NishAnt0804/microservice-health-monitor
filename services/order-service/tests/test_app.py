"""Unit tests for Order Service."""

import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthCheck:
    """Tests for the /api/orders/health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/api/orders/health")
        assert response.status_code == 200

    def test_health_returns_correct_service_name(self, client):
        response = client.get("/api/orders/health")
        data = response.get_json()
        assert data["service"] == "order-service"
        assert data["status"] == "healthy"

    def test_health_contains_required_fields(self, client):
        response = client.get("/api/orders/health")
        data = response.get_json()
        required_fields = ["service", "status", "version", "uptime_seconds", "timestamp", "checks"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestListOrders:
    """Tests for the GET /api/orders endpoint."""

    def test_list_orders_returns_200(self, client):
        response = client.get("/api/orders")
        assert response.status_code == 200

    def test_list_orders_returns_data(self, client):
        response = client.get("/api/orders")
        data = response.get_json()
        assert data["count"] >= 3

    def test_list_orders_filter_by_user(self, client):
        response = client.get("/api/orders?user_id=1")
        data = response.get_json()
        assert all(o["user_id"] == "1" for o in data["orders"])


class TestGetOrder:
    """Tests for the GET /api/orders/<id> endpoint."""

    def test_get_existing_order(self, client):
        response = client.get("/api/orders/101")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "101"

    def test_get_nonexistent_order(self, client):
        response = client.get("/api/orders/999")
        assert response.status_code == 404


class TestCreateOrder:
    """Tests for the POST /api/orders endpoint."""

    def test_create_order_success(self, client):
        response = client.post(
            "/api/orders",
            json={"user_id": "1", "product": "Test Product", "price": 9.99},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["product"] == "Test Product"
        assert data["status"] == "pending"

    def test_create_order_missing_fields(self, client):
        response = client.post("/api/orders", json={"user_id": "1"})
        assert response.status_code == 400


class TestUpdateOrderStatus:
    """Tests for the PATCH /api/orders/<id>/status endpoint."""

    def test_update_status_success(self, client):
        response = client.patch(
            "/api/orders/101/status",
            json={"status": "shipped"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "shipped"

    def test_update_status_invalid(self, client):
        response = client.patch(
            "/api/orders/101/status",
            json={"status": "invalid_status"},
        )
        assert response.status_code == 400

    def test_update_status_not_found(self, client):
        response = client.patch(
            "/api/orders/999/status",
            json={"status": "shipped"},
        )
        assert response.status_code == 404
