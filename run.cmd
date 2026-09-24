@echo off
setlocal EnableExtensions EnableDelayedExpansion
set "LANCTL_PYTHON=python"
for %%P in ("%~dp0.venv\Scripts\python.exe" "%~dp0.venv311\Scripts\python.exe") do (
    if "!LANCTL_PYTHON!"=="python" if exist "%%~P" (
        "%%~P" -c "import sys" >nul 2>nul && set "LANCTL_PYTHON=%%~P"
    )
)
"%LANCTL_PYTHON%" "%~dp0lanctl.py" %*
exit /b %errorlevel%
