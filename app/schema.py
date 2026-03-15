from pydantic import BaseModel , ConfigDict , EmailStr
from datetime import datetime

class FileResponse(BaseModel):
    file_id:int
    file_url:str
    file_name:str
    model_config = ConfigDict(extra="forbid")




class QueryCreate(BaseModel):
    query:str
    file_name:str


class UserCreate(BaseModel):
    username:str
    email:EmailStr
    password:str


class FileDelete(BaseModel):
    filename:str
    


class UserResponse(BaseModel):
    username: str
    email: EmailStr
    created_at: datetime

    class ConfigDict:
        from_attributes = True


class Token(BaseModel):
    access_token:str
    token_type:str


