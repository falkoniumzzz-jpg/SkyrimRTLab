@echo off
cd /d "%~dp0"
RTLabProbe.exe > Probe.log 2>&1
set RTLAB_EXIT=%ERRORLEVEL%
type Probe.log
echo Exit code: %RTLAB_EXIT%
pause
exit /b %RTLAB_EXIT%
