from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core import database
from app.core.database import get_db
from app.schema import schemas
from app.models import models
from app.config import settings

import secrets
import hashlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='user/login')

SECRET_KEY = settings.secret_key  
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minute

def c_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
            
        token_data = schemas.TokenData(id=str(user_id))
    except JWTError:
        raise credentials_exception
        
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.user_id == int(token_data.id)).first()
    
    if not user:
        raise credentials_exception
        
    return user.user_id

def get_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.user_id == int(token_data.id)).first()
    
    if not user:
        raise credentials_exception
        
    return user



REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(user_id: int, db: Session) -> str:
    raw_token = secrets.token_urlsafe(48)
    db.add(models.RefreshToken(user_id=user_id, token_hash=hash_token(raw_token), expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)))
    db.commit()
    return raw_token