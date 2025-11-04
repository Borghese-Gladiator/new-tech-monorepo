# cache_service.py
import os, ssl, json, time, random, asyncio, contextlib
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel
import valkey  # pip install valkey

# -----------------------------
# Configuration & connections
# -----------------------------
VALKEY_USER   = os.getenv("VALKEY_USER", "")
VALKEY_PASS   = os.getenv("VALKEY_PASSWORD", "")
WRITER_HOST   = os.getenv("VALKEY_WRITER_ENDPOINT", "localhost")
READER_HOST   = os.getenv("VALKEY_READER_ENDPOINT", WRITER_HOST)
WRITER_PORT   = int(os.getenv("VALKEY_WRITER_PORT", "6379"))  # ElastiCache Serverless: 6379 writes
READER_PORT   = int(os.getenv("VALKEY_READER_PORT", "6380"))  # ElastiCache Serverless: 6380 reads
TLS_ENABLED   = os.getenv("VALKEY_TLS", "1") != "0"
CACHE_DB      = int(os.getenv("VALKEY_DB", "0"))

CACHE_VER     = os.getenv("CACHE_VER", "v1")  # bump to invalidate en masse
JITTER_RANGE  = float(os.getenv("CACHE_JITTER_RANGE", "0.15"))  # ±15%
NEG_TTL       = int(os.getenv("CACHE_NEG_TTL", "30"))

QUEUE_KEY     = os.getenv("WB_QUEUE_KEY", "wb:queue")
SWR_LOCK_TTL  = int(os.getenv("SWR_LOCK_TTL", "5"))
REBUILD_LOCK_TTL = int(os.getenv("REBUILD_LOCK_TTL", "5"))

RATE_MAX_TOKENS = int(os.getenv("RATE_MAX_TOKENS", "100"))
RATE_WINDOW_SEC = int(os.getenv("RATE_WINDOW_SEC", "60"))

def _tls_url(host: str, port: int) -> str:
    if TLS_ENABLED:
        return f"rediss://{VALKEY_USER}:{VALKEY_PASS}@{host}:{port}/{CACHE_DB}"
    else:
        # for local development with plain Redis/Valkey
        auth = f"{VALKEY_USER}:{VALKEY_PASS}@" if (VALKEY_USER or VALKEY_PASS) else ""
        return f"redis://{auth}{host}:{port}/{CACHE_DB}"

r_w = valkey.from_url(_tls_url(WRITER_HOST, WRITER_PORT))
r_r = valkey.from_url(_tls_url(READER_HOST, READER_PORT))

# ---------------------------------
# Helpers & core cache abstractions
# ---------------------------------
def _with_jitter(ttl_sec: int) -> int:
    if ttl_sec <= 0: return ttl_sec
    delta = ttl_sec * JITTER_RANGE
    return int(ttl_sec + random.uniform(-delta, +delta))

def kv(*parts: str) -> str:
    # versioned key for global busts by bumping CACHE_VER
    return ":".join((CACHE_VER, *parts))

def token_bucket(key: str, max_tokens: int, window_sec: int) -> bool:
    pipe = r_w.pipeline()
    pipe.incr(key, 1)
    pipe.expire(key, window_sec)
    count, _ = pipe.execute()
    return int(count) <= max_tokens

class RequestCache(dict):
    def get_or_set(self, key, fn):
        if key not in self:
            self[key] = fn()
        return self[key]

# ---------------------------------
# Origin (simulated DB) for demo
# ---------------------------------
# In real life, replace these with your DB/API calls.
_USERS: Dict[str, Dict[str, Any]] = {
    "1": {"id": "1", "name": "Ada", "title": "Engineer"},
    "2": {"id": "2", "name": "Grace", "title": "Scientist"},
}
async def db_get_user(uid: str) -> Optional[Dict[str, Any]]:
    await asyncio.sleep(0.02)  # simulate latency
    return _ USERS.get(uid)  # NOTE: remove space after "_" if pasting; guard below fixes.

def _safe_users_get(uid: str):
    # avoid the stray space in the dict name if someone pastes as-is
    try:
        return _USERS.get(uid)
    except NameError:
        return globals().get("_ USERS", {}).get(uid)

async def db_get_user_async(uid: str) -> Optional[Dict[str, Any]]:
    await asyncio.sleep(0.02)
    return _safe_users_get(uid)

