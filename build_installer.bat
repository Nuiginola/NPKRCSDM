@echo off
REM ============================================================================
REM   NPK RC SDM - NSIS Installer Builder (DESKTOP-WINDOW edition)
REM   Builds a Windows installer (.exe) bundling Python + app + packages
REM   Runs as a desktop window (pywebview / desktop_app.py), not a browser
REM
REM   Usage: right-click this file -> Run as administrator
REM
REM   NOTE(lesson#84): NO Thai on executed lines (echo/if/set) - UTF-8 no-BOM
REM   makes cmd mis-parse and the window "flashes then closes" immediately.
REM   => every echoed/executed line in this file is ASCII (English) only.
REM      (all comments are ASCII too, to remove any encoding risk)
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

cls
echo ============================================================================
echo   NPK RC SDM - Installer Builder (Desktop-Window edition)
echo ============================================================================
echo.

REM --- check Administrator privileges ---
net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Please run as Administrator ^(right-click -^> Run as administrator^)
    echo.
    pause
    exit /b 1
)
echo [OK] Administrator privileges confirmed
echo.

REM --- create build directory ---
set BUILD_DIR=%CD%\installer_build
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%\app"
mkdir "%BUILD_DIR%\nsis"
mkdir "%BUILD_DIR%\output"

echo [STEP 1] Copying application files (incl. desktop_app.py + .streamlit)...  [%TIME%]
xcopy /S /Y common "%BUILD_DIR%\app\common\" >nul
xcopy /S /Y app_pages "%BUILD_DIR%\app\app_pages\" >nul
xcopy /S /Y modules "%BUILD_DIR%\app\modules\" >nul
xcopy /S /Y pages "%BUILD_DIR%\app\pages\" >nul
xcopy /S /Y data "%BUILD_DIR%\app\data\" >nul
xcopy /S /Y ".streamlit" "%BUILD_DIR%\app\.streamlit\" >nul
copy /Y app.py "%BUILD_DIR%\app\" >nul
copy /Y desktop_app.py "%BUILD_DIR%\app\" >nul
copy /Y requirements.txt "%BUILD_DIR%\app\" >nul
copy /Y stair_detail_template.png "%BUILD_DIR%\app\" 2>nul
copy /Y stair_rebar_template1.png "%BUILD_DIR%\app\" 2>nul
REM pile-cap + spread-footing SECTION templates (loaded from app root by
REM common\pile_cap_template.py / footing_section_template.py). Without these the
REM installed app cannot find them and falls back to the plain geometry drawing.
copy /Y "1 pile.png" "%BUILD_DIR%\app\" 2>nul
copy /Y "2 pile.png" "%BUILD_DIR%\app\" 2>nul
copy /Y "3 pile.png" "%BUILD_DIR%\app\" 2>nul
copy /Y "4 pile.png" "%BUILD_DIR%\app\" 2>nul
copy /Y "Footing F1.png" "%BUILD_DIR%\app\" 2>nul
echo   [OK] files copied
echo.

echo [STEP 2] Downloading Embedded Python 3.11 (~30MB)...  [%TIME%]
set PYDIR=%BUILD_DIR%\app\python_embedded
mkdir "%PYDIR%"
REM 3.11.9 = last 3.11 release WITH a Windows embeddable zip (3.11.10+ are source-only)
set PYTHON_ZIP=%BUILD_DIR%\python-3.11.9-embed-amd64.zip
set PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip
echo   downloading (progress bar below)...
curl -L -o "%PYTHON_ZIP%" "%PYTHON_URL%"
if not exist "%PYTHON_ZIP%" powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_ZIP%' } catch {}"
if not exist "%PYTHON_ZIP%" (
    echo   [ERROR] Python download failed - check internet and retry
    pause
    exit /b 1
)
REM verify it is a real zip (~10MB), not a tiny error/redirect page
for %%A in ("%PYTHON_ZIP%") do set ZIPSIZE=%%~zA
if !ZIPSIZE! LSS 1000000 (
    echo   [ERROR] downloaded file too small ^(!ZIPSIZE! bytes^) - wrong URL or error page
    echo           delete installer_build and retry
    pause
    exit /b 1
)
echo   [OK] downloaded ^(!ZIPSIZE! bytes^)
echo.

