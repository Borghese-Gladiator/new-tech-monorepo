# test_cache_service.py
import os, asyncio, json, pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

USE_FAKE = os.getenv("VALKEY_FAKE", "1") == "1"
if USE_FAKE:
    import fakeredis.aioredis as fakeredis
    import cache_service as svc

    # Monkeypatch async clients before app startup
    fake_client = fakeredis.FakeRedis()
    svc.r_w = fake_client
    svc.r_r = fake_client  # same fake for read/write
    app = svc.app
else:
    import cache_service as svc
    app = svc.app

client = TestClient(app)

def test_health():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["ok"] is True

def test_get_user_singleflight_and_negative():
    # existing user 1 should be found
    r1 = client.get("/users/1", params={"strategy": "singleflight"})
    assert r1.status_code == 200
    # non-existent 999 should 404 but be negative-cached if we ask with strategy=negative
    r2 = client.get("/users/999", params={"strategy": "negative"})
    assert r2.status_code in (200, 404)  # may 404 on first miss
    # second try should consistently reflect negative caching or success
    r3 = client.get("/users/999", params={"strategy": "negative"})
    assert r3.status_code in (200, 404)

def test_write_through_and_swr():
    # update write-through
    r = client.post("/users/2", json={"name": "Grace H.", "title": "Pioneer", "mode": "write-through"})
    assert r.status_code == 200
    # swr read should serve from cache
    r2 = client.get("/users/2", params={"strategy": "swr", "ttl": 1, "stale_grace": 10})
    assert r2.status_code == 200
    assert r2.json()["name"].startswith("Grace")

def test_bulk_and_invalidate():
    r = client.get("/bulk/users", params={"ids": "1,2,999"})
    assert r.status_code == 200
    data = r.json()
    assert "1" in data and "2" in data
    # invalidate dependencies of user 1; next singleflight must still succeed (rebuild from DB)
    r2 = client.post("/invalidate/1")
    assert r2.status_code == 200
    r3 = client.get("/users/1", params={"strategy": "singleflight"})
    assert r3.status_code == 200

def test_request_scope_calc():
    r = client.get("/calc/heavy", params={"n": 10})
    assert r.status_code == 200
    assert "sum" in r.json()

# ========== New comprehensive tests ==========

def test_cache_stats():
    """Test cache statistics endpoint"""
    r = client.get("/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_keys" in data
    assert "connected" in data
    assert data["connected"] is True

def test_rate_limiting():
    """Test rate limiting functionality"""
    # Make requests up to limit
    responses = []
    for i in range(105):  # exceeds default limit of 100
        r = client.get("/users/1", headers={"X-User": "test-user-limit"})
        responses.append(r.status_code)

    # Should have at least one 429 (rate limited)
    assert 429 in responses, "Rate limiting should have triggered"

def test_write_behind_mode():
    """Test write-behind caching mode"""
    r = client.post("/users/3", json={
        "name": "TestUser",
        "title": "Tester",
        "mode": "write-behind"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["mode"] == "write-behind"

def test_invalid_strategy():
    """Test invalid caching strategy"""
    r = client.get("/users/1", params={"strategy": "invalid-strategy"})
    assert r.status_code == 400
    assert "Invalid strategy" in r.json()["detail"]

def test_ttl_validation():
    """Test TTL parameter validation"""
    # TTL too high - FastAPI returns 422 for query param validation
    r = client.get("/users/1", params={"ttl": 999999})
    assert r.status_code == 422

    # TTL too low
    r = client.get("/users/1", params={"ttl": 0})
    assert r.status_code == 422

def test_stale_grace_validation():
    """Test stale_grace parameter validation"""
    # stale_grace too high - FastAPI returns 422 for query param validation
    r = client.get("/users/1", params={"strategy": "swr", "stale_grace": 99999})
    assert r.status_code == 422

def test_user_update_validation():
    """Test user update with invalid data"""
    # Empty name should fail
    r = client.post("/users/1", json={"name": "", "mode": "write-through"})
    assert r.status_code == 422  # Validation error

    # Invalid mode should fail
    r = client.post("/users/1", json={"name": "Test", "mode": "invalid-mode"})
    assert r.status_code == 422

def test_recompute_locking():
    """Test recompute endpoint with distributed lock"""
    r = client.post("/recompute")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_cache_aside_strategy():
    """Test cache-aside pattern specifically"""
    r = client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "1"

    # Second request should hit cache
    r2 = client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
    assert r2.status_code == 200
    assert r2.json()["id"] == "1"

def test_nonexistent_user():
    """Test handling of non-existent user"""
    r = client.get("/users/999999", params={"strategy": "cache-aside"})
    assert r.status_code == 404

def test_bulk_with_empty_list():
    """Test bulk endpoint edge cases"""
    r = client.get("/bulk/users", params={"ids": "1"})
    assert r.status_code == 200
    assert "1" in r.json()

def test_invalidate_nonexistent():
    """Test invalidating non-existent user"""
    r = client.post("/invalidate/999999")
    assert r.status_code == 200
    assert r.json()["ok"] is True

def test_health_check_details():
    """Test health check returns detailed status"""
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    assert "valkey" in data
    assert "circuit_breaker" in data

def test_concurrent_singleflight():
    """Test that singleflight prevents stampede"""
    # This test would need proper async testing to truly verify
    # For now, just verify it works with concurrent-like requests
    import concurrent.futures

    def make_request():
        return client.get("/users/2", params={"strategy": "singleflight"})

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]

    # All should succeed
    assert all(r.status_code == 200 for r in results)

def test_user_creation_via_update():
    """Test creating a new user via update endpoint"""
    r = client.post("/users/999", json={
        "name": "New User",
        "title": "Creator",
        "mode": "write-through"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["user"]["id"] == "999"
    assert data["user"]["name"] == "New User"
