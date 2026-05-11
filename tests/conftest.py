import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import Base, get_db


@pytest.fixture(scope="function")
def client():
    db_file = "./test_test.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file}"

    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    engine.dispose()
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except:
            pass
