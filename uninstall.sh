#!/usr/bin/env bash

# Uninstaller for E-Paper Movie Frame
# Stops and removes an optional systemd service, and optionally removes venv/config

set -euo pipefail

has_cmd() { command -v "$1" >/dev/null 2>&1; }

confirm() {
  local prompt="$1"; shift || true
  local default="${1:-N}"
  local suffix="[y/N]"
  [ "$default" = "Y" ] && suffix="[Y/n]"
  read -rp "$prompt $suffix " ans || true
  ans=${ans:-$default}
  case "$ans" in
    Y|y|yes|YES) return 0;;
    *) return 1;;
  esac
}

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo "This will remove the Movie Frame service and local artifacts."

if has_cmd systemctl; then
  read -rp "Service name to remove (or blank to skip): " SERVICE_NAME || true
  if [ -n "${SERVICE_NAME:-}" ]; then
    sudo systemctl stop "$SERVICE_NAME" || true
    sudo systemctl disable "$SERVICE_NAME" || true
    sudo rm -f "/etc/systemd/system/${SERVICE_NAME}.service" || true
    sudo systemctl daemon-reload || true
    echo "Removed service $SERVICE_NAME"
  fi
fi

if confirm "Remove project virtual environment (./venv)?" N; then
  rm -rf "$PROJECT_ROOT/venv"
  echo "Removed ./venv"
fi

if confirm "Remove generated config (.env and config.toml)?" N; then
  rm -f "$PROJECT_ROOT/.env" "$PROJECT_ROOT/config.toml"
  echo "Removed .env and config.toml"
fi

echo "Uninstall complete."
