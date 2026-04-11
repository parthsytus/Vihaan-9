"""
SovereignFace Backend Server  (Python — no pip installs required)
─────────────────────────────────────────────────────────────────
Stores biometric scan records (face photos + credentials) in scans_data.json.
Serves the HTML files statically so any device on the network can open them.

Usage:
    python server.py

Access:
    Local   →  http://localhost:3000/newproject.html
    Network →  http://<your-LAN-IP>:3000/newproject.html   (shown on startup)

API endpoints:
    GET    /api/scans          list all records
    GET    /api/scans/<id>     single record
    POST   /api/scans          save new record (JSON body)
    DELETE /api/scans/<id>     delete specific record
    DELETE /api/scans          clear all records
─────────────────────────────────────────────────────────────────
"""

import json
import os
import socket
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

PORT      = 3000
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "scans_data.json")

# ── Data helpers ──────────────────────────────────────────────────────

def read_data():
    if not os.path.exists(DATA_FILE):
        write_data([])
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def write_data(records):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

# Initialise file
if not os.path.exists(DATA_FILE):
    write_data([])


# ── Request handler ───────────────────────────────────────────────────

class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        # Serve files from the same directory as this script
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    # ─── CORS headers on every response ──────────────────────────────
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    # ─── JSON helper ─────────────────────────────────────────────────
    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type",   "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    # ─── Route table ─────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "/api/scans":
            self.send_json(200, read_data())

        elif path.startswith("/api/scans/"):
            scan_id = path.split("/api/scans/")[1]
            record  = next((r for r in read_data() if str(r.get("id")) == scan_id), None)
            if record:
                self.send_json(200, record)
            else:
                self.send_json(404, {"error": "Not found"})

        else:
            # Static file serving (HTML, CSS, images…)
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "/api/scans":
            try:
                record = self.read_json_body()
                if not record.get("id"):
                    import time
                    record["id"] = int(time.time() * 1000)
                from datetime import datetime, timezone
                record["savedAt"] = datetime.now(timezone.utc).isoformat()
                records = read_data()
                records.insert(0, record)
                write_data(records)
                print(f"[+] Scan saved  id={record['id']}  user={record.get('username','?')}")
                self.send_json(201, {"success": True, "id": record["id"]})
            except Exception as e:
                self.send_json(400, {"error": str(e)})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path   = parsed.path.rstrip("/")

        if path == "/api/scans":
            write_data([])
            self.send_json(200, {"success": True})
        elif path.startswith("/api/scans/"):
            scan_id = path.split("/api/scans/")[1]
            records = [r for r in read_data() if str(r.get("id")) != scan_id]
            write_data(records)
            self.send_json(200, {"success": True})
        else:
            self.send_json(404, {"error": "Not found"})

    # Silence access log spam (comment out to see requests)
    def log_message(self, fmt, *args):
        if "/api/" in args[0] if args else False:
            print(f"  {args[0]}")


# ── LAN IP helper ─────────────────────────────────────────────────────

def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── Main ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    lan_ip = get_lan_ip()
    server = HTTPServer(("0.0.0.0", PORT), Handler)

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║  SovereignFace Backend  ●  Running (Python)          ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Local   →  http://localhost:{PORT}/newproject.html      ║")
    print(f"║  Network →  http://{lan_ip}:{PORT}/newproject.html  ".ljust(55) + "║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Share the Network URL with any device on your Wi-Fi ║")
    print("║  Press Ctrl+C to stop the server.                    ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
        sys.exit(0)
