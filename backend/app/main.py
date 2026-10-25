import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from contextlib import asynccontextmanager
import jwt
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from pwdlib import PasswordHash
from sqlalchemy import create_engine, String, Numeric, Integer, ForeignKey, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.exc import IntegrityError

def database_url():
    """Normalize hosted PostgreSQL URLs for the psycopg 3 SQLAlchemy driver."""
    url = os.getenv('DATABASE_URL', 'sqlite:///./dealership.db')
    if url.startswith('postgres://'):
        return 'postgresql+psycopg://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        return 'postgresql+psycopg://' + url[len('postgresql://'):]
    return url

DATABASE_URL = database_url()
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine)
password_hash = PasswordHash.recommended()
security = HTTPBearer()

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='customer')
class Vehicle(Base):
    __tablename__ = 'vehicles'
    id: Mapped[int] = mapped_column(primary_key=True)
    make: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(80))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
class Purchase(Base):
    __tablename__ = 'purchases'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey('vehicles.id'))
    price_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2))

class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
class VehicleInput(BaseModel):
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=80)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    quantity: int = Field(ge=0)

    @model_validator(mode='after')
    def validate_text_fields(self):
        for name in ('make', 'model', 'category'):
            if not getattr(self, name).strip():
                raise ValueError(f'{name} must not be blank')
        return self

class VehicleOutput(VehicleInput):
    id: int
    model_config = ConfigDict(from_attributes=True)
class StockInput(BaseModel):
    quantity: int = Field(gt=0)

def jwt_secret():
    secret = os.getenv('JWT_SECRET', '')
    if len(secret.encode('utf-8')) < 32:
        raise RuntimeError('JWT_SECRET must contain at least 32 bytes')
    return secret

@asynccontextmanager
async def lifespan(app):
    jwt_secret()
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title='Car Dealership Inventory API', version='1.0.0', lifespan=lifespan)
def allowed_origins():
    origins = [origin.strip().rstrip('/') for origin in os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',') if origin.strip()]
    if not origins or '*' in origins:
        raise RuntimeError('CORS_ORIGINS must contain explicit browser origins; wildcard origins are not allowed')
    return origins

app.add_middleware(CORSMiddleware, allow_origins=allowed_origins(), allow_credentials=True, allow_methods=['*'], allow_headers=['*'])

def db_session():
    with SessionLocal() as db: yield db

def current_user(auth: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(db_session)):
    try:
        data = jwt.decode(auth.credentials, jwt_secret(), algorithms=['HS256'])
        user = db.get(User, int(data['sub']))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, 'Invalid or expired token')
    if user is None: raise HTTPException(401, 'User no longer exists')
    return user

def admin_only(user: User = Depends(current_user)):
    if user.role != 'admin': raise HTTPException(403, 'Admin access required')
    return user

def get_vehicle(db, id):
    vehicle = db.get(Vehicle, id)
    if vehicle is None: raise HTTPException(404, 'Vehicle not found')
    return vehicle

@app.post('/api/auth/register', status_code=201)
def register(body: Credentials, db: Session = Depends(db_session)):
    user = User(email=str(body.email).lower(), password_hash=password_hash.hash(body.password), role='customer')
    db.add(user)
    try: db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Email already registered')
    return {'message':'Account created'}

@app.post('/api/auth/login')
def login(body: Credentials, db: Session = Depends(db_session)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if not user or not password_hash.verify(body.password, user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    token = jwt.encode({'sub':str(user.id), 'exp':datetime.now(timezone.utc)+timedelta(hours=2)}, jwt_secret(), algorithm='HS256')
    return {'access_token':token,'token_type':'bearer','role':user.role}

@app.get('/api/vehicles', response_model=list[VehicleOutput])
def vehicles(db: Session = Depends(db_session), user: User = Depends(current_user)):
    return db.scalars(select(Vehicle).order_by(Vehicle.id.desc())).all()

@app.get('/api/vehicles/search', response_model=list[VehicleOutput])
def search(make: Optional[str]=None, model: Optional[str]=None, category: Optional[str]=None, min_price: Optional[Decimal]=Query(None,ge=0), max_price: Optional[Decimal]=Query(None,ge=0), db: Session=Depends(db_session), user: User=Depends(current_user)):
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(422, 'min_price must be less than or equal to max_price')
    q = select(Vehicle)
    if make: q=q.where(Vehicle.make.ilike(f'%{make}%'))
    if model: q=q.where(Vehicle.model.ilike(f'%{model}%'))
    if category: q=q.where(Vehicle.category.ilike(f'%{category}%'))
    if min_price is not None: q=q.where(Vehicle.price >= min_price)
    if max_price is not None: q=q.where(Vehicle.price <= max_price)
    return db.scalars(q.order_by(Vehicle.id.desc())).all()

@app.post('/api/vehicles', response_model=VehicleOutput, status_code=201)
def add_vehicle(body: VehicleInput, db: Session=Depends(db_session), admin: User=Depends(admin_only)):
    v=Vehicle(**body.model_dump()); db.add(v); db.commit(); db.refresh(v); return v

@app.put('/api/vehicles/{id}', response_model=VehicleOutput)
def update_vehicle(id:int, body:VehicleInput, db:Session=Depends(db_session), admin:User=Depends(admin_only)):
    v=get_vehicle(db,id)
    for key,value in body.model_dump().items(): setattr(v,key,value)
    db.commit(); db.refresh(v); return v

@app.delete('/api/vehicles/{id}', status_code=204)
def delete_vehicle(id:int, db:Session=Depends(db_session), admin:User=Depends(admin_only)):
    v=get_vehicle(db,id); db.delete(v); db.commit()

@app.post('/api/vehicles/{id}/purchase', response_model=VehicleOutput)
def purchase(id:int, db:Session=Depends(db_session), user:User=Depends(current_user)):
    # Atomic conditional UPDATE prevents stock from becoming negative under concurrency.
    from sqlalchemy import update
    result=db.execute(update(Vehicle).where(Vehicle.id==id, Vehicle.quantity>0).values(quantity=Vehicle.quantity-1))
    if result.rowcount != 1:
        db.rollback()
        get_vehicle(db,id)
        raise HTTPException(409, 'Out of stock')
    v=get_vehicle(db,id)
    db.add(Purchase(user_id=user.id, vehicle_id=id, price_paid=v.price))
    db.commit(); db.refresh(v); return v

@app.post('/api/vehicles/{id}/restock', response_model=VehicleOutput)
def restock(id:int, body:StockInput, db:Session=Depends(db_session), admin:User=Depends(admin_only)):
    from sqlalchemy import update
    result=db.execute(update(Vehicle).where(Vehicle.id==id).values(quantity=Vehicle.quantity+body.quantity))
    if result.rowcount != 1:
        db.rollback(); raise HTTPException(404,'Vehicle not found')
    db.commit(); return get_vehicle(db,id)
