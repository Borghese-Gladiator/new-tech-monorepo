## Bootstrap
```
uv init redis-valkey-first
cd redis-valkey-first
```
```
uv add fastapi uvicorn pydantic valkey httpx
uv add --dev pytest fakeredis
```

```
# Option A: Use fakeredis (no Valkey needed)
export VALKEY_FAKE=1
uvicorn cache_service:app --reload

# Option B: Use a local Valkey/Redis
# (example: docker run -p 6379:6379 redis:7)
export VALKEY_USER=""
export VALKEY_PASSWORD=""
export VALKEY_WRITER_ENDPOINT="localhost"
export VALKEY_READER_ENDPOINT="localhost"
export VALKEY_WRITER_PORT=6379
export VALKEY_READER_PORT=6379
export VALKEY_TLS=0
uvicorn cache_service:app --reload

```

pytest -q


PROD
```
export VALKEY_USER='<elasticache-user>'
export VALKEY_PASSWORD='<elasticache-password>'
export VALKEY_WRITER_ENDPOINT='xyz-001.valkey-serverless.<region>.cache.amazonaws.com'
export VALKEY_READER_ENDPOINT='xyz-001.valkey-serverless-ro.<region>.cache.amazonaws.com'
export VALKEY_WRITER_PORT=6379   # writes
export VALKEY_READER_PORT=6380   # reads
export VALKEY_TLS=1
```