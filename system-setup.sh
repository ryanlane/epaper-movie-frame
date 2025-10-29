#!/bin/bash

set -e

echo "🔧 Updating APT and installing system-level dependencies..."
sudo apt update

# Detect best-available math/TIFF libs across distros
# Ensure apt-cache show returns a real stanza for this package
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

sudo apt install -y \
	python3-venv python3-pip python3-dev \
	libgl1 "$MATH_PKG" libopenjp2-7 "$TIFF_PKG"

echo "✅ System dependencies installed."
