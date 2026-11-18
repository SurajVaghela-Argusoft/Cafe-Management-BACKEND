from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
import pydantic
from sqlalchemy.orm import Session
from typing import List

from app.core import enum, oauth2, security
from app.core.database import get_db
from app.models import models
from app.schema import schemas

router = APIRouter(prefix='/food', tags=['food'])

@router.get("/getcategories", response_model=schemas.APIResponse[List[schemas.CategoryResponse]], status_code = status.HTTP_200_OK)
def get_categories(db: Session = Depends(get_db)):
    category = db.query(models.MenuCategory).all()
    return schemas.success_response(data=category)



@router.get("/getitems", response_model=schemas.APIResponse[List[schemas.ItemResponse]], status_code = status.HTTP_200_OK)
def get_items(db: Session = Depends(get_db)):
    item = db.query(models.MenuItem).all()
    return schemas.success_response(data=item)