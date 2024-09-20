from fastapi import APIRouter, HTTPException, Depends
from typing import List
from backend.models import User, Product
from backend.services import verify_password, get_password_hash, create_access_token
from fastapi import FastAPI

router = APIRouter()

@router.get("/products", response_model=List[Product])
async def list_products(app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, description, price FROM products")
            result = await cur.fetchall()
            products = [Product(id=row[0], name=row[1], description=row[2], price=row[3]) for row in result]
            return products

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int, app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, description, price FROM products WHERE id = %s", (product_id,))
            result = await cur.fetchone()
            if result:
                return Product(id=result[0], name=result[1], description=result[2], price=result[3])
            else:
                raise HTTPException(status_code=404, detail="Product not found")

@router.post("/products", response_model=Product)
async def create_product(product: Product, app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO products (name, description, price) VALUES (%s, %s, %s)",
                (product.name, product.description, product.price)
            )
            await conn.commit()
            product_id = cur.lastrowid
            return {**product.model_dump(), "id": product_id}

@router.post("/signup")
async def signup(user: User, app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            hashed_password = get_password_hash(user.password)
            await cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed_password))
            await conn.commit()
            return {"message": "User created successfully"}

@router.post("/signin")
async def signin(user: User, app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT password FROM users WHERE username = %s", (user.username,))
            result = await cur.fetchone()
            if result and verify_password(user.password, result[0]):
                access_token = create_access_token(data={"sub": user.username})
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(status_code=400, detail="Invalid username or password")

@router.get("/")
async def read_root(app: FastAPI):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            result = await cur.fetchone()
            return {"result": result}