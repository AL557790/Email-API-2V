from flask import Flask, jsonify, request
import time
import requests

app = Flask(__name__)

BASE_URL = "https://web2.temp-mail.org"

API_KEYS = {
    "123456": "user1",
    "999999": "admin"
}

ip_requests = {}
blocked_ips = {}

MAX_REQUESTS = 10
TIME_WINDOW = 10
BAN_TIME = 60


def check_key():
    key = request.headers.get("x-api-key")
    return API_KEYS.get(key)


def security_check():
    ip = request.remote_addr
    now = time.time()

    if ip in blocked_ips:
        if now < blocked_ips[ip]:
            return False, "IP banned temporarily"
        else:
            del blocked_ips[ip]

    if ip not in ip_requests:
        ip_requests[ip] = []

    ip_requests[ip] = [t for t in ip_requests[ip] if now - t < TIME_WINDOW]

    ip_requests[ip].append(now)

    if len(ip_requests[ip]) > MAX_REQUESTS:
        blocked_ips[ip] = now + BAN_TIME
        return False, "Too many requests (banned)"

    return True, "ok"


class TempMail:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.email = None

    def create_email(self):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Origin": "https://temp-mail.org",
            "Referer": "https://temp-mail.org/"
        }

        try:
            r = self.session.post(
                f"{BASE_URL}/mailbox",
                json={},
                headers=headers,
                timeout=15
            )
        except Exception:
            return None

        print("STATUS:", r.status_code)
        print("TEXT:", r.text[:200])

        if r.status_code != 200:
            return None

        try:
            data = r.json()
        except Exception:
            return None

        self.token = data.get("token")
        self.email = data.get("mailbox")

        if not self.token or not self.email:
            return None

        return data

    def get_messages(self):
        if not self.token:
            return []

        try:
            r = self.session.get(
                f"{BASE_URL}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=15
            )

            if r.status_code != 200:
                return []

            return r.json().get("messages", [])

        except Exception:
            return []


@app.route("/")
def home():
    return jsonify({
        "status": "secure",
        "message": "Secure TempMail API Running"
    })


@app.route("/create")
def create():
    if not check_key():
        return jsonify({"error": "invalid api key"}), 403

    ok, msg = security_check()
    if not ok:
        return jsonify({"error": msg}), 429

    tm = TempMail()
    data = tm.create_email()

    if not data:
        return jsonify({"error": "failed to create email"}), 500

    return jsonify({
        "email": tm.email,
        "token": tm.token,
        "status": "created"
    })


@app.route("/messages")
def messages():
    if not check_key():
        return jsonify({"error": "invalid api key"}), 403

    ok, msg = security_check()
    if not ok:
        return jsonify({"error": msg}), 429

    token = request.headers.get("token")
    if not token:
        return jsonify({"error": "missing token"}), 400

    tm = TempMail()
    tm.token = token

    return jsonify({
        "messages": tm.get_messages()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)