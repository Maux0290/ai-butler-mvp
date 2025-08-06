import pytest
from app.db import get_db
from app.models import User, Conversation

@pytest.fixture(autouse=True)
def clear_tables():
    db = next(get_db())
    # 1. Borra primero conversations (la tabla hija)
    db.query(Conversation).delete()
    # 2. Luego borra users (la tabla padre)
    db.query(User).delete()
    db.commit()

