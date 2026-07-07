# Cortex Track (SentinalOR) — AI Surgical Asset Verification System

Real-time computer vision system that monitors surgical trays and verifies operator identity using YOLOv8 object detection and face recognition, with automated breach alerts and a live monitoring dashboard.

## Setup
1. Add your own `config.json` (see `config.example.json` template) with your email and API key.
2. `python server.py` to start the backend.
3. `python camera_tracker.py` to start the camera monitor.
4. Open `http://127.0.0.1:8000` in your browser.
