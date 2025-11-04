# test_integration.py
"""
Integration tests that run against a real Redis/Valkey instance.
Run with: bin/pytest --runintegration tests/test_integration.py

Requires:
- Redis/Valkey running on localhost:6379
- Or set VALKEY_FAKE=0 and appropriate VALKEY_* env vars
"""
import os
import pytest
import asyncio
import time
from fastapi.testclient import TestClient

# Only run if explicitly requested
pytestmark = pytest.mark.integration

# Import with real Redis
os.environ["VALKEY_FAKE"] = "0"
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import cache_service as svc

client = TestClient(svc.app)


@pytest.fixture(autouse=True)
def cleanup_redis():
    """Clean up Redis before each test"""
    yield
    # Cleanup after test
    try:
        asyncio.run(_cleanup())
    except:
        pass


async def _cleanup():
    """Async cleanup helper"""
    try:
        await svc.r_w.flushdb()
    except:
        pass


class TestIntegrationReal:
    """Integration tests with real Redis"""

    def test_connection(self):
        """Test that we can connect to Redis"""
        r = client.get("/healthz")
        assert r.status_code == 200
        data = r.json()
        assert data["valkey"] is True, "Redis/Valkey should be connected"

    def test_cache_persistence(self):
        """Test that cache actually persists between requests"""
        # First request - cache miss
        r1 = client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
        assert r1.status_code == 200

        # Second request - should hit cache
        r2 = client.get("/users/1", params={"strategy": "cache-aside", "ttl": 60})
        assert r2.status_code == 200
        assert r1.json() == r2.json()

    def test_swr_refresh(self):
        """Test stale-while-revalidate with short TTL"""
        # Initial request
        r1 = client.get("/users/1", params={
            "strategy": "swr",
            "ttl": 1,  # 1 second
            "stale_grace": 10
        })
        assert r1.status_code == 200

        # Wait for stale
        time.sleep(1.5)

        # Should still serve stale and trigger background refresh
        r2 = client.get("/users/1", params={
            "strategy": "swr",
            "ttl": 1,
            "stale_grace": 10
        })
        assert r2.status_code == 200

    def test_negative_caching_real(self):
        """Test negative caching with real Redis"""
        # First request for non-existent user
        r1 = client.get("/users/99999", params={"strategy": "negative"})
        assert r1.status_code == 404

        # Second request should hit negative cache
        r2 = client.get("/users/99999", params={"strategy": "negative"})
        assert r2.status_code == 404

    def test_bulk_operations_real(self):
        """Test bulk operations with real Redis"""
        # Ensure users exist
        client.post("/users/1", json={"name": "User1", "mode": "write-through"})
        client.post("/users/2", json={"name": "User2", "mode": "write-through"})

        # Bulk fetch
        r = client.get("/bulk/users", params={"ids": "1,2,3"})
        assert r.status_code == 200
        data = r.json()
        assert "1" in data
        assert "2" in data

    def test_invalidation_real(self):
        """Test cache invalidation with real Redis"""
        # Cache a user
        r1 = client.get("/users/1", params={"strategy": "cache-aside"})
        assert r1.status_code == 200

        # Invalidate
        r2 = client.post("/invalidate/1")
        assert r2.status_code == 200

        # Update user
        r3 = client.post("/users/1", json={
            "name": "Updated Name",
            "mode": "write-through"
        })
        assert r3.status_code == 200

        # Fetch again - should have new data
        r4 = client.get("/users/1", params={"strategy": "cache-aside"})
        assert r4.status_code == 200
        assert r4.json()["name"] == "Updated Name"

    def test_write_behind_queue_real(self):
        """Test write-behind queue with real Redis"""
        r = client.post("/users/100", json={
            "name": "Async User",
            "title": "Async",
            "mode": "write-behind"
        })
        assert r.status_code == 200

        # Wait for background worker to process
        time.sleep(0.5)

        # User should be in cache
        r2 = client.get("/users/100", params={"strategy": "cache-aside"})
        assert r2.status_code == 200

    def test_distributed_lock_real(self):
        """Test distributed locking with real Redis"""
        import concurrent.futures

        def call_recompute():
            return client.post("/recompute")

        # Try to run recompute concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(call_recompute) for _ in range(5)]
            results = [f.result() for f in futures]

        # At least one should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        locked_count = sum(1 for r in results if r.status_code == 423)

        assert success_count >= 1
        assert success_count + locked_count == 5

    def test_rate_limiting_real(self):
        """Test rate limiting with real Redis"""
        # Make requests that exceed limit
        responses = []
        for i in range(105):
            r = client.get("/users/1", headers={"X-User": "integration-test-user"})
            responses.append(r.status_code)

        # Should have rate limit errors
        rate_limited = [r for r in responses if r == 429]
        assert len(rate_limited) > 0, "Should have rate limited some requests"

    def test_cache_stats_real(self):
        """Test cache statistics with real Redis"""
        # Add some data
        client.post("/users/1", json={"name": "Test", "mode": "write-through"})

        r = client.get("/stats")
        assert r.status_code == 200
        data = r.json()

        assert data["connected"] is True
        assert data["total_keys"] > 0
        # memory_usage and uptime_seconds may be None with fakeredis
        # which is fine for testing

    def test_connection_pooling_stress(self):
        """Test connection pooling under load"""
        import concurrent.futures

        def make_requests():
            results = []
            for _ in range(10):
                r = client.get("/users/1", params={"strategy": "cache-aside"})
                results.append(r.status_code)
            return results

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_requests) for _ in range(10)]
            all_results = []
            for f in futures:
                all_results.extend(f.result())

        # All requests should succeed
        assert all(status == 200 for status in all_results)
        assert len(all_results) == 100
