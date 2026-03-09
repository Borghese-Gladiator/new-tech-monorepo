## Tenant identification: system design options (and what I’d recommend)

Think of “tenant identification” as: **how the backend decides which tenant context to run the request in**, and **how you prevent spoofing**.

### Option A — Subdomain per tenant (most common SaaS default)

* Example: `https://acme.yourapp.com`
* **How backend identifies tenant:** read `Host` header → extract `acme` → look up tenant by slug.
* **Pros:** great UX, easy to reason about, no tenant headers needed.
* **Cons:** needs wildcard DNS + TLS (`*.yourapp.com`), special handling for custom domains.

**Recommendation:** Use this as your primary identifier.

### Option B — Custom domains (often added later)

* Example: `https://app.acme.com`
* **How backend identifies tenant:** map `Host` to tenant in DB (`tenant_domains` table).
* **Pros:** enterprise-friendly.
* **Cons:** domain verification + TLS issuance/renewal complexity.

**Recommendation:** Support when you need it; same backend flow as subdomains (Host→tenant).

### Option C — Tenant in JWT / access token (always do this too)

* Even if you identify by Host, you should still embed `tenant_id` in the JWT (or session) and **verify it matches** the tenant resolved from Host.
* **Why:** prevents “token from tenant A used on tenant B subdomain” issues.

**Recommendation:** Put `tenant_id` (or `org_id`) in the token and enforce match.

### Option D — Explicit header like `X-Tenant-Id` (good for internal tools)

* **Pros:** easy for APIs.
* **Cons:** easy to spoof if it’s the only mechanism.

**Recommendation:** Only use for trusted internal calls, or require it to match token claims.

---

## End-to-end example (Frontend + FastAPI + SQLAlchemy + Postgres) with strong isolation

This example uses:

* Tenant identified by **subdomain**
* Auth via simple JWT containing `tenant_id`
* Postgres **Row Level Security (RLS)** so the DB enforces isolation even if a dev forgets a filter
* SQLAlchemy session sets `SET LOCAL app.tenant_id` for each request

### 1) Postgres schema + RLS (run once)

```sql
-- tenants
create table if not exists tenants (
  id bigserial primary key,
  slug text not null unique
);

-- users (simplified)
create table if not exists users (
  id bigserial primary key,
  tenant_id bigint not null references tenants(id),
  email text not null,
  password_hash text not null,
  unique (tenant_id, email)
);

-- projects are tenant-scoped
create table if not exists projects (
  id bigserial primary key,
  tenant_id bigint not null references tenants(id),
  name text not null,
  unique (tenant_id, name)
);

-- Enable RLS
alter table projects enable row level security;

-- Force RLS (optional but recommended)
alter table projects force row level security;

-- Policy: only allow rows matching the app tenant setting
create policy projects_tenant_isolation
on projects
using (
  tenant_id = current_setting('app.tenant_id', true)::bigint
)
with check (
  tenant_id = current_setting('app.tenant_id', true)::bigint
);
```

### 2) Backend: FastAPI + SQLAlchemy (SQLAlchemy 2.0 style)

#### `db.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/mt_demo"

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False, future=True)
```

#### `models.py`

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, BigInteger, ForeignKey, UniqueConstraint

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),)

class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_projects_tenant_name"),)
```

#### `auth.py` (simple JWT)

```python
import time
from typing import Any, Dict
import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = "dev-only-change-me"
JWT_ALG = "HS256"
JWT_TTL_SECONDS = 60 * 60

def hash_password(pw: str) -> str:
    return pwd_context.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_context.verify(pw, pw_hash)

def make_token(*, user_id: int, tenant_id: int) -> str:
    now = int(time.time())
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
```

#### `main.py`

