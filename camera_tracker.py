import cv2
import requests
import threading
import face_recognition
from ultralytics import YOLO
import json
import sys

# FIX: Load config ONCE at startup for maximum speed
try:
    with open("config.json") as f:
        API_KEY = json.load(f)["TRACKER_API_KEY"]
except Exception as e:
    print("[FATAL ERROR] Could not load config.json. Exiting.")
    sys.exit(1)

print("[STATUS] Loading AI Models...")
model = YOLO('yolov8n.pt')

# ==========================================
# 🟢 SURGEON IDENTITY MATRIX SETUP
# ==========================================
try:
    # The AI needs a baseline photo to know what the authorized surgeon looks like.
    # Make sure you have a picture of yourself named 'surgeon.jpg' in this folder!
    surgeon_image = face_recognition.load_image_file("mani.jpg")
    surgeon_face_encoding = face_recognition.face_encodings(surgeon_image)[0]

    known_face_encodings = [surgeon_face_encoding]
    known_face_names = ["Dr. Mani"]
    print("[STATUS] Surgeon Identity Matrix Loaded Successfully.")

except FileNotFoundError:
    print("[WARNING] 'mani.jpg' not found! Please add a photo of yourself to the folder.")
    known_face_encodings = []
    known_face_names = []
except IndexError:
    print("[WARNING] No face detected in 'mani.jpg'. Please use a clearer photo.")
    known_face_encodings = []
    known_face_names = []
# ==========================================

# Open the webcam stream
cap = cv2.VideoCapture(0)

# FIX: Prevent the script from crashing silently if the camera is busy
if not cap.isOpened():
    print("\n[FATAL ERROR] Webcam failed to open! Is another app using it?")
    sys.exit(1)

def send_telemetry(data):
    try:
        # Use the global API_KEY loaded at startup
        requests.post("http://127.0.0.1:8000/api/scan-workspace", json=data, headers={"X-API-Key": API_KEY}, timeout=1)
    except requests.exceptions.RequestException:
        pass

# --- SPEED OPTIMIZATION VARIABLES ---
frame_counter = 0
skip_rate = 3 # Only run heavy AI math every 3rd frame

# Memory variables to keep boxes on screen during skipped frames
current_operator = "Awaiting Scan..."
item_a_state = "WAITING"
item_b_state = "WAITING"
last_boxes = []

print("[STATUS] Camera Active. Press 'q' in the window to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_counter += 1

    # 🟢 ONLY RUN AI ON EVERY 3RD FRAME
    if frame_counter % skip_rate == 0:
        item_a_state = "WAITING"
        item_b_state = "WAITING"
        current_operator = "Unknown Operator"
        last_boxes = []

        # -- YOLOV8 OBJECT DETECTION --
        results = model(frame, stream=True, verbose=False)
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]

                if class_name == "cell phone":
                    item_a_state = "FOUND"
                    last_boxes.append((x1, y1, x2, y2, "Surgical Clamp", (255, 0, 0))) 
                elif class_name == "bottle":
                    item_b_state = "FOUND"
                    last_boxes.append((x1, y1, x2, y2, "Medical Sponge", (0, 255, 0)))

        # -- FACE RECOGNITION (DOWNSCALED FOR SPEED) --
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            if True in matches:
                first_match_index = matches.index(True)
                current_operator = known_face_names[first_match_index]
            
            # Scale coordinates back up by 4 for drawing
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            last_boxes.append((left, top, right, bottom, f"OPERATOR: {current_operator}", (0, 165, 255))) # Orange box

        # -- SEND TELEMETRY IN THE BACKGROUND --
        # FIX: The vault is stable as long as the items are there. 
        # The operator's face flickering no longer triggers a fake breach.
        system_status = "STABLE" if (item_a_state == "FOUND" and item_b_state == "FOUND") else "DORMANT"
        
        payload = {
            "status": system_status,
            "operator": current_operator,
            "items": {
                "Item_A": item_a_state,
                "Item_B": item_b_state
            },
            "agents": {
                "compliance_log": "All surgical items accounted for on tray." if system_status == "STABLE" else f"[🚨 RSI BREACH]: Missing surgical items! Surgeon: {current_operator}",
                "charge_nurse_alert": "Inventory stable." if system_status == "STABLE" else "AUTOMATED RSI TICKET GENERATED."
            }
        }
        
        # Fire and forget!
        threading.Thread(target=send_telemetry, args=(payload,), daemon=True).start()

    # 🟢 DRAW GRAPHICS ON EVERY FRAME (Keeps video smooth)
    for (x1, y1, x2, y2, label, color) in last_boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Show the live feed
    cv2.imshow("Cortex Track Vision Stream", frame)    
    if cv2.waitKey(1) == ord('q'):
        break

print("[STATUS] Shutting down vision stream. Sending OFFLINE signal to server...")


final_payload = {
    "status": "DORMANT",
    "operator": "System Offline",
    "items": {
        "Item_A": "WAITING",
        "Item_B": "WAITING"
    },
    "agents": {
        "compliance_log": "Vision stream terminated by user.",
        "charge_nurse_alert": "TRACKING OFFLINE."
    }
}
# We call it directly (without a thread) so the script doesn't exit before the request finishes!
send_telemetry(final_payload)

cap.release()
cv2.destroyAllWindows()
print("[STATUS] Safe shutdown complete.")