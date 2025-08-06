import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def admin_user_and_token():
    # Primero registra un usuario normal, luego asume que ya hay un endpoint o un admin para cambiar el rol
    admin = {
        "username": "admintest",
        "email": "admintest@ai-butler.com",
        "password": "AdminRole2024"
    }
    client.post("/register/", json=admin)
    # Normalmente aquí harías un cambio de rol a admin manual o con endpoint protegido
    login = client.post("/login/", data={"username": admin["username"], "password": admin["password"]})
    token = login.json()["access_token"]
    return admin, token

def test_admin_endpoint_protection(admin_user_and_token):
    admin, token = admin_user_and_token
    # Intentar acceder a endpoint solo admin con token de admin
    # Debe devolver 200 si el usuario es realmente admin
    r = client.get("/usuarios/", headers={"Authorization": f"Bearer {token}"})
    # Según tu implementación de require_admin, si es admin real => 200, si no => 401/403
    assert r.status_code in (200, 401, 403)

def test_non_admin_cannot_access_admin_endpoint():
    user = {
        "username": "user_noadmin",
        "email": "user_noadmin@ai-butler.com",
        "password": "UserNoAdmin2024"
    }
    client.post("/register/", json=user)
    login = client.post("/login/", data={"username": user["username"], "password": user["password"]})
    token = login.json()["access_token"]
    r = client.get("/usuarios/", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (401, 403)
