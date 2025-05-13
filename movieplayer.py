#!/usr/bin/env python3

import threading
import time
import logging
import argparse
from utils import video_utils, eframe_inky, config
from web import webui


def setup_logger(log_level):
    logging.basicConfig(level=log_level,
                        format="%(asctime)s [%(levelname)s] %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    return logger

def keyboard_control(video_settings,logger):
    while True:
        if keyboard.is_pressed('u'):
            video_utils.play_video(video_settings,logger)

def run_webui():
    webui.app   

def main():
    print("starting up")
    toml_file_path = 'config.toml'
    config_data = config.read_toml_file(toml_file_path)
    parser = argparse.ArgumentParser()
    
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help="Set the log level")
    parser.add_argument('--auto', action='store_true', help="Run auto function")

    args = parser.parse_args()

    log_level = getattr(logging, args.log_level)
    logger = setup_logger(log_level)
    video_settings = video_utils.VideoSettings()
    video_settings.video_root_path = config_data.get('VIDEO_DIRECTORY')
    video_settings.output_image = config_data.get('OUTPUT_IMAGE_PATH')
    new_res = eframe_inky.get_inky_resolution()
    print(f"display resolution: {new_res}")
    video_settings.resolution = new_res

    logger.info(f"logging level: {args.log_level}")

    if args.auto:
         while True:    
                video_utils.load_data_state(video_settings)            
                video_utils.play_video(video_settings,logger)
                print
                time.sleep(video_settings.time_per_frame / 1000)        
        
    else:
        video_utils.playback_init(video_settings,logger)
        while True:
            # # Create an instance with default values
            # default_settings = video_utils.VideoSettings()
            # DEFAULT_DATA = video_utils.load_data_state(default_settings)
            print(video_settings.video_path)
            video_utils.play_video(video_settings,logger)
            
            time.sleep(video_settings.time_per_frame / 1000)           
        
if __name__ == "__main__":
    try:
        run_webui()
        # # Create and start threads for webui.app.run() and main()
        
        # main_thread = threading.Thread(target=main)
        # webui_thread = threading.Thread(target=run_webui)

        # webui_thread.start()
        # main_thread.start()

        # # Join threads to ensure they finish execution before the main thread exits
        # webui_thread.join()
        # main_thread.join()      
    except KeyboardInterrupt:
        print('stopped')

