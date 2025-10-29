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

# Detect package manager
PKG_MGR=""
if has_cmd apt; then PKG_MGR="apt"; fi

# Ask for system packages
INSTALL_SYS_DEPS=false
if [ -n "$PKG_MGR" ]; then
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
    libgl1 "$MATH_PKG" libopenjp2-7 "$TIFF_PKG"
  success "System dependencies installed."
fi


# ---------------------------
# Virtual environment
# ---------------------------
section "Python virtual environment"
DEFAULT_VENV="$PROJECT_ROOT/venv"
VENV_PATH=$(prompt "Where should the virtual environment live?" "$DEFAULT_VENV")

if [ ! -d "$VENV_PATH" ]; then
  info "Creating venv at $VENV_PATH"
  python3 -m venv "$VENV_PATH"
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
  error "Aborting due to pip install failure. After installing system packages, re-run ./install.sh or run 'pip install -e .' inside your venv."
  exit 1
fi

success "Project installed in editable mode and dependencies installed."


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
  if confirm "Install as a systemd service (run on boot)?" N; then
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
if confirm "Start the app now in the foreground?" N; then
  ./launch.sh || true
else
  info "You can start later by running: ./launch.sh"
fi

success "Installation complete. Enjoy!"
