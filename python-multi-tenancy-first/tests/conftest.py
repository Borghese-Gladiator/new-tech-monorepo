import pytest
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from multi_tenancy.models import Base, Tenant, User, Project
from multi_tenancy.auth import hash_password

# Single shared in-memory SQLite DB that works across threads
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
_TestSession = sessionmaker(bind=_engine, class_=Session, autoflush=False, autocommit=False, future=True)


@pytest.fixture()
def db_engine():
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture()
def db_session(db_engine):
    db = _TestSession()
    yield db
    db.close()


@pytest.fixture()
def seeded_db(db_session):
    """Seed two tenants with users and projects."""
    acme = Tenant(id=1, slug="acme")
    globex = Tenant(id=2, slug="globex")
    db_session.add_all([acme, globex])
    db_session.flush()

    acme_user = User(id=1, tenant_id=1, email="admin@example.com", password_hash=hash_password("password"))
    globex_user = User(id=2, tenant_id=2, email="admin@example.com", password_hash=hash_password("password"))
    db_session.add_all([acme_user, globex_user])

    acme_proj = Project(id=1, tenant_id=1, name="acme-project")
    globex_proj = Project(id=2, tenant_id=2, name="globex-project")
    db_session.add_all([acme_proj, globex_proj])
    db_session.commit()

    return db_session


@pytest.fixture()
def client(seeded_db, monkeypatch):
    """TestClient with SessionLocal patched to use in-memory SQLite."""
    import multi_tenancy.app as app_module

    # Patch SessionLocal so both get_db and tenant_scoped_db use the test DB
    monkeypatch.setattr(app_module, "SessionLocal", _TestSession)

    with TestClient(app_module.app) as c:
        yield c
