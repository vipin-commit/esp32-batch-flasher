@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install -r requirements.txt
  goto :done
)
where python >nul 2>nul
if %errorlevel%==0 (
  python -m pip install -r requirements.txt
  goto :done
)
echo Python 3 is required. Install Python 3.10+ and add it to PATH.
pause
exit /b 1
:done
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
echo Dependencies installed.
pause
