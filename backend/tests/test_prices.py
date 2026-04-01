import pytest
import datetime

@pytest.fixture
def auth_token(client):
    client.post("/api/auth/register", json={"username": "priceuser", "password": "password123"})
    return client.post(
        "/api/auth/login",
        data={"username": "priceuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    ).json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def setup_product_and_competitor(client, auth_headers):
    # 1. Add product (own_price = 1000)
    res_p = client.post(
        "/api/products/",
        json={"product_name": "Test Item", "own_price": "1000"},
        headers=auth_headers
    )
    assert res_p.status_code == 200, res_p.text
    prod_id = res_p.json()["id"]

    # 2. Add competitor
    res_c = client.post(
        f"/api/products/{prod_id}/competitors/",
        json={"competitor_name": "RivalShop", "url": "https://rival.com/item"},
        headers=auth_headers
    )
    assert res_c.status_code == 200, res_c.text
    comp_url_id = res_c.json()["id"]

    return prod_id, comp_url_id

def test_price_alerts_and_history(client, auth_headers, setup_product_and_competitor, db_session):
    import models
    prod_id, comp_url_id = setup_product_and_competitor

    # Insert fake price history manually since we don't have scraper running here
    from datetime import timezone
    hist = models.PriceHistory(
        competitor_url_id=comp_url_id,
        price=800,  # lower than own_price(1000)
        stock_status="在庫あり",
        scraped_at=datetime.datetime.now(timezone.utc)
    )
    db_session.add(hist)
    db_session.commit()

    # Get Alerts
    res = client.get("/api/prices/alerts", headers=auth_headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) == 1
    assert alerts[0]["product_id"] == prod_id
    assert float(alerts[0]["own_price"]) == 1000.0
    assert float(alerts[0]["competitor_price"]) == 800.0
    assert float(alerts[0]["price_diff"]) == 200.0

    # Get History
    res_hist = client.get(f"/api/prices/{prod_id}/history", headers=auth_headers)
    assert res_hist.status_code == 200
    history = res_hist.json()
    assert len(history) == 1
    assert float(history[0]["price"]) == 800.0
