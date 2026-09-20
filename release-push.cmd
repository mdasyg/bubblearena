@echo off
rem release-push.cmd - Windows CMD wrapper for release-push.ps1
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0release-push.ps1" %*
exit /b %ERRORLEVEL%
