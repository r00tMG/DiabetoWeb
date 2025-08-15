from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


# Mapper User
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
        from_attributes = True

#Mapper Prediction
class Prediction(BaseModel):
    patientid : int
    result:str
    created_ad: datetime

class PredictionResponse(BaseModel):
    patientid : int
    result:str
    created_ad: datetime

    class Config:
        from_attributes = True


# Mapper Patient
class Patient(BaseModel):
    medecin: UserResponse
    name: str
    age: int
    sex: str
    glucose: float
    bmi : float
    bloodpressure: float
    pedigree: float
    created_at: datetime


class PatientResponse(BaseModel):
    doctorid: User
    name: str
    age: int
    sex: str
    glucose: float
    bmi : float
    bloodpressure: float
    pedigree: float
    predictions: List[PredictionResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

