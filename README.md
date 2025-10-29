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
- Inky
- Flask
- SQLite3 (included with Python)

Note: On Raspberry Pi, additional hardware libraries (SPI/GPIO) are installed via the optional extras group:

```bash
pip install -e '.[rpi]'
```

---

## ⚙️ Setup

### 1. Clone the repo

```bash
git clone https://github.com/ryanlane/epaper-movie-frame.git
cd epaper-movie-frame
````
### 2. Configure Pi
Make sure that SPI is enabled via `sudo raspi-config` or by editing `/boot/config.txt.`

### 3. Run the guided installer (recommended)

This sets up system packages (optional), creates a Python virtual environment, installs dependencies, writes `.env` and `config.toml`, and can install a systemd service.

```bash
chmod +x install.sh
./install.sh
```

Prefer manual steps? You can skip the installer and follow the "Manual installation (no installer)" section below. You may optionally run system-level deps first:

```bash
# Optional: system deps (apt)
./system-setup.sh
```

### Manual installation (no installer)

If you prefer to set everything up by hand (or the installer isn't suitable), follow these steps:

1) System packages (Debian/Ubuntu/Raspberry Pi OS)

```bash
sudo apt update
sudo apt install -y \
	python3-venv python3-pip python3-dev \
	libgl1 libopenblas-dev libopenjp2-7 libtiff-dev

# If installing Raspberry Pi hardware extras via pip and it fails to build lgpio,
# install these and retry the pip step:
#   sudo apt install -y swig liblgpio-dev
```

2) Create and activate a Python virtual environment, then install the project (editable)

```bash
python3 -m venv ./venv
source ./venv/bin/activate
python -m pip install --upgrade pip

# Desktop/WSL (no hardware):
pip install -e .

# Raspberry Pi (hardware support):
pip install -e '.[rpi]'
```

3) Create configuration files

- `.env` controls how scripts choose the environment and venv path.

```bash
cat > .env << 'EOF'
ENVIRONMENT=development   # or production
VENV_PATH=./venv          # path to your virtualenv
EOF
```

- `config.toml` controls app behavior. For development (no hardware), use:

```bash
cat > config.toml << 'EOF'
TARGET_WIDTH = 800
TARGET_HEIGHT = 600
VIDEO_DIRECTORY = "videos"
OUTPUT_IMAGE_PATH = "frame.jpg"
DEVELOPMENT_MODE = true
EOF
```

For hardware on a Pi, set `DEVELOPMENT_MODE = false` and ensure SPI is enabled via `sudo raspi-config` or by editing `/boot/config.txt`.

4) Create needed directories

```bash
mkdir -p videos
```

5) Launch the app

```bash
chmod +x launch.sh
./launch.sh
## or, inside the venv
movieframe
```

The database and default settings are created automatically on first run.

6) Optional: run as a systemd service (Pi/Linux with systemd)

```bash
SERVICE_NAME=movieframe
SERVICE_FILE=/etc/systemd/system/${SERVICE_NAME}.service

sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=E-Paper Movie Frame
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=$(pwd)
Environment=ENVIRONMENT=${ENVIRONMENT:-production}
ExecStart=$(pwd)/launch.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"
sudo systemctl --no-pager status "$SERVICE_NAME"
```

---

## 🚀 Launch the App

After the installer, you can start the app anytime with:

```bash
./launch.sh
```

Or, from within the virtual environment, you can use the console script:

```bash
movieframe
```

If you chose to install a systemd service, it can be managed with:

```bash
sudo systemctl status movieframe   # or your chosen name
sudo systemctl start movieframe
sudo systemctl stop movieframe
```

---

## 🖥️ Development Mode

You can run the system on a regular PC by enabling:

```toml
DEVELOPMENT_MODE = true
```

This disables hardware access and renders images to disk instead of using the e-paper display.

Tip: The installer can set this for you. It writes `ENVIRONMENT=development` to `.env` and toggles `DEVELOPMENT_MODE` in `config.toml`.

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

## 🧹 Uninstall

To remove the service and local artifacts:

```bash
chmod +x uninstall.sh
./uninstall.sh
```

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
