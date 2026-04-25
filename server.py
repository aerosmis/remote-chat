print("=== BON SERVEUR LANCÉ ===")

from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send, emit
from zoneinfo import ZoneInfo
from datetime import datetime
import json
import os

# ===== CONFIG =====
app = Flask(__name__)
app.secret_key = "secret123"
socketio = SocketIO(app, async_mode='threading')

users = []

HISTORY_FILE = "messages.json"
REACTIONS_FILE = "reactions.json"

users_db = {
    "Aero":     {"pwd": "7462",    "avatar": "a1.png"},
    "Astrolex": {"pwd": "6700",    "avatar": "a2.png"},
    "Lepro2.0": {"pwd": "67",      "avatar": "a3.png"},
    "Lily":     {"pwd": "lily001", "avatar": "a4.png"}
}

# ===== HELPERS =====
def load_messages():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_messages(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_reactions():
    if not os.path.exists(REACTIONS_FILE):
        return {}
    with open(REACTIONS_FILE, "r") as f:
        return json.load(f)

def save_reactions(reactions):
    with open(REACTIONS_FILE, "w") as f:
        json.dump(reactions, f)

# ===== ROUTES =====
@app.route("/", methods=["GET", "POST"])
def login():
    avatars = os.listdir("static/avatars")
    if request.method == "POST":
        user   = request.form.get("username")
        pwd    = request.form.get("password")
        avatar = request.form.get("avatar")
        if user in users_db and users_db[user]["pwd"] == pwd:
            session["logged_in"] = True
            session["user"]      = user
            session["avatar"]    = avatar
            return redirect("/chat")
    return render_template("login.html", avatars=avatars)

@app.route("/chat")
def chat():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("index.html")

# ===== SOCKET EVENTS =====
@socketio.on("connect")
def handle_connect():
    user = session.get("user")
    emit("history", load_messages())
    emit("reactions_history", load_reactions())
    if user and user not in users:
        users.append(user)
    socketio.emit("users", users)

@socketio.on("disconnect")
def handle_disconnect():
    user = session.get("user")
    if user in users:
        users.remove(user)
    socketio.emit("users", users)

@socketio.on("message")
def handle_message(msg):
    user   = session.get("user")
    avatar = session.get("avatar")
    time   = datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M")
    data   = f"{time}|{user}|{avatar}|{msg}"
    messages = load_messages()
    messages.append(data)
    messages = messages[-100:]
    save_messages(messages)
    send(data, broadcast=True)

@socketio.on("image")
def handle_image(data):
    user   = session.get("user")
    avatar = session.get("avatar")
    time   = datetime.now(ZoneInfo("Europe/Paris")).strftime("%H:%M")
    msg    = f"{time}|{user}|{avatar}|[img]{data}"
    messages = load_messages()
    messages.append(msg)
    messages = messages[-100:]
    save_messages(messages)
    emit("message", msg, broadcast=True)

@socketio.on("reaction")
def handle_reaction(data):
    reactions = load_reactions()
    msg_id    = data["msg_id"]
    emoji     = data["emoji"]
    if msg_id not in reactions:
        reactions[msg_id] = {}
    reactions[msg_id][emoji] = reactions[msg_id].get(emoji, 0) + 1
    save_reactions(reactions)
    emit("reaction", data, broadcast=True)

# ===== RUN =====
if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )