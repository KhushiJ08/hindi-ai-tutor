#!/bin/bash
echo "============================================"
echo "   Prajna - Hindi AI Tutor"
echo "============================================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[!] No virtual environment found. Using system Python."
fi

# Install dependencies if needed
echo "Checking dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null

# Ensure Ollama is running in the background
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama server..."
    ollama serve &
    sleep 5
fi

# Pull the model if not already downloaded
ollama pull gemma4:e4b

# Launch the Prajna server
echo "============================================"
echo "   Prajna is running!"
echo "   Open http://localhost:8080/login.html"
echo "============================================"

python3 server.py
