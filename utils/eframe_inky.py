from PIL import Image
from inky.auto import auto


inky = auto(ask_user=True, verbose=True)

def get_inky_resolution():
    return inky.resolution

def show_on_inky(imagepath, saturation = 0.5):
    # Open the image file and load it into a PIL Image
    try:
        image = Image.open(imagepath)
        inky.set_image(image, saturation=saturation)
        inky.show()
    except FileNotFoundError:
        print(f"Error: Image file not found at {imagepath}")
    except Exception as e:
        print(f"Error: Unable to open the image. {e}")