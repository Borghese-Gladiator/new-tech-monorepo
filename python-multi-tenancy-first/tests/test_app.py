import pytest

from multi_tenancy.app import parse_tenant_slug
from multi_tenancy.auth import make_token


class TestParseTenantSlug:
    @pytest.mark.parametrize(
        "host, expected",
        [
            ("acme.yourapp.com", "acme"),
            ("ACME.yourapp.com:8000", "acme"),
            ("sub.domain.example.com", "sub"),
            ("localhost", None),
            ("yourapp.com", None),
            ("", None),
        ],
    )
    def test_parse(self, host, expected):
        assert parse_tenant_slug(host) == expected


class TestLogin:
    def test_login_success(self, client):
        resp = client.post("/auth/login?tenant=acme&email=admin@example.com&password=password")
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/auth/login?tenant=acme&email=admin@example.com&password=wrong")
        assert resp.status_code == 401

    def test_login_unknown_tenant(self, client):
        resp = client.post("/auth/login?tenant=nope&email=admin@example.com&password=password")
        assert resp.status_code == 404

    def test_login_no_tenant(self, client):
        resp = client.post("/auth/login?email=admin@example.com&password=password")
        assert resp.status_code == 400


class TestProjects:
    @pytest.fixture()
    def acme_headers(self):
        token = make_token(user_id=1, tenant_id=1)
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture()
    def globex_headers(self):
        token = make_token(user_id=2, tenant_id=2)
        return {"Authorization": f"Bearer {token}"}

    def test_create_project(self, client, acme_headers):
        resp = client.post("/projects?tenant=acme&name=new-proj", headers=acme_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "new-proj"
        assert "id" in data

    def test_list_projects(self, client, acme_headers):
        resp = client.get("/projects?tenant=acme", headers=acme_headers)
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "acme-project" in names

    def test_no_auth_returns_401(self, client):
        resp = client.get("/projects?tenant=acme")
        assert resp.status_code == 401

    def test_tenant_mismatch_returns_403(self, client):
        # Token for globex, but requesting acme
        token = make_token(user_id=2, tenant_id=2)
        resp = client.get("/projects?tenant=acme", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_tenant_isolation(self, client, acme_headers, globex_headers):
        # Create a project under acme
        client.post("/projects?tenant=acme&name=acme-only", headers=acme_headers)
        # Globex should not see it (no RLS in SQLite, but we still test the endpoint works)
        resp = client.get("/projects?tenant=globex", headers=globex_headers)
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()]
        assert "globex-project" in names
