@echo off
REM Complete cache cleanup + restart

echo ===================================
echo NPK RC SDM — Full Cache Cleanup
echo ===================================
echo.

REM 1. Kill Streamlit process
echo (1) ปิด Streamlit processes...
taskkill /f /im streamlit.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM 2. Go to project directory
cd /d "%~dp0"

REM 3. Delete .streamlit
echo (2) ลบ .streamlit ในโปรเจกต์...
if exist .streamlit rmdir /s /q .streamlit >nul 2>&1

REM 4. Delete __pycache__ everywhere
echo (3) ลบ __pycache__...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)

REM 5. Delete Streamlit user cache
echo (4) ลบ Streamlit user cache...
if exist "%USERPROFILE%\.streamlit" rmdir /s /q "%USERPROFILE%\.streamlit" >nul 2>&1

REM 6. Delete Streamlit config cache
echo (5) ลบ config cache...
if exist "%APPDATA%\Streamlit" rmdir /s /q "%APPDATA%\Streamlit" >nul 2>&1

echo.
echo ===================================
echo ✓ Cleanup เสร็จ
echo ===================================
echo.
echo ขั้นตอนต่อไป:
echo 1. ปิด browser ทั้งหมด (localhost:8501)
echo 2. รัน run_app.bat
echo.
pause
