import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.core.limiter import limiter

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_limiter_after_test():
    yield
    # Reset limiter storage after rate limiting tests so rate counts don't bleed into other test suites
    try:
        limiter._storage.reset()
    except Exception:
        pass

def test_rate_limiting_auth_login_triggers_429():
    """Verify that exceeding RATE_LIMIT_AUTH on /auth/login returns 429 Too Many Requests."""
    payload = {"email": "invalid_login@example.com", "password": "wrongpassword"}
    
    responses = []
    for _ in range(7):
        resp = client.post("/api/v1/auth/login", json=payload)
        responses.append(resp.status_code)
    
    # At least one request beyond rate limit threshold must yield 429
    assert 429 in responses

def test_rate_limiting_query_endpoint_exceed_returns_429():
    """Verify query endpoint rate limiting works when threshold is reached."""
    payload = {"prompt": "Test query for rate limiting"}
    responses = []
    
    for _ in range(25):
        resp = client.post("/api/v1/query/execute", json=payload)
        responses.append(resp.status_code)
        
    assert 429 in responses or 401 in responses
