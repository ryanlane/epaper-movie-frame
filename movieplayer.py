#!/usr/bin/env python3

import threading
import time
import requests
import logging
import argparse
import database

import webui
from utils import video_utils, eframe_inky, config

def setup_logger(log_level):
    logging.basicConfig(level=log_level,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    return logging.getLogger(__name__)

def init_database():
    database.init_db()
    if not database.get_settings():
        database.insert_default_settings()
    else:
        database.check_config_against_settings()


def run_webui():
    # Launch Flask server in a background thread
    # threading.Thread(target=lambda: webui.app.run(host="0.0.0.0", port=8000), daemon=True).start()

    def start_flask():
        from webui import app
        app.run(host="0.0.0.0", port=8000, debug=False)
    
    thread = threading.Thread(target=start_flask, daemon=True)
    thread.start()

    # Wait until Flask server responds
    for _ in range(30):  # wait up to ~15 seconds
        try:
            res = requests.get("http://127.0.0.1:8000/")
            if res.status_code == 200:
                print("[INFO] Flask server is up.")
                break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    else:
        print("[ERROR] Flask server did not start in time.")


def main():
    from database import get_active_movie, set_now_playing

    logger = setup_logger(logging.INFO)
    wait_counter = 0

    movie = get_active_movie()
    eframe_inky.show_startup_status(movie)
        

    while True:
        movie = get_active_movie()

        if not movie:
            if wait_counter % 12 == 0:
                print("[INFO] No active movie. Waiting...")
            wait_counter += 1
            time.sleep(5)
            continue

        movie_id = movie['id']
        set_now_playing(movie_id)
        wait_counter = 0

        from utils import video_utils
        video_utils.play_video(logger)

        # Sleep based on DB-defined interval (in minutes)
        time.sleep(movie['time_per_frame'] * 60)


if __name__ == "__main__":
    init_database()  # Initialize the database
    run_webui()  # Start Flask
    main()       # Start movie playback
