#!/usr/bin/env bash

# Modern guided installer for E-Paper Movie Frame
# - Installs system packages (optional)
# - Creates Python venv and installs requirements
# - Creates/updates .env and config.toml
# - Optionally installs a systemd service
# - Offers to launch the app

set -euo pipefail

# ---------------------------
# UI helpers (gum if available)
# ---------------------------
has_cmd() { command -v "$1" >/dev/null 2>&1; }

GUM_AVAILABLE=false
if has_cmd gum; then
  GUM_AVAILABLE=true
fi

cecho() { # colored echo
  local color="$1"; shift
  local msg="$*"
  local reset="\033[0m"
  local code=""
  case "$color" in
    red) code="\033[31m";;
    green) code="\033[32m";;
    yellow) code="\033[33m";;
    blue) code="\033[34m";;
    magenta) code="\033[35m";;
    cyan) code="\033[36m";;
    *) code="";;
  esac
  if [ -t 1 ]; then
    echo -e "${code}${msg}${reset}"
  else
    echo "$msg"
  fi
}

info()    { cecho cyan    "[INFO]  $*"; }
success() { cecho green   "[OK]    $*"; }
warn()    { cecho yellow  "[WARN]  $*"; }
error()   { cecho red     "[ERROR] $*"; }

confirm() {
  local prompt="$1"; shift || true
  local default="${1:-Y}"
  if $GUM_AVAILABLE; then
    if gum confirm --default=$( [ "$default" = "Y" ] && echo "true" || echo "false" ) "$prompt"; then
      return 0
    else
      return 1
    fi
  else
    local suffix="[Y/n]"
    [ "$default" = "N" ] && suffix="[y/N]"
    read -rp "$prompt $suffix " ans || true
    ans=${ans:-$default}
    case "$ans" in
      Y|y|yes|YES) return 0;;
      *) return 1;;
    esac
  fi
}

prompt() {
  local question="$1"; shift || true
  local default_val="${1:-}"
  local value
  if $GUM_AVAILABLE; then
    if [ -n "$default_val" ]; then
      value=$(gum input --placeholder "$default_val" --value "$default_val" --prompt "$question ")
    else
      value=$(gum input --prompt "$question ")
    fi
  else
    if [ -n "$default_val" ]; then
      read -rp "$question [$default_val] " value || true
      value=${value:-$default_val}
    else
      read -rp "$question " value || true
    fi
  fi
  echo "$value"
}

section() {
  local title="$1"
  if $GUM_AVAILABLE; then
    gum style --border normal --margin "1 0" --padding "1 2" --border-foreground 212 "$title"
  else
    echo
    cecho magenta "===== $title ====="
  fi
}


# ---------------------------
# Pre-flight checks
# ---------------------------
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

section "E-Paper Movie Frame • Installer"
echo "This guided setup will prepare your system and project environment."

# Python check (3.10+ recommended)
if has_cmd python3; then
  PY_VER=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])') || PY_VER="0.0"
  info "Detected Python $PY_VER"
else
  error "python3 not found. Please install Python 3.10+ and re-run."
  exit 1
fi

# Detect Raspberry Pi and handle Python 3.13+ C-extension header issues
IS_RPI=false
if [ -f /proc/device-tree/model ] && grep -qi "raspberry pi" /proc/device-tree/model 2>/dev/null; then
  IS_RPI=true
fi

PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)

# Make apt package check helper available early
apt_has_pkg() {
  local pkg="$1"
  apt-cache show "$pkg" 2>/dev/null | grep -q "^Package: $pkg$"
}

APT_EXTRA_PKGS=""
VENV_SITEPKG_FLAG=""
PI_ENV_PATH=""

if $IS_RPI && [ "${PY_MAJOR:-0}" -eq 3 ] && [ "${PY_MINOR:-0}" -ge 13 ]; then
  section "Raspberry Pi: Python $PY_VER detected"
  warn "Python $PY_VER is newer than what many Pi wheels support today."
  warn "C-extensions (like spidev) may fail to build without matching Python headers."
  info "You can choose between two setup paths:"
  info "  Path A (recommended): Uses system Python and apt's spidev; fastest and most reliable on Pi."
  info "  Path B: Keep your custom Python and compile spidev; requires matching python3.X-dev headers."

  if confirm "Use Path A (RECOMMENDED): system Python + apt spidev + venv with system site packages?" Y; then
    PI_ENV_PATH="A"
    VENV_SITEPKG_FLAG="--system-site-packages"
    APT_EXTRA_PKGS="python3 python3-venv python3-dev python3-pip python3-spidev build-essential"
    info "Selected Path A. We'll prefer apt's spidev and share it into the venv."
  else
    PI_ENV_PATH="B"
    # Try to install a matching dev headers package if available
    DEV_PKG="python3.${PY_MINOR}-dev"
    if apt_has_pkg "$DEV_PKG"; then
      APT_EXTRA_PKGS="${APT_EXTRA_PKGS} ${DEV_PKG} build-essential"
      info "Selected Path B. Will install $DEV_PKG for header files."
    else
      APT_EXTRA_PKGS="${APT_EXTRA_PKGS} build-essential"
      warn "Package $DEV_PKG not found. If build fails, consider Path A or install a supported Python (3.11/3.12) via pyenv."
    fi
  fi
