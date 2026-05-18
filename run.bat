@echo off
echo ============================================
echo    Prajna - Hindi AI Tutor
echo ============================================

set PYTHONIOENCODING=utf-8

:: Kill phantom processes from previous runs
echo [0/4] Cleaning up old processes...
taskkill /F /IM python.exe >NUL 2>&1
taskkill /F /IM python3.13.exe >NUL 2>&1
taskkill /F /IM ollama.exe >NUL 2>&1
timeout /t 2 /nobreak >NUL
echo      Done.

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo [1/4] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [!] No virtual environment found. Using system Python.
)

:: Install dependencies if needed
echo [2/4] Checking dependencies...
pip install -r requirements.txt --quiet 2>NUL

:: Start Ollama fresh
echo [3/4] Starting Ollama server...
start /B ollama serve
timeout /t 5 /nobreak >NUL

:: Pull the model only if not already cached
echo [4/4] Ensuring model is available...
ollama list 2>NUL | find /I "gemma4:e4b" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo      Pulling model gemma4:e4b (first time setup ? this may take a while^)...
    ollama pull gemma4:e4b
) else (
    echo      Model gemma4:e4b already available.
)

:: Launch the Prajna server
echo ============================================
echo    Prajna is running!
echo    Open http://localhost:8080
echo ============================================
python server.py

pause
