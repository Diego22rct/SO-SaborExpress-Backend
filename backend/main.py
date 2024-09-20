from fastapi import FastAPI
from backend.Database.database import init_db, close_db
from backend.Routes import routes

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db(app)

@app.on_event("shutdown")
async def shutdown():
    await close_db(app)

app.include_router(routes.router)