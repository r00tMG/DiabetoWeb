from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username:str
    adresse: str
    email: EmailStr
    password: str
    confirm_password: str

class UserResponse(BaseModel):
    username: str
    adresse: str
    email: EmailStr

    class Config:
        orm_mod = True

