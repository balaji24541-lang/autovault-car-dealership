import os
os.environ['DATABASE_URL']='sqlite:///./test_dealership.db'
os.environ['JWT_SECRET']='test-secret-only'
import pytest
from fastapi.testclient import TestClient
from app.main import app, Base, engine, SessionLocal, User, password_hash

@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(User(email='admin@example.com', password_hash=password_hash.hash('AdminPass123'), role='admin'))
        db.commit()
    with TestClient(app) as c: yield c
    Base.metadata.drop_all(bind=engine)

def token(client,email,password):
    r=client.post('/api/auth/login',json={'email':email,'password':password})
    assert r.status_code==200, r.text
    return {'Authorization':'Bearer '+r.json()['access_token']}

@pytest.fixture
def admin(client): return token(client,'admin@example.com','AdminPass123')
@pytest.fixture
def customer(client):
    client.post('/api/auth/register',json={'email':'user@example.com','password':'Customer123'})
    return token(client,'user@example.com','Customer123')
@pytest.fixture
def vehicle(): return {'make':'Toyota','model':'Camry','category':'Sedan','price':'24500.00','quantity':2}