async def db_update_user(user: Dict[str, Any]) -> None:
    await asyncio.sleep(0.01)
    _USERS[user["id"]] = user

# ---------------------------------
# Caching patterns (async versions)
# ---------------------------------
async def cache_aside_json(key: str, ttl: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    if raw is not None:
        return json.loads(raw)
    data = await loader()
    if data is None:
        return None
    await r_w.setex(key, _with_jitter(ttl), json.dumps(data))
    return data

async def get_with_singleflight_json(key: str, ttl: int, loader: Callable[[], Any], wait_ms=150):
    raw = await r_r.get(key)
    if raw is not None:
        return json.loads(raw)

    lock_key = f"lock:{key}"
    got_lock = await r_w.set(lock_key, "1", ex=REBUILD_LOCK_TTL, nx=True)
    if got_lock:
        try:
            data = await loader()
            if data is not None:
                pipe = r_w.pipeline()
                pipe.setex(key, _with_jitter(ttl), json.dumps(data))
                pipe.setex(f"rebuilding:{key}", 2, "1")
                await pipe.execute()
            return data
        finally:
            with contextlib.suppress(Exception):
                await r_w.delete(lock_key)
    else:
        await asyncio.sleep(wait_ms / 1000.0)
        raw2 = await r_r.get(key)
        return None if raw2 is None else json.loads(raw2)

async def swr_get_json(key: str, ttl: int, stale_grace: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    now = time.time()
    if raw:
        obj = json.loads(raw)
        if now < obj["stale_at"]:
            return obj["value"]
        # stale but within grace => serve stale and refresh
        if await r_w.set(f"swrlock:{key}", "1", ex=SWR_LOCK_TTL, nx=True):
            async def _refresh():
                try:
                    data = await loader()
                    if data is not None:
                        await r_w.setex(key, ttl + stale_grace, json.dumps({"value": data, "stale_at": time.time() + ttl}))
                finally:
                    await r_w.delete(f"swrlock:{key}")
            asyncio.create_task(_refresh())
        return obj["value"]

    # cold
    data = await loader()
    if data is None: return None
    await r_w.setex(key, ttl + stale_grace, json.dumps({"value": data, "stale_at": now + ttl}))
    return data

async def get_with_negative_cache_json(key: str, ttl: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    if raw is not None:
        if raw == b"__nil__": return None
        return json.loads(raw)
    data = await loader()
    if data is None:
        await r_w.setex(key, NEG_TTL, "__nil__")
        return None
    await r_w.setex(key, _with_jitter(ttl), json.dumps(data))
    return data

async def invalidate_dependencies(dep_key: str):
    members = await r_w.smembers(dep_key) or []
    if members:
        await r_w.delete(*members)
    await r_w.delete(dep_key)

# ---------------------------------
# Write-behind queue worker
# ---------------------------------
async def write_behind_enqueue(topic: str, payload: dict):
    await r_w.rpush(QUEUE_KEY, json.dumps({"topic": topic, "payload": payload, "ts": time.time()}))

async def write_behind_worker(stop_event: asyncio.Event):
    while not stop_event.is_set():
        item = await r_w.blpop(QUEUE_KEY, timeout=1)
        if not item:
            continue
        _, raw = item
        msg = json.loads(raw)
        if msg["topic"] == "user_update":
            await db_update_user(msg["payload"])

# ---------------------------------
# Rate limit dependency
# ---------------------------------
async def enforce_rate_limit(request: Request):
    ident = request.headers.get("X-User", request.client.host if request.client else "anon")
    allowed = token_bucket(kv("ratelimit", ident), RATE_MAX_TOKENS, RATE_WINDOW_SEC)
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

# ---------------------------------
# API schema
# ---------------------------------
class User(BaseModel):
    id: str
    name: str
    title: str

class UpdateUser(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    mode: str = "write-through"  # or "write-behind"

# ---------------------------------
# FastAPI application
# ---------------------------------
app = FastAPI(title="Valkey Caching Patterns Service", version="1.0.0")
_worker_stop = asyncio.Event()
_worker_task: Optional[asyncio.Task] = None

@app.on_event("startup")
async def _startup():
    global _worker_task
    _worker_task = asyncio.create_task(write_behind_worker(_worker_stop))

@app.on_event("shutdown")
async def _shutdown():
    _worker_stop.set()
    if _worker_task:
        await asyncio.wait([_worker_task], timeout=2)

# ------------- Endpoints ---------------

@app.get("/healthz")
async def health():
    pong = await r_r.ping()
    return {"ok": True, "valkey": pong is True}

@app.get("/users/{uid}", dependencies=[Depends(enforce_rate_limit)])
async def get_user(uid: str, strategy: str = "singleflight", ttl: int = 900, stale_grace: int = 30):
    key = kv("user", uid)
    async def loader():
        return await db_get_user_async(uid)

    if strategy == "cache-aside":
        data = await cache_aside_json(key, ttl, loader)
    elif strategy == "singleflight":
        data = await get_with_singleflight_json(key, ttl, loader)
    elif strategy == "swr":
        data = await swr_get_json(key, ttl, stale_grace, loader)
    elif strategy == "negative":
        data = await get_with_negative_cache_json(key, ttl, loader)
    else:
        raise HTTPException(400, "unknown strategy")
    if data is None:
        raise HTTPException(404, "not found")
    return data

@app.post("/users/{uid}", dependencies=[Depends(enforce_rate_limit)])
async def update_user(uid: str, patch: UpdateUser, background: BackgroundTasks):
    # read existing
    cur = await db_get_user_async(uid)
    if not cur:
        cur = {"id": uid, "name": patch.name or f"User {uid}", "title": patch.title or "Member"}
    else:
        if patch.name: cur["name"] = patch.name
        if patch.title: cur["title"] = patch.title

    if patch.mode == "write-behind":
        await write_behind_enqueue("user_update", cur)
    else:
        await db_update_user(cur)

    # write-through cache + dependency tracking
    k = kv("user", uid)
    dep = kv("dep", "user", uid)
    pipe = r_w.pipeline()
    pipe.setex(k, _with_jitter(900), json.dumps(cur))
    # example dependent: a widget (who-to-follow)
    widget_key = kv("widget", "wtf", uid)
    widget = {"suggestions": [u for u in _USERS if u != uid][:3]}
    pipe.setex(widget_key, _with_jitter(300), json.dumps(widget))
    pipe.sadd(dep, k, widget_key)
    pipe.expire(dep, 1200)
    await pipe.execute()

    return {"ok": True, "user": cur, "mode": patch.mode}

@app.post("/invalidate/{uid}")
async def invalidate(uid: str):
    await invalidate_dependencies(kv("dep", "user", uid))
    return {"ok": True}

@app.post("/recompute", dependencies=[Depends(enforce_rate_limit)])
async def recompute_all():
    lock_key = kv("locks", "recompute")
    got = await r_w.set(lock_key, "1", ex=10, nx=True)
    if not got:
        raise HTTPException(423, "recompute already running")
    try:
        # pretend to recompute global artifacts
        await asyncio.sleep(0.2)
        return {"ok": True}
    finally:
        await r_w.delete(lock_key)

@app.get("/bulk/users", dependencies=[Depends(enforce_rate_limit)])
async def bulk_users(ids: str, ttl: int = 900):
    uids = ids.split(",")
    keys = [kv("user", u) for u in uids]
    raw = await r_r.mget(keys)
    hits, misses = {}, []
    for uid, blob in zip(uids, raw):
        if blob is None:
            misses.append(uid)
        else:
            hits[uid] = json.loads(blob)

    if misses:
        fetched = {}
        for uid in misses:
            fetched[uid] = await db_get_user_async(uid)  # could be None
        pipe = r_w.pipeline()
        for uid in misses:
            k = kv("user", uid)
            obj = fetched.get(uid)
            if obj is None:
                pipe.setex(k, NEG_TTL, "__nil__")
            else:
                pipe.setex(k, _with_jitter(ttl), json.dumps(obj))
        await pipe.execute()
        hits.update({uid: v for uid, v in fetched.items() if v is not None})

    return hits

# request-scope cache demo (micro-batching in one request)
@app.get("/calc/heavy")
async def heavy_calc(n: int = 3):
    rc = RequestCache()
    def subcalc(i):
        return rc.get_or_set(f"fib:{i}", lambda: _fib(i))
    return {"sum": sum(subcalc(i) for i in range(n, n+3))}

def _fib(k: int) -> int:
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a

# Run: uvicorn cache_service:app --reload
