@echo off
title CortexTrack Host Controller
cd /d "%~dp0"

echo Checking required libraries...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo.
    echo [ERROR] Some libraries failed to install.
    echo Try running this manually to see what failed:
    echo     pip install -r requirements.txt
    echo.
    goto :error
)

echo Checking dlib...
python -c "import dlib" 2>nul
if errorlevel 1 (
    echo Installing dlib-bin - prebuilt, no compiler needed
    pip install dlib-bin --quiet
)

echo Checking face_recognition...
python -c "import face_recognition" 2>nul
if errorlevel 1 (
    echo Installing face_recognition without pulling source dlib
    pip install face_recognition --no-deps --quiet
)

python -c "import dlib, face_recognition" 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] face_recognition setup failed.
    echo Run these manually one by one:
    echo     pip install dlib-bin
    echo     pip install numpy Pillow Click face_recognition_models
    echo     pip install face_recognition --no-deps
    echo.
    goto :error
)

echo.
echo Starting secure server stream...
python server.py
pause
exit /b 0

:error
echo.
echo Press any key to close this window...
pause
exit /b 1
