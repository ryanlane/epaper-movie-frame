#!/bin/bash

# === USER CONFIGURATION START ===
# Update these paths and values as needed

PROJECT_DIR="/home/pi/myproject"           # Full path to your project directory
SERVICE_NAME="movieplayer"                 # Name for the systemd service (no spaces)
PYTHON_BIN="/usr/bin/python3"              # Path to the Python interpreter
USER_NAME="pi"                             # The user who should run the service

# === USER CONFIGURATION END ===

LAUNCH_SCRIPT="$PROJECT_DIR/launch.sh"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "🔧 Step 1: Creating launch script at $LAUNCH_SCRIPT"

# Create a simple shell script to launch your Python app
cat > "$LAUNCH_SCRIPT" <<EOF
#!/bin/bash
# Launch script for the Movie Frame Player

# Change to the project directory
cd "$PROJECT_DIR"

# Run the main Python script with the --auto flag
$PYTHON_BIN movieplayer.py --auto
EOF

# Make sure the launch script is executable
chmod +x "$LAUNCH_SCRIPT"
echo "✅ launch.sh created and marked executable"

echo "🔧 Step 2: Creating systemd service file at $SERVICE_FILE"

# Create the systemd service file that tells Linux how to manage your script
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Movie Frame Player Service
After=network.target

[Service]
# Path to the launch script created above
ExecStart=$LAUNCH_SCRIPT

# Where the service should run from
WorkingDirectory=$PROJECT_DIR

# Always restart if the script fails or crashes
Restart=always

# Which user should run the service
User=$USER_NAME

# Optional: set environment variables here
Environment=ENVIRONMENT=production

# Log output to the system journal
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd service file created"

echo "🔄 Step 3: Reloading systemd daemon to pick up the new service"
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "🚀 Step 4: Enabling and starting the $SERVICE_NAME service"
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

echo "📋 Step 5: Showing the status of the new service"
sudo systemctl status "$SERVICE_NAME" --no-pager

echo "✅ Setup complete! Your script should now be running as a service."
