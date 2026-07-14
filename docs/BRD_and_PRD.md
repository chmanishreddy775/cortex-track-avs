# Cortex Track (SentinelOR) — BRD & PRD

---

## Business Requirements Document (BRD)

### Why are we building this?

Operating rooms face two recurring, high-stakes risks that manual processes handle poorly:
- Retained surgical instruments during procedures, which can cause serious patient harm and expose hospitals to malpractice liability.
- Unverified personnel present in the OR without real-time detection.

Manual instrument counts and staff checks depend entirely on human vigilance during high-pressure procedures — there is no automated safety net.

### What business value will it create?

- Reduces risk of retained-instrument incidents and the associated patient harm and legal liability.
- Reduces reliance on manual, error-prone counting processes.
- Creates an auditable, timestamped log of OR activity for compliance and review.
- Positions the hospital as an early adopter of AI-driven patient safety tooling.

### Who are the stakeholders?

| Stakeholder | Role |
|---|---|
| OR staff (surgeons, nurses) | Primary users — operate under system monitoring |
| Hospital administration | Manages deployment, reviews compliance logs |
| Charge nurse / safety officer | Receives breach alerts, takes corrective action |
| Patients | Indirect beneficiaries — reduced risk of retained-instrument harm |

### High-level solution overview

A real-time computer vision system using two parallel monitoring feeds — instrument detection (YOLOv8) and staff face verification (face_recognition) — that logs all activity locally and triggers immediate alerts when instruments go missing or an unrecognized person is detected.

### Success metrics

- Zero missed instrument-removal events during monitored procedures.
- Alert triggered and logged within seconds of a breach.
- Staff verification accuracy sufficient to distinguish enrolled vs. unenrolled individuals reliably.

---

## Product Requirements Document (PRD)

### What are we building?

A locally-run web application with two components:
1. A camera-based monitoring process (`camera_tracker.py`) that runs YOLOv8 object detection and face recognition in real time.
2. A backend server (`server.py`) that receives detection data, authenticates users, stores history in SQLite, and serves a live dashboard.

### How will it work for users?

1. Authorized staff log into the dashboard via username/password (hashed + salted).
2. The camera tracker starts, continuously scanning the tray for tracked items and the operator's face.
3. The dashboard displays live status: which items are present, who the current operator is, and recent event history.
4. If an item goes missing or an unrecognized face triggers a mismatch, the system logs a breach event and sends an automated email alert to the charge nurse.

### Functional requirements

- Real-time object detection on camera feed (YOLOv8)
- Real-time face verification against enrolled identities
- User login with hashed password authentication
- Live dashboard showing current status and history
- Automated email alert on breach detection
- Persistent event logging (SQLite)

### Non-functional requirements

- Must run fully offline/locally — no cloud dependency
- Detection loop must maintain usable frame rate (current implementation processes every 3rd frame for performance)
- API endpoints protected by token/API-key authentication
- Config secrets (email credentials, API keys) must never be committed to version control

### Constraints & assumptions

- Built and tested on Windows with Python 3.12
- Object detection currently uses proxy objects (e.g. everyday items standing in for real surgical instruments) due to the lack of a custom-trained surgical instrument dataset within the hackathon timeframe
- Single-camera, single-room setup for the current demo scope

### Acceptance criteria

- System correctly identifies enrolled operator via face match with a defined similarity threshold
- System correctly flags missing tracked items and updates dashboard status within a few seconds
- Breach event triggers exactly one email alert per incident (no duplicate spam)
- Dashboard reflects live state without requiring manual refresh
