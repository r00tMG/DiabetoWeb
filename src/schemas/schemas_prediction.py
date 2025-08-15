from datetime import datetime

from pydantic import BaseModel

from src.schemas import PatientResponse


#Mapper Prediction
class Prediction(BaseModel):
    patientid : int
    result:str
    created_ad: datetime

class PredictionResponse(BaseModel):
    patientid : int
    patient: PatientResponse
    result:str
    created_ad: datetime

    class Config:
        orm_mode = True
