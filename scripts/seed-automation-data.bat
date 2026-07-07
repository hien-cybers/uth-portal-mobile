@echo off
setlocal

cd /d "%~dp0\.."

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=python"
)

"%PYTHON%" "scripts\seed-automation-data.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to seed automation data.
    exit /b 1
)

echo.
echo [OK] Automation data is ready in uth_portal_final.db
endlocal
