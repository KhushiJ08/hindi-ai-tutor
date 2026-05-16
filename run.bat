@echo off
echo ============================================
echo    Prajna - Hindi AI Tutor
echo ============================================

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

:: Check if Ollama is running, start it if not
echo [3/4] Checking Ollama server...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo      Starting Ollama server...
    start /B ollama serve
    timeout /t 5 /nobreak >NUL
) else (
    echo      Ollama is already running.
)

:: Pull the model only if not already cached
echo [4/4] Ensuring model is available...
ollama list 2>NUL | find /I "gemma4:e4b" >NUL
if %ERRORLEVEL% NEQ 0 (
    echo      Pulling model gemma4:e4b (first time setup — this may take a while^)...
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
