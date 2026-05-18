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

# ── Automatic hardware detection & model setup ──
python3 setup_model.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[FATAL] Hardware check failed. Prajna cannot start."
    echo "        Please read the error message above."
    exit 1
fi

# Read the model choice written by setup_model.py
if [ -f ".prajna_model" ]; then
    export PRAJNA_MODEL=$(cat .prajna_model)
    echo "Using model: $PRAJNA_MODEL"
else
    export PRAJNA_MODEL="gemma4:e2b"
    echo "[!] .prajna_model not found. Defaulting to $PRAJNA_MODEL"
fi

# Launch with Gunicorn (production WSGI server — no dev-server warning)
echo "============================================"
echo "   Prajna is running!"
echo "   Open http://localhost:8080"
echo "============================================"

gunicorn --workers 2 --bind 0.0.0.0:8080 --timeout 120 server:app
