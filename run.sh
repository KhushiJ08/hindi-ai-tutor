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

# Pull the model only if not already cached
if ! ollama list 2>/dev/null | grep -q "gemma4:e4b"; then
    echo "Pulling model gemma4:e4b (first time setup — this may take a while)..."
    ollama pull gemma4:e4b
else
    echo "Model gemma4:e4b already available."
fi

# Launch with Gunicorn (production WSGI server — no dev-server warning)
echo "============================================"
echo "   Prajna is running!"
echo "   Open http://localhost:8080"
echo "============================================"

gunicorn --workers 2 --bind 0.0.0.0:8080 --timeout 120 server:app
