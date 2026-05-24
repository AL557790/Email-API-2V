from flask import Flask, jsonify, request, render_template_string
import requests
import time
import os

app = Flask(__name__)

class TempMailAPI:
    def __init__(self):
        self.base_url = "https://web2.temp-mail.org"
        self.session = requests.Session()
        
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
        })

    def create_mailbox(self):
        try:
            r = self.session.post(f"{self.base_url}/mailbox", json={}, timeout=25)
            if r.status_code == 200:
                data = r.json()
                return {
                    "success": True,
                    "email": data.get("mailbox"),
                    "token": data.get("token")
                }
            return {"success": False, "error": f"Status {r.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

temp_api = TempMailAPI()
mailboxes = {}

# ===================== HTML Template =====================
HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TempMail API</title>
    <style>
        body { font-family: Arial; background: #0f0f0f; color: #0f0; text-align: center; padding: 20px; }
        .container { max-width: 700px; margin: auto; background: #1a1a1a; padding: 20px; border-radius: 10px; }
        button { padding: 12px 25px; font-size: 18px; background: #00ff00; color: black; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #00cc00; }
        .email { font-size: 22px; color: #00ffaa; margin: 20px 0; word-break: break-all; }
        pre { background: #000; padding: 10px; text-align: right; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌐 TempMail API</h1>
        <p>السيرفر شغال الآن</p>
        
        <button onclick="createEmail()">🔥 إنشاء إيميل جديد</button>
        
        <div id="result" class="email"></div>
        
        <script>
            async function createEmail() {
                document.getElementById('result').innerHTML = 'جاري الإنشاء...';
                const res = await fetch('/create', { method: 'POST' });
                const data = await res.json();
                
                if (data.status === 'success') {
                    document.getElementById('result').innerHTML = 
                        `<strong>📧 الإيميل:</strong><br>${data.email}<br><br>` +
                        `<strong>🔑 التوكن:</strong><br><small>${data.token}</small>`;
                } else {
                    document.getElementById('result').innerHTML = '❌ فشل: ' + JSON.stringify(data);
                }
            }
        </script>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """عند فتح الموقع يظهر الصفحة الجميلة"""
    return render_template_string(HTML)

@app.route('/create', methods=['POST'])
def create_email():
    result = temp_api.create_mailbox()
    if result.get("success"):
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
        return jsonify({"error": "Invalid token"}), 401

    try:
        r = temp_api.session.get(
            f"{temp_api.base_url}/messages",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.status_code == 200:
            return jsonify({"messages": r.json().get("messages", [])})
        return jsonify({"error": f"Status {r.status_code}"}), 400
    except:
        return jsonify({"error": "connection error"}), 500


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "running",
        "active_mailboxes": len(mailboxes)
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)