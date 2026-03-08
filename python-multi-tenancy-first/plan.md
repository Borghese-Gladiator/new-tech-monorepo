# Multi-Tenancy PoC — Implementation Plan

## Brief
Implement the "easiest option" from blah.md: subdomain-based tenant identification with FastAPI + SQLAlchemy + Postgres RLS. Extract blah.md's code blocks into proper files.

## Changes
- Rename `main.py` → `app.py` (FastAPI app with routes, tenant resolution, auth context)
- Create `db.py` (engine + session factory)
- Create `models.py` (Tenant, User, Project with SQLAlchemy 2.0 mapped_column)
- Create `auth.py` (JWT + password hashing)
- Create `schema.sql` (Postgres schema + RLS setup)
- Create `requirements.txt` (dependencies)
- Rename `blah.md` → `DESIGN.md`

## Tests

### Unit
- N/A for PoC (no pytest infra yet)

### Manual
1. `pip install -r requirements.txt`
2. Run Postgres, execute `schema.sql`
3. `uvicorn app:app --reload`
4. POST `/auth/login?tenant=acme` with email/password
5. GET `/projects?tenant=acme` with Bearer token — verify only tenant's projects returned
