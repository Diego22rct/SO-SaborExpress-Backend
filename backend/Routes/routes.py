from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from backend.Models.models import User, Product
from backend.Services.services import verify_password, get_password_hash, create_access_token
from backend.Database.database import get_db

router = APIRouter()

@router.get("/products", response_model=List[Product])
async def list_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products

@router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/products", response_model=Product)
async def create_product(product: Product, db: AsyncSession = Depends(get_db)):
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

@router.post("/signup")
async def signup(user: User, db: AsyncSession = Depends(get_db)):
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    db.add(user)
    await db.commit()
    return {"message": "User created successfully"}

@router.post("/signin")
async def signin(user: User, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user.username))
    db_user = result.scalar_one_or_none()
    if db_user and verify_password(user.password, db_user.password):
        access_token = create_access_token(data={"sub": user.username})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=400, detail="Invalid username or password")

@router.get("/")
async def read_root(db: AsyncSession = Depends(get_db)):
    result = await db.execute("SELECT 1")
    return {"result": result.scalar()}