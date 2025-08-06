import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_register_and_login():
    user = {
        "username": "testuser_login",
        "email": "testuser_login@ai-butler.com",
        "password": "Test123456"
    }
    r = client.post("/register/", json=user)
    assert r.status_code == 200
    login = client.post("/login/", data={"username": user["username"], "password": user["password"]})
    # ----------- CAMBIO AQUÍ -----------
    assert login.status_code == 200, f"Login fallo con status {login.status_code}: {login.json()}"
    token = login.json()["access_token"]
    assert token

def test_register_duplicate_user():
    user = {
        "username": "testuser_login_dup",
        "email": "testuser_login_dup@ai-butler.com",
        "password": "Test123456"
    }
    r1 = client.post("/register/", json=user)
    assert r1.status_code == 200
    r2 = client.post("/register/", json=user)
    assert r2.status_code == 400
    assert r2.json()["detail"] == "Usuario o email ya existe"

def test_wrong_password():
    user = {
        "username": "testuser_wrongpw",
        "email": "testuser_wrongpw@ai-butler.com",
        "password": "CorrectPass123"
    }
    client.post("/register/", json=user)
    login = client.post("/login/", data={"username": user["username"], "password": "WrongPass"})
    assert login.status_code == 401

def test_get_profile_requires_auth():
    r = client.get("/perfil/")
    assert r.status_code == 401 or r.status_code == 403

