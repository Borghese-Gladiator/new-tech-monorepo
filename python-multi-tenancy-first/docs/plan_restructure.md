# Plan: Restructure into package + add tests

## Brief
Restructure flat files into a proper `src/` package layout so imports work cleanly,
then add pytest tests that validate auth, tenant resolution, and API endpoints
using an in-memory SQLite DB (no Postgres required).

## Changes
1. Move source files into `src/multi_tenancy/` package
2. Update `pyproject.toml` with missing deps + test deps (httpx, pytest)
3. Add `conftest.py` with fixtures (test DB, test client, seeded data)
4. Write tests for `auth`, `app` (endpoints), and `parse_tenant_slug`

## Tests

### Unit
- `tests/test_auth.py` — hash/verify password, make/decode token, expired token
- `tests/test_app.py` — parse_tenant_slug, login, create/list projects, tenant isolation, error cases

### Manual
- `poetry run pytest` from project root
