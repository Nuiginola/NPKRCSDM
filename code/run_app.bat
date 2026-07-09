@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
set PYTHONDONTWRITEBYTECODE=1
echo Clearing old cached files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
echo Checking and installing any missing tools...
pip install -r requirements.txt --quiet --disable-pip-version-check
echo Starting NPK RC SDM...
start /b streamlit run app.py --server.headless true
timeout /t 5 /nobreak > nul
echo Opening home page...
start "" http://localhost:8501
echo.
echo NPK RC SDM is running. Close this window to stop the program.
pause
