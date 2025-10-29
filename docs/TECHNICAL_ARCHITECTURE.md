# E‑Paper Movie Frame — Technical Architecture

Last updated: 2025‑10‑11

This document describes the architecture, data model, services, dependencies, and operational considerations of the E‑Paper Movie Frame project so another team can re‑implement or port the system to a different platform.


## System Overview

The system plays a video extremely slowly by periodically rendering a single frame to an e‑paper display. A local web UI manages uploads and playback settings. Playback state and settings persist in SQLite.

High-level components:
- Web UI Server (Flask): routes, templates, uploads, settings forms
- Player Loop: background loop that advances frames and updates the display
- Video Processing: OpenCV-based frame extraction and resizing with pillarboxing
- Hardware Abstraction: Inky display integration with a development mode
- Persistence: SQLite database for settings and movies
- Static Assets: rendered frames, CSS, fonts


## Codebase Map

- webui.py — Flask app, routes, templating, upload handling
- movieplayer.py — entry point; starts web UI in background thread and runs main playback loop
- database.py — SQLite schema, migrations, CRUD helpers
- utils/
  - video_utils.py — OpenCV operations, frame save, playback logic, quiet hours, disk stats
  - eframe_inky.py — Inky hardware integration and startup screen
  - config.py — TOML reader
- templates/ — Jinja pages for home, movies, movie details, upload, settings, partials
- static/ — CSS, fonts, favicon, and per‑movie rendered frame images under static/<movie_id>/frame.jpg
- config.toml — runtime configuration (mirrors config.example.toml)


## Runtime Topology and Data Flow

1) Initialization
- movieplayer.py calls init_database(), which ensures tables and default Settings exist and optionally prompts to sync config.toml with DB.
- movieplayer.run_webui() starts the Flask server on 0.0.0.0:8000 in a daemon thread and polls for readiness.
- eframe_inky.show_startup_status() renders a startup image with IP address/URL and optional QR code; in DEV_MODE it only saves to disk.

2) Web UI interactions (webui.py)
- GET /: dashboard summary including quiet hours status and current playback info.
- GET /movies: list all movies and disk stats.
- GET /first_run: lists files in VIDEO_DIRECTORY for initial configuration.
- GET /movie/<id>: per‑movie settings page and live preview.
- POST /add_movie: registers a selected file from VIDEO_DIRECTORY as a Movie, computes total_frames, saves first frame.
- GET/POST /upload: uploads directly to VIDEO_DIRECTORY; then registers Movie, computes total_frames, processes first frame; returns JSON with new movie_id.
- POST /update_movie: updates Movie fields (time_per_frame, skip_frames, current_frame, isRandom, total_frames recalculated); regenerates preview frame.
- POST /start_playback/<id>: marks exactly one Movie as active.
- POST /stop_playback: clears active movie.
- POST /trigger_display_update/<id>: regenerates current frame and pushes to Inky immediately.
- GET/POST /settings: reads/updates Settings (quiet hours fields).

3) Playback loop (movieplayer.main)
- Polls database for the active movie. If none, sleeps 5s and repeats.
- For the active movie, calls video_utils.play_video(logger):
  - Honors quiet hours via should_skip_due_to_quiet_hours(settings).
  - Reads the current frame, target resolution, and path from DB.
  - Opens video via OpenCV, seeks to current_frame, resizes with black borders to Settings.Resolution, writes to static/<movie_id>/frame.jpg.
  - If not DEV_MODE, sends image to Inky via eframe_inky.show_on_inky().
  - Estimates remaining playback time; logs next display update time.
  - Increments current_frame by skip_frames (wraps to 0 when >= total_frames) and persists to DB.
- Sleeps time_per_frame minutes, then repeats.


## Configuration

- config.toml (example in config.example.toml)
  - TARGET_WIDTH, TARGET_HEIGHT: used at DB insert_default_settings() to seed Settings.Resolution (WIDTH,HEIGHT)
  - VIDEO_DIRECTORY: path used as Settings.VideoRootPath
  - OUTPUT_IMAGE_PATH: not used by runtime paths (legacy)
  - DEVELOPMENT_MODE: read by utils.video_utils (DEV_MODE) and eframe_inky.show_startup_status() to decide whether to push to hardware

- .env (optional): controls eframe_inky hardware access via ENVIRONMENT=development


## Persistence and Schema

Database file: database.sqlite

Tables:
- Settings
  - id INTEGER PK
  - VideoRootPath TEXT (directory containing videos)
  - Resolution TEXT ("WIDTH,HEIGHT")
  - use_quiet_hours BOOLEAN DEFAULT 0
  - quiet_start INTEGER DEFAULT 22
  - quiet_end INTEGER DEFAULT 7

- Movie
  - id INTEGER PK
  - video_path TEXT (filename only; joined with Settings.VideoRootPath)
  - total_frames INTEGER
  - time_per_frame INTEGER (minutes; 0 used as sentinel for "custom" in UI but stored as a concrete integer)
  - skip_frames INTEGER (frames to advance per tick)
  - current_frame INTEGER (0‑based for extractor; UI shows 1‑based semantics)
  - isActive BOOLEAN DEFAULT 0 (unique index ensures at most one active movie)
  - isRandom BOOLEAN DEFAULT 0 (checkbox exposed in UI; not used in playback path yet)

- NowPlaying
  - id INTEGER PK
  - movie_id INTEGER
  - updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- SchemaVersion
  - version INTEGER (migration guard; currently set to 3)

