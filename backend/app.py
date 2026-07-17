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
from auth import auth_bp, login_required, admin_required

app = Flask(__name__)
app.secret_key = SECRET_KEY

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
CORS(app, supports_credentials=True)

app.register_blueprint(auth_bp, url_prefix='/auth')

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
@login_required
def chat():
    """
    Receive message and mode. Manages mode state using Flask sessions
    and handles modular text parsing for file uploads.
    """
    # 1. Initialize core contextual variables
    input_mode = None
    message = ""
    file_context = ""

    # 2. Extract input text and files from multi-part or JSON payloads
    if request.files or request.form:
        input_mode = request.form.get("mode")
        message = request.form.get("message", "").strip()
        
        # Access the file safely using native Flask/Werkzeug request bindings
        uploaded_file = request.files.get("file")
        if uploaded_file and uploaded_file.filename != "":
            if uploaded_file.filename.lower().endswith('.pdf'):
                # Read file stream safely into bytes directly out of memory
                file_bytes = uploaded_file.read()
                pdf_text = extract_text_from_pdf(file_bytes)
                
                if pdf_text:
                    # Keep file context separate so it doesn't corrupt clean message history
                    file_context = f"\n\n[ATTACHED DOCUMENT CONTEXT]:\n{pdf_text}\n"
                else:
                    return jsonify({"error": "Unable to extract raw text content from the uploaded PDF."}), 422
            else:
                return jsonify({"error": "Unsupported file layout format. Please provide a standard .pdf document."}), 400
    
    # Fallback to pure JSON request processing
    else:
        data = request.get_json() or {}
        message = data.get("message", "").strip()
        input_mode = data.get("mode")

    # Guard clause: Ensure we have at least text or an uploaded file
    if not message and not file_context:
        return jsonify({"error": "Message parameter context string or file attachment cannot be empty"}), 400

    # 3. Handle Session State Initialization
    if "history" not in session:
        session["history"] = []
    if "mode" not in session:
        session["mode"] = "concept"  # Global application default fallback

    # 4. Text Command Interception & State Routing Logic
    clean_msg = message.lower().strip()
    if clean_msg == "cv":
        session["mode"] = "cv"
    elif "internship" in clean_msg or "find internships" in clean_msg:
        session["mode"] = "internship"
    elif "concept" in clean_msg or "explain" in clean_msg:
        session["mode"] = "concept"
    elif "exam" in clean_msg or "quiz" in clean_msg:
        session["mode"] = "exam"
    # If the client frontend explicitly passed a valid mode payload, respect it
    elif input_mode and input_mode in ["concept", "exam", "cv", "internship"]:
        session["mode"] = input_mode

    # 5. Build the AI Payload
    # Always pull the active system prompt dynamically from the persistent session state
    current_mode = session["mode"]
    messages = [{"role": "system", "content": get_prompt(current_mode)}]
    
    # Inject past conversation logs
    messages += session["history"]
    
    # Formulate current outgoing prompt block
    current_user_payload = message
    if file_context:
        if message:
            current_user_payload = f"{message}\n{file_context}".strip()
        else:
            current_user_payload = f"Analyze attached document:{file_context}"
    
    messages.append({"role": "user", "content": current_user_payload})

    # 6. Dispatch Context Request to AI Runtime
    try:
        reply = call_groq(messages)
    except Exception as e:
        print(f"AI Model runtime inference exception: {str(e)}")
        return jsonify({"error": "Failed to generate AI response payload."}), 500

    # 7. Update Session State History Safely
    # Log clean user text strings to memory arrays—NOT the giant raw PDF context block
    history_user_string = message if message else "[Uploaded Document]"
    session["history"].append({"role": "user", "content": history_user_string})
    session["history"].append({"role": "assistant", "content": reply})
    session.modified = True

    return jsonify({"reply": reply, "mode": current_mode})


@app.route("/history", methods=["GET"])
@login_required
def history():
    """Return the current session's conversation history."""
    return jsonify({"history": session.get("history", [])})


@app.route("/reset", methods=["POST"])
@login_required
def reset():
    """Clear the session history and start fresh."""
    session.clear()
    return jsonify({"message": "Session cleared"})


@app.route("/compare", methods=["POST"])
@login_required 
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

@app.route("/admin/system-status", methods=["GET"])
@admin_required
def system_status():
    """Protected dashboard for administrative users only."""
    return jsonify({
        "status": "online",
        "active_sessions": len(session),
        "message": "Authorized admin access granted."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True) 