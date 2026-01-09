"""
Tests for the Admin Control Plane API server.

This test suite covers:
- Health check endpoints (success/failure)
- Queue statistics (with/without metrics enabled)
- Lifecycle management (drain, reload)
- Error handling and status codes
"""
import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from types import SimpleNamespace
from vllm.entrypoints.admin_server import build_admin_app

@pytest.fixture
def mock_engine_client():
    client = AsyncMock()
    # Setup default behaviors
    client.check_health = AsyncMock(return_value=None)
    client.pause_generation = AsyncMock(return_value=None)
    return client

@pytest.fixture
def mock_app_state(mock_engine_client):
    state = SimpleNamespace()
    state.engine_client = mock_engine_client
    # Simulate disabled metrics by default
    # state.server_load_metrics = ... 
    return state

@pytest.fixture
def admin_client(mock_app_state):
    args = SimpleNamespace(
        disable_fastapi_docs=False,
    )
    app = build_admin_app(args)
    # Inject mock state
    app.state = mock_app_state
    return TestClient(app)

def test_health_endpoint(admin_client, mock_engine_client):
    response = admin_client.get("/v1/admin/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    mock_engine_client.check_health.assert_awaited_once()

def test_health_endpoint_failure(admin_client, mock_engine_client):
    mock_engine_client.check_health.side_effect = Exception("Engine died")
    response = admin_client.get("/v1/admin/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unhealthy"

def test_queue_stats_endpoint_no_metrics(admin_client):
    response = admin_client.get("/v1/admin/queue")
    assert response.status_code == 200
    assert "not currently tracked" in response.json()["detail"]

def test_queue_stats_endpoint_with_metrics(admin_client, mock_app_state):
    # Inject metrics
    mock_app_state.server_load_metrics = {"some_metric": 123}
    response = admin_client.get("/v1/admin/queue")
    assert response.status_code == 200
    assert response.json() == {"server_load": {"some_metric": 123}}

def test_drain_endpoint(admin_client, mock_engine_client):
    response = admin_client.post("/v1/admin/drain")
    assert response.status_code == 200
    assert response.json() == {"status": "draining"}
    mock_engine_client.pause_generation.assert_awaited_once_with(wait_for_inflight_requests=True)

def test_drain_endpoint_not_implemented(admin_client, mock_engine_client):
    mock_engine_client.pause_generation.side_effect = NotImplementedError
    response = admin_client.post("/v1/admin/drain")
    assert response.status_code == 501
    assert "not supported" in response.json()["detail"]

def test_reload_model_endpoint(admin_client):
    response = admin_client.post("/v1/admin/reload_model")
    assert response.status_code == 501
    assert "Not yet implemented" in response.json().get("detail", "") or "not yet implemented" in response.json().get("detail", "")
