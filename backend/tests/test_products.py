import pytest

@pytest.fixture
def auth_token(client):
    client.post(
        "/api/auth/register",
        json={"username": "produser", "password": "password123"}
    )
    res = client.post(
        "/api/auth/login",
        data={"username": "produser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return res.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

def test_create_product(client, auth_headers):
    response = client.post(
        "/api/products/",
        json={"product_name": "Test Product", "own_price": "1000", "category": "Test"},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Test Product"
    assert "id" in data

def test_get_products(client, auth_headers):
    # Create product first
    client.post(
        "/api/products/",
        json={"product_name": "Test Product 2", "own_price": "2000"},
        headers=auth_headers
    )
    response = client.get("/api/products/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(p["product_name"] == "Test Product 2" for p in data)

def test_add_competitor(client, auth_headers):
    # Create product
    res = client.post(
        "/api/products/",
        json={"product_name": "Comp Test", "own_price": "3000"},
        headers=auth_headers
    )
    prod_id = res.json()["id"]

    # Add competitor
    add_res = client.post(
        f"/api/products/{prod_id}/competitors/",
        json={"competitor_name": "Amazon", "url": "https://amazon.co.jp/dp/test"},
        headers=auth_headers
    )
    assert add_res.status_code == 200
    data = add_res.json()
    assert data["competitor_name"] == "Amazon"

def test_add_competitor_wrong_owner(client):
    # Create user1 product
    client.post(
        "/api/auth/register",
        json={"username": "user1", "password": "password123"}
    )
    tok1 = client.post(
        "/api/auth/login",
        data={"username": "user1", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    ).json()["access_token"]

    res1 = client.post(
        "/api/products/",
        json={"product_name": "User1 Product", "own_price": "1000"},
        headers={"Authorization": f"Bearer {tok1}"}
    )
    prod_id = res1.json()["id"]

    # Try to add comp with user2 (auth_headers)
    # Register auth_headers user
    client.post(
        "/api/auth/register",
        json={"username": "user2", "password": "password123"}
    )
    tok2 = client.post(
        "/api/auth/login",
        data={"username": "user2", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    ).json()["access_token"]
    
    add_res = client.post(
        f"/api/products/{prod_id}/competitors/",
        json={"competitor_name": "Amazon", "url": "https://amazon.co.jp/dp/test"},
        headers={"Authorization": f"Bearer {tok2}"}
    )
    assert add_res.status_code == 404 # Depends on your error implementation, typically 404 or 403
