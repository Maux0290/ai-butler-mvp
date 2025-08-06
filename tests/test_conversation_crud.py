import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def user_and_token():
    user = {
        "username": "convuser",
        "email": "convuser@ai-butler.com",
        "password": "TestConv2024"
    }
    client.post("/register/", json=user)
    login = client.post("/login/", data={"username": user["username"], "password": user["password"]})
    token = login.json()["access_token"]
    return user, token

def test_create_and_list_conversation(user_and_token):
    user, token = user_and_token
    payload = {
        "business": "LegacyWealth",
        "question": "¿Cómo mejoro mis finanzas?"
    }
    r = client.post("/ask-rag/", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    response = client.get("/conversations/")
    assert response.status_code == 200
    conversations = response.json()
    assert any(c["question"] == payload["question"] for c in conversations)
