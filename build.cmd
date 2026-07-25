@echo off
setlocal
cd /d "%~dp0"
python -m PyInstaller --noconfirm --clean LANCTL.spec
if errorlevel 1 exit /b %errorlevel%
if exist "data\als" xcopy "data\als\*" "dist\data\als\" /E /I /Y /H >nul
exit /b %errorlevel%
