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
