@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

if not exist "app.py" (
    echo ERROR: app.py not found in this folder.
    pause
    exit /b 1
)

set PYTHON_CMD=

where py >nul 2>nul
if !errorlevel!==0 set PYTHON_CMD=py -3

if "!PYTHON_CMD!"=="" (
    where python >nul 2>nul
    if !errorlevel!==0 set PYTHON_CMD=python
)

if "!PYTHON_CMD!"=="" (
    echo ERROR: Python not found. Install it from python.org and add to PATH.
    pause
    exit /b 1
)

echo Using: !PYTHON_CMD!
echo.

!PYTHON_CMD! -c "import flask" >nul 2>nul
if !errorlevel!==0 goto :flask_ok

echo Installing Flask and requests...
!PYTHON_CMD! -m pip install flask requests
echo.

:flask_ok
echo Starting server at http://127.0.0.1:5000
echo Press Ctrl+C to stop.
echo.

start "" http://127.0.0.1:5000

!PYTHON_CMD! app.py

echo.
echo Server stopped.
pause