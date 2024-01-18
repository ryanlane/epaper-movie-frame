from PIL import Image
import os
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