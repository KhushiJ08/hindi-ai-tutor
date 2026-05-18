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

:: ── Automatic hardware detection and model setup ──
echo [4/4] Detecting hardware and setting up model...
python setup_model.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [FATAL] Hardware check failed. Prajna cannot start.
    echo         Please read the error message above.
    pause
    exit /b 1
)

:: Read the model choice written by setup_model.py
if exist ".prajna_model" (
    set /p PRAJNA_MODEL=<.prajna_model
    echo Using model: %PRAJNA_MODEL%
) else (
    set PRAJNA_MODEL=gemma4:e2b
    echo [!] .prajna_model not found. Defaulting to gemma4:e2b
)

:: Launch the Prajna server
echo ============================================
echo    Prajna is running!
echo    Open http://localhost:8080
echo ============================================
python server.py

pause
