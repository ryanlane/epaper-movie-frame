# E-Paper Movie Frame

This Python project plays a video back at an extremely slow pace, updating a frame on a color e-paper display (like Pimoroni Inky Impression) at a defined interval. A local web interface allows you to manage and view playback in real-time.

---

## ✨ Highlights

- Inspired by [Bryan Boyer’s Very Slow Movie Player](https://medium.com/s/story/very-slow-movie-player-499f76c48b62) and [Tom Whitwell’s 2020 version](https://debugger.medium.com/how-to-build-a-very-slow-movie-player-in-2020-c5745052e4e4)
- Powered by a Raspberry Pi and a Pimoroni Inky display
- Web UI for uploading videos, setting frame intervals, and previewing current frames
- Playback state stored in SQLite for full synchronization
- Optional development mode for testing on desktop

---

## 🖼️ Example

![photo of a frame showing a frame from the TV mini series Scavengers Reign](https://images.squarespace-cdn.com/content/v1/596ebdf720099ea43cf390d8/380eb70e-eb34-433f-92f6-c1fd0e31f202/IMG_0953.jpeg?format=1500w)

📺 [Video demo of frame update](https://youtu.be/L7wVuyFQOXI)

---

## 🧰 Requirements

### Hardware

- Raspberry Pi (Zero W or newer recommended)
- [Pimoroni Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3)

### Software

- Python 3.10+
- OpenCV (`sudo apt install python3-opencv`)
- NumPy
- Pillow
- Inky driver: `pip install inky[rpi,example-depends]`
- Flask (`pip install flask`)
- `python-dotenv`
- SQLite3 (included with Python)

---

## ⚙️ Setup

1. **Clone the repo:**

```bash
git clone https://github.com/ryanlane/epaper-movie-frame.git
cd epaper-movie-frame
```

2. **Install dependencies:**

```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

3. **Edit your `config.toml`:**

```toml
VIDEO_DIRECTORY = "/home/pi/videos"
TARGET_WIDTH = 800
TARGET_HEIGHT = 480
OUTPUT_IMAGE_PATH = "frame.jpg"
DEVELOPMENT_MODE = false
```

4. **Start the application:**

```bash
python movieplayer.py
```

---

## 🖥️ Development Mode

You can run the system on a regular PC by enabling:

```toml
DEVELOPMENT_MODE = true
```

This disables hardware access and renders images to disk for viewing in the browser.

---

## 🌐 Web Interface

Run the web server on your Pi and open it from a browser on the network:

```bash
http://<your-pi-ip>:8000
```

Features:
- Upload videos
- Adjust frame update intervals
- Toggle playback
- View live preview of the frame

---

## 🧱 Architecture Changes

- ✅ Replaced `VideoSettings` with SQLite as the single source of truth
- ✅ All timing and frame data now pulled live from the database
- ✅ Playback state (`current_frame`) is updated after each frame
- ✅ Supports real-time updates from the web interface without restarting

---

## 🧪 To Do

- [ ] Playlist or folder-based auto playback
- [ ] Better error handling around bad video files
- [ ] Add Waveshare display support
- [ ] Optionally export video metadata or history
- [ ] Offline-friendly log viewer in the web UI

---

## 🙋 Author

**Ryan Lane**  
Website: [ryanlane.com](http://ryanlane.com)

Support me on Ko-fi:  
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D81I8VM)
