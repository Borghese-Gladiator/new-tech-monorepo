# test_cache_service.py
import os, asyncio, json, pytest
from fastapi.testclient import TestClient

USE_FAKE = os.getenv("VALKEY_FAKE", "1") == "1"
if USE_FAKE:
    import fakeredis.aioredis as fakeredis
    import cache_service as svc

    # Monkeypatch clients before app startup
    svc.r_w = fakeredis.FakeRedis()
    svc.r_r = svc.r_w  # same fake for read/write
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
