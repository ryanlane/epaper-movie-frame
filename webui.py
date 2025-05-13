import os
import uvicorn
import logging
from fastapi import FastAPI, Depends, Request, Form, status, HTTPException
from logging.handlers import RotatingFileHandler

from starlette.responses import RedirectResponse, JSONResponse
from starlette.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine

from utils import video_utils, eframe_inky

logger = logging.getLogger(__name__)
handler = RotatingFileHandler('webui.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)

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

app.mount("/static", StaticFiles(directory="static"), name="static")      

@app.on_event("startup")
async def startup_event():
   logger.info("Starting up webui")
   db = SessionLocal()
   settings = db.query(models.Settings).first()

   if not settings:
       settings = models.Settings(VideoRootPath="videos", Resolution="800,480")
       db.add(settings)
       db.commit()



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

@app.get('/movie/{movie_id}')
def movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()

    # Check if frame.jpg exists in the static folder for the movie_id
    static_folder = f"static/{movie_id}"
    frame_path = os.path.join(static_folder, "frame.jpg")
    if os.path.exists(frame_path):
        current_image_path = os.path.abspath(frame_path)
    else:
        current_image_path = None

    return templates.TemplateResponse("movie_details.html", {"request": request, "movie": movie, "current_image_path": current_image_path})

# Move the decorator above the function declaration
@app.post('/add_movie')
def add_movie(request: Request, db: Session = Depends(get_db), video_path: str = Form(...)):
    movie = models.Movie(video_path=video_path)
    existingMovie = db.query(models.Movie).filter(models.Movie.video_path == video_path).first()

    settings = db.query(models.Settings).first()
    
    # if existingMovie exists then redirect to update_movie

    if existingMovie:
        url = app.url_path_for('movie', movie_id=existingMovie.id)
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    else: 
        movie.total_frames = video_utils.get_total_frames(video_path)
        movie.time_per_frame = 60
        movie.skip_frames = 1
        movie.current_frame = 1
        movie.isActive = False

        
        db.add(movie)
        db.commit()
        db.refresh(movie)

        video_utils.process_video(movie,settings)  

        url = app.url_path_for('home')
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)


@app.post('/update_movie')
def update_movie(
    payload: models.movieSetting,
    db: Session = Depends(get_db)
):

    movie = db.query(models.Movie).filter(models.Movie.id == payload.id).first()

    if not movie:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "invalid id", "message": "Movie not found"})
    
    settings = db.query(models.Settings).first()
    
    # movie.isActive = not movie.isActive
    if payload.time_per_frame == 0:
        payload.time_per_frame = payload.custom_time
    movie.time_per_frame = payload.time_per_frame
    movie.skip_frames = payload.skip_frames
    movie.current_frame = payload.current_frame
    movie.isRandom = payload.isRandom 

    #update database record
    db.add(movie)
    db.commit()

    video_utils.process_video(movie,settings)  

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": f"{payload.id} Movie item updated successfully"})


@app.post('/delete_movie/{movie_id}')
def delete_movie(request: Request, movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(models.Movie).filter(models.Movie.id == movie_id).first()
    if movie:
        db.delete(movie)
        db.commit()

        return JSONResponse(status_code=status.HTTP_302_FOUND, content={"message": "Movie item deleted successfully"})
    else:        
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": "invalid id", "message": "Movie not found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)