fi

# Detect package manager
PKG_MGR=""
if has_cmd apt; then PKG_MGR="apt"; fi

# Ask for system packages
INSTALL_SYS_DEPS=false
if [ -n "$PKG_MGR" ]; then
  info "Optionally install system packages via apt (build tools and libraries used by OpenCV, TIFF/JP2, and Python headers)."
  info "Recommended on Raspberry Pi or fresh installs. Safe to skip if you've already installed these."
  if confirm "Install/Update system dependencies with apt?" Y; then
    INSTALL_SYS_DEPS=true
  fi
else
  warn "No supported package manager detected; skipping system dependencies."
fi

if $INSTALL_SYS_DEPS; then
  section "Installing system packages"
  info "Updating apt and installing base libraries (sudo required)."
  sudo apt update
  # Detect best-available math/TIFF libs across distros
  # More robust than exit code: ensure apt-cache show returns a real stanza for this package
  apt_has_pkg() {
    local pkg="$1"
    apt-cache show "$pkg" 2>/dev/null | grep -q "^Package: $pkg$"
  }

  MATH_PKG="libatlas-base-dev"
  if ! apt_has_pkg "$MATH_PKG"; then
    MATH_PKG="libopenblas-dev"
  fi

  TIFF_PKG="libtiff5"
  if ! apt_has_pkg "$TIFF_PKG"; then
    if apt_has_pkg libtiff6; then
      TIFF_PKG="libtiff6"
    else
      TIFF_PKG="libtiff-dev"
    fi
  fi

  # Install core packages; rely on pip for opencv-python
  sudo apt install -y \
    python3-venv python3-pip python3-dev \
    libgl1 "$MATH_PKG" libopenjp2-7 "$TIFF_PKG" ${APT_EXTRA_PKGS}
  success "System dependencies installed."
fi


# ---------------------------
# Virtual environment
# ---------------------------
section "Python virtual environment"
DEFAULT_VENV="$PROJECT_ROOT/venv"
info "We'll create a Python virtual environment to isolate this project's Python packages."
if [ -n "$VENV_SITEPKG_FLAG" ]; then
  info "Because you selected Path A, the venv will include --system-site-packages so it can use apt-installed modules like spidev."
fi
VENV_PATH=$(prompt "Where should the virtual environment live?" "$DEFAULT_VENV")

if [ ! -d "$VENV_PATH" ]; then
  info "Creating venv at $VENV_PATH"
  python3 -m venv $VENV_SITEPKG_FLAG "$VENV_PATH"
else
  info "Using existing venv at $VENV_PATH"
fi

# shellcheck disable=SC1090
source "$VENV_PATH/bin/activate"
python -m pip install --upgrade pip

# ---------------------------
# App configuration (choose mode before Python deps)
# ---------------------------
section "Application configuration"

# .env controls how launch.sh picks the venv path via ENVIRONMENT
info "Development mode disables hardware access and writes rendered frames to disk for testing on non-Pi machines."
info "Production mode targets the Inky display; ensure SPI is enabled and hardware is connected."
if confirm "Use development mode (no hardware, renders to disk)?" N; then
  ENVIRONMENT="development"
  DEV_MODE=true
else
  ENVIRONMENT="production"
  DEV_MODE=false
fi

# Install Python deps via pip only; no hardware-extras prompts or auto-apt.
set +e
pip install -e .
PIP_STATUS=$?
set -e
if [ $PIP_STATUS -ne 0 ]; then
  warn "pip install failed. If the error mentions 'lgpio' or '-llgpio' on Raspberry Pi, install system packages and retry:"
  echo "  sudo apt install -y swig liblgpio-dev"
  warn "If errors mention 'Python.h' missing on Pi, see README Troubleshooting for Path A/Path B guidance."
  error "Aborting due to pip install failure. After installing system packages, re-run ./install.sh or run 'pip install -e .' inside your venv."
  exit 1
fi

success "Project installed in editable mode and dependencies installed."

