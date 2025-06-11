import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from flowbridge.app import create_app
from flowbridge.config.loader import load_config

@pytest.fixture
def app() -> Flask:
    """Create Flask application for testing."""
    config = load_config("config.yaml")
    app = create_app(config)
    return app

@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create test client."""
    return app.test_client()

def test_health_endpoint(client: FlaskClient):
    """Test health endpoint returns correct response."""
    response: TestResponse = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'timestamp' in data
    assert 'request_id' in data
    assert data['status'] == 'healthy'

def test_config_endpoint(client: FlaskClient):
    """Test config endpoint returns configuration."""
    response: TestResponse = client.get('/config')
    assert response.status_code == 200
    data = response.get_json()
    assert 'config' in data
    assert 'request_id' in data
    config = data['config']
    assert 'general' in config
    assert 'server' in config
    assert 'filtering' in config
    assert 'routes' in config

def test_nonexistent_endpoint(client: FlaskClient):
    """Test that nonexistentendpoint returns 404."""
    response: TestResponse = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data
