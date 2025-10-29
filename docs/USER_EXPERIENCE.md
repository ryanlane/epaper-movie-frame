# E‑Paper Movie Frame — User Experience Guide

Last updated: 2025‑10‑11

This document captures the end‑to‑end UX: personas, primary flows, screens, states, and micro‑interactions. It is intended to help another team recreate the same behavior on a new platform.


## Personas

- Owner/Installer: Sets up the device, loads videos, configures timing and quiet hours, and verifies playback.
- Occasional Visitor: Glances at the frame; may open the Web UI to see current frame or playback time.


## Core Concepts

- Movie: A video file registered for slow playback. Identified by filename; stored under the configured video directory.
- Active Movie: The single movie that is currently being rendered to the e‑paper display.
- Frame Interval: The minutes between updates. Common presets: 10 minutes, 1 hour, 1 day; plus a custom value.
- Skip Frames: How many frames to advance per update. Larger values progress the video faster.
- Quiet Hours: A time window where playback pauses to avoid unnecessary refreshes (and flashing).


## First‑Run & Upload Flows

1) Upload via Web UI
- Navigate to Upload Movie.
- Choose a video file (mp4/avi/mkv/mov).
- See a progress bar during upload; on success, you are redirected to the movie details page.
- If the redirect does not occur, the Upload page provides a link to the First‑Run configuration page.

2) Configure from Existing Files (First Run)
- Navigate to the First Run page.
- Select a video filename already present under the configured video directory.
- Submit to register and process the first frame.

Notes:
- Duplicate uploads/files return you to the existing movie’s details.
- The system calculates total frame count and saves the initial frame preview.


## Navigation Structure

- Home: Overview with current status and quiet hours banner.
- Movies: List of registered movies; active item is marked with a ▶️ icon.
- Upload Movie: Upload form with progress and automatic redirect.
- Settings: Quiet Hours configuration.

Navigation is available via a top nav bar. On smaller screens, a hamburger menu toggles the links.


## Screens and States

### Home
- If an active movie exists: shows the playback status panel with current frame image, progress bar, frame counters, estimated remaining playback time, and Start/Stop button depending on state.
- If no active movie: shows a message with a link to select a movie.
- Quiet Hours Info: Visible banner indicating enabled/disabled and current activity (active or not) with a link to Settings.
- DEV Mode: If development mode is enabled, a banner warns that frames are not being sent to the e‑ink display.

### Movies
- Displays a vertical list of all movies by filename.
- The currently active movie shows a ▶️ indicator.
- Each item links to Movie Details.
- A Stop Playback button is provided below the list.

### Movie Details
- Title: “Settings for <filename>”.
- Controls:
  - Frame Interval: Dropdown with presets (10 min, 1 hr, 1 day) and “Other.”
  - Custom Time: Numeric field shown only if “Other” is selected; interpreted as minutes.
  - Skip Frames: Numeric field; must be ≥ 1.
  - Current Frame: Numeric field; updates starting point or current position.
  - Chaos Mode (Random): Checkbox for isRandom; stored but not currently used by playback logic.
  - Submit: Saves settings and refreshes the current frame preview on the server (stays on page).
  - Update Display Now: Triggers a one‑off display update immediately.
- Playback Panel: Shows the current frame image, a progress bar, numeric frame counts, and an estimated total remaining time.
- Start/Stop: Depending on whether this movie is active, shows Start Playback or Stop Playback.

Validation and Feedback:
- Submit posts JSON; on success, console logs. Consider adding a visual toast/snackbar.
- Update Display Now returns a JSON message and shows a browser alert.

### Upload Movie
- Single file input and Upload button.
- Shows OS file picker; on submit, shows progress bar and disables the button until completion.
- On success (HTTP 200), auto‑redirects to the Movie Details page.
- On error, automatically retries after 3 seconds.

### Settings
- Quiet Hours: Toggle checkbox to enable/disable.
- Quiet Start/End Hours: Inputs accepting 0–23; supports cross‑midnight windows.
- Save Settings: Ajax POST; alerts on success.


## Global Behaviors

- Active Frame Preview: Each movie has an image at /static/<movie_id>/frame.jpg used throughout the UI.
- Start/Stop Playback: Exactly one movie can be active at a time.
- Quiet Hours: If enabled, playback updates are paused and the banner on Home indicates the current state.
- Disk Stats: Movies and Home pages show total/used/free disk and size of the configured video directory.
- Responsiveness: Layout adapts for mobile; hamburger menu toggles nav links.


## Error States & Edge Cases

- Unsupported file types: Upload endpoint rejects files with a JSON error (UI currently shows generic failure and retries).
- Missing first frame: If frame extraction fails (e.g., bad video), Movie Details will lack a preview image; the server logs an error.
- current_frame beyond total_frames: The system wraps to 0.
- Multiple active movies: Database enforces a unique index; web actions always set only one active.
- Display hardware unavailable: In DEV Mode or development ENVIRONMENT, updates are saved to disk only.


## Text and Labels

- Buttons: Start Playback, Stop Playback, Submit, Update Display Now, Upload.
- Headings: Movie Frame Controls, Settings for <filename>, Upload a Movie, Configure Movie.
- Quiet Hours Banner: “Quiet Hours are enabled (start – end) and active now / not currently active.”


## Timing and Feedback Expectations

- After changing settings, the next automatic display update will occur at the configured interval; the server logs show the exact time.
- The “Update Display Now” button provides immediate feedback and display refresh.
- The Home page does not auto‑refresh; users can navigate or refresh manually to see updates.


## Accessibility & Internationalization

- Forms use labels and standard HTML inputs.
- No language localization features are included; porting teams can externalize labels and messages as needed.


## Porting Considerations

- Keep URL structure and JSON payloads stable or adjust the UI accordingly.
- Maintain per‑movie frame preview at a stable URL to simplify page rendering.
- Preserve DEV Mode banner and quiet hours banner behavior.
- If adding auth, consider a simple session or token model and CSRF handling for POSTs.


## Success Criteria Checklist

- [ ] User can register an existing file or upload a new one and land on its details page.
- [ ] Movie details show a preview image and accurate frame counters.
- [ ] User can start/stop playback and see state reflected on Home.
- [ ] Quiet hours settings affect playback and are visible in the Home banner.
- [ ] Upload progress displays and redirects on completion.
- [ ] Mobile layout functions via hamburger menu.

