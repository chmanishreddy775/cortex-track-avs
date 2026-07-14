# Cortex Track (SentinelOR) — AI Surgical Asset Verification System

Real-time computer vision system that monitors surgical trays and verifies operating room staff identity, using YOLOv8 object detection and face recognition, with automated breach alerts and a live monitoring dashboard.

---

## The Problem

Operating rooms face two persistent, high-stakes risks:

- **Retained surgical instruments** — instruments miscounted or left behind during a procedure can cause serious patient harm and expose hospitals to malpractice liability.
- **Unverified OR access** — without automated checks, unauthorized personnel can be present in a sterile, high-risk environment without anyone noticing in real time.

Manual instrument counts and staff checks are slow, error-prone, and rely entirely on human vigilance during high-pressure procedures.

---

## The Solution

Cortex Track uses two cameras running in parallel:

1. **Instrument Detection (YOLOv8)** — continuously scans the surgical tray and identifies which instruments are present, flagging if any go missing mid-procedure.
2. **Face Verification (dlib + face_recognition)** — matches OR staff against enrolled identities in real time, flagging any unrecognized person in the room.

Both feeds are processed locally (no cloud dependency), logged to a database, and displayed on a live web dashboard — with automated alerts the moment something looks wrong.

---

## Features

- Real-time surgical instrument detection and tracking
- Face-based staff identity verification with configurable match strictness
- Live web dashboard showing camera feed, detections, and alerts
- Automated breach/anomaly alerting
- Fully local, offline-capable — no cloud dependency required
- Persistent logging of all detections and access events

---

## Tech Stack

| Layer | Technology |
|---|---|
| Object Detection | YOLOv8 (Ultralytics) |
| Face Recognition | dlib, face_recognition |
| Computer Vision / Camera Handling | OpenCV (DirectShow backend) |
| Backend | Python (custom HTTP server) |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |

---

## Project Structure

```
cortex-track-avs/
├── server.py            # Backend HTTP server
├── camera_tracker.py    # Camera capture, YOLOv8 + face recognition pipeline
├── index.html           # Live monitoring dashboard (frontend)
├── lightfall.js          # Frontend dashboard logic
├── config.example.json  # Template config (copy to config.json, add your own keys)
├── yolov8n.pt            # YOLOv8 detection model weights
├── START.bat             # One-click launcher (Windows)
└── README.md
```

---

## Setup & Installation

**Requirements:** Python 3.12, Windows (tested), webcam

1. Clone the repository
   ```
   git clone https://github.com/chmanishreddy775/cortex-track-avs.git
   cd cortex-track-avs
   ```
2. Install dependencies
   ```
   pip install -r requirements.txt
   ```
3. Copy `config.example.json` to `config.json` and add your own email/API credentials — **never commit your real `config.json`**.
4. Run the backend
   ```
   python server.py
   ```
5. Run the camera tracker
   ```
   python camera_tracker.py
   ```
6. Open the dashboard in your browser
   ```
   http://127.0.0.1:8000
   ```

**Quick start (Windows):** double-click `START.bat` to launch both processes automatically.

---

## Usage

1. Enroll authorized staff faces (see enrollment step in `camera_tracker.py`).
2. Start the system — the camera begins monitoring the tray and OR entrance.
3. View live detections and alerts on the dashboard.
4. Any missing instrument or unrecognized face triggers an immediate on-screen alert.

---

## Future Scope

- Expand instrument detection to a larger, hospital-specific dataset covering more tool types
- Cloud-based multi-OR monitoring for hospital-wide deployment
- Integration with existing Hospital Management Systems (HMS) / EHR
- Role-based access control and 2FA for administrative actions
- Regulatory compliance pathway (CDSCO certification) for real clinical deployment

---

## Team

**Future Innovators**
- CH. Manish Reddy — AI/CV development, system integration

---

## License

MIT License