Access layer functions (database.py) encapsulate CRUD and simple migrations.


## External Interfaces (Routes)

- GET /
- GET /movies
- GET /first_run
- GET /movie/<int:movie_id>
- POST /add_movie (form-encoded)
- GET|POST /upload (multipart; JSON response)
- POST /update_movie (JSON)
- POST /start_playback/<int:movie_id>
- POST /stop_playback
- POST /delete_movie/<int:movie_id> (JSON result; not linked in UI)
- POST /trigger_display_update/<int:movie_id> (JSON)
- GET|POST /settings (HTML/JSON)

Notes:
- Upload flow returns JSON then client redirects to /movie/<id>.
- Error handling is minimal (e.g., upload type check, null checks); callers should be resilient when porting.


## Video Processing Details

- OpenCV VideoCapture with CAP_PROP_POS_FRAMES seek to current_frame.
- Frame resizing preserves aspect ratio and pads with black borders to target resolution from Settings.Resolution.
- Images saved as JPEG at quality 90 to static/<movie_id>/frame.jpg.
- total_frames is obtained via CAP_PROP_FRAME_COUNT on the full path.

Edge cases and behaviors:
- If current_frame >= total_frames, wrap to 0.
- If a frame cannot be read, the tick is skipped; current_frame is not advanced.
- Skip_frames is applied on each successful tick.


## Display Integration

- Inky detection via inky.auto.auto(ask_user=True, verbose=True) unless ENVIRONMENT=development in .env
- show_on_inky(image_path, saturation=0.5) loads PIL image and calls inky.set_image then inky.show()
- Startup screen (show_startup_status) draws title, date/time, now-playing text, Web UI URL, and QR code

To support other displays, replace utils/eframe_inky.py with an adapter while preserving show_on_inky(imagepath) and get_inky_resolution().


## Quiet Hours

- Feature flags in Settings: use_quiet_hours, quiet_start, quiet_end
- should_skip_due_to_quiet_hours(settings) returns True if current hour is inside the defined interval; supports cross‑midnight windows (e.g., 22→7)
- When active, play_video() returns without updating display or advancing frames


## Logging

- movieplayer.setup_logger configures root logging level/format
- webui.py attaches RotatingFileHandler('webui.log', 10KB, 1 backup)
- movieplayer prints readiness and no‑active‑movie heartbeat messages


## Dependencies

Key runtime packages:
- Flask (3.1)
- Jinja2 (3.1)
- OpenCV (opencv-python 4.11)
- numpy >= 2.0
- Pillow 11.x
- inky 2.1
- qrcode 8.x
- python-dotenv
- requests (for readiness check)

OS-level considerations (on Raspberry Pi): SPI enabled; Inky drivers and GPIO access (spidev, gpiod, gpiozero, rpi-lgpio) per requirements.txt


## Deployment

- Typical target: Raspberry Pi running Linux with Inky Impression attached
- Scripts: system-setup.sh (apt packages), project-install.sh (venv + pip), launch.sh (activate and start movieplayer.py)
- Service installation examples are provided as shell scripts (install_as_service.example.sh)

Network:
- Web UI binds 0.0.0.0:8000
- Startup screen shows http://<pi-ip>:8000

Storage:
- database.sqlite in project root
- Videos under Settings.VideoRootPath (defaults to ./videos)
- Rendered frames under ./static/<movie_id>/frame.jpg


## Porting Guide — Recommended Contracts

When porting to another platform/service, preserve these contracts:

- Data model:
  - Settings fields and semantics; Resolution as "WIDTH,HEIGHT"
  - Movie fields and behaviors (wrapping, skip_frames increment)
- File layout:
  - Per‑movie preview/render path at static/<movie_id>/frame.jpg (or an equivalent URL served by the web layer)
- APIs:
  - Route set and payloads listed above, or provide compatible equivalents for the UI
- Processing behavior:
  - Resize with letter/pillarboxing to exact Resolution
  - JPEG output around quality 90 (or visually equivalent)
  - Quiet hours suppression without advancing state
- Playback cadence:
  - Advance time_per_frame minutes between ticks, using skip_frames frames per tick, wrapping to 0


## Known Gaps and Opportunities

- models.py (SQLAlchemy) is not used by runtime (SQLite via sqlite3 module is used instead)
- isRandom flag is not implemented in playback logic
- Some duplicate calls and redundant imports in webui.py (double fetch in /movie route)
- Minimal error handling and validation for bad/corrupt video files
- No authentication for the web UI
- DEV_MODE is read from config.toml; hardware dev mode is also controlled via .env, which may diverge


## Security and Privacy

- Web UI is unauthenticated and listens on all interfaces; consider securing or binding to localhost when necessary
- Uploaded files are saved under VideoRootPath using werkzeug.secure_filename
- No PII; ensure logs do not leak network details in sensitive environments


## Testing and Observability

- Manual testing through the Web UI; no automated tests present
- Logs: webui.log (rotating), stdout for movieplayer
- Consider adding health endpoint, structured logs, and unit tests around video_utils and database access if porting


## Acceptance and Readiness Checklist

- [ ] Can list videos from VideoRootPath and register as Movie with computed total_frames
- [ ] Can upload via /upload and redirect to /movie/<id>
- [ ] Can start/stop playback and see frame file update under static/<id>/frame.jpg
- [ ] Quiet hour suppression works and does not advance current_frame
- [ ] Player wraps to frame 0 at end of video
- [ ] Startup screen renders and shows correct IP URL
- [ ] Web routes respond and show expected templates

