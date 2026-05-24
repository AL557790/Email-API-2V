from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

BASE_URL = "https://web2.temp-mail.org"


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

            print("STATUS:", r.status_code)
            print("TEXT:", r.text[:200])

            if r.status_code != 200:
                return None

            data = r.json()

            self.token = data.get("token")
            self.email = data.get("mailbox")

            if not self.token or not self.email:
                return None

            return data

        except Exception as e:
            print("ERROR:", e)
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

            if r.status_code != 200:
                return []

            return r.json().get("messages", [])

        except Exception:
            return []


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)