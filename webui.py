import logging
from fastapi import FastAPI, Depends, Request, Form, status
from logging.handlers import RotatingFileHandler

from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="../web/templates")

app = FastAPI()
# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define a route for the home page
@app.get('/')
def home(request: Request, db: Session = Depends(get_db)):
    movies = db.query(models.Movie).all()
    return templates.TemplateResponse("index.html", {"request": request, "movies": movies})


