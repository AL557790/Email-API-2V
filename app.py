from flask import Flask, jsonify, request
import requests
import time
import os
from datetime import datetime

app = Flask(__name__)

class TempMailAPI:
    def __init__(self):
        self.base_url = "https://web2.temp-mail.org"
        self.session = requests.Session()
        
        # Headers تبدو كـ Android Browser حقيقي
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "ar-DZ,ar;q=0.9,en-US;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://temp-mail.org",
            "Referer": "https://temp-mail.org/",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": '"Android"',
            "Connection": "keep-alive",
        })

    def create_mailbox(self):
        try:
            r = self.session.post(
                f"{self.base_url}/mailbox", 
                json={},
                timeout=25
            )
            
            print(f"[DEBUG] Status: {r.status_code} | Encoding: {r.headers.get('content-encoding')}")
            
            if r.status_code == 200:
                data = r.json()
                return {
                    "success": True,
                    "email": data.get("mailbox"),
                    "token": data.get("token")
                }
            else:
                return {
                    "success": False, 
                    "error": f"Status {r.status_code}",
                    "details": r.text[:300]
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_messages(self, token):
        try:
            r = self.session.get(
                f"{self.base_url}/messages",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15
            )
            if r.status_code == 401:
                return {"error": "expired"}
            if r.status_code == 200:
                return r.json().get("messages", [])
            return []
        except:
            return []

temp_api = TempMailAPI()
mailboxes = {}

# ===================== Routes =====================

@app.route('/create', methods=['POST'])
def create_email():
    result = temp_api.create_mailbox()
    if result["success"]:
        token = result["token"]
        mailboxes[token] = {"email": result["email"], "created_at": time.time()}
        return jsonify({
            "status": "success",
            "email": result["email"],
            "token": token
        })
    return jsonify(result), 400


@app.route('/messages', methods=['GET'])
def get_messages():
    token = request.args.get('token')
    if not token or token not in mailboxes:
        return jsonify({"error": "Invalid or missing token"}), 401

    msgs = temp_api.get_messages(token)
    if isinstance(msgs, dict) and "error" in msgs:
        return jsonify({"error": "Session expired"}), 401

    return jsonify({"messages": msgs})


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "active_mailboxes": len(mailboxes)
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)