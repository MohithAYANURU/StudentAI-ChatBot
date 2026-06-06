"""
app.py — Flask server for StudentOS.
Defines all API endpoints. Business logic lives in models.py and prompts.py.
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
from config import SECRET_KEY
from prompts import get_prompt
from models import call_groq, call_all_models

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)


@app.route("/chat", methods=["POST"])
def chat():
    """
    Receive a message and mode from the frontend.
    Maintain conversation history in the session.
    Return the AI reply as JSON.
    """
    data    = request.get_json()
    message = data.get("message", "").strip()
    mode    = data.get("mode", "concept")

    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # Initialize session history if first message
    if "history" not in session:
        session["history"] = []
        session["mode"]    = mode

    # Build the full message list: system prompt + history + new message
    messages = [{"role": "system", "content": get_prompt(mode)}]
    messages += session["history"]
    messages.append({"role": "user", "content": message})

    # Call Groq and get the reply
    reply = call_groq(messages)

    # Save to session history
    session["history"].append({"role": "user",      "content": message})
    session["history"].append({"role": "assistant", "content": reply})
    session.modified = True

    return jsonify({"reply": reply, "mode": mode})


@app.route("/history", methods=["GET"])
def history():
    """Return the current session's conversation history."""
    return jsonify({"history": session.get("history", [])})


@app.route("/reset", methods=["POST"])
def reset():
    """Clear the session history and start fresh."""
    session.clear()
    return jsonify({"message": "Session cleared"})


@app.route("/compare", methods=["POST"])
def compare():
    """
    Send the same prompt to Groq, Gemini and Mistral.
    Return all 3 replies and their response times for benchmarking.
    """
    data          = request.get_json()
    prompt        = data.get("prompt", "").strip()
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    results = call_all_models(prompt, system_prompt)
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)