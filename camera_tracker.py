import cv2
import requests
import threading
import face_recognition
from ultralytics import YOLO
import json
import sys
import time

try:
    with open("config.json") as f:
        API_KEY = json.load(f)["TRACKER_API_KEY"]
except Exception as e:
    print("[FATAL ERROR] Could not load config.json. Exiting.")
    sys.exit(1)

print("[STATUS] Loading AI Models...")
model = YOLO('yolov8n.pt')


try:
    surgeon_image = face_recognition.load_image_file("Navaneeth.jpg")
    surgeon_face_encoding = face_recognition.face_encodings(surgeon_image)[0]

    known_face_encodings = [surgeon_face_encoding]
    known_face_names = ["Dr. Navaneeth"]
    print("[STATUS] Surgeon Identity Matrix Loaded Successfully.")

except FileNotFoundError:
    print("[WARNING] 'Navaneeth.jpg' not found! Please add a photo of yourself to the folder.")
    known_face_encodings = []
    known_face_names = []
except IndexError:
    print("[WARNING] No face detected in 'Navaneeth.jpg'. Please use a clearer photo.")
    known_face_encodings = []
    known_face_names = []

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("\n[FATAL ERROR] Webcam failed to open! Is another app using it?")
    sys.exit(1)

def send_telemetry(data):
    try:
        requests.post("http://127.0.0.1:8000/api/scan-workspace", json=data, headers={"X-API-Key": API_KEY}, timeout=1)
    except requests.exceptions.RequestException:
        pass


frame_counter = 0
skip_rate = 3  

current_operator = "Awaiting Scan..."
item_a_state = "WAITING"
item_b_state = "WAITING"
last_boxes = []


DEBOUNCE_THRESHOLD = 5
confirmed_operator = "Awaiting Scan..."
candidate_operator = "Awaiting Scan..."
candidate_count = 0
operator_since = time.time()

print("[STATUS] Camera Active. Press 'q' in the window to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    frame_counter += 1

    if frame_counter % skip_rate == 0:
        item_a_state = "WAITING"
        item_b_state = "WAITING"
        raw_operator = "Unknown Operator"
        last_boxes = []

        
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

        
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = face_distances.argmin()
                if face_distances[best_match_index] < 0.5:
                    raw_operator = known_face_names[best_match_index]

            top *= 4; right *= 4; bottom *= 4; left *= 4
            last_boxes.append((left, top, right, bottom, f"OPERATOR: {raw_operator}", (0, 165, 255)))

    
        if raw_operator == candidate_operator:
            candidate_count += 1
        else:
            candidate_operator = raw_operator
            candidate_count = 1

        operator_just_changed = False
        if candidate_count >= DEBOUNCE_THRESHOLD and candidate_operator != confirmed_operator:
            confirmed_operator = candidate_operator
            operator_since = time.time()
            operator_just_changed = True

        current_operator = confirmed_operator  

        system_status = "STABLE" if (item_a_state == "FOUND" and item_b_state == "FOUND") else "DORMANT"

        payload = {
            "status": system_status,
            "operator": current_operator,
            "operator_changed": operator_just_changed,          
            "duration_seconds": round(time.time() - operator_since, 1),
            "items": {
                "Item_A": item_a_state,
                "Item_B": item_b_state
            },
            "agents": {
                "compliance_log": "All surgical items accounted for on tray." if system_status == "STABLE" else f"[🚨 RSI BREACH]: Missing surgical items! Surgeon: {current_operator}",
                "charge_nurse_alert": "Inventory stable." if system_status == "STABLE" else "AUTOMATED RSI TICKET GENERATED."
            }
        }

        threading.Thread(target=send_telemetry, args=(payload,), daemon=True).start()

    for (x1, y1, x2, y2, label, color) in last_boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Cortex Track Vision Stream", frame)
    if cv2.waitKey(1) == ord('q'):
        break

print("[STATUS] Shutting down vision stream. Sending OFFLINE signal to server...")

final_payload = {
    "status": "DORMANT",
    "operator": "System Offline",
    "operator_changed": True,
    "duration_seconds": 0,
    "items": {"Item_A": "WAITING", "Item_B": "WAITING"},
    "agents": {
        "compliance_log": "Vision stream terminated by user.",
        "charge_nurse_alert": "TRACKING OFFLINE."
    }
}
send_telemetry(final_payload)

cap.release()
cv2.destroyAllWindows()
print("[STATUS] Safe shutdown complete.")
