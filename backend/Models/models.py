from pydantic import BaseModel

class User(BaseModel):
    username: str
    password: str

class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
