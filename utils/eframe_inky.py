from PIL import Image, ImageDraw, ImageFont
import datetime
import os
import socket
import qrcode
from utils import config
from dotenv import load_dotenv
from inky.auto import auto

# since I'm not writing my code directly on the raspberry pi, I'm using the .env
# to handle whether or not I want to expose the actual inky hardware

# Load environment variables from .env file
load_dotenv()

use_fake_data = os.getenv("ENVIRONMENT") == "development"

if not use_fake_data:
    inky = auto(ask_user=True, verbose=True)

def get_inky_resolution():

    if use_fake_data:
        return [800,480]
    else:
        width = inky.resolution[0]
        height = inky.resolution[1]
        res = [width, height]
        return res

def show_on_inky(imagepath, saturation = 0.5):
    if use_fake_data:
        print("dev build mode: this is when the inky would load the image and display it.")
    else:
        # Open the image file and load it into a PIL Image
        try:
            image = Image.open(imagepath)
            inky.set_image(image, saturation=saturation)
            print("\n frame being displayed on inky")
            inky.show()
        except FileNotFoundError:
            print(f"Error: Image file not found at {imagepath}")
        except Exception as e:
            print(f"Error: Unable to open the image. {e}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "Unavailable"

def show_startup_status(movie=None):
    from .eframe_inky import show_on_inky  # Use relative import inside project
    DEV_MODE = config.read_toml_file("config.toml").get("DEVELOPMENT_MODE", False)

    WIDTH = 800
    HEIGHT = 480
    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)

    draw.text((20, 20), "E-Paper Movie Frame", font=title_font, fill=(0, 0, 0))
    draw.text((20, 80), f"Service started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", font=small_font, fill=(0, 0, 0))

    if movie:
        draw.text((20, 140), f"Now playing: {movie['video_path']}", font=small_font, fill=(0, 0, 0))
    else:
        draw.text((20, 140), "No movie is currently active", font=small_font, fill=(0, 0, 0))

    ip = get_local_ip()
    url = f"http://{ip}:8000" if ip != "Unavailable" else "http://<your-pi-ip>:8000"
    draw.text((20, 200), f"Web UI: {url}", font=small_font, fill=(0, 0, 0))

    if ip != "Unavailable":
        qr = qrcode.make(url)
        qr = qr.resize((120, 120))
        image.paste(qr, (WIDTH - 140, HEIGHT - 140))

    image_path = "startup_frame.jpg"
    image.save(image_path)

    if not DEV_MODE:
        show_on_inky(image_path)
    else:
        print(f"[DEV_MODE] Skipping e-ink update. Saved {image_path}")