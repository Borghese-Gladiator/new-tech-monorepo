(Claude Code for the entirety of it)

# Valkey/Redis Caching Patterns Service

Production-ready FastAPI service demonstrating advanced caching patterns with Valkey/Redis. Features async I/O, circuit breaker, comprehensive error handling, and full test coverage.

## Features

- **4 Caching Strategies**: Cache-aside, singleflight, stale-while-revalidate, negative caching
- **Write Patterns**: Write-through and write-behind with queue worker
- **Resilience**: Circuit breaker, error handling, graceful degradation
- **Observability**: Structured logging, health checks, cache statistics
- **Security**: Rate limiting, input validation
- **AWS Ready**: ElastiCache Serverless compatible with separate read/write endpoints
- **Testing**: 31 automated tests (100% pass rate) + manual test suite

## Quick Start

### Bootstrap New Project (Optional)
If starting from scratch:
```bash
# Initialize project
uv init redis-valkey-first
cd redis-valkey-first

# Install runtime dependencies
uv add fastapi uvicorn pydantic valkey httpx

# Install dev dependencies
uv add --dev pytest fakeredis colorama coverage

# Sync environment
uv sync
```

### Install Dependencies (Existing Project)
```bash
uv sync
```

### Run with Fake Redis (No Infrastructure)
```bash
export VALKEY_FAKE=1
make serve
# or: uvicorn src.cache_service:app --reload
```

### Run Tests
```bash
make test
```

## Caching Strategies

### 1. Cache-Aside
Standard read-through pattern with TTL and jitter to prevent thundering herd.

```bash
curl "http://localhost:8000/users/1?strategy=cache-aside&ttl=900"
```

### 2. Singleflight
Prevents cache stampede by coalescing concurrent requests for the same key.

```bash
curl "http://localhost:8000/users/1?strategy=singleflight&ttl=900"
```

### 3. Stale-While-Revalidate (SWR)
Serves stale data immediately while refreshing in background. Best for high-traffic endpoints.

```bash
curl "http://localhost:8000/users/1?strategy=swr&ttl=60&stale_grace=300"
```

### 4. Negative Caching
Caches non-existent entries to prevent repeated expensive lookups.

```bash
curl "http://localhost:8000/users/999?strategy=negative&ttl=900"
```

## API Endpoints

### Core Operations
```bash
# Health check (includes circuit breaker status)
GET /healthz

# Cache statistics
GET /stats

# Get user with caching strategy
GET /users/{uid}?strategy={strategy}&ttl={seconds}

# Update user (write-through or write-behind)
POST /users/{uid}
{
  "name": "Ada Lovelace",
  "title": "Programmer",
  "mode": "write-through"  # or "write-behind"
}

# Bulk fetch users
GET /bulk/users?ids=1,2,3

# Invalidate user cache and dependencies
POST /invalidate/{uid}

# Distributed lock demo
POST /recompute
```

### Query Parameters
- `strategy`: `cache-aside`, `singleflight`, `swr`, `negative`
- `ttl`: Time-to-live in seconds (1-86400)
- `stale_grace`: Grace period for SWR (0-3600)

## Testing

### Run All Tests (31 tests)
```bash
make test
```

### Unit Tests (No Redis Required)
```bash
export VALKEY_FAKE=1
.venv/bin/pytest tests/test_cache_service.py -v
```

### Integration Tests (Requires Redis)
```bash
docker run -d -p 6379:6379 redis:7
export VALKEY_FAKE=0
.venv/bin/pytest tests/test_integration.py -v
```

### Manual Interactive Tests
```bash
# Terminal 1: Start server
make serve

# Terminal 2: Run manual tests with colored output
python manual_test.py
```

