# Video Playback and Frame Capture

This Python script allows you to play back a video at a specified time interval, capturing and resizing frames along the way so that the still frame can be displayed on an ePaper style display. 

## Project Background and Inspiration
This project draws inspiration from the December 2018 post by Bryan Boyer, titled [“Creating a Very Slow Movie Player”](https://medium.com/s/story/very-slow-movie-player-499f76c48b62). In his thought-provoking essay, Boyer explores the interplay of light, Brasília, and architecture. The focal point of his project is an e-paper display designed to showcase films at an extraordinarily slow rate of 24 frames per hour, in stark contrast to the conventional 24 frames per second. This unique approach transforms the viewing experience, requiring an entire year to play the 142-minute masterpiece, "2001: A Space Odyssey."

In August 2020, Tom Whitwell further contributed to the concept with his post ["How to Build a Very Slow Movie Player for £120 in 2020"](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4)". Whitwell provided detailed instructions on constructing a Very Slow Movie Player (VSMP) using the then-new [7.5-inch, Raspberry Pi-compatible e-paper display from Waveshare](https://www.waveshare.com/product/displays/e-paper/epaper-1/7.5inch-e-paper-hat.htm).

### My Version

Inspired by these pioneering works, this project aims to extend the concept of Very Slow Movie Players. By utilizing Python, OpenCV, and the [Pimoroni Inky Impression](https://shop.pimoroni.com/products/inky-impression-7-3?variant=40512683376723) display, this version of the "movie player" strives to provide an accessible and customizable platform for enthusiasts to create their own cinematic experiences at an intentionally decelerated pace with the addition of color.

## Prerequisites

- Python 3
- OpenCV (`pip install opencv-python`)
- NumPy (`pip install numpy`)

## Usage

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/ryanlane/epaper-movie-frame.git


2. Navigate to the script's directory:

   ```bash
   cd epaper-movie-frame
   ```

3. Run the script:

   ```bash
   python movieplayer.py
   ```

4. Follow the on-screen prompts to select a video, set update intervals, frames to skip, and start the playback.

## Configuration

- `TARGET_WIDTH` and `TARGET_HEIGHT`: Set the target dimensions for resizing frames. This value will be detected by the Inky hardware.
- `VIDEO_DIRECTORY`: Specify the directory where your video files are located.
- `OUTPUT_IMAGE_PATH`: Path to save the resized frame as an image.
- `MOVIE_DATA`: File to store and load playback data.

## Class: VideoSettings

The `VideoSettings` class is used to manage video playback settings. It includes the following attributes:

- `video_path`: Path to the selected video file.
- `time_per_frame`: Time interval between frame updates.
- `skip_frames`: Number of frames to skip during playback.
- `current_frame`: Current frame during playback.
- `total_frames`: Total number of frames in the video.
- `resolution`: Target resolution for resizing frames.
- `video_root_path`: Root path for video files.
- `output_image`: Path to save the resized frame as an image.

## Functions

- `save_data_state(video_settings)`: Save the video settings to a JSON file.
- `load_data_state(video_settings)`: Load video settings from a JSON file.
- `check_file_existence(video_settings)`: Check if a playback file exists and decide whether to continue or start over.
- `list_video_files(directory)`: List all video files in the specified directory.
- `calculate_playback_time(video_settings)`: Calculate estimated playback time based on video settings.
- `render_future_date(milliseconds=0)`: Render a future date based on milliseconds.
- `select_video(video_files, video_settings)`: Prompt the user to select a video from the list.
- `get_update_interval()`: Get the user's choice for frame update intervals.
- `get_frames_to_skip()`: Get the user's choice for the number of frames to skip.
- `get_total_frames(cap)`: Get the total number of frames in a video.
- `extract_frame_as_image(cap, frame_number)`: Extract a specific frame as an image.
- `render_playback_time(video_settings)`: Render estimated playback time and future frame date.
- `save_frame_as_image(frame, video_settings)`: Save a frame as an image with specified quality.
- `resize_with_black_borders(image, target_width, target_height)`: Resize an image while maintaining its aspect ratio and adding black borders.
- `process_video(cap, video_settings)`: Process a video, extract a specific frame, resize it, and save it as an image.
- `progress_animation(percentage)`: Display a progress animation during video processing.
- `playback_init(video_settings, logger)`: Initialize video playback settings and prompt user decisions.
- `play_video(video_settings, logger)`: Play the video based on the current settings.

## Author

Ryan Lane
You can find more information about my other projects on my site [http://ryanlane.com](http://ryanlane.com)

```

## TO DO
[x] Update README.md
[ ] add images to this document
[ ] Complete Inky display integration
[ ] Add Waveshare hardware
[ ] Build web based management