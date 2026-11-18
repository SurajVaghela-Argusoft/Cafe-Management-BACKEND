from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, utils
from sqlalchemy.orm import Session
from starlette import schemas, status
from typing import List

from app.models import models

from app.schema import schemas
from app.core.database import get_db
from app.core import security
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.core import oauth2



router = APIRouter(prefix='/user', tags=['User'])


@router.post("/", response_model=schemas.APIResponse[None], status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered."
        )
    user_data = user.model_dump()
    user_data["password"] = security.hash(user.password)
    
    new_user = models.User(**user_data)
 
    
    db.add(new_user)    
    db.commit()    
    db.refresh(new_user)
    
    return schemas.success_response(message=f"user {new_user.email} created successfully")




# @router.post('/login', response_model = schemas.APIResponse[schemas.Token])
# def login(user_credentials : OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)): 
#     user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
#     if not security.verify(user_credentials.password, user.password):
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Invalid Credentials")
#     # role_value = user.role
#     role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
#     access_token = oauth2.c_access_token(data = {"user_id" : user.user_id, "role" : role_value})
#     return schemas.success_response(data={"access_token": access_token, "token_type": "bearer"})

@router.post('/login', response_model=schemas.APIResponse[schemas.Token])
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user or not security.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = oauth2.c_access_token(data={"user_id": user.user_id, "role": role_value})
    refresh_token = oauth2.create_refresh_token(user.user_id, db)

    return schemas.success_response(data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    })


@router.post('/refresh', response_model=schemas.APIResponse[schemas.Token])
def refresh(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    now = datetime.utcnow()

    stored = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == oauth2.hash_token(body.refresh_token)).first()
    if stored is None:
        raise invalid

    if stored.revoked_at is not None:
        db.query(models.RefreshToken).filter(models.RefreshToken.user_id == stored.user_id, models.RefreshToken.revoked_at == None).update({"revoked_at": now})
        db.commit()
        raise invalid

    if stored.expires_at < now:
        raise invalid

    user = db.query(models.User).filter(models.User.user_id == stored.user_id).first()
    if user is None:
        raise invalid

    stored.revoked_at = now
    new_refresh = oauth2.create_refresh_token(user.user_id, db)

    role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = oauth2.c_access_token(data={"user_id": user.user_id, "role": role_value})

    return schemas.success_response(data={"access_token": access_token,"refresh_token": new_refresh, "token_type": "bearer"})


@router.post('/logout', response_model=schemas.APIResponse[None])
def logout(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    stored = db.query(models.RefreshToken).filter(models.RefreshToken.token_hash == oauth2.hash_token(body.refresh_token),models.RefreshToken.revoked_at == None).first()
    if stored:
        stored.revoked_at = datetime.utcnow()
        db.commit()
    return schemas.success_response(message="Logged out")

        
@router.get("/gettable", response_model=schemas.APIResponse[List[schemas.TableResponse]], status_code=status.HTTP_200_OK)
def get_table(db: Session = Depends(get_db)):
    tables = db.query(models.Table).all()
    return schemas.success_response(data=tables)

# doubt : reserved table kewi rite show karu.. interceptors