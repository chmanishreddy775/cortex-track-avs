# Cortex Track — Asset Verification System (AVS)

A browser-based operator and asset verification system for tracked equipment zones. It combines real-time face recognition, real-time object detection, and automated breach alerting — all running client-side, no backend server required for the hosted demo.

**Live demo:** https://chmanishreddy775.github.io/cortex-track-avs/

---

## What it does

1. **Operator verification (face recognition)** — the live camera feed is matched against an enrolled reference photo of the authorized operator, using `face-api.js` (TinyFaceDetector + face landmarks + face descriptors) running entirely in the browser.
2. **Asset tracking (object detection)** — two tracked zones are monitored using TensorFlow.js + COCO-SSD, a pretrained object detection model:
   - **Item A** — phone
   - **Item B** — book
3. **Breach detection & alerting** — if the operator isn't verified or either tracked item goes missing, the system flags a breach on the dashboard (with a red pulsing UI), logs it to the on-screen activity timeline, and sends a real email alert via EmailJS.
4. **Live activity log** — a rolling timeline of detection events, styled to resemble a compliance/audit log.

---

## How it works (architecture)

Everything in the hosted demo (`docs/index.html`) runs client-side in the browser:

| Capability | Library | Notes |
|---|---|---|
| Face detection & matching | [`@vladmandic/face-api`](https://github.com/vladmandic/face-api) | Maintained fork of face-api.js, compatible with modern TensorFlow.js |
| Object detection | [`@tensorflow-models/coco-ssd`](https://github.com/tensorflow/tfjs-models/tree/master/coco-ssd) | Pretrained on the 80-class COCO dataset |
| Email alerts | [EmailJS](https://www.emailjs.com/) | Sends a real email the moment a breach starts (with a cooldown to avoid spam) |
| UI effects | Custom vanilla JS/CSS | Border-glow cards, breathing status aura, WebGL "lightfall" background |

A short grace period (debounce) is applied before flipping an item's status to "WAITING," so momentary detection noise (a frame or two of low confidence) doesn't cause false alerts.

---

## Production vision

This hosted page is a **browser-only demo** meant to showcase the concept without requiring any install. The intended production deployment is a **local system** running:

- A custom-trained **YOLOv8** model for surgical-instrument-specific detection (rather than generic COCO classes)
- **dlib** for higher-accuracy face recognition
- Direct **OpenCV** camera access via a local Python process (more reliable than browser camera permissions)
- A persistent database (e.g. SQLite) for the compliance/activity log, instead of the in-memory log used in the browser demo

---

## Configuration

To enable email breach alerts, set these values near the top of the `<script>` block in `docs/index.html`:

```javascript
const EMAILJS_PUBLIC_KEY = "";   // EmailJS: Account -> General
const EMAILJS_SERVICE_ID = "";   // EmailJS: Email Services
const EMAILJS_TEMPLATE_ID = "";  // EmailJS: Email Templates
const ALERT_RECIPIENT_EMAIL = ""; // inbox to receive breach alerts
```

The EmailJS template body should contain the single variable `{{message}}`, which is populated with the full formatted alert text (operator status, item statuses, timestamp) from the code.

To change the enrolled operator, replace the reference photo (`Navaneeth.jpg`) on the `main` branch with a clear front-facing photo of the new operator's face.

---

## Running locally

This is a static site — no build step required.

```bash
git clone https://github.com/chmanishreddy775/cortex-track-avs.git
cd cortex-track-avs/docs
# serve with any static server, e.g.:
python3 -m http.server 8000
```

Then open `http://localhost:8000` and allow camera access.

---

## Tech stack

- HTML / CSS / vanilla JavaScript
- [face-api.js (vladmandic fork)](https://github.com/vladmandic/face-api) for face recognition
- [TensorFlow.js](https://www.tensorflow.org/js) + [COCO-SSD](https://github.com/tensorflow/tfjs-models/tree/master/coco-ssd) for object detection
- [EmailJS](https://www.emailjs.com/) for client-side email alerts
- Hosted via GitHub Pages
