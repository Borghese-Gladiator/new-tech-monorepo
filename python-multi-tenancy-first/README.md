Quick PoC that I generated when looking at how companies implement multi-tenancy

# Python Multi-Tenancy PoC

Subdomain-based multi-tenant API using FastAPI + SQLAlchemy 2.0 + Postgres Row Level Security (RLS).

## Directory Structure

```
src/multi_tenancy/
  app.py      — FastAPI app: tenant resolution, JWT auth, RLS-scoped sessions, routes
  auth.py     — JWT token creation/decode + bcrypt password hashing
  db.py       — SQLAlchemy engine + session factory
  models.py   — ORM models: Tenant, User, Project
  seed.py     — Creates tables, applies RLS policies, seeds demo data
tests/
  conftest.py — Fixtures: in-memory SQLite DB, seeded data, test client
  test_auth.py — Password hashing + JWT tests
  test_app.py  — Tenant slug parsing, login, project CRUD, isolation tests
```

## Setup

```bash
poetry install
cp .env.example .env.local
createdb mt_demo
python -m multi_tenancy.seed
```

## Run

```bash
uvicorn multi_tenancy.app:app --reload
```

## Test

```bash
poetry run pytest
```

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login?tenant=acme` | None | Login with `email` + `password` query params, returns JWT |
| `POST` | `/projects?name=foo` | Bearer JWT | Create a project (RLS-scoped) |
| `GET` | `/projects` | Bearer JWT | List projects (RLS-scoped) |

## How Isolation Works

1. **Tenant resolution** — extracted from `Host` header subdomain or `?tenant=` fallback
2. **JWT enforcement** — token contains `tenant_id`, backend verifies it matches the resolved tenant
3. **Postgres RLS** — `SET LOCAL app.tenant_id` is set per transaction; even unfiltered queries only return rows for the current tenant
