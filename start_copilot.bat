@echo off
title Ableton AI Copilot
echo Starting Ableton AI Copilot GUI...
echo Close this window to exit the application.
echo.

REM Start GUI in new process
start "Ableton AI Copilot" /B python gui_copilot.py

echo GUI started in background.
echo You can close this window now.
pause
