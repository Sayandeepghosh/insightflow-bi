from fastapi.testclient import TestClient
from insightflow.api import app

client = TestClient(app)

def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_api_schema():
    res = client.get("/v1/schema")
    assert res.status_code == 200
    assert "products" in res.json()["tables"]

def test_api_query_endpoint():
    res = client.post("/v1/query", json={"prompt": "regional revenue breakdown"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_safe"] is True
    assert len(data["rows"]) > 0

def test_api_query_rejection():
    res = client.post("/v1/query", json={"prompt": "hack", "raw_sql": "DROP TABLE accounts;"})
    assert res.status_code == 400
