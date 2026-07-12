from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to ModelOps Doctor",
        "documentation": "/docs",
        "health": "/api/v1/health",
    }


def test_health_endpoint() -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "X-Request-ID": "test-request-id",
        },
    )

    response_data = response.json()

    assert response.status_code == 200
    assert response_data["status"] == "healthy"
    assert response_data["service"] == "modelops-doctor-api"
    assert response_data["version"] == "0.1.0"
    assert "timestamp" in response_data

    assert response.headers["X-Request-ID"] == ("test-request-id")
    assert "X-Process-Time-MS" in response.headers


def test_unknown_endpoint_returns_404() -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
