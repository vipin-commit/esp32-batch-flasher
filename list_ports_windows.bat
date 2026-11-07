@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 flasher.py --list-ports
) else (
  python flasher.py --list-ports
)
pause
