# Python Multi-Tenancy PoC

Subdomain-based multi-tenant API using FastAPI + SQLAlchemy 2.0 + Postgres Row Level Security (RLS).

## Directory Structure

| File | Description |
|---|---|
| `app.py` | FastAPI app — tenant resolution (subdomain / `?tenant=`), JWT auth, RLS-scoped sessions, routes |
| `auth.py` | JWT token creation/decode + bcrypt password hashing |
| `db.py` | SQLAlchemy engine + session factory (reads `DATABASE_URL` from env) |
| `models.py` | ORM models: `Tenant`, `User`, `Project` (SQLAlchemy 2.0 `mapped_column`) |
| `seed.py` | Creates tables via ORM, applies RLS policies, seeds demo tenants/users/projects |
| `.env.example` | Example environment config — copy to `.env.local` and adjust |
| `requirements.txt` | Python dependencies |
| `DESIGN.md` | System design notes on tenant identification options |
| `plan.md` | Implementation plan |

## Setup

```bash
cp .env.example .env.local
pip install -r requirements.txt
createdb mt_demo
python seed.py
```

## Run

```bash
uvicorn app:app --reload
```

## Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login?tenant=acme` | None | Login with `email` + `password` query params, returns JWT |
| `POST` | `/projects?name=foo` | Bearer JWT | Create a project (RLS-scoped) |
| `GET` | `/projects` | Bearer JWT | List projects (RLS-scoped, no manual tenant filter needed) |

All endpoints resolve the tenant from the `Host` subdomain (e.g. `acme.yourapp.com`) or the `?tenant=` query param for local dev.

## Example Usage

```bash
# Login as the seeded user on the "acme" tenant
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login?tenant=acme&email=admin@example.com&password=password" | jq -r .access_token)

# List projects
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/projects?tenant=acme" | jq

# Create a project
curl -s -X POST -H "Authorization: Bearer $TOKEN" "http://localhost:8000/projects?tenant=acme&name=my-project" | jq
```

## How Isolation Works

1. **Tenant resolution** — extracted from `Host` header subdomain or `?tenant=` fallback
2. **JWT enforcement** — token contains `tenant_id`, backend verifies it matches the resolved tenant
3. **Postgres RLS** — `SET LOCAL app.tenant_id` is set per transaction; even unfiltered `SELECT` queries only return rows for the current tenant
