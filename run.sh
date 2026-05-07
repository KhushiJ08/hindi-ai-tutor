#!/bin/bash
# Activate the virtual environment
source venv/bin/activate

# Ensure Ollama is running in the background
if ! pgrep -x "ollama" > /dev/null
then
    ollama serve &
    sleep 5
fi

# Run the app
streamlit run app.py