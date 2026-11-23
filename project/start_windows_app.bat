@echo off
setlocal
cd /d "%~dp0"
title PancRISK+ Care launcher

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10 - 3.12 from python.org and tick "Add Python to PATH", then run this again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo First run: setting things up. This takes a few minutes, please wait...
  python -m venv .venv
  if errorlevel 1 goto fail
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  if errorlevel 1 goto fail
  ".venv\Scripts\python.exe" -m pip install -r requirements-app.txt
  if errorlevel 1 goto fail
)

if not exist "models\model.joblib" (
  echo Training the model...
  ".venv\Scripts\python.exe" src\train_final.py
  if errorlevel 1 goto fail
)

echo Starting the app...
start "PancRISK+ server (close this window to stop the app)" /min ".venv\Scripts\python.exe" -m uvicorn app.server:app --port 8000
timeout /t 6 /nobreak >nul
start "" msedge --app=http://localhost:8000
echo.
echo The app is open in its own window. To stop it, close the minimized "PancRISK+ server" window.
echo If the app window did not open, go to http://localhost:8000 in any browser.
pause
exit /b 0

:fail
echo.
echo Something went wrong. Please copy the messages above and send them to whoever is helping you.
pause
exit /b 1
