import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

@pytest.fixture
def user_data():
    return {
        "username": "user_test",
        "email": "user_test@ai-butler.com",
        "password": "Test123456"
    }

@pytest.fixture
def admin_data():
    return {
        "username": "admin_test",
        "email": "admin_test@ai-butler.com",
        "password": "AdminTest1234"
    }

def register_user(user_data):
    return client.post("/register/", json=user_data)

def login_user(username, password):
    response = client.post("/login/", data={"username": username, "password": password})
    # ----------- CAMBIO AQUÍ -----------
    assert response.status_code == 200, f"Login fallo con status {response.status_code}: {response.json()}"
    return response.json()["access_token"]

def test_register_and_login_user(user_data):
    r = register_user(user_data)
    assert r.status_code == 200
    token = login_user(user_data["username"], user_data["password"])
    assert token

def test_admin_cannot_be_created_by_public(user_data):
    user_data_with_role = user_data.copy()
    user_data_with_role["role"] = "admin"
    r = client.post("/register/", json=user_data_with_role)
    assert r.status_code == 200
    token = login_user(user_data["username"], user_data["password"])
    profile = client.get("/mi-perfil/", headers={"Authorization": f"Bearer {token}"})
    assert profile.json()["role"] == "user"

def test_admin_protected_endpoints(admin_data):
    r = register_user(admin_data)
    assert r.status_code == 200
    admin_token = login_user(admin_data["username"], admin_data["password"])
    r2 = client.get("/usuarios/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 403 or r2.status_code == 401

def test_role_change_requires_admin(user_data, admin_data):
    register_user(user_data)
    register_user(admin_data)
    user_token = login_user(user_data["username"], user_data["password"])
    r = client.patch(
        "/admin/users/1/role/",
        data={"new_role": "admin"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert r.status_code in (401, 403)

