import cv2
import numpy as np
import os
import sys
import json
from utils import eframe_inky

from datetime import datetime, timedelta

MOVIE_DATA = "movie_data.json"

class VideoSettings:
    def __init__(
            self,
            video_path="",
            time_per_frame=3600,
            skip_frames=1,
            current_frame=0, 
            total_frames=0, 
            resolution=(800,600), 
            video_root_path="",
            output_image=""
        ):
        self.video_path = video_path
        self.time_per_frame = time_per_frame
        self.skip_frames = skip_frames
        self.current_frame = current_frame
        self.total_frames = total_frames
        self.resolution = resolution
        self.video_root_path = video_root_path
        self.output_image = output_image

    def update_settings(self, **kwargs):
        # Update the values of the instance variables.
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"'VideoSettings' object has no attribute '{key}'")

    def load_from_json(self, json_file_path):
        # Load values from a JSON file.
        with open(json_file_path, 'r') as json_file:
            loaded_data = json.load(json_file)
        self.update_settings(**loaded_data)

    def to_dict(self):
        # Convert instance variables to a dictionary
        return {
            'video_path': self.video_path,
            'time_per_frame': self.time_per_frame,
            'skip_frames': self.skip_frames,
            'current_frame': self.current_frame,
            'total_frames': self.total_frames
        }

    def save_to_json(self, json_file_path):
        # Save instance variables to a JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(self.to_dict(), json_file)


def save_data_state(video_settings):
    with open(MOVIE_DATA, 'w') as json_file:
        json.dump(video_settings.__dict__, json_file)

def load_data_state(video_settings):
    with open(MOVIE_DATA, 'r') as json_file:
        loaded_data = json.load(json_file)
    video_settings.update_settings(**loaded_data)

def check_file_existence(video_settings):
    """
    Check if existing slow movie playback has already been started.

    Parameters:
    - file_path (str): The path to the file.

    Returns:
    - str: The user's decision ('use', 'start_over').
    """
    if os.path.exists(MOVIE_DATA):
        print(f"a movie is already being played back.")

        while True:
            load_data_state(video_settings)
            playback_years, playback_days, playback_hours, playback_minutes = calculate_playback_time(video_settings)
            print(f"current video: {video_settings.video_path}/n")
            print(f"Estimated playback time: {playback_years} years, {playback_days} days, {playback_hours} hours, {playback_minutes} minutes/n")

            user_choice = input("Do you want to continue playback (Y/N)? ").lower()
            
            if user_choice in ('y', 'n'):
                return user_choice
            else:
                print("Invalid choice. Please enter 'Y' or 'N'.")
    else:
        return 'start_over'

def list_video_files(directory):
    """
    List all video files in the specified directory.

    Parameters:
    - directory (str): The directory path.

    Returns:
    - video_files (list): A list of video file names.
    """
    video_files = []
    for filename in os.listdir(directory):
        # Check if the file has a video extension (you can customize this list)
        if filename.lower().endswith(('.mp4', '.avi', '.mkv', '.mov', '.wmv')):
            video_files.append(filename)
    return video_files

def calculate_playback_time(video_settings):
    adjusted_frames = video_settings.total_frames - video_settings.current_frame
     # Calculate total playback time in milliseconds
    total_milliseconds = (adjusted_frames / video_settings.skip_frames) * video_settings.time_per_frame

    # Convert milliseconds to years, days, hours, and minutes
    years, remainder = divmod(total_milliseconds, 31536000000)
    days, remainder = divmod(remainder, 86400000)
    hours, remainder = divmod(remainder, 3600000)
    minutes, seconds = divmod(remainder, 60000)

    return int(years), int(days), int(hours), int(minutes)

def render_future_date(milliseconds=0):
    current_time = datetime.now()
    if(milliseconds > 0):
        current_time = current_time + timedelta(milliseconds=milliseconds)

    current_time_and_date = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
    return current_time_and_date

