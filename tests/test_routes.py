def test_affiliate_info(client):
    r = client.get("/api/affiliate/info")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert "affiliate_id" in data
    assert "domain" in data


def test_leads_public_alias(client):
    payload = {
        "email": "test@example.com",
        "origin": "BLR",
        "destination": "DXB",
        "departureDate": "2026-03-01",
        "last_seen_price": 12345,
        "currency": "INR",
    }
    r = client.post("/api/leads", json=payload)
    assert r.status_code == 202
    data = r.json()
    assert data.get("status") == "accepted"
