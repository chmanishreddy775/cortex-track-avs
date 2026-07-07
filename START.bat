@echo off
title CortexTrack Host Controller
cd /d "%~dp0"
echo Starting secure server stream...
python server.py
pause