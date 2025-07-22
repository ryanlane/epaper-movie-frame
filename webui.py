import os
import logging
from flask import Flask, render_template, request, redirect, url_for, jsonify
from logging.handlers import RotatingFileHandler
from utils import video_utils, eframe_inky, config
from werkzeug.utils import secure_filename
from datetime import datetime
import database

config_data = config.read_toml_file("config.toml")
VIDEO_DIRECTORY = config_data.get("VIDEO_DIRECTORY", "videos")

# Ensure the video directory exists
os.makedirs(VIDEO_DIRECTORY, exist_ok=True)

UPLOAD_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv'}

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = VIDEO_DIRECTORY


with app.app_context():
    database.init_db()
    if not database.get_settings():
        database.insert_default_settings()

@app.route('/')
def home():
    movies = database.get_all_movies()
    settings = database.get_settings()
    active_movie = database.get_active_movie()

    disk_stats = video_utils.get_disk_usage_stats("/")
    video_dir_size = video_utils.get_directory_size_gb(settings['VideoRootPath'])

    playback_time = None
    if active_movie:
        playback_time = video_utils.calculate_playback_time(active_movie)

    quiet_info = {
        "enabled": bool(int(settings['use_quiet_hours'])),
        "start": settings['quiet_start'],
        "end": settings['quiet_end'],
        "active": video_utils.should_skip_due_to_quiet_hours(settings)
    }

    return render_template(
        "index.html",
        movies=movies,
        disk_stats=disk_stats,
        video_dir_size=round(video_dir_size, 2),
        dev_mode=config_data.get("DEVELOPMENT_MODE", False),
        active_movie=active_movie,
        playback_time=playback_time,
        quiet_info=quiet_info
    )

@app.route('/movies')
def movies():
    movies = database.get_all_movies()
    settings = database.get_settings()

    disk_stats = video_utils.get_disk_usage_stats("/")
    video_dir_size = video_utils.get_directory_size_gb(settings['VideoRootPath'])

    return render_template(
        "movies.html",
        movies=movies,
        disk_stats=disk_stats,
        video_dir_size=round(video_dir_size, 2),
        dev_mode=config_data.get("DEVELOPMENT_MODE", False)
    )

@app.route('/first_run')
def first_run():
    available_movies = video_utils.list_video_files(VIDEO_DIRECTORY)
    return render_template("firstrun.html", movies=available_movies)

@app.route('/movie/<int:movie_id>')
def movie(movie_id):
    movie = database.get_movie_by_id(movie_id)
    settings = database.get_settings()

    frame_path = os.path.join(f"static/{movie_id}", "frame.jpg")
    current_image_path = os.path.abspath(frame_path) if os.path.exists(frame_path) else None

    from database import get_movie_by_id, get_settings
    movie = get_movie_by_id(movie_id)
    settings = get_settings()
    playback_time = video_utils.calculate_playback_time(movie)

    return render_template(
        "movie_details.html",
        movie=movie,
        current_image_path=current_image_path,
        playback_time=playback_time,
        dev_mode=config_data.get("DEVELOPMENT_MODE", False),
    )

@app.route('/add_movie', methods=['POST'])
def add_movie():
    video_path = request.form['video_path']  # just the filename
    existing = database.get_movie_by_path(video_path)
    settings = database.get_settings()

    if existing:
        return redirect(url_for('movie', movie_id=existing['id']))

    # Construct full path for OpenCV
    full_path = os.path.join(settings['VideoRootPath'], video_path)

    # Get total frames from full path
    total_frames = video_utils.get_total_frames(full_path)

    # Insert movie using just the filename
    movie = database.insert_movie(video_path, total_frames)

    # Process first frame using movie + settings
    video_utils.process_video(movie, settings)

    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    settings = database.get_settings()

    if request.method == 'POST':
        uploaded_file = request.files.get('video')
        if not uploaded_file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(uploaded_file.filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in UPLOAD_EXTENSIONS:
            return jsonify({"error": "Unsupported file type"}), 400

        # Ensure upload directory exists
        os.makedirs(settings['VideoRootPath'], exist_ok=True)

        save_path = os.path.join(settings['VideoRootPath'], filename)
        uploaded_file.save(save_path)

        existing = database.get_movie_by_path(filename)
        if existing:
            return jsonify({"message": "Upload complete!", "movie_id": existing['id']}), 200

        total_frames = video_utils.get_total_frames(save_path)
        movie = database.insert_movie(filename, total_frames)
        video_utils.process_video(movie, settings)

        return jsonify({"message": "Upload complete!", "movie_id": movie['id']}), 200

    return render_template('upload.html')



@app.route('/update_movie', methods=['POST'])
def update_movie():
    payload = request.get_json()
    db_movie = database.get_movie_by_id(payload['id'])
    settings = database.get_settings()

    if not db_movie or not settings:
        return jsonify({"error": "Invalid ID or missing settings"}), 400

    # Handle "Other" option with custom time
    if int(payload['time_per_frame']) == 0:
        payload['time_per_frame'] = int(payload.get('custom_time', 1))  # fallback to 1 minute

    # Recalculate total frames using full video path
    full_path = os.path.join(settings['VideoRootPath'], db_movie['video_path'])
    total_frames = video_utils.get_total_frames(full_path)
    payload['total_frames'] = total_frames

    # Update database and process frame
    updated_movie = database.update_movie(payload)
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

@app.route('/trigger_display_update/<int:movie_id>', methods=['POST'])
def trigger_display_update(movie_id):
    movie = database.get_movie_by_id(movie_id)
    settings = database.get_settings()

    if not movie or not settings:
        return jsonify({"error": "Invalid ID or settings"}), 400

    video_utils.process_video(movie, settings)
    frame_path = os.path.join(f"static/{movie_id}", "frame.jpg")
    eframe_inky.show_on_inky(frame_path)

    return jsonify({"message": "E-Ink display updated"})

@app.route('/settings', methods=['GET', 'POST'])
def settings_page():
    if request.method == 'POST':
        payload = request.get_json()
        updated = database.update_settings(payload)
        return jsonify({"message": "Settings updated", "settings": dict(updated)})

    settings = database.get_settings()
    return render_template('settings.html', settings=settings)

