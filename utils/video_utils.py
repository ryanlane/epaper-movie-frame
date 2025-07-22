import cv2
import numpy as np
import os
import sys
import shutil
from utils import eframe_inky, config
import sqlite3
from datetime import datetime, timedelta

DEV_MODE = config.read_toml_file("config.toml").get("DEVELOPMENT_MODE", False)

def should_skip_due_to_quiet_hours(settings):
    try:
        if not int(settings['use_quiet_hours']):
            return False

        quiet_start = int(settings['quiet_start'])
        quiet_end = int(settings['quiet_end'])
        current_hour = datetime.now().hour

        print(f"[QUIET HOURS CHECK] now={current_hour}, start={quiet_start}, end={quiet_end}")

        if quiet_start < quiet_end:
            return quiet_start <= current_hour < quiet_end
        else:
            return current_hour >= quiet_start or current_hour < quiet_end
    except KeyError as e:
        print(f"[WARNING] Missing expected quiet hour field: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Quiet hour check failed: {e}")
        return False

def calculate_playback_time(movie):
    total_frames = movie['total_frames']
    current_frame = movie['current_frame']
    skip_frames = movie['skip_frames']
    time_per_frame_minutes = movie['time_per_frame']

    time_per_frame_ms = time_per_frame_minutes * 60 * 1000
    adjusted_frames = total_frames - current_frame
    total_milliseconds = (adjusted_frames / skip_frames) * time_per_frame_ms

    years, remainder = divmod(total_milliseconds, 31536000000)
    days, remainder = divmod(remainder, 86400000)
    hours, remainder = divmod(remainder, 3600000)
    minutes, _ = divmod(remainder, 60000)

    return int(years), int(days), int(hours), int(minutes)

def render_future_date(minutes=0):
    future_time = datetime.now() + timedelta(minutes=minutes)
    return future_time.strftime("%Y-%m-%d %H:%M:%S")

def get_total_frames(video_path):
    captured_video = cv2.VideoCapture(video_path)
    if not captured_video.isOpened():
        print(f"[ERROR] Failed to open video file: {video_path}")
        return 0
    total_frames = int(captured_video.get(cv2.CAP_PROP_FRAME_COUNT))
    captured_video.release()
    return total_frames

def extract_frame_as_image(cap, frame_number):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    return frame if ret else None

def save_frame_as_image(frame, movie_id):
    directory = f"static/{movie_id}"
    os.makedirs(directory, exist_ok=True)
    cv2.imwrite(f"{directory}/frame.jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

def list_video_files(directory):
    video_files = []
    for filename in os.listdir(directory):
        if filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
            video_files.append(filename)
    return video_files

# Function to process a video, extract a specific frame, resize it, and save as an image
def process_video(movie, settings):
    video_path = f"{settings['VideoRootPath']}/{movie['video_path']}"
    print(f"[DEBUG] Attempting to open video: {video_path}")
    captured_video = cv2.VideoCapture(video_path)

    resolution_string = settings['Resolution'].split(',')
    resolution = [int(x) for x in resolution_string]
    
    # Extract the specified frame from the video
    movie_frame = extract_frame_as_image(captured_video, movie['current_frame'])
    # progress_animation(30)
    # Resize the frame with black borders to the target dimensions    
    final_size_frame = resize_with_black_borders(movie_frame, resolution[0], resolution[1])
    # progress_animation(60)
    # Save the resized frame as an image
    save_frame_as_image(final_size_frame, movie['id'])
    captured_video.release()    


def resize_with_black_borders(image, target_width, target_height):
    original_height, original_width = image.shape[:2]
    original_aspect_ratio = original_width / original_height
    target_aspect_ratio = target_width / target_height

    if original_aspect_ratio > target_aspect_ratio:
        new_width = target_width
        new_height = int(target_width / original_aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * original_aspect_ratio)

    resized_image = cv2.resize(image, (new_width, new_height))
    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image
    return canvas

def play_video(logger):
    from database import get_active_movie, get_settings, update_current_frame

    movie = get_active_movie()
    settings = get_settings()

    if should_skip_due_to_quiet_hours(settings):
        logger.info("Playback skipped due to quiet hours.")
        return

    if not movie or not settings:
        logger.warning("No active movie or settings found.")
        return

    video_path = os.path.join(settings['VideoRootPath'], movie['video_path'])
    resolution = [int(x) for x in settings['Resolution'].split(',')]
    current_frame = movie['current_frame']
    total_frames = movie['total_frames']
    skip_frames = movie['skip_frames']
    time_per_frame = movie['time_per_frame']
    movie_id = movie['id']

    if current_frame >= total_frames:
        current_frame = 0

    logger.info(f"Rendering frame - {current_frame} of {total_frames}")
    cap = cv2.VideoCapture(video_path)
    frame = extract_frame_as_image(cap, current_frame)
    if frame is None:
        logger.error(f"[ERROR] Could not read frame {current_frame} from {video_path}")
        cap.release()
        return

    final_frame = resize_with_black_borders(frame, resolution[0], resolution[1])
    save_frame_as_image(final_frame, movie_id)
    
    image_path = os.path.join(f"static/{movie_id}", "frame.jpg")

    if DEV_MODE:
        print("[DEV_MODE] Frame saved to static only.")
    else:
        eframe_inky.show_on_inky(image_path)

    y, d, h, m = calculate_playback_time(movie)
    logger.info(f"Estimated playback time: {y}y {d}d {h}h {m}m")
    logger.info(f"Next frame will be displayed at: {render_future_date(time_per_frame)}")

    next_frame = current_frame + skip_frames
    if next_frame >= total_frames:
        next_frame = 0

    update_current_frame(movie_id, next_frame)
    cap.release()

def get_disk_usage_stats(path="/"):
    usage = shutil.disk_usage(path)
    return {
        "total_gb": usage.total // (1024**3),
        "used_gb": usage.used // (1024**3),
        "free_gb": usage.free // (1024**3)
    }

def get_directory_size_gb(directory):
    total = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
            except FileNotFoundError:
                continue
    return total / (1024**3)
