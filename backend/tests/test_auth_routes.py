import pytest
from fastapi.routing import APIRoute
from app.main import app
from app.core.security import create_access_token

PUBLIC_ALLOWLIST = {
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("GET", "/api/v1/verify/{hash_val}"),
    ("POST", "/api/v1/verify/upload"),
    ("GET", "/"),
    ("GET", "/docs"),
    ("GET", "/openapi.json"),
    ("GET", "/redoc"),
    ("GET", "/docs/oauth2-redirect")
}

def get_all_api_routes():
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                if method in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                    routes.append((method, route.path))
    return sorted(list(set(routes)))

ALL_ROUTES = get_all_api_routes()

@pytest.mark.parametrize("method,path", ALL_ROUTES)
def test_every_route_requires_auth_or_is_in_allowlist(client, method, path):
    """
    Parametrized test hitting EVERY registered route with no token.
    Must reject with 401 unless strictly on the public allowlist.
    """
    if (method, path) in PUBLIC_ALLOWLIST:
        return

    # Replace path params with dummy values for request execution
    req_path = path.replace("{id}", "1").replace("{case_id}", "1").replace("{job_id}", "job-test").replace("{hash_val}", "00"*32).replace("{chain}", "tron").replace("{address}", "TXDemoxHotWalletPrimary88888888888")

    # Send unauthenticated request (no token)
    res = client.request(method, req_path)
    
    # Must be 401 Unauthorized
    assert res.status_code == 401, f"Route {method} {path} (requested as {req_path}) was open to unauthenticated access! Returned status: {res.status_code}"

def test_rbac_wrong_role_forbidden_on_admin_routes(client, investigator_token):
    """Investigator token accessing admin-only routes must return 403 Forbidden."""
    admin_paths = [
        ("GET", "/api/v1/admin/settings"),
        ("POST", "/api/v1/admin/settings"),
        ("GET", "/api/v1/webhooks"),
        ("POST", "/api/v1/webhooks"),
        ("POST", "/api/v1/labels")
    ]
    
    for method, path in admin_paths:
        res = client.request(method, path, headers={"Authorization": f"Bearer {investigator_token}"}, json={"key": "test", "value": "test", "name": "hook", "target_url": "https://example.com", "address": "0x1111111111111111111111111111111111111111", "chain": "ethereum", "entity": "test"})
        assert res.status_code == 403, f"Expected 403 Forbidden for investigator on {method} {path}, got {res.status_code}"

def test_rbac_supervisor_access_to_analytics_and_audit(client, supervisor_token, investigator_token):
    """Supervisor can view analytics & audit log, but investigator cannot view audit log."""
    # Supervisor accessing audit log
    sup_res = client.get("/api/v1/audit-log", headers={"Authorization": f"Bearer {supervisor_token}"})
    assert sup_res.status_code == 200

    # Investigator accessing audit log -> 403
    inv_res = client.get("/api/v1/audit-log", headers={"Authorization": f"Bearer {investigator_token}"})
    assert inv_res.status_code == 403

def test_unknown_or_inactive_user_returns_401(client):
    """Token for non-existent or inactive user returns 401, not 404."""
    fake_token, _, _ = create_access_token(data={"sub": "nonexistent@user.com", "role": "investigator"})
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_token}"})
    assert res.status_code == 401

    inactive_token, _, _ = create_access_token(data={"sub": "inactive@demo", "role": "investigator"})
    res_inactive = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {inactive_token}"})
    assert res_inactive.status_code == 401
