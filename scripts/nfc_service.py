from flask import Flask, request, jsonify
from write_nfc import write_to_card

app = Flask(__name__)

@app.post("/write_card")
def write_card():
    data = request.get_json()
    code = data.get("code")

    try:
        write_to_card(code)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

app.run(host="0.0.0.0", port=5001)

