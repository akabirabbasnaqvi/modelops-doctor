from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint_returns_welcome_message() -> None:
    response = client.get("/")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data == {
        "message": "Welcome to ModelOps Doctor",
        "documentation": "/docs",
        "health": "/api/v1/health",
    }


def test_health_endpoint_returns_healthy_status() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200

    response_data = response.json()

    assert response_data["status"] == "healthy"
    assert response_data["service"] == "modelops-doctor-api"
    assert response_data["version"] == "0.1.0"
    assert response_data["environment"] == "development"
    assert "timestamp" in response_data


def test_old_health_endpoint_does_not_exist() -> None:
    response = client.get("/health")

    assert response.status_code == 404
