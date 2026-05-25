from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)

BASE_URL = "https://web2.temp-mail.org"


# =========================
# TempMail Client
# =========================
class TempMail:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.email = None

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 Chrome/120 Safari/537.36",
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Origin": "https://temp-mail.org",
            "Referer": "https://temp-mail.org/"
        }

        self.session.headers.update(self.headers)

    def create_email(self):
        url = f"{BASE_URL}/mailbox"

        try:
            r = self.session.post(url, json={}, timeout=15)

            print("\n[DEBUG CREATE]")
            print("STATUS:", r.status_code)
            print("TEXT:", r.text[:300])

            if r.status_code != 200:
                return None

            data = r.json()

            self.token = data.get("token")
            self.email = data.get("mailbox")

            return data

        except Exception as e:
            print("[ERROR create_email]", e)
            return None

    def get_messages(self):
        if not self.token:
            return []

        try:
            r = self.session.get(
                f"{BASE_URL}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=15
            )

            print("\n[DEBUG MESSAGES]")
            print("STATUS:", r.status_code)
            print("TEXT:", r.text[:200])

            if r.status_code != 200:
                return []

            return r.json().get("messages", [])

        except Exception as e:
            print("[ERROR messages]", e)
            return []


# =========================
# API
# =========================
tm = TempMail()


@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": "TempMail API"
    })


@app.route("/create")
def create():
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
    token = request.headers.get("token")

    if token:
        tm.token = token

    return jsonify({
        "messages": tm.get_messages()
    })


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)