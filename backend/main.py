from typing import Union
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from passlib.context import CryptContext
import aiomysql
import jwt
import datetime

app = FastAPI()

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Union[datetime.timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.on_event("startup")
async def startup():
    app.state.pool = await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        db='sabor_express',
        minsize=1,
        maxsize=10
    )

@app.on_event("shutdown")
async def shutdown():
    app.state.pool.close()
    await app.state.pool.wait_closed()

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
    async with app.state.pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            result = await cur.fetchone()
            return {"result": result}