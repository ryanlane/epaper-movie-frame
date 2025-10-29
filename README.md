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

- Raspberry Pi (Zero 2 W or better recommended)
- [Pimoroni Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3)
- Photo frame [FrameWorks 8” x 10”](https://www.amazon.com/dp/B09KML783D)
- Custom Matboard [Matboard & More](https://www.matboardandmore.com/)

### Software

- Python 3.10+ recommended (works with 3.11/3.12 with patching)
- OpenCV
- NumPy
- Pillow
- `inky[rpi,example-depends]`
- FastAPI
- SQLite3 (included with Python)

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/ryanlane/epaper-movie-frame.git
cd epaper-movie-frame
````
### 2. Configure Pi
Make sure that SPI is enabled via `sudo raspi-config` or by editing `/boot/config.txt.`

### 3. Run system-level setup (one-time only)

This installs required packages like OpenCV, dev headers, and virtualenv support.

```bash
chmod +x system-setup.sh
./system-setup.sh
```

### 4. Create virtual environment and install Python dependencies

```bash
chmod +x project-install.sh
./project-install.sh
```

### 5. Create your `config.toml`

If it doesn’t exist, the app will prompt you. Example contents:

```toml
VIDEO_DIRECTORY = "videos"
OUTPUT_IMAGE_PATH = "output/frame.jpg"
DEVELOPMENT_MODE = false
```

---

## 🚀 Launch the App

Use the launch script to activate the environment and run the player:

```bash
./launch.sh
```

---

## 🖥️ Development Mode

You can run the system on a regular PC by enabling:

```toml
DEVELOPMENT_MODE = true
```

This disables hardware access and renders images to disk instead of using the e-paper display.

---

## 🌐 Web Interface

After starting the app, access the web UI at:

```text
http://<your-pi-ip>:8000
```

Features:

* Upload videos
* Adjust frame update intervals
* Toggle playback
* View live preview of the frame

---

## 🧱 Architecture Changes

* ✅ Replaced `VideoSettings` JSON state with SQLite
* ✅ All timing and frame data now pulled live from the database
* ✅ Playback state (`current_frame`) is updated after each frame
* ✅ Supports real-time updates from the web interface

---

## 📚 Documentation

- Technical Architecture: docs/TECHNICAL_ARCHITECTURE.md
- User Experience Guide: docs/USER_EXPERIENCE.md

These documents support handoff and porting this project to other platforms.

---

## 🧪 To Do

* [ ] Playlist or folder-based auto playback
* [ ] Better error handling around bad video files
* [ ] Add Waveshare display support
* [ ] Optionally export video metadata or history
* [ ] Offline-friendly log viewer in the web UI
* [ ] Build full OOBE for easy deployment

---

## 🙋 Author

**Ryan Lane**
Website: [ryanlane.com](http://ryanlane.com)

Support me on Ko-fi:
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/D1D81I8VM)
