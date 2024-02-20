#!/bin/bash

# Update package information
sudo apt-get update

# Install dependencies
sudo apt-get install -y python3-opencv

# Install additional dependencies using pip
pip install inky[rpi,example-depends] python-dotenv numpy Pillow fastapi "uvicorn[standard]" python-multipart sqlalchemy jinja2 
