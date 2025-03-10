#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3.12 is installed
if ! command_exists python3.12; then
    echo "Python 3.12 not found. Installing..."
    sudo apt update && \
    sudo apt install -y software-properties-common && \
    sudo add-apt-repository ppa:deadsnakes/ppa && \
    sudo apt update && \
    sudo apt install -y python3.12 python3.12-venv
else
    echo "Python 3.12 is already installed"
fi

# Install pipx if not present
if ! command_exists pipx; then
    echo "Installing pipx..."
    sudo apt update && sudo apt install -y pipx
    pipx ensurepath
    # Source the updated PATH
    source ~/.bashrc
else
    echo "pipx is already installed"
fi

# Check if dipdup CLI is installed
if ! command_exists dipdup; then
    echo "DipDup not found. Installing..."
    pipx install dipdup
else
    echo "DipDup is already installed"
fi

# Check if pdm is installed
if ! command_exists pdm; then
    echo "PDM not found. Installing..."
    pipx install pdm
else
    echo "PDM is already installed"
fi

# Initialize PDM project and install dipdup if not already set up
if [ ! -f "pyproject.toml" ]; then
    echo "Initializing PDM project..."
    pdm init --python 3.12 --lib <<EOF
y
EOF
    
    echo "Creating PDM virtual environment..."
    pdm venv create
    
    echo "Installing dipdup..."
    pdm add "dipdup>=8,<9" --venv
    
    echo "Activating virtual environment..."
    eval "$(pdm venv activate)"
else
    echo "PDM project already initialized"
fi

# Check if .env exists, if not create it from example
if [ ! -f defi_space_indexer/.env ]; then
    cp defi_space_indexer/env.example defi_space_indexer/.env
    echo "Created .env file from template"
fi

# Make the script executable
chmod +x scripts/setup.sh

echo "Setup completed successfully!"