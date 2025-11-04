# cache_service.py
import os, ssl, json, time, random, asyncio, contextlib, logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Query
from pydantic import BaseModel, Field, field_validator
import valkey.asyncio as valkey  # async valkey client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Async clients with connection pooling
r_w = valkey.from_url(
    _tls_url(WRITER_HOST, WRITER_PORT),
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    decode_responses=False  # we handle encoding/decoding manually
)
r_r = valkey.from_url(
    _tls_url(READER_HOST, READER_PORT),
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    decode_responses=False
)

# Circuit breaker state
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.is_open = False

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.error("Circuit breaker opened due to repeated failures")

    def can_attempt(self) -> bool:
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time > self.recovery_timeout:
            logger.info("Circuit breaker attempting recovery")
            self.is_open = False
            self.failure_count = 0
            return True
        return False

circuit_breaker = CircuitBreaker()

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

async def safe_redis_operation(operation: Callable, *args, fallback=None, **kwargs):
    """Wrapper for Redis operations with error handling and circuit breaker"""
    if not circuit_breaker.can_attempt():
        logger.warning("Circuit breaker open, skipping Redis operation")
        return fallback

    try:
        result = await operation(*args, **kwargs)
        circuit_breaker.record_success()
        return result
    except (valkey.ConnectionError, valkey.TimeoutError, asyncio.TimeoutError) as e:
        logger.error(f"Redis operation failed: {e}")
        circuit_breaker.record_failure()
        return fallback
    except Exception as e:
        logger.exception(f"Unexpected error in Redis operation: {e}")
        return fallback

async def token_bucket(key: str, max_tokens: int, window_sec: int) -> bool:
    """Async token bucket rate limiting"""
    try:
        pipe = r_w.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, window_sec)
        results = await pipe.execute()
        count = results[0]
        return int(count) <= max_tokens
    except Exception as e:
        logger.error(f"Token bucket error: {e}")
        return True  # fail open on errors

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
async def db_get_user_async(uid: str) -> Optional[Dict[str, Any]]:
    """Simulate async database fetch with latency"""
    await asyncio.sleep(0.02)
    return _USERS.get(uid)

async def db_update_user(user: Dict[str, Any]) -> None:
    await asyncio.sleep(0.01)
    _USERS[user["id"]] = user

# ---------------------------------
# Caching patterns (async versions)
# ---------------------------------
async def cache_aside_json(key: str, ttl: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    if raw is not None:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        return json.loads(raw)
    data = await loader()
    if data is None:
        return None
    await r_w.setex(key, _with_jitter(ttl), json.dumps(data))
    return data

async def get_with_singleflight_json(key: str, ttl: int, loader: Callable[[], Any], wait_ms=150):
    raw = await r_r.get(key)
    if raw is not None:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
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
        if raw2 is not None:
            if isinstance(raw2, bytes):
                raw2 = raw2.decode('utf-8')
            return json.loads(raw2)
        return None

async def swr_get_json(key: str, ttl: int, stale_grace: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    now = time.time()
    if raw:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        obj = json.loads(raw)
        # Check if it's in SWR format
        if isinstance(obj, dict) and "value" in obj and "stale_at" in obj:
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
        else:
            # Old format, treat as cold miss
            pass

    # cold
    data = await loader()
    if data is None: return None
    await r_w.setex(key, ttl + stale_grace, json.dumps({"value": data, "stale_at": now + ttl}))
    return data

async def get_with_negative_cache_json(key: str, ttl: int, loader: Callable[[], Any]):
    raw = await r_r.get(key)
    if raw is not None:
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        if raw == "__nil__": return None
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
    allowed = await token_bucket(kv("ratelimit", ident), RATE_MAX_TOKENS, RATE_WINDOW_SEC)
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
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    mode: str = Field(default="write-through", pattern="^(write-through|write-behind)$")

    @field_validator('mode')
    @classmethod
    def validate_mode(cls, v):
        if v not in ['write-through', 'write-behind']:
            raise ValueError('mode must be write-through or write-behind')
        return v

class CacheStats(BaseModel):
    total_keys: int
    memory_usage: Optional[int] = None
    connected: bool
    uptime_seconds: Optional[int] = None

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
    logger.info("Shutting down application...")
    _worker_stop.set()
    if _worker_task:
        await asyncio.wait([_worker_task], timeout=2)
    # Close Redis connections
    try:
        await r_w.aclose()
        await r_r.aclose()
        logger.info("Redis connections closed")
    except Exception as e:
        logger.error(f"Error closing Redis connections: {e}")

# ------------- Endpoints ---------------

@app.get("/healthz")
async def health():
    try:
        pong = await asyncio.wait_for(r_r.ping(), timeout=2.0)
        return {
            "ok": True,
            "valkey": pong is True,
            "circuit_breaker": "closed" if not circuit_breaker.is_open else "open"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "ok": False,
            "valkey": False,
            "circuit_breaker": "closed" if not circuit_breaker.is_open else "open",
            "error": str(e)
        }

@app.get("/stats", response_model=CacheStats)
async def cache_stats():
    """Get cache statistics"""
    try:
        dbsize = await r_r.dbsize()
        # Try to get info, but handle fakeredis not supporting it
        try:
            info = await r_r.info()
            memory_usage = info.get('used_memory')
            uptime = info.get('uptime_in_seconds')
        except Exception:
            # Fakeredis doesn't support INFO command
            memory_usage = None
            uptime = None

        return CacheStats(
            total_keys=dbsize,
            memory_usage=memory_usage,
            connected=True,
            uptime_seconds=uptime
        )
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(503, f"Unable to retrieve cache stats: {e}")

@app.get("/users/{uid}", dependencies=[Depends(enforce_rate_limit)])
async def get_user(
    uid: str,
    strategy: str = Query(default="singleflight"),
    ttl: int = Query(default=900, ge=1, le=86400),
    stale_grace: int = Query(default=30, ge=0, le=3600)
):
    # Validate strategy
    valid_strategies = ["cache-aside", "singleflight", "swr", "negative"]
    if strategy not in valid_strategies:
        raise HTTPException(400, f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}")

    # Validate ttl and stale_grace
    if ttl < 1 or ttl > 86400:
        raise HTTPException(400, "ttl must be between 1 and 86400 seconds")
    if stale_grace < 0 or stale_grace > 3600:
        raise HTTPException(400, "stale_grace must be between 0 and 3600 seconds")

    key = kv("user", uid)
    async def loader():
        return await db_get_user_async(uid)

    try:
        if strategy == "cache-aside":
            data = await cache_aside_json(key, ttl, loader)
        elif strategy == "singleflight":
            data = await get_with_singleflight_json(key, ttl, loader)
        elif strategy == "swr":
            data = await swr_get_json(key, ttl, stale_grace, loader)
        elif strategy == "negative":
            data = await get_with_negative_cache_json(key, ttl, loader)

        if data is None:
            raise HTTPException(404, "not found")

        logger.info(f"GET /users/{uid} strategy={strategy} ttl={ttl}")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting user {uid}: {e}")
        raise HTTPException(500, "Internal server error")

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
        if blob is None or blob == b'' or blob == '':
            misses.append(uid)
        else:
            # Handle both bytes and str
            if isinstance(blob, bytes):
                blob = blob.decode('utf-8')
            try:
                data = json.loads(blob)
                # Handle SWR format
                if isinstance(data, dict) and "value" in data:
                    hits[uid] = data["value"]
                else:
                    hits[uid] = data
            except json.JSONDecodeError:
                logger.warning(f"Failed to decode JSON for user {uid}, treating as miss")
                misses.append(uid)

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
