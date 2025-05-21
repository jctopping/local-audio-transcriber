#!/bin/bash

echo "Creating virtual environment..."
python3 -m venv diarize_env
source diarize_env/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Copying .env.sample to .env (edit your token inside)..."
cp .env.sample .env

echo "Setup complete. Edit .env to include your Hugging Face token."