"""
app.py — Refactored Flask server for StudentOS.
Supports standard text messaging and text-based file uploads (PDF) for CV analysis.
"""

import io
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from pypdf import PdfReader
from config import SECRET_KEY
from prompts import get_prompt
from models import call_groq, call_all_models


app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, supports_credentials=True)


def extract_text_from_pdf(file_bytes):
    """Reads PDF binary streams and extracts textual data strings."""
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        extracted_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text.append(text)
        return "\n".join(extracted_text).strip()
    except Exception as e:
        print(f"PDF extraction subsystem fault: {str(e)}")
        return ""


@app.route("/chat", methods=["POST"])
def chat():
    """
    Receive message and mode. Handles both pure JSON payloads and 
    Multipart Form Data uploads for structural document parsing.
    """
    mode = "concept"
    message = ""

    # Check if request contains files via standard multipart form-data handling
    if request.files or request.form:
        mode = request.form.get("mode", "concept")
        message = request.form.get("message", "").strip()
        
        # Access the file safely using native Flask/Werkzeug request bindings
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename != "":
            if uploaded_file.filename.lower().endswith('.pdf'):
                # Read file stream safely into bytes directly out of memory
                file_bytes = uploaded_file.read()
                pdf_text = extract_text_from_pdf(file_bytes)
                
                if pdf_text:
                    # Inject parsed text seamlessly into the model payload
                    file_context = f"\n\n[ATTACHED DOCUMENT CONTEXT]:\n{pdf_text}\n"
                    message = f"{message}{file_context}" if message else f"Analyze attached document:{file_context}"
                else:
                    return jsonify({"error": "Unable to extract raw text content from the uploaded PDF."}), 422
            else:
                return jsonify({"error": "Unsupported file layout format. Please provide a standard .pdf document."}), 400
    
    # Fallback to pure JSON request processing
    else:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        mode = data.get("mode", "concept")

    if not message:
        return jsonify({"error": "Message parameter context string cannot be empty"}), 400

    # Initialize session tracking states
    if "history" not in session:
        session["history"] = []
        session["mode"] = mode

    # Construct the model prompt execution array
    messages = [{"role": "system", "content": get_prompt(mode)}]
    messages += session["history"]
    messages.append({"role": "user", "content": message})

    # Dispatch context request to the AI runtime
    reply = call_groq(messages)

    # Append state transitions back to memory arrays
    session["history"].append({"role": "user", "content": message})
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
    data          = request.get_json() or {}
    prompt        = data.get("prompt", "").strip()
    system_prompt = data.get("system_prompt", "You are a helpful assistant.")

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    results = call_all_models(prompt, system_prompt)
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True, port=5000)