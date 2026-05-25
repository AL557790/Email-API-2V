from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

BASE_URL = "https://api.internal.temp-mail.io/api/v3"


# فحص سرعة السرفر
@app.route("/test", methods=["GET"])
def test_server():

    try:
        start = time.time()

        response = requests.get(
            f"{BASE_URL}/domains",
            timeout=10
        )

        ping = round((time.time() - start) * 1000, 2)

        return jsonify({
            "status": "online",
            "status_code": response.status_code,
            "response_time_ms": ping
        })

    except requests.exceptions.Timeout:
        return jsonify({
            "status": "timeout",
            "message": "Server too slow"
        }), 408

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# إنشاء إيميل مؤقت
@app.route("/new", methods=["GET"])
def create_email():

    try:
        start = time.time()

        response = requests.post(
            f"{BASE_URL}/email/new",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={}
        )

        ping = round((time.time() - start) * 1000, 2)

        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "status_code": response.status_code
            })

        data = response.json()

        return jsonify({
            "status": "success",
            "response_time_ms": ping,
            "data": data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# جلب الرسائل
@app.route("/messages/<email>", methods=["GET"])
def fetch_messages(email):

    try:
        start = time.time()

        response = requests.get(
            f"{BASE_URL}/email/{email}/messages",
            headers={
                "Accept": "application/json"
            }
        )

        ping = round((time.time() - start) * 1000, 2)

        if response.status_code != 200:
            return jsonify({
                "status": "failed",
                "status_code": response.status_code
            })

        return jsonify({
            "status": "success",
            "response_time_ms": ping,
            "messages": response.json()
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# تشغيل السرفر
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )