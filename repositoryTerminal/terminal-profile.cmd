@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0terminal-profile.ps1" %*
exit /b %errorlevel%
