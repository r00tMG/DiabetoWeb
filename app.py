from http.client import responses

from fastapi import FastAPI, Depends, status, Request, Form
from fastapi.openapi.models import Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
import security
from src import models, database
from src.database import SessionLocal
from src.schemas import User

#Chargement de la base de données
models.Base.metadata.create_all(bind=database.engine)

#Chargement d'une instance de fastapi
app = FastAPI()

# Chargement des templates et fichiers statics
template = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

#Session de la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users", status_code=status.HTTP_201_CREATED)
def create(request: User, response: Response, db: Session= Depends(get_db)):
    new_user = models.User(username=request.username, adresse=request.adresse,email=request.email, password=request.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    if not new_user:
        return {
            "satus": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "message": "error"
        }
    return new_user

# APi all users
@app.get("/getUsers")
def index(db: Session=Depends(get_db)):
    users = db.query(models.User).all()
    return users

# Api pour récupérer un utilisateur
@app.get("/user/{id}", status_code=status.HTTP_200_OK)
async def show(id, respone: Response, db:Session = Depends(get_db)):
    user = db.query(models.User).where(models.User.id == id).first()
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        respone.status_code = status.HTTP_404_NOT_FOUND
    return user

# Path home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return template.TemplateResponse("/home.html", {"request":request})

@app.get('/index', response_class=HTMLResponse)
async def index(request: Request, db: Session=Depends(get_db)):
    users = db.query(models.User).all()
    return template.TemplateResponse("/users/index.html", {"request":request, "users": users})


#Route de la page register
@app.get("/register", response_class=HTMLResponse)
async def register(request: Request, db:Session=Depends(get_db)):
    return template.TemplateResponse("/users/register.html", {"request":request})
#Service register
@app.post("/register", response_class=HTMLResponse)
async def register(
    username: str = Form(...),
    adresse: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db:Session=Depends(get_db)):
    print(f"username: {username}\n,adresse: {adresse},\nemail: {email},\npassword: {password},\nconfirmation password:{confirm_password}")
    if password != confirm_password:
        return RedirectResponse(url="/register", status_code=status.HTTP_303_SEE_OTHER)
    hash = security.hash_password(password)
    new_user = models.User(
        username = username,
        adresse = adresse,
        email = email,
        password = hash
    )

    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

# Route de la page login
@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return template.TemplateResponse("/users/login.html", {"request": request})
# Service Login
@app.post("/login", response_class=HTMLResponse)
async def login(email=Form(...), password=Form(...), db: Session = Depends(get_db)):
    print(f"email: {email},\npassword: {password}")
    #Trouver l'utilisateur ayant cet email dans le db
    user = db.query(models.User).where(models.User.email == email).first()
    print("user connected", user.email)
    #Verification de l'existance de l'utilisateur
    if user and (user.email == email) and (security.verify_password(password, user.password)):
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
