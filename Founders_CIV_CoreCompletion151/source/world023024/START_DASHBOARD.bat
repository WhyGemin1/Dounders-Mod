@echo off
cd /d "%~dp0"
echo Starting Founders-CIV Observatory...
py launch.py --browser
if errorlevel 1 (
 echo.
 echo If the Python launcher is unavailable, run: python launch.py --browser
 pause
)
