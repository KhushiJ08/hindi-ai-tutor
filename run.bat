@echo off
echo Installing dependencies...
pip install streamlit requests >nul 2>&1

echo Clearing port 11434...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :11434') do taskkill /F /PID %%a >nul 2>&1

echo Starting Ollama server...
start "" /min cmd /c "ollama serve >nul 2>&1"
timeout /t 5 /nobreak >nul

echo Starting Streamlit app...
python -m streamlit run app.py

pause