def select_video(video_files, video_settings):
    """
    Prompt the user to select a video from the list.

    Parameters:
    - video_files (list): A list of video file names.

    Returns:
    - selected_video (str): The selected video file path.
    """
    if not video_files:
        print("No video files found.")
        return None

    print("Available video files:")
    for i, video_file in enumerate(video_files, start=1):
        print(f"{i}. {video_file}")

    while True:
        try:
            choice = int(input("Enter the number of the video you want to process: "))
            if 1 <= choice <= len(video_files):
                selected_video = os.path.join(video_settings.video_root_path, video_files[choice - 1])
                return selected_video
            else:
                print("Invalid choice. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_update_interval():
    print("Select how often the image updates:")
    print("1. Every 10 minutes")
    print("2. Every hour")
    print("3. Every day")
    print("4. Other (provide custom time in milliseconds)")

    choice = input("Enter the number corresponding to your choice: ")

    if choice == '1':
        return 10 * 60 * 1000  # 10 minutes in milliseconds
    elif choice == '2':
        return 60 * 60 * 1000  # 1 hour in milliseconds
    elif choice == '3':
        return 24 * 60 * 60 * 1000  # 1 day in milliseconds
    elif choice == '4':
        custom_time = input("Enter the custom time in milliseconds: ")
        try:
            return int(custom_time)
        except ValueError:
            print("Invalid input. Using default update interval.")
            return 10 * 60 * 1000  # Default to 10 minutes if input is not a valid number
    else:
        print("Invalid choice. Using default update interval.")
        return 10 * 60 * 1000  # Default to 10 minutes for invalid choices

def get_frames_to_skip():
    default_frames_to_skip = 1

    try:
        frames_to_skip = int(input(f"Enter the number of frames to skip (default is {default_frames_to_skip}): "))
        return frames_to_skip if frames_to_skip > 0 else default_frames_to_skip
    except ValueError:
        print("Invalid input. Using default frames to skip.")
        return default_frames_to_skip

# Function to get the total number of frames in a video
def get_total_frames(cap):
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return total_frames

# Function to extract a specific frame as an image
def extract_frame_as_image(cap, frame_number):
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if ret:
        return frame
    else:
        print(f"Error reading frame {frame_number}")

def render_playback_time(video_settings):
    playback_years, playback_days, playback_hours, playback_minutes = calculate_playback_time(video_settings)
    print(f"Estimated playback time: {playback_years} years, {playback_days} days, {playback_hours} hours, {playback_minutes} minutes")
    future_frame = render_future_date(video_settings.time_per_frame)
    print(f"next frame will be displayed: {future_frame}")

# Function to save a frame as an image with specified quality
def save_frame_as_image(frame, video_settings):
    cv2.imwrite(video_settings.output_image, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    # print(f"Frame {frame_number} saved as {output_path}")

# Function to resize an image while maintaining its aspect ratio and adding black borders
def resize_with_black_borders(image, target_width, target_height):
    original_height, original_width = image.shape[:2]
    original_aspect_ratio = original_width / original_height
    target_aspect_ratio = target_width / target_height
    
    # Calculate new dimensions to maintain aspect ratio
    if original_aspect_ratio > target_aspect_ratio:
        new_width = target_width
        new_height = int(target_width / original_aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * original_aspect_ratio)
    
    # Resize the image
    resized_image = cv2.resize(image, (new_width, new_height))
    
    # Create a canvas with black borders
    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)
    
    # Calculate the offset to center the resized image on the canvas
    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    
    # Copy the resized image onto the canvas
    canvas[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image
    
    return canvas


# Function to process a video, extract a specific frame, resize it, and save as an image
def process_video(cap, video_settings):
    progress_animation(0)    
    
    # Extract the specified frame from the video
    movie_frame = extract_frame_as_image(cap, video_settings.current_frame)
    progress_animation(30)
    # Resize the frame with black borders to the target dimensions    
    final_size_frame = resize_with_black_borders(movie_frame, video_settings.resolution[0], video_settings.resolution[1])
    progress_animation(60)
    # Save the resized frame as an image
    save_frame_as_image(final_size_frame, video_settings)
    
    progress_animation(100)

    print("\n image processing completed \n")
    

def progress_animation(percentage):
    sys.stdout.write("\rProcessing Video: [{}{}] {}%".format("#" * percentage, "." * (100 - percentage), percentage))
    sys.stdout.flush()

def playback_init(video_settings, logger):
    user_decision = check_file_existence(video_settings)

    if user_decision == 'y':
        logger.info("Using existing file.")
    else:
        available_video_files = list_video_files(video_settings.video_root_path)
        video_settings.video_path = select_video(available_video_files,video_settings)

        captured_video = cv2.VideoCapture(video_settings.video_path)
        video_settings.total_frames = get_total_frames(captured_video)

        video_settings.time_per_frame = get_update_interval()
        logger.info(f"Selected update interval: {video_settings.time_per_frame} milliseconds")

        video_settings.skip_frames = get_frames_to_skip()
    
        logger.info(f"Selected frames to skip: {video_settings.skip_frames}")

        render_playback_time(video_settings)

        save_data_state(video_settings)

        captured_video.release()

def play_video(video_settings, logger):
    # Log the path of the selected video
    logger.info(video_settings.video_path)
    
    # Store the path of the selected video
    selected_video = video_settings.video_path
    
    # Retrieve the current frame for rendering
    current_frame = video_settings.current_frame
    
    # Log the information about the rendering frame
    logger.info(f"Rendering frame - {current_frame}")
    
       
    # Open the video file for capturing frames
    captured_video = cv2.VideoCapture(selected_video)
    
    # Process the video to extract, resize, and save the frame
    process_video(captured_video, video_settings)
    
    # Show the processed frame on the e-ink display
    eframe_inky.show_on_inky(video_settings.output_image)
    
    # Calculate the next frame to be displayed
    nextframe = current_frame + video_settings.skip_frame
    if nextframe <= video_settings.total_frames:
        new_frame = nextframe
    else:
        # for now we'll start over
        new_frame = 0
    
    # Update the current frame in the VideoSettings instance
    video_settings.current_frame = new_frame
    
    # Render playback time
    render_playback_time(video_settings)

    # Save the updated video settings to maintain state
    save_data_state(video_settings)


