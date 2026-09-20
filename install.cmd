@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0repositoryTerminal\repository.ps1" %*
exit /b %errorlevel%
