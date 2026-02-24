from fastapi import FastAPI , File , UploadFile , HTTPException , status , Depends
from sqlalchemy.orm import Session 
from sqlalchemy import select , or_ , and_
from app.database import Base , engine , get_db
from app.model import Files , User
from app.schema import FileResponse, QueryCreate , UserCreate , Token , UserResponse
import boto3
from app.rag_test import save_file
from app.rag_query import get_results
from app.auth import get_pass_hash , verify_pass_hash , OAuth2PasswordRequestForm , create_access_token , get_current_user , TOKEN_EXPIRATION_DURATION
from datetime import datetime , timezone , timedelta

from app.vector_db import create_collection



MAX_LOGIN_ATTEMPTS = 36
LOCKIN_DURATION_MINUTES = 15

s3 = boto3.client("s3")
app = FastAPI()
Base.metadata.create_all(bind=engine)


BUCKET_NAME = "rag-fastapi"
FOLDER_NAME = "pdfs/"


@app.on_event("startup")
def startup():
    create_collection()
    

@app.get("/test")
def get():    
    return "reached server"

@app.post("/uploadfile/" , response_model=FileResponse)
async def create_upload_file(file: UploadFile , db:Session = Depends(get_db) ,user : User = Depends(get_current_user)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="file must be a pdf type")
    
    save_file(file , user.user_id)

    
    s3key = f"{FOLDER_NAME}{file.filename}"
    file.file.seek(0,2)
    file__size = file.file.tell()
    file.file.seek(0)
    

    s3.upload_fileobj(file.file,BUCKET_NAME,s3key,ExtraArgs={
        "ContentType":"application/pdf"
    })
    file__url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{s3key}"

    new_file = Files(
        file_name = file.filename,
        file_url = file__url,
        file_size = file__size,
        mime_type = file.content_type,
        user_id = user.user_id
    )


    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    url = s3.generate_presigned_url(
        'get_object',
        Params={
            "Bucket":BUCKET_NAME,
            "Key":s3key
        },
        ExpiresIn=3600
    )

    return {"file_id":new_file.file_id,"file_url":url,"file_name":file.filename}



@app.post("/query")
def query(query:QueryCreate , user:User = Depends(get_current_user)):
    return get_results(query.query , query.file_name , user.user_id)


@app.post("/users/register" , response_model=UserResponse)
def register(user:UserCreate , db:Session= Depends(get_db)):
    stmt1 = select(User).where(User.username == user.username)
    existing_username = db.scalars(stmt1).first()


    stmt2 = select(User).where(User.email == user.email)
    existing_email = db.scalars(stmt2).first()

    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="username already registered")

    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="email already registered")
    
    new_user = User(
        username = user.username,
        email = user.email,
        password = get_pass_hash(user.password)
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "username":user.username,
        "email":user.email,
        "created_at":datetime.now(timezone.utc)
    }



@app.post("/users/login" ,response_model=Token )
def login_user(form_data:OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_db)):

    stmt = select(User).where(
        or_(
            User.username == form_data.username,
            User.email == form_data.username
        )
    )
    existing_user = db.scalars(stmt).first()

    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid_credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if not existing_user:
        verify_pass_hash("dummy_password",get_pass_hash("dummy_password"))
        raise invalid_credentials_exception
    
    if existing_user.locked_until and existing_user.locked_until > datetime.now(timezone.utc):
        remaining_time = (existing_user.locked_until - datetime.now(timezone.utc)).seconds //60
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Account is locked. Try again in {remaining_time} minutes "
        )
    

    if not existing_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    if not verify_pass_hash( form_data.password, existing_user.password):
        existing_user.failed_login_attempts += 1
        if existing_user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            existing_user.locked_until = (datetime.now(timezone.utc) + timedelta(minutes = LOCKIN_DURATION_MINUTES))
            db.commit()
            time_remaining = (existing_user.locked_until - datetime.now(timezone.utc)).seconds//60
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to too many failed attempts  , Try again in {LOCKIN_DURATION_MINUTES} minutes"
            )
        db.commit()
        raise invalid_credentials_exception
    existing_user.failed_login_attempts = 0
    existing_user.locked_until = None
    existing_user.last_login = datetime.now(timezone.utc)
    db.commit()
    

    access_token = create_access_token(
        data = {"user_id":existing_user.user_id},
        expire_data=timedelta(minutes=TOKEN_EXPIRATION_DURATION))

    return {
        "access_token": access_token,
        "token_type":"bearer"
    }



#get user
@app.get("/users/me")
def get_current_user_info(current_user : User = Depends(get_current_user)):
    return current_user

    

    










    

    



