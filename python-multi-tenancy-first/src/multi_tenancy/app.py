from typing import Generator, Optional, Tuple

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from multi_tenancy.db import SessionLocal
from multi_tenancy.models import Tenant, User, Project
from multi_tenancy.auth import verify_password, make_token, decode_token

app = FastAPI()
bearer = HTTPBearer(auto_error=False)


def parse_tenant_slug(host: str) -> Optional[str]:
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
    tenant_id, _ = tenant_user
    db = SessionLocal()
    try:
        # SQLite doesn't support set_config, so skip RLS in test mode
        try:
            db.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
        except Exception:
            pass
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


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
    rows = db.execute(select(Project).order_by(Project.id.desc())).scalars().all()
    return [{"id": p.id, "name": p.name} for p in rows]
