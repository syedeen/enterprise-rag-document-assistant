from jose import jwt ,JWTError 
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime , timedelta , timezone
import os
from fastapi import Depends , HTTPException , status
from app.database import get_db 
from sqlalchemy.orm import Session 
from app.model import User

pwd_context = CryptContext(schemes=["argon2"],  deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

TOKEN_EXPIRATION_DURATION = 35 
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = "HS256"

def get_pass_hash(password):
    hashed_pass = pwd_context.hash(password)
    return hashed_pass

def verify_pass_hash(password:str , hashed_password:str):
    return pwd_context.verify(password,hashed_password)

def create_access_token(data:dict , expire_data:Optional[timedelta]):
    to_encode = data.copy()
    if expire_data:
        expire = datetime.now(timezone.utc)+expire_data
    else:
        expire = datetime.now(timezone.utc)+timedelta(TOKEN_EXPIRATION_DURATION)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token:str , credentials_exception):
    try:
        payload = jwt.decode(token,SECRET_KEY,ALGORITHM)
        user_id = int(payload["user_id"])
        if user_id is None:
            raise credentials_exception
        
        return user_id
    except JWTError:
        raise credentials_exception


def get_current_user(token:str = Depends(oauth2_scheme) , db:Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = verify_access_token(token, credentials_exception)
    user = db.query(User).filter(User.user_id == int(user_id)).first()

    if user is None:
        raise credentials_exception
    return user

    