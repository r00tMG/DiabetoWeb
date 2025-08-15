import pickle
import pandas as pd
from fastapi import FastAPI, Depends, status, Request, Form
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.functions import now
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import security
from src import models, database
from src.exception import validation_exception_handler
from src.models import Patient
from src.security import login_required
from src.database import SessionLocal

# Chargement de la base de données
models.Base.metadata.create_all(bind=database.engine)

# Chargement d'une instance de fastapi
app = FastAPI()

# Chargement du model risque diabète
with open("models/risque_diabete.pkl", "rb") as f:
    modele = pickle.load(f)

# Chargement des templates et fichiers statics
template = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Installation SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="un_secret_key_tres_long")

#Enregistrement du handler exception
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Session de la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Route de la page register
@app.get("/register", response_class=HTMLResponse, tags=['users'])
async def register(request: Request, db: Session = Depends(get_db)):
    error = request.session.pop("error", None)
    return template.TemplateResponse("/users/register.html", {"request": request, "error": error})


# Service register
@app.post("/register", response_class=HTMLResponse, tags=['users'])
async def register(request: Request,
                   username: str = Form(...),
                   adresse: str = Form(...),
                   email: str = Form(...),
                   password: str = Form(...),
                   confirm_password: str = Form(...),
                   db: Session = Depends(get_db)):
    print(
        f"username: {username}\n,adresse: {adresse},\nemail: {email},\npassword: {password},\nconfirmation password:{confirm_password}")
    if password != confirm_password:
        request.session["error"] = {"status": "error",
                                    "message": "Veuillez verifier si ton mot de passe est confirmé"}

        return RedirectResponse(url="/register", status_code=status.HTTP_303_SEE_OTHER)
    hash = security.hash_password(password)
    new_user = models.User(
        username=username,
        adresse=adresse,
        email=email,
        password=hash
    )

    db.add(new_user)
    db.commit()
    request.session["success"] = {"status": "success",
                                  "message": "Votre compte est crée avec succés, veuillez-vous connecter!"}
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# Route de la page login
@app.get("/login", response_class=HTMLResponse, tags=['users'])
async def login(request: Request):
    error = request.session.pop("error", None)
    success = request.session.pop("success", None)
    success_logout = request.session.pop("success_logout", None)
    return template.TemplateResponse("/users/login.html", {"request": request, "error": error, "success": success,
                                                           "success_logout": success_logout})


# Service Login
@app.post("/login", response_class=HTMLResponse, tags=['users'])
async def login(request: Request, email=Form(...), password=Form(...), db: Session = Depends(get_db)):
    print(f"email: {email},\npassword: {password}")
    # Trouver l'utilisateur ayant cet email dans le db
    user = db.query(models.User).where(models.User.email == email).first()
    # Verification de l'existance de l'utilisateur
    if (user != None) and (user.email == email) and (security.verify_password(password, user.password)):
        print("user connected", user.email)
        request.session['success'] = {"status": "success", "message": "Connexion réussie"}
        request.session["user_id"] = user.id
        return RedirectResponse(url="/patients/index", status_code=status.HTTP_303_SEE_OTHER)
    # sauvegarde du message et du user dans la session
    request.session["error"] = {"status": "error", "message": "Email incorrect!"}
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# Formulaire pour créer un patient
@app.get("/patients/create", response_class=HTMLResponse, tags=['patients'])
@login_required
async def create_patients(request: Request):
    print(request.session.get("user_id"))
    status_risque = request.session.pop("status_risque", None)
    success = request.session.pop("success", None)
    return template.TemplateResponse("/patients/create.html",{
                "request": request,
                "status_risque": status_risque,
                "success": success,
            })


@app.post("/patients/create", response_class=HTMLResponse, tags=['patients'])
async def create_patients(request: Request, name: str = Form(...), age: int = Form(...), sex: str = Form(...),
                          glucose: float = Form(...), bmi: float = Form(...), bloodpressure: float = Form(...),
                          pedigree: float = Form(...), db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")

    new_patient = models.Patient(
        doctorid=user_id,
        name=name,
        age=age,
        sex=sex,
        glucose=glucose,
        bmi=bmi,
        bloodpressure=bloodpressure,
        pedigree=pedigree,
        created_at=now()
    )
    # Prepaparation des données
    # ,Pregnancies,Glucose,BloodPressure,SkinThickness,Insulin,BMI,DiabetesPedigreeFunction,Age
    data = pd.DataFrame([{
        "Pregnancies": 1,
        "Glucose": glucose,
        "BloodPressure": bloodpressure,
        "SkinThickness": 1,
        "Insulin": 1,
        "BMI": bmi,
        "DiabetesPedigreeFunction": pedigree,
        "Age": age

    }])

    # Le cluster dont les moyennes des variables Glucose (>126),
    # BMI (>30) et Diabetes Pedigree Function (>0,5) dépassent les seuils critiques peut être interprété comme à haut risque de diabète.
    # Faire la prédiction
    prediction = modele.predict(data)

    if prediction[0] == 0:
        status_risque = "diabétique"
    else:
        status_risque = "non diabétique"
    print("Prédiction :", prediction)

    if not new_patient:
        return RedirectResponse(url="/patients/create", status_code=status.HTTP_303_SEE_OTHER)
    # print("docterId", new_patient.doctorid, "created_at", new_patient.created_at)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    last_patient = db.query(models.Patient).order_by(models.Patient.id.desc()).first()
    if status_risque:
        new_prediction = models.Prediction(
            patientid = last_patient.id,
            result = status_risque,
            created_at = now()
        )
        db.add(new_prediction)
        db.commit()
        db.refresh(new_prediction)

        request.session["status_risque"] = {
            'status': "success",
            'message': f"Ce patient est {status_risque}"
        }
    # return RedirectResponse(url="/patients/create", status_code=status.HTTP_201_CREATED)
        return template.TemplateResponse("/patients/create.html", {
            "request": request,
            "glucose": glucose,
            "bmi": bmi,
            "age": age,
            "pedigree": pedigree,
            "status_risque": status_risque
        })
    else:
        return "Error lors de l'enregistrement du patient"


# Tableau patients
@app.get("/patients/index", response_class=HTMLResponse, tags=['patients'])
@login_required
async def index_patients(request: Request, db: Session = Depends(get_db)):
    patients = db.query(models.Patient).options(selectinload(Patient.predictions)).order_by(models.Patient.doctorid).all()
    print(patients)
    success = request.session.pop("success", None)
    return template.TemplateResponse("/patients/index.html",
                                     {'request': request, "patients": patients, "success": success})


# logout
@app.get("/logout")
async def logout(request: Request):
    if "user_id" in request.session:
        del request.session["user_id"]
        request.session["success_logout"] = {
            "status": "success",
            "message": "Vous êtes déconnecté avec succés"
        }
    # request.session.pop("user_id", None)

    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


# Delete un patient
@app.post("/patients/delete/{id}", response_class=HTMLResponse, tags=["patients"])
async def delete(request: Request, id: int, db: Session = Depends(get_db)):
    if not id:
        print("test")
        request.session["error_deleted"] = {
            "status": "success",
            "message": f"Patient with id = {id} is not exist"
        }
    query = db.query(models.Patient).where(models.Patient.id == id).delete(synchronize_session=False)
    db.commit()

    if query == True:
        print("test1")
        request.session["success_deleted"] = {
            "status": "success",
            "message": "Patient deleted with success"
        }
    return RedirectResponse(url="/patients/index", status_code=status.HTTP_303_SEE_OTHER)