# If on Raspberry Pi and Path B, attempt to build/install spidev in this venv
if [ "${PI_ENV_PATH:-}" = "B" ]; then
  section "Installing spidev for custom Python"
  python -V || true
  info "Upgrading build tooling and installing spidev via pip (will compile if needed)."
  pip install --upgrade pip setuptools wheel || true
  if pip install spidev; then
    success "Installed spidev via pip."
  else
    warn "Failed to install spidev. Ensure matching Python headers are installed (e.g., python${PY_VER}-dev) or switch to Path A."
  fi
fi

# Verify spidev availability
if $IS_RPI; then
  section "Verifying spidev"
  if python - <<'PY'
try:
    import spidev
    import sys
    print(f"spidev OK, version: {getattr(spidev, '__version__', 'unknown')}")
except Exception as e:
    import sys
    print(f"spidev import failed: {e}")
    sys.exit(1)
PY
  then
    success "spidev is available to Python."
  else
    if [ "${PI_ENV_PATH:-}" = "A" ]; then
      warn "spidev not found in venv. Ensure 'python3-spidev' is installed via apt and that this venv uses --system-site-packages."
    else
      warn "spidev not found. Try 'sudo apt install python3.${PY_MINOR}-dev build-essential' (if available) and re-run, or switch to Path A."
    fi
  fi
fi


# ---------------------------
# App configuration
# ---------------------------
echo "ENVIRONMENT=$ENVIRONMENT" > .env
echo "VENV_PATH=$VENV_PATH" >> .env
success "Wrote .env (ENVIRONMENT=$ENVIRONMENT)."

# config.toml
CFG_FILE="config.toml"
if [ ! -f "$CFG_FILE" ]; then
  info "Creating $CFG_FILE"
  VIDEO_DIR_DEFAULT="videos"
  VIDEO_DIR=$(prompt "Video directory path" "$VIDEO_DIR_DEFAULT")
  mkdir -p "$VIDEO_DIR"
  cat > "$CFG_FILE" <<EOF
TARGET_WIDTH = 800
TARGET_HEIGHT = 480
VIDEO_DIRECTORY = "$VIDEO_DIR"
OUTPUT_IMAGE_PATH = "frame.jpg"
DEVELOPMENT_MODE = $DEV_MODE
EOF
  success "Created $CFG_FILE"
else
  info "$CFG_FILE already exists."
  if confirm "Update DEVELOPMENT_MODE in $CFG_FILE to $DEV_MODE?" Y; then
    # Update or add DEVELOPMENT_MODE
    if grep -q '^DEVELOPMENT_MODE' "$CFG_FILE"; then
      sed -i "s/^DEVELOPMENT_MODE.*/DEVELOPMENT_MODE = $DEV_MODE/" "$CFG_FILE"
    else
      echo "DEVELOPMENT_MODE = $DEV_MODE" >> "$CFG_FILE"
    fi
    success "Updated DEVELOPMENT_MODE in $CFG_FILE"
  fi
fi


# ---------------------------
# Optional: systemd service
# ---------------------------
if has_cmd systemctl; then
  section "System service (optional)"
  info "This will install a systemd service so the app starts on boot and can be managed with systemctl."
  info "You'll be asked for a service name and which user it should run as (non-root recommended)."
  if confirm "Install as a systemd service (run on boot)?" N; then
    info "Pick a simple, lowercase service name. A file will be created in /etc/systemd/system/<name>.service."
    SERVICE_NAME=$(prompt "Service name" "movieframe")
    RUN_AS_USER=$(prompt "Run service as user" "${USER:-pi}")

    LAUNCH_CMD="$(printf '%q' "$PROJECT_ROOT")/launch.sh"

    # Ensure launch.sh is executable
    chmod +x "$PROJECT_ROOT/launch.sh"

    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    info "Writing $SERVICE_FILE (sudo required)"
    sudo bash -c "cat > '$SERVICE_FILE'" <<EOF
[Unit]
Description=E-Paper Movie Frame
After=network.target

[Service]
Type=simple
User=$RUN_AS_USER
WorkingDirectory=$PROJECT_ROOT
Environment=ENVIRONMENT=$ENVIRONMENT
ExecStart=$LAUNCH_CMD
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable "$SERVICE_NAME"
    if confirm "Start service now?" Y; then
      sudo systemctl start "$SERVICE_NAME"
      sudo systemctl --no-pager --full status "$SERVICE_NAME" || true
    fi
    success "Service $SERVICE_NAME installed."
  fi
else
  warn "systemd not detected. Skipping service setup."
fi


# ---------------------------
# Launch option
# ---------------------------
section "Ready to launch"
info "You can launch now to test the web UI. Default port is 8000; browse to http://<your-pi-ip>:8000."
if confirm "Start the app now in the foreground?" N; then
  ./launch.sh || true
else
  info "You can start later by running: ./launch.sh"
  info "From inside the venv, you can also use the console command: 'movieframe'"
fi

success "Installation complete. Enjoy!"
