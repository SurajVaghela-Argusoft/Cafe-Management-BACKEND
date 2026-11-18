import os

from fastapi import FastAPI

from app.core import database
from app.models import models
from app.routers import admin, customer, employee, food, user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

database.Base.metadata.create_all(bind=database.engine)

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:5174", 
    "http://127.0.0.1:5174",
        

]

frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.append(frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            
    allow_credentials=True,
    allow_methods=["*"],         
    allow_headers=["*"],            
)


app.include_router(user.router)
app.include_router(admin.router)
app.include_router(food.router)
app.include_router(customer.router)
app.include_router(employee.router)

@app.get("/")
def root():
    return {"msg": "Hello Naina"}