```python
from typing import Generator, Optional, Tuple

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db import SessionLocal
from models import Tenant, User, Project
from auth import verify_password, make_token, decode_token

app = FastAPI()
bearer = HTTPBearer(auto_error=False)

# --- Tenant resolution from Host (subdomain) ---
def parse_tenant_slug(host: str) -> Optional[str]:
    # Examples:
    #   acme.yourapp.com -> "acme"
    #   localhost:5173 -> None (dev fallback)
    host = host.split(":")[0].lower()
    parts = host.split(".")
    if len(parts) >= 3:  # tenant.yourapp.com
        return parts[0]
    return None

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def resolve_tenant(request: Request, db: Session = Depends(get_db)) -> Tenant:
    slug = parse_tenant_slug(request.headers.get("host", ""))
    if slug is None:
        # dev fallback: allow ?tenant=acme for localhost
        slug = request.query_params.get("tenant")

    if not slug:
        raise HTTPException(status_code=400, detail="Tenant not provided (subdomain or ?tenant=)")

    tenant = db.execute(select(Tenant).where(Tenant.slug == slug)).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Unknown tenant")
    return tenant

def auth_context(
    tenant: Tenant = Depends(resolve_tenant),
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
) -> Tuple[int, int]:
    """
    Returns (tenant_id, user_id), and enforces that token tenant matches Host tenant.
    """
    if not creds:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    token_tenant_id = int(payload.get("tenant_id"))
    user_id = int(payload.get("sub"))

    if token_tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")

    return (tenant.id, user_id)

def tenant_scoped_db(
    tenant_user: Tuple[int, int] = Depends(auth_context),
) -> Generator[Session, None, None]:
    """
    Create a session and set Postgres RLS tenant var for this transaction.
    """
    tenant_id, _ = tenant_user
    db = SessionLocal()
    try:
        # SET LOCAL applies for the current transaction; SQLAlchemy opens one on first use.
        # To be explicit, issue it immediately.
        db.execute(text("select set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# --- Auth endpoints (demo) ---
@app.post("/auth/login")
def login(
    email: str,
    password: str,
    tenant: Tenant = Depends(resolve_tenant),
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == email)
    ).scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Bad credentials")

    return {"access_token": make_token(user_id=user.id, tenant_id=tenant.id)}

# --- Tenant-scoped API (RLS enforced) ---
@app.post("/projects")
def create_project(
    name: str,
    tenant_user: Tuple[int, int] = Depends(auth_context),
    db: Session = Depends(tenant_scoped_db),
):
    tenant_id, _ = tenant_user
    p = Project(name=name, tenant_id=tenant_id)
    db.add(p)
    db.flush()
    return {"id": p.id, "name": p.name}

@app.get("/projects")
def list_projects(
    db: Session = Depends(tenant_scoped_db),
):
    # Note: no tenant filter. RLS enforces tenant isolation.
    rows = db.execute(select(Project).order_by(Project.id.desc())).scalars().all()
    return [{"id": p.id, "name": p.name} for p in rows]
```

**Why this is strong:** even if someone accidentally writes `select(Project)` without filtering, Postgres RLS blocks cross-tenant rows as long as `app.tenant_id` is set.

---

## 3) Frontend: simple React (Vite-style) that uses subdomain + JWT

### `src/api.ts`

```ts
export function getTenantSlug(): string | null {
  const host = window.location.hostname; // e.g. acme.yourapp.com
  const parts = host.split(".");
  if (parts.length >= 3) return parts[0];
  return new URLSearchParams(window.location.search).get("tenant");
}

const API_BASE = "http://localhost:8000"; // dev backend

export async function login(email: string, password: string): Promise<string> {
  const tenant = getTenantSlug();
  const qs = tenant ? `?tenant=${encodeURIComponent(tenant)}` : "";
  const res = await fetch(`${API_BASE}/auth/login${qs}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) throw new Error(await res.text());
  const data = await res.json();
  return data.access_token as string;
}

export async function listProjects(token: string) {
  const tenant = getTenantSlug();
  const qs = tenant ? `?tenant=${encodeURIComponent(tenant)}` : "";
  const res = await fetch(`${API_BASE}/projects${qs}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createProject(token: string, name: string) {
  const tenant = getTenantSlug();
  const qs = tenant ? `?tenant=${encodeURIComponent(tenant)}` : "";
  const res = await fetch(`${API_BASE}/projects${qs}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
```

### `src/App.tsx`

```tsx
import { useState } from "react";
import { login, listProjects, createProject, getTenantSlug } from "./api";

export default function App() {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("password");
  const [token, setToken] = useState<string>("");
  const [projects, setProjects] = useState<any[]>([]);
  const [newName, setNewName] = useState("");

  const tenant = getTenantSlug();

  return (
    <div style={{ maxWidth: 720, margin: "40px auto", fontFamily: "system-ui" }}>
      <h2>Multi-tenant demo {tenant ? `(tenant: ${tenant})` : ""}</h2>

      {!token ? (
        <>
          <h3>Login</h3>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
          <br />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="password"
            type="password"
          />
          <br />
          <button
            onClick={async () => {
              const t = await login(email, password);
              setToken(t);
              const ps = await listProjects(t);
              setProjects(ps);
            }}
          >
            Sign in
          </button>
        </>
      ) : (
        <>
          <button
            onClick={async () => {
              const ps = await listProjects(token);
              setProjects(ps);
            }}
          >
            Refresh projects
          </button>

          <h3>Create project</h3>
          <input value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="Name" />
          <button
            onClick={async () => {
              await createProject(token, newName);
              setNewName("");
              setProjects(await listProjects(token));
            }}
          >
            Create
          </button>

          <h3>Projects</h3>
          <ul>
            {projects.map((p) => (
              <li key={p.id}>
                #{p.id} {p.name}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
```

---

## The key design guardrails (don’t skip these)

* **Tenant resolved from Host**, not from a user-controlled header.
* JWT includes **tenant_id** and you enforce **tenant match**.
* DB enforces isolation with **RLS** (best safety net).
* Unique constraints include `tenant_id` so tenants can reuse names safely.

---

### What I need from you

1. Do you want tenants to be primarily **subdomains**, **custom domains**, or both?
2. Will users ever belong to **multiple tenants** (multi-org accounts), or exactly one?

### Suggested next step

Tell me those two answers and I’ll adapt the example to your exact UX (including “switch org” flows if users can belong to multiple tenants).
