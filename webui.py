import os
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
from logging.handlers import RotatingFileHandler
from utils import video_utils, eframe_inky, config
import database

config_data = config.read_toml_file("config.toml")
VIDEO_DIRECTORY = config_data.get("VIDEO_DIRECTORY", "videos")

# app = Flask(__name__, static_folder='static', template_folder='templates')
app = Flask(__name__)


with app.app_context():
    database.init_db()
    if not database.get_settings():
        database.insert_default_settings()

@app.route('/')
def home():
    movies = database.get_all_movies()
    return render_template("index.html", movies=movies)

@app.route('/first_run')
def first_run():
    available_movies = video_utils.list_video_files(VIDEO_DIRECTORY)
    return render_template("firstrun.html", movies=available_movies)

@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    movie = database.get_movie_by_id(movie_id)
    frame_path = os.path.join(f"static/{movie_id}", "frame.jpg")
    current_image_path = os.path.abspath(frame_path) if os.path.exists(frame_path) else None
    return render_template("movie_details.html", movie=movie, current_image_path=current_image_path)

@app.route('/add_movie', methods=['POST'])
def add_movie():
    video_path = request.form['video_path']
    existing = database.get_movie_by_path(video_path)
    settings = database.get_settings()

    if existing:
        return redirect(url_for('movie', movie_id=existing['id']))

    total_frames = video_utils.get_total_frames(video_path)
    movie = database.insert_movie(video_path, total_frames)
    video_utils.process_video(movie, settings)

    return redirect(url_for('home'))

@app.route('/update_movie', methods=['POST'])
def update_movie():
    payload = request.get_json()
    if int(payload['time_per_frame']) == 0:
        payload['time_per_frame'] = int(payload.get('custom_time', 60))

    updated_movie = database.update_movie(payload)
    settings = database.get_settings()
    video_utils.process_video(updated_movie, settings)

    return jsonify({"message": "Movie updated successfully"})

@app.post('/start_playback/<int:movie_id>')
def start_playback(movie_id):
    database.set_active_movie(movie_id)
    return redirect(url_for('home'))


@app.post('/stop_playback')
def stop_playback():
    database.clear_active_movie()
    return redirect(url_for('home'))


@app.route('/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    movie = database.delete_movie(movie_id)
    if movie:
        return jsonify({"message": "Movie item deleted successfully"}), 302
    else:
        return jsonify({"error": "Movie not found"}), 404

if __name__ == "__main__":
    handler = RotatingFileHandler('webui.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    app.run(host="0.0.0.0", port=8000, debug=True)
