@echo off
REM ลบ Streamlit cache ทั้งหมด

echo ===== กำลังลบ cache =====
echo.

REM 1. ลบ .streamlit ในโปรเจกต์
echo (1) ลบ .streamlit ในโปรเจกต์...
cd /d "%~dp0"
if exist .streamlit rmdir /s /q .streamlit
if exist .streamlit echo [ลบไม่ได้] ปิด Streamlit ให้หมด

REM 2. ลบ __pycache__ ทั้งหมด
echo (2) ลบ __pycache__ ในโปรเจกต์...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" >nul 2>&1
)

REM 3. ลบ Streamlit user cache
echo (3) ลบ Streamlit user cache (%USERPROFILE%\.streamlit)...
if exist "%USERPROFILE%\.streamlit" rmdir /s /q "%USERPROFILE%\.streamlit"

REM 4. ลบ Streamlit config cache
echo (4) ลบ config cache (%APPDATA%\Streamlit)...
if exist "%APPDATA%\Streamlit" rmdir /s /q "%APPDATA%\Streamlit"

echo.
echo ===== สำเร็จ =====
echo.
echo ✓ ลบ cache เสร็จแล้ว
echo ✓ ปิด browser ทั้งหมด (localhost:8501)
echo ✓ รัน run_app.bat ใหม่
echo.
pause
