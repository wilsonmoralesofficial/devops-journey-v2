from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"mensaje": "Mi primera API containerizada", "version": "v2"}

def test_salud():
    r = client.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"