' ============================================================================
'  NPK RC SDM - Silent launcher (VBScript)
'
'  Double-click THIS file to start the program with NO console window at all.
'  It launches run_app.bat completely hidden (window style 0). All setup and
'  program output still goes to run_log.txt in the same folder for debugging.
'
'  Fixed 2026-07-12: previous version required command-line arguments and just
'  showed a popup when double-clicked. Now it self-locates its own folder and
'  runs run_app.bat directly, so a plain double-click works and stays hidden.
'  Paths are fully quoted to survive spaces in the folder path
'  (e.g. "C:\Users\NUI\OneDrive\NPK RC SDM\code").
' ============================================================================
Option Explicit
Dim shell, fso, scriptDir, batPath
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = scriptDir & "\run_app.bat"

' run from the script's own folder so relative paths inside the .bat resolve
shell.CurrentDirectory = scriptDir

' Run run_app.bat with the __run__ marker so it skips its own self-hide relaunch.
' 0 = hidden window, False = do not wait (this .vbs exits immediately; the
' hidden cmd keeps running until the program window is closed).
shell.Run """" & batPath & """ __run__", 0, False