echo [STEP 3] Extracting Python into app\python_embedded...  [%TIME%]
powershell -Command "Expand-Archive -Path '%PYTHON_ZIP%' -DestinationPath '%PYDIR%' -Force"
if not exist "%PYDIR%\python.exe" (
    echo   [ERROR] Python extract failed
    pause
    exit /b 1
)
echo   [OK] extracted
echo.

echo [STEP 4] Enabling site-packages + installing pip and packages...  [%TIME%]
REM (4.1) rewrite ._pth to enable site-packages (embedded python disables it by default)
> "%PYDIR%\python311._pth" echo python311.zip
>> "%PYDIR%\python311._pth" echo .
>> "%PYDIR%\python311._pth" echo Lib\site-packages
>> "%PYDIR%\python311._pth" echo import site
REM (4.2) bootstrap pip
echo   [4.1] downloading get-pip.py...
curl -L -o "%PYDIR%\get-pip.py" https://bootstrap.pypa.io/get-pip.py
echo   [4.2] installing pip...
"%PYDIR%\python.exe" "%PYDIR%\get-pip.py" --no-warn-script-location
echo.
echo   [4.3] installing packages (streamlit, pywebview, matplotlib, pandas, numpy, pillow)
echo   *** THIS IS THE LONGEST STEP (~200MB, several minutes) ***
echo   *** pip will print Collecting / Downloading / Installing for each package ***
echo   *** as long as lines keep moving, it is working - do NOT close ***
echo.
"%PYDIR%\python.exe" -m pip install --no-warn-script-location --progress-bar on -r "%BUILD_DIR%\app\requirements.txt"
if errorlevel 1 (
    echo   [ERROR] package install failed
    pause
    exit /b 1
)
REM (4.4) verify imports actually work (catch missing packages at build time)
echo   [4.4] verifying imports...
"%PYDIR%\python.exe" -c "import streamlit, webview, matplotlib, pandas, numpy, PIL; print('   IMPORTS OK')" || (
    echo   [ERROR] import check failed - packages incomplete
    pause
    exit /b 1
)
echo   [OK] packages installed
echo.

echo [STEP 5] Creating launcher scripts (desktop window + self-heal)...  [%TIME%]
cd "%BUILD_DIR%\app"
REM launcher.bat -- self-heal (kill stale) then open desktop_app.py via pythonw (no console)
(
echo @echo off
echo cd /d "%%~dp0"
echo powershell -NoProfile -Command "Get-CimInstance Win32_Process ^| Where-Object { $_.CommandLine -and ($_.CommandLine -like '*desktop_app.py*' -or $_.CommandLine -like '*streamlit*run*') } ^| ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {} }" ^>nul 2^>^&1
echo "%%~dp0python_embedded\pythonw.exe" "%%~dp0desktop_app.py"
) > launcher.bat
REM launcher.vbs -- run launcher.bat hidden (no window)
(
echo Set objShell = CreateObject("WScript.Shell"^)
echo strPath = CreateObject("Scripting.FileSystemObject"^).GetParentFolderName(WScript.ScriptFullName^)
echo objShell.Run """" ^& strPath ^& "\launcher.bat""", 0, False
) > launcher.vbs
cd "%BUILD_DIR%"
echo   [OK] launchers created
echo.

echo [STEP 6] Checking / downloading NSIS...  [%TIME%]
set NSIS_URL=https://sourceforge.net/projects/nsis/files/NSIS%%203/3.10/nsis-3.10-setup.exe/download
set NSIS_INSTALLER=%BUILD_DIR%\nsis_setup.exe
if not exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    if not exist "%NSIS_INSTALLER%" (
        echo   downloading NSIS ~2MB...
        curl -L -o "%NSIS_INSTALLER%" "%NSIS_URL%"
    )
    if exist "%NSIS_INSTALLER%" (
        echo   installing NSIS...
        "%NSIS_INSTALLER%" /S /D=C:\Program Files ^(x86^)\NSIS >nul 2>&1
    )
)
if not exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo   [ERROR] NSIS not found. Install from https://nsis.sourceforge.io/ then rerun.
    pause
    exit /b 1
)
echo   [OK] NSIS ready
echo.

