import os
import sys
import subprocess
import json
import sqlite3
import hashlib
import secrets
import smtplib
from threading import Lock
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Load secure config
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_FILE) as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    print("[ERROR] config.json not found. Please create it.")
    sys.exit(1)

DB_FILE = os.path.join(os.path.dirname(__file__), "vault.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Users table now includes dynamic salts
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password_hash TEXT, salt TEXT, token TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, operator TEXT, event_log TEXT)''')
    
    # Pre-seed Admin accounts with dynamic salts
    authorized_users = [
        ("manish", b"mani@2007"),
        ("karthik", b"karthik@2007"),
        ("aravind", b"aravind@2007"),
        ("bunny", b"bunny@2007")
    ]

    for username, password in authorized_users:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if not c.fetchone():
            user_salt = secrets.token_hex(16)
            pw_hash = hashlib.pbkdf2_hmac('sha256', password, user_salt.encode(), 100000).hex()
            c.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)", (username, pw_hash, user_salt))
    conn.commit()
    conn.close()

init_db()

def send_alert_email(operator):
    try:
        msg = EmailMessage()
        msg.set_content(f"CRITICAL: Cortex Track Asset Verification system detected missing tracked items during operation. Operator on duty: {operator}. Immediate OR reconciliation required.")
        msg['Subject'] = '🚨 Cortex Track Asset Alert'
        msg['From'] = CONFIG.get("EMAIL_SENDER")
        msg['To'] = CONFIG.get("EMAIL_RECEIVER")

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(CONFIG.get("EMAIL_SENDER"), CONFIG.get("EMAIL_APP_PASSWORD"))
        server.send_message(msg)
        server.quit()
        print(f"[AGENT] Charge Nurse OR alert successfully dispatched to {CONFIG.get('EMAIL_RECEIVER')}")
    except Exception as e:
        print(f"[AGENT ERROR] Email failed: {e}")

# Global State
current_operator = "Awaiting Scan..."
item_a_state = "WAITING"
item_b_state = "WAITING"
system_status = "DORMANT"
email_sent_this_session = False
state_lock = Lock()

class SecureLogisticsServer(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "OK")
        self.end_headers()

    def verify_token(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header: return False
        token = auth_header.replace("Bearer ", "")
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE token=?", (token,))
        user = c.fetchone()
        conn.close()
        return user is not None

    def do_GET(self):
        global current_operator, item_a_state, item_b_state, system_status
        
        # -----------------------------------------
        # 1. API ROUTE: Dashboard Telemetry Status
        # -----------------------------------------
        if self.path == '/api/status':
            if not self.verify_token():
                self.send_response(403)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT timestamp, event_log FROM history ORDER BY id DESC LIMIT 5")
            history = [{"time": row[0], "log": row[1]} for row in c.fetchall()]
            conn.close()

            response_data = {
                "operator": current_operator,
                "items": {"Item_A": item_a_state, "Item_B": item_b_state},
                "history": history
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        # -----------------------------------------
        # 2. STATIC FILES: Serve the Web Dashboard
        # -----------------------------------------
        
        # Route to serve the main HTML page
        elif self.path == '/' or self.path == '/index.html':
            try:
                with open('index.html', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "File not found: index.html")
            return

        # Route to serve the Lightfall JS module
        elif self.path == '/lightfall.js':
            try:
                with open('lightfall.js', 'rb') as f:
                    self.send_response(200)
                    # Must serve with the correct JS MIME type for ES modules!
                    self.send_header('Content-type', 'application/javascript')
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_error(404, "File not found: lightfall.js")
            return
            
        # Optional: Route to serve your profile image (if you decide to use it in the UI)
        elif self.path == '/mani.jpg':
             try:
                with open('mani.jpg', 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'image/jpeg')
                    self.end_headers()
                    self.wfile.write(f.read())
             except FileNotFoundError:
                 self.send_error(404, "File not found: mani.jpg")
             return

        # -----------------------------------------
        # 3. CATCH-ALL: 404 Not Found
        # -----------------------------------------
        else:
            self.send_error(404, f"Route not found: {self.path}")

    def do_POST(self):
        global current_operator, item_a_state, item_b_state, system_status, email_sent_this_session
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = json.loads(self.rfile.read(content_length).decode('utf-8')) if content_length > 0 else {}

        if self.path == '/api/login':
            username = post_data.get("username", "").strip()
            password = post_data.get("password", "").strip()

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT salt FROM users WHERE username=?", (username,))
            row = c.fetchone()
            
            if row:
                user_salt = row[0]
                pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), user_salt.encode(), 100000).hex()
                c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
                user = c.fetchone()
                
                if user:
                    token = secrets.token_hex(32)
                    c.execute("UPDATE users SET token=? WHERE username=?", (token, username))
                    c.execute("INSERT INTO history (operator, event_log) VALUES (?, ?)", (username, "Operator authenticated and logged into Asset Verification System (AVS)."))
                    conn.commit()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "SUCCESS", "username": username, "token": token}).encode('utf-8'))
                    conn.close()
                    return

            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "FAIL"}).encode('utf-8'))
            conn.close()

        elif self.path == '/api/scan-workspace':
            # 🟢 API KEY AUTHENTICATION
            api_key = self.headers.get('X-API-Key')
            if api_key != CONFIG.get("TRACKER_API_KEY"):
                self.send_response(401)
                self.end_headers()
                return

            new_operator = post_data.get("operator", "Unknown Operator")
            item_a_state = post_data.get("items", {}).get("Item_A", "WAITING")
            item_b_state = post_data.get("items", {}).get("Item_B", "WAITING")
            new_status = post_data.get("status", "DORMANT")

            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()

            if new_operator != current_operator and new_operator != "Unknown Operator":
                c.execute("INSERT INTO history (operator, event_log) VALUES (?, ?)", (new_operator, f"Face-ID verified Operator at terminal."))
            
            if new_status == "DORMANT" and system_status == "STABLE":
                # FIX: Actually read the dynamic payload from the camera tracker
                compliance_message = post_data.get("agents", {}).get("compliance_log", f"🚨 BREACH: Missing tracked items! Operator: {new_operator}")
                
                c.execute("INSERT INTO history (operator, event_log) VALUES (?, ?)", (new_operator, compliance_message))
                if not email_sent_this_session:
                    send_alert_email(new_operator)
                    email_sent_this_session = True
            
            if new_status == "STABLE":
                email_sent_this_session = False

            conn.commit()
            conn.close()

            # Update the globals safely
            with state_lock:
                current_operator = new_operator
                system_status = new_status

            self.send_response(200)
            self.end_headers()

        elif self.path == '/api/activate':
            if not self.verify_token():
                self.send_response(403)
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "camera_tracker.py")], creationflags=subprocess.CREATE_NEW_CONSOLE)

def run():
    print("[Cortex Track] Enterprise SQL & Secure Auth Core Running on Port 8000")
    ThreadingHTTPServer(('127.0.0.1', 8000), SecureLogisticsServer).serve_forever()

if __name__ == '__main__':
    init_db()
    run()