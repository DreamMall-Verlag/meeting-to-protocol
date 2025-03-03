#!/bin/bash

echo "Setting up Meeting-to-Protocol environment..."

# Create directories if they don't exist
mkdir -p uploads
mkdir -p texts

# Create and activate virtual environment (if needed)
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Ensure pip is up to date
pip install --upgrade pip

# Uninstall current numpy and any existing whisper packages
echo "Removing current NumPy and Whisper installations..."
pip uninstall -y numpy whisper openai-whisper

# Install compatible NumPy version first
echo "Installing compatible NumPy version..."
pip install 'numpy<2.0'

# Install the OpenAI Whisper package specifically
echo "Installing OpenAI Whisper package..."
pip install openai-whisper

# Install the rest of the dependencies
echo "Installing remaining dependencies..."
pip install -r requirements.txt

# Verify Whisper installation
echo "Verifying Whisper installation..."
python -c "import whisper; print(f'Whisper version: {getattr(whisper, \"__version__\", \"Unknown\")}'); print(f'Has load_model: {hasattr(whisper, \"load_model\")}')"

echo "Setup complete! Activate the virtual environment with:"
echo "source venv/bin/activate"
