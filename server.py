print("=== BON SERVEUR LANCÉ ===")

from flask import request
from datetime import datetime

from flask_socketio import emit

users = []

from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send, emit
import json
import pytz
import os

HISTORY_FILE = "messages.json"



app = Flask(__name__)
app.secret_key = "secret123"

socketio = SocketIO(app, async_mode='threading')

users_db = { 
    "Aero": {"pwd": "7462", "avatar": "a1.png"},
    "Astrolex": {"pwd": "6700", "avatar": "a2.png"},
    "Lepro2.0": {"pwd": "67", "avatar": "a3.png"},
    "Lily": {"pwd": "lily001", "avatar": "a4.png"}
}

@app.route("/", methods=["GET", "POST"])
def login():
    avatars = os.listdir("static/avatars")

    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")
        avatar = request.form.get("avatar")

        if user in users_db and users_db[user]["pwd"] == pwd:
            session["logged_in"] = True
            session["user"] = user
            session["avatar"] = avatar  # 👈 IMPORTANT

            return redirect("/chat")

    return render_template("login.html", avatars=avatars)

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
    avatar = session.get("avatar")

    messages = load_messages()

    paris = pytz.timezone("Europe/Paris")
    time = datetime.now(paris).strftime("%H:%M")

    data = f"{time}|{user}|{avatar}|{msg}"

    messages.append(data)
    messages = messages[-100:]

    save_messages(messages)

    send(data, broadcast=True)

@socketio.on("image")
def handle_image(data):
    user = session.get("user")

    paris = pytz.timezone("Europe/Paris")
    time = datetime.now(paris).strftime("%H:%M")

    messages = load_messages()

    # on ajoute un tag spécial [img]
    msg = f"{time}|{user}|[img]{data}"

    messages.append(msg)
    messages = messages[-100:]

    save_messages(messages)

    emit("message", msg, broadcast=True)

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
