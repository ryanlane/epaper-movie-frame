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
    logger = setup_logger(logging.INFO)

    wait_counter = 0
    while True:
        result = video_utils.load_active_video_settings()
        if not result:
            if wait_counter % 12 == 0:
                print("[INFO] No active movie. Waiting...")
            wait_counter += 1
            time.sleep(5)
            continue
        wait_counter = 0

        video_settings, movie, settings = result
        video_utils.play_video(video_settings, logger)
        time.sleep(video_settings.time_per_frame / 1000)


# def main():
#     print("Starting movieplayer")
#     toml_file_path = 'config.toml'
#     config_data = config.read_toml_file(toml_file_path)

#     parser = argparse.ArgumentParser()
#     parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
#     parser.add_argument('--auto', action='store_true', help="Run auto mode")

#     args = parser.parse_args()
#     logger = setup_logger(getattr(logging, args.log_level))

#     video_settings = video_utils.VideoSettings()
#     video_settings.video_root_path = config_data.get('VIDEO_DIRECTORY')
#     video_settings.output_image = config_data.get('OUTPUT_IMAGE_PATH')
#     video_settings.resolution = eframe_inky.get_inky_resolution()

#     logger.info("Starting playback...")

#     if args.auto:
#         while True:
#             video_utils.load_data_state(video_settings)
#             video_utils.play_video(video_settings, logger)
#             time.sleep(video_settings.time_per_frame / 1000)
#     else:
#         video_utils.playback_init(video_settings, logger)
#         while True:
#             video_utils.play_video(video_settings, logger)
#             time.sleep(video_settings.time_per_frame / 1000)

if __name__ == "__main__":
    init_database()  # Initialize the database
    run_webui()  # Start Flask
    main()       # Start movie playback
