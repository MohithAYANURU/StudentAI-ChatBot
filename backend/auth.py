import json
import os
from functools import wraps
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint('auth', __name__)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin@epita.fr": {
                "password_hash": generate_password_hash("Admin2026!"),
                "role": "admin"
            },
            "student@epita.fr": {
                "password_hash": generate_password_hash("Student2026!"),
                "role": "student"
            }
        }
        save_users(default_users)
        return default_users
        
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Authentication required. Please log in."}), 401
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Authentication required."}), 401
        if session["user"].get("role") != "admin":
            return jsonify({"error": "Access denied. Administrative rights required."}), 403
        return f(*args, **kwargs)
    return wrapper

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    users = load_users()
    user = users.get(email)
    
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password credentials."}), 401

    session["user"] = {
        "email": email,
        "role": user.get("role", "student")
    }
    
    session.pop("history", None)
    session.modified = True

    return jsonify({"message": "Authentication successful.", "user": session["user"]}), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"message": "Session cleared and logged out safely."})