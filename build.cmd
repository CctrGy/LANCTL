@echo off
setlocal
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean LANCTL.spec
if errorlevel 1 exit /b %errorlevel%
exit /b %errorlevel%
