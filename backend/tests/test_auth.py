import pytest

def test_register(client):
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_register_duplicate(client):
    client.post(
        "/api/auth/register",
        json={"username": "testuser2", "password": "password123"}
    )
    response = client.post(
        "/api/auth/register",
        json={"username": "testuser2", "password": "password123"}
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_login(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={"username": "loginuser", "password": "password123"}
    )
    # Then Login
    response = client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"username": "wrongpwuser", "password": "password123"}
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "wrongpwuser", "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 401
