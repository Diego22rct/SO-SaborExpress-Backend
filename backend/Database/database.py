from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import FastAPI


engine = create_async_engine("mariadb+pymysql://root:root@localhost:3306/sabor_express?charset=utf8mb4")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

async def init_db(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.state.db = SessionLocal

async def close_db(app: FastAPI):
    await engine.dispose()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()