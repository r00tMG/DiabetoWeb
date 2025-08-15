from sqlalchemy import Column, Integer, String, DATETIME, ForeignKey, func, DateTime, Float
from sqlalchemy.orm import relationship

from src.database import Base


class User(Base):

    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    adresse = Column(String, nullable=False)
    email = Column(String, nullable=False)
    password = Column(String, nullable=False)
    medecin = relationship("Patient", back_populates="user")

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True, index=True)
    doctorid = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    age = Column(Integer, nullable = False)
    sex = Column(String, nullable = False)
    glucose = Column(Float, nullable = False)
    bmi = Column(Float, nullable = False)
    bloodpressure = Column(Float, nullable=False)
    pedigree = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="medecin")
    predictions = relationship("Prediction", back_populates="patient", uselist=False, cascade="all, delete-orphan")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    patientid = Column(Integer, ForeignKey("patients.id"), nullable=False)
    result = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now(), nullable=False)
    patient = relationship("Patient", back_populates="predictions")
