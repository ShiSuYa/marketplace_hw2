from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
import uuid
import jwt
from datetime import datetime, timedelta

app = FastAPI()

# =========================
# CONFIG
# =========================

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 20
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

# =========================
# ROLES
# =========================

class UserRole(str, Enum):
    USER = "USER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"

# =========================
# DATABASES (in-memory)
# =========================

users_db = {}
products_db = {}
orders_db = {}
promo_codes_db = {
    "DISCOUNT10": 10
}

# =========================
# MODELS
# =========================

class RegisterRequest(BaseModel):
    email: str
    password: str
    role: Optional[UserRole] = UserRole.USER

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

# -------- PRODUCTS --------

class ProductCreate(BaseModel):
    name: str
    price: float

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    seller_id: str

# -------- ORDERS --------

class Item(BaseModel):
    name: str
    price: float
    quantity: int

class OrderCreate(BaseModel):
    items: List[Item]
    promo_code: Optional[str] = None

class OrderUpdate(BaseModel):
    items: Optional[List[Item]] = None

class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[Item]
    promo_code: Optional[str]
    total_price: float
    status: str

# -------- PROMO --------

class PromoCreate(BaseModel):
    code: str
    discount_percent: int

# =========================
# UTILS
# =========================

def access_denied():
    raise HTTPException(status_code=403, detail={"error_code": "ACCESS_DENIED"})

def calculate_total(items: List[Item], promo_code: Optional[str]) -> float:
    total = sum(i.price * i.quantity for i in items)

    if promo_code and promo_code in promo_codes_db:
        discount = promo_codes_db[promo_code]
        total *= (1 - discount / 100)

    return round(total, 2)

def create_access_token(user_id: str, role: str):
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: str):
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail={"error_code": "TOKEN_EXPIRED"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error_code": "TOKEN_INVALID"})

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail={"error_code": "TOKEN_INVALID"})

    return {
        "id": payload.get("sub"),
        "role": payload.get("role")
    }

# =========================
# AUTH
# =========================

@app.post("/auth/register")
def register(data: RegisterRequest):
    if data.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())

    users_db[data.email] = {
        "id": user_id,
        "password": data.password,
        "role": data.role
    }

    return {"message": "User registered successfully"}

@app.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = users_db.get(data.email)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": create_access_token(user["id"], user["role"]),
        "refresh_token": create_refresh_token(user["id"])
    }

@app.post("/auth/refresh")
def refresh(data: RefreshRequest):
    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail={"error_code": "REFRESH_TOKEN_INVALID"})

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={"error_code": "REFRESH_TOKEN_INVALID"})

    user_id = payload.get("sub")

    role = None
    for u in users_db.values():
        if u["id"] == user_id:
            role = u["role"]
            break

    return {"access_token": create_access_token(user_id, role)}

# =========================
# PRODUCTS (ROLE MATRIX)
# =========================

@app.get("/products", response_model=List[ProductResponse])
def list_products():
    return list(products_db.values())

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: str):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/products", response_model=ProductResponse)
def create_product(data: ProductCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SELLER, UserRole.ADMIN]:
        access_denied()

    product_id = str(uuid.uuid4())

    product = {
        "id": product_id,
        "name": data.name,
        "price": data.price,
        "seller_id": current_user["id"]
    }

    products_db[product_id] = product
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: str, data: ProductUpdate, current_user: dict = Depends(get_current_user)):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user["role"] == UserRole.USER:
        access_denied()

    if current_user["role"] == UserRole.SELLER and product["seller_id"] != current_user["id"]:
        access_denied()

    if data.name is not None:
        product["name"] = data.name
    if data.price is not None:
        product["price"] = data.price

    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    product = products_db.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if current_user["role"] == UserRole.USER:
        access_denied()

    if current_user["role"] == UserRole.SELLER and product["seller_id"] != current_user["id"]:
        access_denied()

    del products_db[product_id]
    return {"message": "Product deleted"}

# =========================
# ORDERS (ROLE MATRIX)
# =========================

@app.post("/orders", response_model=OrderResponse)
def create_order(data: OrderCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == UserRole.SELLER:
        access_denied()

    order_id = str(uuid.uuid4())

    total_price = calculate_total(data.items, data.promo_code)

    order = {
        "id": order_id,
        "user_id": current_user["id"],
        "items": data.items,
        "promo_code": data.promo_code,
        "total_price": total_price,
        "status": "ACTIVE"
    }

    orders_db[order_id] = order
    return order

@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user["role"] == UserRole.SELLER:
        access_denied()

    if current_user["role"] == UserRole.USER and order["user_id"] != current_user["id"]:
        access_denied()

    return order

@app.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(order_id: str, data: OrderUpdate, current_user: dict = Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user["role"] == UserRole.SELLER:
        access_denied()

    if current_user["role"] == UserRole.USER and order["user_id"] != current_user["id"]:
        access_denied()

    if data.items is not None:
        order["items"] = data.items
        order["total_price"] = calculate_total(order["items"], order["promo_code"])

    return order

@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user["role"] == UserRole.SELLER:
        access_denied()

    if current_user["role"] == UserRole.USER and order["user_id"] != current_user["id"]:
        access_denied()

    order["status"] = "CANCELLED"
    return {"message": "Order cancelled"}

# =========================
# PROMO CODES
# =========================

@app.post("/promo-codes")
def create_promo(data: PromoCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SELLER, UserRole.ADMIN]:
        access_denied()

    promo_codes_db[data.code] = data.discount_percent
    return {"message": "Promo code created"}