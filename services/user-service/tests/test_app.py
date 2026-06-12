"""Unit tests for User Service."""

import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestHealthCheck:
    """Tests for the /api/users/health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/api/users/health")
        assert response.status_code == 200

    def test_health_returns_correct_service_name(self, client):
        response = client.get("/api/users/health")
        data = response.get_json()
        assert data["service"] == "user-service"
        assert data["status"] == "healthy"

    def test_health_contains_required_fields(self, client):
        response = client.get("/api/users/health")
        data = response.get_json()
        required_fields = ["service", "status", "version", "uptime_seconds", "timestamp", "checks"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestListUsers:
    """Tests for the GET /api/users endpoint."""

    def test_list_users_returns_200(self, client):
        response = client.get("/api/users")
        assert response.status_code == 200

    def test_list_users_returns_all_users(self, client):
        response = client.get("/api/users")
        data = response.get_json()
        assert data["count"] >= 5

    def test_list_users_filter_by_role(self, client):
        response = client.get("/api/users?role=admin")
        data = response.get_json()
        assert all(u["role"] == "admin" for u in data["users"])


class TestGetUser:
    """Tests for the GET /api/users/<id> endpoint."""

    def test_get_existing_user(self, client):
        response = client.get("/api/users/1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "1"

    def test_get_nonexistent_user(self, client):
        response = client.get("/api/users/999")
        assert response.status_code == 404


class TestCreateUser:
    """Tests for the POST /api/users endpoint."""

    def test_create_user_success(self, client):
        response = client.post(
            "/api/users",
            json={"name": "Test User", "email": "test@example.com"},
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == "Test User"

    def test_create_user_missing_fields(self, client):
        response = client.post("/api/users", json={"name": "Only Name"})
        assert response.status_code == 400


class TestRequestTracing:
    """Tests for request ID middleware."""

    def test_response_contains_request_id(self, client):
        response = client.get("/api/users/health")
        assert "X-Request-ID" in response.headers

    def test_custom_request_id_is_preserved(self, client):
        custom_id = "test-trace-12345"
        response = client.get(
            "/api/users/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers["X-Request-ID"] == custom_id
