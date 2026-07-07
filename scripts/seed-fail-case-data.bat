@echo off
setlocal
cd /d "%~dp0\.."
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "scripts\seed-fail-case-data.py" %*
) else (
  python "scripts\seed-fail-case-data.py" %*
)
