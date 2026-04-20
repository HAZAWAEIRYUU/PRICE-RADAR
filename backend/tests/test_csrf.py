"""CSRF middleware behaviour.

The goal: protect cookie-authenticated sessions from cross-site POSTs,
but don't get in the way of non-browser clients that have no cookie
(CLI, mobile, scripts, integrations).
"""


def test_anon_post_without_origin_is_allowed(client):
    # Registration has no ambient credential -> no CSRF surface.
    resp = client.post(
        "/api/auth/register",
        json={"username": "csrf_anon", "password": "Passw0rd!", "email": "csrf_anon@example.com"},
        headers={"origin": ""},
    )
    assert resp.status_code == 200, resp.text


def test_anon_post_with_bad_origin_is_allowed(client):
    # Bearer-style clients often set Origin: null or whatever -- still OK,
    # because no auth cookie -> no session to forge.
    resp = client.post(
        "/api/auth/register",
        json={"username": "csrf_anon2", "password": "Passw0rd!", "email": "csrf_anon2@example.com"},
        headers={"origin": "https://evil.example.com"},
    )
    assert resp.status_code == 200, resp.text


def test_cookie_post_with_bad_origin_is_blocked(client):
    # Register -> server sets HttpOnly cookie on the TestClient jar.
    r1 = client.post(
        "/api/auth/register",
        json={"username": "csrf_session", "password": "Passw0rd!", "email": "csrf_session@example.com"},
    )
    assert r1.status_code == 200, r1.text
    # Now the cookie is present; a forged cross-site POST must 403.
    r2 = client.post(
        "/api/auth/logout",
        headers={"origin": "https://evil.example.com"},
    )
    assert r2.status_code == 403, r2.text


def test_cookie_post_with_allowed_origin_passes(client):
    client.post(
        "/api/auth/register",
        json={"username": "csrf_session2", "password": "Passw0rd!", "email": "csrf_session2@example.com"},
    )
    r = client.post("/api/auth/logout", headers={"origin": "http://localhost:3000"})
    assert r.status_code == 200, r.text


def test_stripe_webhook_is_exempt_from_csrf(client):
    # /api/stripe/webhook must be reachable with no Origin so Stripe
    # edge IPs can deliver events. (We rely on Stripe signature instead.)
    r = client.post("/api/stripe/webhook", headers={"origin": ""})
    # Signature header missing -> 422 (FastAPI), NOT 403 from CSRF.
    assert r.status_code != 403
