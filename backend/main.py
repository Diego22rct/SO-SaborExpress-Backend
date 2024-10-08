from typing import List, Union
from fastapi import FastAPI
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
import aiomysql
import jwt
import datetime


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available: bool
    image: str

class Category(BaseModel):
    id: int
    name: str
    description: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Union[datetime.timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc)+ expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


app = FastAPI(
    title="Sabor Express API",
    description="API for the Sabor Express application",
    port=8080
)

@app.on_event("startup")
async def startup():
    try:
        app.state.pool = await aiomysql.create_pool(
            host='localhost',
            port=3306,
            user='root',
            password='root',
            db='sabor_express',
            minsize=1,
            maxsize=10
        )
        print("Connected to the database")
        # Test the connection
        async with app.state.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                print("Test query result:", result)
    except Exception as e:
        print("Error during connection to the database: ", e)

@app.on_event("shutdown")
async def shutdown():
    app.state.pool.close()
    await app.state.pool.wait_closed()

@app.get("/categories", response_model=List[Category])
async def list_categories():
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, description FROM categories")
            result = await cur.fetchall()
            categories = [Category(id=row[0], name=row[1], description=row[2]) for row in result]
            return categories

@app.get("/products", response_model=List[Product])
async def list_products():
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, description, price, available, image FROM products")
            result = await cur.fetchall()
            products = [Product(id=row[0], name=row[1], description=row[2], price=row[3], available=row[4], image=row[5]) for row in result]
            return products

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id, name, description, price FROM products WHERE id = %s", (product_id,))
            result = await cur.fetchone()
            if result:
                return Product(id=result[0], name=result[1], description=result[2], price=result[3])
            else:
                raise HTTPException(status_code=404, detail="Product not found")

@app.post("/products", response_model=Product)
async def create_product(product: Product):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT INTO products (name, description, price) VALUES (%s, %s, %s)",
                (product.name, product.description, product.price)
            )
            await conn.commit()
            product_id = cur.lastrowid
            return {**product.model_dump(), "id": product_id}


@app.post("/signup")
async def signup(user: User):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            hashed_password = get_password_hash(user.password)
            await cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed_password))
            await conn.commit()
            return {"message": "User created successfully"}

@app.post("/signin")
async def signin(user: User):
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT password FROM users WHERE username = %s", (user.username,))
            result = await cur.fetchone()
            if result and verify_password(user.password, result[0]):
                access_token = create_access_token(data={"sub": user.username})
                return {"access_token": access_token, "token_type": "bearer"}
            else:
                raise HTTPException(status_code=400, detail="Invalid username or password")

@app.get("/")
async def read_root():
    try: 
        async with app.state.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                result = await cur.fetchone()
                if result:
                    return {"connection": "OK"}
                else:
                    return {"connection": "Error"}
    except Exception as e:
        return {"connection": "Error", "error": str(e)}
