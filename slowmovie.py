import cv2
import numpy as np
import os
import sys
import time
import json
from datetime import datetime, timedelta
 
import utils


# Define target width and height for resizing frames
TARGET_WIDTH = 800
TARGET_HEIGHT = 600

VIDEO_DIRECTORY = "videos"
OUTPUT_IMAGE_PATH = "frame.jpg"
MOVIE_DATA = "movie_data.json"

DEFAULT_DATA = {
  "video_path": "",
  "time_per_frame": 3600,
  "skip_frames": 1,
  "current_frame": 0,
  "total_frames": 0,
}

# def save_data_state(json_data):
#     with open(MOVIE_DATA, 'w') as json_file:
#       json.dump(json_data, json_file)

# def load_data_state(json_data):
#     with open(MOVIE_DATA, 'r') as json_file:
#       loaded_data = json.load(json_file)
#     return loaded_data

def check_file_existence(file_path):
    """
    Check if existing slow movie playback has already been started.

    Parameters:
    - file_path (str): The path to the file.

    Returns:
    - str: The user's decision ('use', 'start_over').
    """
    if os.path.exists(file_path):
        print(f"a movie is already being played back.")

        while True:
            DEFAULT_DATA = utils.video_utils.load_data_state(MOVIE_DATA)
            playback_years, playback_days, playback_hours, playback_minutes = calculate_playback_time(DEFAULT_DATA)
            print(f"current video: {DEFAULT_DATA['video_path']}/n")
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


def select_video(video_files):
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
                selected_video = os.path.join(VIDEO_DIRECTORY, video_files[choice - 1])
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

def calculate_playback_time(data):
    total_frames = data["total_frames"]
    skip_frames = data["skip_frames"]
    time_per_frame = data["time_per_frame"]
    current_frame = data["current_frame"]

    adjusted_frames = total_frames - current_frame
     # Calculate total playback time in milliseconds
    total_milliseconds = (adjusted_frames / skip_frames) * time_per_frame

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

# Function to save a frame as an image with specified quality
def save_frame_as_image(frame, frame_number, output_path):
    cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
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
def get_total_frames(cap):
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return total_frames

# Function to process a video, extract a specific frame, resize it, and save as an image
def process_video(cap, frame_number_to_save, output_image_path):
    progress_animation(0)
    
    
    # # Get total number of frames in the video
    # total_frames = get_total_frames(cap)
    progress_animation(25)
    # print(f"Total number of frames in the video: {total_frames}")
    
    # Extract the specified frame from the video
    movie_frame = extract_frame_as_image(cap, frame_number_to_save)
    progress_animation(50)
    # Resize the frame with black borders to the target dimensions
    final_size_frame = resize_with_black_borders(movie_frame, TARGET_WIDTH, TARGET_HEIGHT)
    progress_animation(75)
    # Save the resized frame as an image
    save_frame_as_image(final_size_frame, frame_number_to_save, output_image_path)
    progress_animation(100)
    

def progress_animation(percentage):
    sys.stdout.write("\rProcessing Video: [{}{}] {}%".format("#" * percentage, "." * (100 - percentage), percentage))
    sys.stdout.flush()

def render_playback_time():
    playback_years, playback_days, playback_hours, playback_minutes = calculate_playback_time(DEFAULT_DATA)
    print(f"Estimated playback time: {playback_years} years, {playback_days} days, {playback_hours} hours, {playback_minutes} minutes")
    future_frame = render_future_date(DEFAULT_DATA["time_per_frame"])
    print(f"next frame will be displayed: {future_frame}")

def playback_init():
        
    user_decision = check_file_existence(MOVIE_DATA)

    if user_decision == 'y':
        print("Using existing file.")

    else:
        available_video_files = list_video_files(VIDEO_DIRECTORY)
        selected_video = select_video(available_video_files)

        DEFAULT_DATA["video_path"] = selected_video
        captured_video = cv2.VideoCapture(selected_video)
        total_frames = get_total_frames(captured_video)
        DEFAULT_DATA["total_frames"] = total_frames

        # Example usage
        update_interval = get_update_interval()
        DEFAULT_DATA["time_per_frame"] = update_interval
        print(f"Selected update interval: {update_interval} milliseconds")

        frames_to_skip = get_frames_to_skip()
        DEFAULT_DATA["skip_frames"] = frames_to_skip
        print(f"Selected frames to skip: {frames_to_skip}")

        render_playback_time()

        utils.video_utils.save_data_state(DEFAULT_DATA)

        # save_data_state(DEFAULT_DATA)
        # frame_number_to_save = 5600  # Change this to the desired frame number
        # process_video(captured_video, frame_number_to_save, OUTPUT_IMAGE_PATH)
        # Release the video capture object
        captured_video.release()


def play_video():
    DEFAULT_DATA = utils.video_utils.load_data_state(MOVIE_DATA)
    print("/n")

    selected_video = DEFAULT_DATA["video_path"]
    current_frame = DEFAULT_DATA["current_frame"]
    print(f"rendering frame - {current_frame}")
    render_playback_time()
    captured_video = cv2.VideoCapture(selected_video)
    process_video(captured_video, current_frame, OUTPUT_IMAGE_PATH)
    new_frame = current_frame + DEFAULT_DATA['skip_frames']
    DEFAULT_DATA["current_frame"] = new_frame

    utils.video_utils.save_data_state(DEFAULT_DATA)
    # save_data_state(DEFAULT_DATA)

if __name__ == "__main__":
    try:
        # Check if a command-line argument is provided
        if len(sys.argv) != 2:
            playback_init()
            while True:
                # Create an instance with default values
                default_settings = utils.video_utils.VideoSettings(**DEFAULT_DATA)
                DEFAULT_DATA = utils.video_utils.load_data_state(default_settings)
                play_video()
                
                time.sleep(DEFAULT_DATA["time_per_frame"] / 1000)
            
        else:
            # Get the command-line argument
            command_argument = sys.argv[1].lower()
            if command_argument == "auto":
                while True:
                    DEFAULT_DATA = utils.video_utils.load_data_state(MOVIE_DATA)
                    play_video()
                    
                    time.sleep(DEFAULT_DATA["time_per_frame"] / 1000)
        
    except KeyboardInterrupt:
        print("stopped")
        pass    