### Test Coverage
```bash
make cov
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VALKEY_FAKE` | `1` | Use fakeredis (1) or real Redis (0) |
| `VALKEY_USER` | `""` | Username for authentication |
| `VALKEY_PASSWORD` | `""` | Password for authentication |
| `VALKEY_WRITER_ENDPOINT` | `localhost` | Write endpoint hostname |
| `VALKEY_READER_ENDPOINT` | `localhost` | Read endpoint hostname |
| `VALKEY_WRITER_PORT` | `6379` | Write port |
| `VALKEY_READER_PORT` | `6379` | Read port (6380 for ElastiCache Serverless) |
| `VALKEY_TLS` | `1` | Enable TLS (1=yes, 0=no) |
| `VALKEY_DB` | `0` | Redis database number |
| `CACHE_VER` | `v1` | Cache version for mass invalidation |
| `RATE_MAX_TOKENS` | `100` | Rate limit max requests |
| `RATE_WINDOW_SEC` | `60` | Rate limit time window |

### Local Development
```bash
export VALKEY_FAKE=1
make serve
```

### With Local Redis
```bash
docker run -d -p 6379:6379 redis:7

export VALKEY_FAKE=0
export VALKEY_TLS=0
export VALKEY_WRITER_ENDPOINT=localhost
export VALKEY_READER_ENDPOINT=localhost
make serve
```

### Production (AWS ElastiCache Serverless)
```bash
export VALKEY_FAKE=0
export VALKEY_USER='<your-user>'
export VALKEY_PASSWORD='<your-password>'
export VALKEY_WRITER_ENDPOINT='xyz-001.valkey-serverless.<region>.cache.amazonaws.com'
export VALKEY_READER_ENDPOINT='xyz-001.valkey-serverless-ro.<region>.cache.amazonaws.com'
export VALKEY_WRITER_PORT=6379
export VALKEY_READER_PORT=6380
export VALKEY_TLS=1

uvicorn src.cache_service:app --host 0.0.0.0 --port 8000
```

## Architecture

### Key Components

**Connection Pooling**
- Max 50 connections per endpoint
- 5-second socket timeout
- Automatic retry on timeout

**Circuit Breaker**
- Opens after 5 consecutive failures
- 60-second recovery timeout
- Prevents cascading failures

**Rate Limiting**
- Token bucket algorithm
- Per-user via `X-User` header
- Configurable limits and windows

**Write-Behind Queue**
- Background worker for async writes
- Redis list as queue
- Automatic retry on failures

### Caching Patterns

```
┌─────────────┐
│   Client    │
└─────┬───────┘
      │
      ▼
┌─────────────┐     ┌──────────┐
│   FastAPI   │────▶│  Valkey  │
│   Service   │◀────│  (Redis) │
└─────────────┘     └──────────┘
      │
      ▼
┌─────────────┐
│  Origin DB  │
│  (Simulated)│
└─────────────┘
```

## Production Features

✅ **Async/Await** - Fully async with `valkey.asyncio`
✅ **Error Handling** - Circuit breaker and graceful degradation
✅ **Logging** - Structured logging for all operations
✅ **Input Validation** - Query params and request body validation
✅ **Health Checks** - Readiness and liveness endpoints
✅ **Graceful Shutdown** - Proper connection cleanup
✅ **Rate Limiting** - Token bucket per user
✅ **Distributed Locks** - Prevent duplicate work
✅ **Dependency Tracking** - Invalidate related cache entries

## Development

### Available Make Targets
```bash
make help      # Show all targets
make init      # Initialize project
make sync      # Sync dependencies
make serve     # Start dev server
make test      # Run tests
make cov       # Coverage report
make lint      # Lint code
make format    # Format code
make clean     # Clean artifacts
```

## Documentation

- **CHANGELOG.md** - Complete version history, features added, bugs fixed, and migration guides
- **manual_test.py** - Interactive testing with colored output

## Dependencies

**Runtime:**
- FastAPI - Web framework
- Uvicorn - ASGI server
- Valkey - Async Redis client
- Pydantic - Data validation
- httpx - Async HTTP client

**Development:**
- pytest - Testing framework
- fakeredis - Redis mock for testing
- colorama - Colored terminal output

## License

MIT
