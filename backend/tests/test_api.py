def test_registration_and_duplicate(client):
    data={'email':'new@example.com','password':'Password123'}
    assert client.post('/api/auth/register',json=data).status_code==201
    assert client.post('/api/auth/register',json=data).status_code==409

def test_login_rejects_wrong_password(client):
    assert client.post('/api/auth/login',json={'email':'admin@example.com','password':'wrongpass'}).status_code==401

def test_auth_required(client):
    assert client.get('/api/vehicles').status_code in (401,403)

def test_customer_cannot_manage_inventory(client,customer,vehicle):
    assert client.post('/api/vehicles',json=vehicle,headers=customer).status_code==403

def test_admin_crud_and_search(client,admin,vehicle):
    created=client.post('/api/vehicles',json=vehicle,headers=admin)
    assert created.status_code==201
    id=created.json()['id']
    assert len(client.get('/api/vehicles/search?make=toy&min_price=20000',headers=admin).json())==1
    assert client.get('/api/vehicles/search?max_price=100',headers=admin).json()==[]
    changed={**vehicle,'price':'25000.00'}
    assert client.put(f'/api/vehicles/{id}',json=changed,headers=admin).json()['price']=='25000.00'
    assert client.delete(f'/api/vehicles/{id}',headers=admin).status_code==204
    assert client.delete(f'/api/vehicles/{id}',headers=admin).status_code==404

def test_purchase_decrements_and_prevents_oversell(client,admin,customer,vehicle):
    id=client.post('/api/vehicles',json={**vehicle,'quantity':1},headers=admin).json()['id']
    assert client.post(f'/api/vehicles/{id}/purchase',headers=customer).json()['quantity']==0
    assert client.post(f'/api/vehicles/{id}/purchase',headers=customer).status_code==409

def test_restock_admin_only(client,admin,customer,vehicle):
    id=client.post('/api/vehicles',json=vehicle,headers=admin).json()['id']
    assert client.post(f'/api/vehicles/{id}/restock',json={'quantity':3},headers=customer).status_code==403
    assert client.post(f'/api/vehicles/{id}/restock',json={'quantity':3},headers=admin).json()['quantity']==5

def test_validation(client,admin,vehicle):
    assert client.post('/api/vehicles',json={**vehicle,'price':-1},headers=admin).status_code==422
    assert client.post('/api/vehicles',json={**vehicle,'quantity':-2},headers=admin).status_code==422

def test_search_rejects_inverted_price_range(client,admin):
    response=client.get('/api/vehicles/search?min_price=50000&max_price=10000',headers=admin)
    assert response.status_code==422

def test_customers_can_search_and_cannot_restock(client,admin,customer,vehicle):
    created=client.post('/api/vehicles',json=vehicle,headers=admin)
    vehicle_id=created.json()['id']
    assert client.get('/api/vehicles/search?model=Cam',headers=customer).status_code==200
    assert client.post(f'/api/vehicles/{vehicle_id}/restock',json={'quantity':1},headers=customer).status_code==403

def test_registration_never_accepts_client_role(client):
    response=client.post('/api/auth/register',json={'email':'role@example.com','password':'Password123','role':'admin'})
    assert response.status_code==201
    login=client.post('/api/auth/login',json={'email':'role@example.com','password':'Password123'})
    assert login.json()['role']=='customer'

def test_startup_rejects_short_jwt_secret(monkeypatch):
    import pytest
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setenv('JWT_SECRET', 'too-short')
    with pytest.raises(RuntimeError, match='at least 32 bytes'):
        with TestClient(app):
            pass

def test_vehicle_listing_returns_inventory(client,admin,vehicle):
    assert client.post('/api/vehicles',json=vehicle,headers=admin).status_code==201
    response=client.get('/api/vehicles',headers=admin)
    assert response.status_code==200
    assert response.json()[0]['model']=='Camry'

def test_malformed_bearer_token_is_rejected(client):
    response=client.get('/api/vehicles',headers={'Authorization':'Bearer not-a-valid-jwt'})
    assert response.status_code==401

def test_blank_vehicle_text_and_missing_restock_are_rejected(client,admin,vehicle):
    assert client.post('/api/vehicles',json={**vehicle,'make':'  '},headers=admin).status_code==422
    assert client.post('/api/vehicles/999/restock',json={'quantity':1},headers=admin).status_code==404

def test_hosted_postgres_urls_use_psycopg_driver(monkeypatch):
    from app.main import database_url
    monkeypatch.setenv('DATABASE_URL', 'postgres://demo:password@db.example.test:5432/autovault')
    assert database_url() == 'postgresql+psycopg://demo:password@db.example.test:5432/autovault'
    monkeypatch.setenv('DATABASE_URL', 'postgresql://demo:password@db.example.test:5432/autovault')
    assert database_url() == 'postgresql+psycopg://demo:password@db.example.test:5432/autovault'

def test_cors_origins_are_explicit_and_trimmed(monkeypatch):
    from app.main import allowed_origins
    monkeypatch.setenv('CORS_ORIGINS', ' https://autovault.example , https://preview.example/ ')
    assert allowed_origins() == ['https://autovault.example', 'https://preview.example']
    monkeypatch.setenv('CORS_ORIGINS', '*')
    import pytest
    with pytest.raises(RuntimeError, match='wildcard origins'):
        allowed_origins()
