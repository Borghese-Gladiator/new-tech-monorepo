"""
Seed script: creates tables (via ORM), applies RLS policies, and inserts demo data.

Usage: python -m multi_tenancy.seed
"""
import os

from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv(".env.local")

from multi_tenancy.db import engine
from multi_tenancy.models import Base, Tenant, User, Project
from multi_tenancy.auth import hash_password
from sqlalchemy.orm import Session

# --- 1) Create all ORM-defined tables ---
Base.metadata.create_all(engine)

# --- 2) Apply RLS policies (ORM can't express these) ---
RLS_STATEMENTS = [
    "ALTER TABLE projects ENABLE ROW LEVEL SECURITY",
    "ALTER TABLE projects FORCE ROW LEVEL SECURITY",
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_policies WHERE policyname = 'projects_tenant_isolation'
        ) THEN
            EXECUTE '
                CREATE POLICY projects_tenant_isolation ON projects
                USING (tenant_id = current_setting(''app.tenant_id'', true)::bigint)
                WITH CHECK (tenant_id = current_setting(''app.tenant_id'', true)::bigint)
            ';
        END IF;
    END
    $$;
    """,
]

with engine.begin() as conn:
    for stmt in RLS_STATEMENTS:
        conn.execute(text(stmt))

print("Tables created + RLS policies applied.")

# --- 3) Seed tenants, users, and sample projects ---
tenant_slugs = os.environ.get("SEED_TENANT_SLUGS", "acme,globex").split(",")
seed_email = os.environ.get("SEED_USER_EMAIL", "admin@example.com")
seed_password = os.environ.get("SEED_USER_PASSWORD", "password")

with Session(engine) as db:
    for slug in tenant_slugs:
        slug = slug.strip()
        existing = db.execute(
            text("SELECT id FROM tenants WHERE slug = :slug"), {"slug": slug}
        ).scalar_one_or_none()

        if existing:
            print(f"  Tenant '{slug}' already exists (id={existing}), skipping.")
            continue

        tenant = Tenant(slug=slug)
        db.add(tenant)
        db.flush()

        user = User(
            tenant_id=tenant.id,
            email=seed_email,
            password_hash=hash_password(seed_password),
        )
        db.add(user)

        project = Project(tenant_id=tenant.id, name=f"{slug}-default-project")
        db.add(project)

        print(f"  Seeded tenant '{slug}' (id={tenant.id}) with user '{seed_email}' and sample project.")

    db.commit()

print("Done.")
