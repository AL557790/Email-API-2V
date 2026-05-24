from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import uuid

app = Flask(__name__)
CORS(app)

BASE_URL = "https://web2.temp-mail.org"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "ar-DZ,ar;q=0.9,en-US;q=0.8",
    "Origin": "https://temp-mail.org",
    "Referer": "https://temp-mail.org/",
    "Content-Type": "application/json"
}

# تخزين الجلسات في الذاكرة: { session_id: { email, token } }
SESSIONS = {}


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get("https://temp-mail.org/", timeout=10)
    except Exception:
        pass
    return s


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "name": "TempMail API",
        "version": "2.0.0",
        "endpoints": {
            "POST /mailbox": "إنشاء إيميل → يرجع session_id + email فقط",
            "GET /messages/<session_id>": "جلب الرسائل بالـ session_id",
            "DELETE /mailbox/<session_id>": "حذف الجلسة",
            "GET /health": "حالة الـ API"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "active_sessions": len(SESSIONS)})


@app.route("/mailbox", methods=["POST"])
def create_mailbox():
    """إنشاء إيميل — التوكن يُحفظ server-side فقط"""
    try:
        sess = make_session()
        r = sess.post(f"{BASE_URL}/mailbox", json={}, timeout=15)

        if r.status_code != 200:
            return jsonify({"success": False, "error": f"فشل الطلب: {r.status_code}"}), 502

        data = r.json()
        email = data.get("mailbox")
        token = data.get("token")

        if not email or not token:
            return jsonify({"success": False, "error": "لم يُرجع السيرفر mailbox أو token", "raw": data}), 502

        # نحفظ التوكن عندنا ونرجع فقط session_id
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = {"email": email, "token": token}

        return jsonify({
            "success": True,
            "session_id": session_id,
            "email": email
            # ❌ token لا يُرسل للمستخدم أبداً
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "انتهى وقت الاتصال"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/messages/<session_id>", methods=["GET"])
def get_messages(session_id):
    """جلب الرسائل — المستخدم يرسل session_id فقط"""
    session = SESSIONS.get(session_id)

    if not session:
        return jsonify({"success": False, "error": "session_id غير موجود أو منتهي"}), 404

    token = session["token"]  # نجيب التوكن من الذاكرة

    try:
        sess = make_session()
        r = sess.get(
            f"{BASE_URL}/messages",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )

        if r.status_code == 401:
            # نحذف الجلسة المنتهية
            SESSIONS.pop(session_id, None)
            return jsonify({"success": False, "error": "انتهت صلاحية الإيميل", "expired": True}), 401

        if r.status_code != 200:
            return jsonify({"success": False, "error": f"خطأ: {r.status_code}"}), 502

        messages = r.json().get("messages", [])

        cleaned = []
        for m in messages:
            cleaned.append({
                "id": m.get("_id"),
                "from": m.get("from"),
                "subject": m.get("subject"),
                "date": m.get("createdAt") or m.get("date"),
                "body_text": m.get("bodyText") or m.get("text_body"),
                "body_html": m.get("bodyHtml") or m.get("html_body"),
            })

        return jsonify({
            "success": True,
            "email": session["email"],
            "count": len(cleaned),
            "messages": cleaned
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "error": "انتهى وقت الاتصال"}), 504
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mailbox/<session_id>", methods=["DELETE"])
def delete_mailbox(session_id):
    """حذف الجلسة من الذاكرة"""
    if session_id in SESSIONS:
        SESSIONS.pop(session_id)
        return jsonify({"success": True, "message": "تم حذف الجلسة"})
    return jsonify({"success": False, "error": "session_id غير موجود"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)