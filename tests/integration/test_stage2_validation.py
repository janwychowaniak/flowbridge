import json
import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from flowbridge import create_app, load_config

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

def test_app_startup_with_config(app: Flask):
    """Validate Flask app starts with valid config."""
    assert app is not None
    assert app.config.get('SERVER_CONFIG') is not None
    assert app.config.get('GENERAL_CONFIG') is not None

def test_health_endpoint_response(client: FlaskClient):
    """Validate health endpoint returns correct response."""
    response: TestResponse = client.get('/health')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'request_id' in data

def test_config_endpoint_response(client: FlaskClient):
    """Validate config endpoint returns loaded configuration."""
    response: TestResponse = client.get('/config')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'request_id' in data
    assert 'config' in data
    
    # Verify the configuration structure
    config = data['config']
    assert 'general' in config
    assert 'server' in config
    assert 'filtering' in config
    assert 'routes' in config

def test_error_handling_integration(client: FlaskClient):
    """Validate error handling integration."""
    # Test non-existent endpoint
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data
    
    # Test method not allowed
    response = client.post('/health')
    assert response.status_code == 405
    data = response.get_json()
    assert 'error' in data
    assert 'request_id' in data
