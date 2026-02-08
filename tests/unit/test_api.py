"""
Unit Tests for API Endpoints
Testing in isolation with mocked dependencies
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_liveness_probe(self):
        """Test liveness probe always returns 200"""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "alive"}
    
    def test_readiness_probe_when_ready(self):
        """Test readiness probe when app is ready"""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "uptime_seconds" in data
    
    def test_startup_probe(self):
        """Test startup probe"""
        response = client.get("/health/startup")
        assert response.status_code == 200


class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_returns_service_info(self):
        """Test root endpoint returns service information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "environment" in data
        assert data["status"] == "operational"


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint"""
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint returns Prometheus format"""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        # Check for some expected metrics
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content


class TestItemsEndpoints:
    """Test items CRUD endpoints"""
    
    def test_get_items_returns_list(self):
        """Test GET /items returns list of items"""
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10  # Default limit
    
    def test_get_items_with_pagination(self):
        """Test GET /items with skip and limit"""
        response = client.get("/api/v1/items?skip=5&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == 5  # First item should have id=5
    
    def test_get_item_by_id(self):
        """Test GET /items/{item_id}"""
        response = client.get("/api/v1/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert "name" in data
        assert "price" in data
    
    def test_get_item_invalid_id(self):
        """Test GET /items/{item_id} with invalid ID"""
        response = client.get("/api/v1/items/-1")
        assert response.status_code == 400
        assert "must be non-negative" in response.json()["detail"]
    
    def test_get_item_not_found(self):
        """Test GET /items/{item_id} when item doesn't exist"""
        response = client.get("/api/v1/items/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_item(self):
        """Test POST /items creates new item"""
        payload = {
            "name": "Test Item",
            "description": "Test Description",
            "price": 99.99
        }
        response = client.post("/api/v1/items", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["price"] == payload["price"]
        assert "id" in data
    
    def test_create_item_invalid_data(self):
        """Test POST /items with invalid data"""
        payload = {
            "name": "",  # Empty name
            "price": -10  # Negative price
        }
        response = client.post("/api/v1/items", json=payload)
        assert response.status_code == 422  # Validation error


class TestTestingEndpoints:
    """Test endpoints for testing/debugging"""
    
    def test_slow_endpoint(self):
        """Test slow endpoint"""
        response = client.get("/api/v1/slow?delay=1")
        assert response.status_code == 200
        assert "Completed after" in response.json()["message"]
    
    def test_error_endpoint_400(self):
        """Test error endpoint returns 400"""
        response = client.get("/api/v1/error?error_type=400")
        assert response.status_code == 400
    
    def test_error_endpoint_500(self):
        """Test error endpoint returns 500"""
        response = client.get("/api/v1/error?error_type=500")
        assert response.status_code == 500
    
    def test_cache_endpoint_hit(self):
        """Test cache endpoint with cache hit"""
        response = client.get("/api/v1/cache-test?use_cache=true")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] in ["cache", "database"]


class TestMiddleware:
    """Test custom middleware"""
    
    def test_correlation_id_in_response(self):
        """Test that correlation ID is added to response headers"""
        response = client.get("/")
        assert "X-Correlation-ID" in response.headers
    
    def test_custom_correlation_id_preserved(self):
        """Test that custom correlation ID is preserved"""
        custom_id = "test-correlation-123"
        response = client.get("/", headers={"X-Correlation-ID": custom_id})
        assert response.headers["X-Correlation-ID"] == custom_id


class TestCORS:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present"""
        response = client.options("/api/v1/items")
        assert "access-control-allow-origin" in response.headers


@pytest.mark.asyncio
class TestAsyncBehavior:
    """Test async behavior"""
    
    async def test_concurrent_requests(self):
        """Test that concurrent requests are handled properly"""
        import asyncio
        
        async def make_request():
            return client.get("/api/v1/items/1")
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)


# Test fixtures

@pytest.fixture
def mock_database():
    """Mock database connection"""
    with patch('app.core.database.get_db') as mock:
        mock.return_value = MagicMock()
        yield mock


@pytest.fixture
def authenticated_client():
    """Client with authentication headers"""
    return TestClient(
        app,
        headers={"Authorization": "Bearer test-token"}
    )


# Parametrized tests

@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),
    (100, 200),
    (-1, 400),
    (999, 404),
])
def test_get_item_various_ids(item_id, expected_status):
    """Test GET /items with various IDs"""
    response = client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == expected_status


@pytest.mark.parametrize("delay", [1, 2, 5])
def test_slow_endpoint_various_delays(delay):
    """Test slow endpoint with various delays"""
    response = client.get(f"/api/v1/slow?delay={delay}")
    assert response.status_code == 200
    assert f"after {delay} seconds" in response.json()["message"]
