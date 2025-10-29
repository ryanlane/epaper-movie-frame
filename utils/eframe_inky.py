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

# Attempt to initialize Inky when not in development mode, but avoid
# interactive prompts and fail gracefully if detection isn't possible.
inky = None
if not use_fake_data:
    # Allow forcing model/colour via environment, eg: INKY_TYPE=spectra73 INKY_COLOUR=red
    forced_type = os.getenv("INKY_TYPE")
    forced_colour = os.getenv("INKY_COLOUR")
    try:
        if forced_type or forced_colour:
            try:
                inky = auto(ask_user=False, verbose=True, type=forced_type, colour=forced_colour)
            except TypeError:
                # Older inky.auto may not accept type/colour kwargs; fall back to plain auto
                inky = auto(ask_user=False, verbose=True)
        else:
            inky = auto(ask_user=False, verbose=True)
    except Exception:
        print("[WARN] Failed to initialise Inky (auto). If you have a board attached, you can set INKY_TYPE (eg 'spectra73')"
              " and INKY_COLOUR ('red'|'yellow'|'black') in .env. Falling back to non-hardware mode.")
        use_fake_data = True
        inky = None

def get_inky_resolution():
    # Default to the common Inky Impression 7.3" resolution if hardware is unavailable
    if use_fake_data or inky is None:
        return [800, 480]
    else:
        width, height = inky.resolution
        return [width, height]

def show_on_inky(imagepath, saturation=0.5):
    if use_fake_data or inky is None:
        print("[DEV/NON-HW] Would display image on Inky: skipping hardware update.")
        return
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