print("=== BON SERVEUR LANCÉ ===")

from flask import request
from datetime import datetime
users = []

from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send, emit
import json
import os

HISTORY_FILE = "messages.json"

print("=== BON SERVEUR LANCÉ ===")

app = Flask(__name__)
app.secret_key = "secret123"

socketio = SocketIO(app, async_mode='threading')

users_db = { 
    "Aero": "7462",
    "Astrolex": "6700",
    "Lepro2.0": "67",
    "Lily": "lily001"
}

@app.route("/", methods=["GET", "POST"])
def login(): 
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")

        print("USER:", user)
        print("PASS:", pwd)

        if user in users_db and users_db[user] == pwd:
            print("LOGIN OK")
            session["logged_in"] = True
            session["user"] = user
            return redirect("/chat")
        else:
            print("LOGIN FAIL")

    return render_template("login.html")

@app.route("/chat")
def chat():
    if not session.get("logged_in"):
        return redirect("/")
    return render_template("index.html")

def save_messages(messages):
    with open(HISTORY_FILE, "w") as f:
        json.dump(messages, f)

def load_messages():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

@socketio.on("message")
def handle_message(msg):
    user = session.get("user")

    messages = load_messages()

    time = datetime.now().strftime("%H:%M")  # 👈 heure

    data = f"{time}|{user}|{msg}"  # 👈 nouveau format
    messages.append(data)

    messages = messages[-100:]
    save_messages(messages)

    send(data, broadcast=True)

@socketio.on("connect")
def handle_connect():
    user = session.get("user")  # 👈 AJOUT

    messages = load_messages()
    emit("history", messages)

    if user and user not in users:
        users.append(user)

    socketio.emit("users", users)

@socketio.on("disconnect")
def disconnect():
    user = session.get("user")

    if user in users:
        users.remove(user)

    socketio.emit("users", users)

    

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True 
    )
