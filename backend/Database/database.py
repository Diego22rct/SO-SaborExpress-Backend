import aiomysql
from fastapi import FastAPI

async def init_db(app: FastAPI):
    app.state.pool = await aiomysql.create_pool(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        db='sabor_express',
        minsize=1,
        maxsize=10
    )

async def close_db(app: FastAPI):
    app.state.pool.close()
    await app.state.pool.wait_closed()
