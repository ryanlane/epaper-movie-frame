import logging
from fastapi import FastAPI, Depends, Request, Form, status
from logging.handlers import RotatingFileHandler

from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine

from utils import video_utils

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

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

@app.get('/first_run')
def first_run(request: Request, db: Session = Depends(get_db)):
    # movies = db.query(models.Movie).all()
    available_movies = video_utils.list_video_files("videos/")
    return templates.TemplateResponse("firstrun.html", {"request": request, "movies": available_movies})

# Move the decorator above the function declaration
@app.post('/add_movie/')
def add_movie(request: Request, db: Session = Depends(get_db), video_path: str = Form(...)):
    movie = models.Movie(video_path=video_path)
    db.add(movie)
    db.commit()

    url = app.url_path_for('home')
    return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)

@app.post('/update_movie/{movie_id}')
def update_movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    movie.isActive = not movie.isActive
    db.commit()

    url = app.url_path_for('home')
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)

@app.post('/delete_movie/{movie_id}')
def delete_movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    db.delete(movie)
    db.commit()

    url = app.url_path_for('home')
    return RedirectResponse(url=url, status_code=status.HTTP_303_FOUND)
