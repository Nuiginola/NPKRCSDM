@echo off
REM ============================================================================
REM   NPK RC SDM - Run App
REM
REM   2026-07-12 fix #3: hide the terminal window + start faster.
REM     * Self-hide: when double-clicked directly (no argument), this script
REM       re-launches itself through run_hidden.vbs with window style 0, so no
REM       black console window stays on screen. The real work then runs under
REM       the "__run__" marker in that hidden window.
REM     * The program is launched with pythonw.exe (no console) in hidden mode,
REM       and desktop_app.py starts the Streamlit child with CREATE_NO_WINDOW,
REM       so nothing pops up a console at any point.
REM     * All output (setup, pip, python errors, Thai text from the app) is
REM       redirected to run_log.txt in this folder for debugging.
REM
REM   NOTE (lesson learned): never put Thai / multi-byte text on lines that
REM   cmd.exe actually executes (echo/if/pause/set). Some Windows builds mangle
REM   it and try to run fragments as commands. Keep executed lines ASCII only;
REM   Thai lives only in REM comments and in the run_log.txt content.
REM
REM   Modes:
REM     (double-click)         -> re-launch hidden via run_hidden.vbs, then exit
REM     run_app.bat __run__    -> real run, hidden, no pause (used by the .vbs)
REM     run_app.bat debug      -> real run WITH console + pause (for diagnosis)
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

set MODE=%~1
if /I "%MODE%"=="__run__" goto :work
if /I "%MODE%"=="debug" goto :work

REM ---- default: launched by double-click. Re-run hidden and quit. ----
start "" wscript.exe "%~dp0run_hidden.vbs"
exit /b

:work
REM ---------------------------------------------------------------------------
REM   Self-heal: kill orphaned instances of THIS app left over from a previous
REM   run that did not exit cleanly, BEFORE doing anything else. Such orphans
REM   (pythonw.exe / python.exe running desktop_app.py or the Streamlit server)
REM   hold run_log.txt and the server port locked, which is what makes the app
REM   "open the first time but not the next times". We kill them here so every
REM   launch starts clean. This targets ONLY processes whose command line
REM   references THIS app (desktop_app.py or the streamlit server) -- unrelated
REM   python processes on the machine are left completely untouched.
REM ---------------------------------------------------------------------------
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -like '*desktop_app.py*' -or $_.CommandLine -like '*streamlit*run*') } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }" >nul 2>&1

set LOGFILE=%~dp0run_log.txt
echo ============================================== > "%LOGFILE%"
echo NPK RC SDM run log - %DATE% %TIME% >> "%LOGFILE%"
echo ============================================== >> "%LOGFILE%"

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] .venv\Scripts\activate.bat not found >> "%LOGFILE%"
    if /I "%MODE%"=="debug" (
        echo [ERROR] .venv not found in this folder. See run_log.txt.
        pause
    )
    exit /b 1
)

call .venv\Scripts\activate.bat >> "%LOGFILE%" 2>&1

python -c "import webview" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
    echo [SETUP] pywebview not found - installing automatically... >> "%LOGFILE%"
    python -m pip install --upgrade pywebview >> "%LOGFILE%" 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to install pywebview >> "%LOGFILE%"
        if /I "%MODE%"=="debug" (
            echo [ERROR] Failed to install pywebview. See run_log.txt.
            pause
        )
        exit /b 1
    )
)

REM Hidden run uses pythonw.exe (no console); debug run uses python.exe.
set PYRUN=pythonw
if /I "%MODE%"=="debug" set PYRUN=python

echo [RUN] Opening NPK RC SDM window... >> "%LOGFILE%"
%PYRUN% desktop_app.py >> "%LOGFILE%" 2>&1
set APP_EXIT=%errorlevel%

if not "%APP_EXIT%"=="0" (
    echo [ERROR] The program exited with code %APP_EXIT% >> "%LOGFILE%"
    if /I "%MODE%"=="debug" (
        echo [ERROR] Exit code %APP_EXIT%. See run_log.txt for the real error.
        pause
    )
)

endlocal
