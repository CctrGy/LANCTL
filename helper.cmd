@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0fullHelp.py" %*
    exit /b
)

for %%P in (python.exe) do if not "%%~$PATH:P"=="" (
    "%%~$PATH:P" "%~dp0fullHelp.py" %*
    exit /b
)

for /d %%D in ("%LocalAppData%\Programs\Python\Python*") do if exist "%%~fD\python.exe" (
    "%%~fD\python.exe" "%~dp0fullHelp.py" %*
    exit /b
)

py -3 "%~dp0fullHelp.py" %*
if not errorlevel 1 exit /b 0

echo [ERROR] No se ha encontrado una instalación funcional de Python 3.
exit /b 1