echo [STEP 7] Writing NSIS installer script...  [%TIME%]
cd "%BUILD_DIR%\nsis"
REM disable delayed expansion so NSIS "!" prefixes (!include/!define/!insertmacro) survive echo
setlocal disabledelayedexpansion
(
echo ; NPK RC SDM Installer
echo !include "MUI2.nsh"
echo !define PRODUCT_NAME "NPK RC SDM"
echo !define PRODUCT_VERSION "1.3.2"
echo !define INSTALL_DIR "$PROGRAMFILES64\NPK_RC_SDM"
echo.
echo RequestExecutionLevel admin
echo Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
echo OutFile "..\output\NPK_RC_SDM_Setup.exe"
echo InstallDir "${INSTALL_DIR}"
echo Icon "..\app\data\app_icon.ico"
echo UninstallIcon "..\app\data\app_icon.ico"
echo.
echo !insertmacro MUI_PAGE_DIRECTORY
echo !insertmacro MUI_PAGE_INSTFILES
echo !insertmacro MUI_LANGUAGE "English"
echo.
echo Section "NPK RC SDM"
echo   SetOutPath "$INSTDIR"
echo   File /r "..\app\*.*"
echo   CreateDirectory "$SMPROGRAMS\NPK RC SDM"
echo   CreateShortCut "$SMPROGRAMS\NPK RC SDM\NPK RC SDM.lnk" "wscript.exe" '"$INSTDIR\launcher.vbs"' "$INSTDIR\data\app_icon.ico" 0
echo   CreateShortCut "$DESKTOP\NPK RC SDM.lnk" "wscript.exe" '"$INSTDIR\launcher.vbs"' "$INSTDIR\data\app_icon.ico" 0
echo   WriteUninstaller "$INSTDIR\Uninstall.exe"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "DisplayName" "${PRODUCT_NAME}"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "DisplayVersion" "${PRODUCT_VERSION}"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "Publisher" "Nopphakhun Duangsri"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "DisplayIcon" "$INSTDIR\data\app_icon.ico"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "UninstallString" "$INSTDIR\Uninstall.exe"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "InstallLocation" "$INSTDIR"
echo   WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "NoModify" 1
echo   WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM" "NoRepair" 1
echo SectionEnd
echo.
echo Section "Uninstall"
echo   RMDir /r "$INSTDIR"
echo   Delete "$DESKTOP\NPK RC SDM.lnk"
echo   RMDir /r "$SMPROGRAMS\NPK RC SDM"
echo   DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\NPK_RC_SDM"
echo SectionEnd
) > NPK_RC_SDM.nsi
endlocal
echo   [OK] NSIS script written
echo.

echo [STEP 8] Building installer .exe (packing files, please wait)...  [%TIME%]
"C:\Program Files (x86)\NSIS\makensis.exe" /V2 NPK_RC_SDM.nsi
if errorlevel 1 (
    echo   [ERROR] NSIS build failed
    pause
    exit /b 1
)
echo   [OK] Setup.exe built
echo.

echo [STEP 9] Splitting installer into 3 parts...  [%TIME%]
cd "%BUILD_DIR%\output"
if not exist "NPK_RC_SDM_Setup.exe" (
    echo   [ERROR] NPK_RC_SDM_Setup.exe not found
    pause
    exit /b 1
)
powershell -Command "$file='NPK_RC_SDM_Setup.exe'; $size=(Get-Item $file).Length; $ps=31457280; $s=[System.IO.File]::OpenRead($file); $buf=New-Object byte[] $ps; for($i=0;$i -lt [math]::Ceiling($size/$ps);$i++){ $n=$s.Read($buf,0,$ps); if($i -lt 2){$o='NPK_RC_SDM_Setup_split.z'+([string]($i+1)).PadLeft(2,'0')}else{$o='NPK_RC_SDM_Setup_split.zip'}; [System.IO.File]::WriteAllBytes($o,$buf[0..($n-1)]); Write-Host ('   OK '+$o+' ('+$n+' bytes)'); }; $s.Close()"
echo   [OK] split done
echo.

echo ============================================================================
echo   INSTALLER BUILD COMPLETE!   [%TIME%]
echo ============================================================================
echo   Output: %BUILD_DIR%\output\
echo     - NPK_RC_SDM_Setup.exe        (full installer)
echo     - NPK_RC_SDM_Setup_split.z01  (30MB)
echo     - NPK_RC_SDM_Setup_split.z02  (30MB)
echo     - NPK_RC_SDM_Setup_split.zip  (remaining)
echo ============================================================================
echo.
pause
