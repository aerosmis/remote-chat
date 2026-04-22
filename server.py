print("=== BON SERVEUR LANCÉ ===")

from flask import request
users = {}

from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, send
import os

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

@socketio.on('message')
def handle_message(msg):
    if not session.get("logged_in"):
        return

    username = session.get("user")

    users[request.sid] = username
    socketio.emit('users', list(set(users.values())))  # éviter doublons

    send(username + "|" + msg, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in users:
        del users[request.sid]

    socketio.emit('users', list(set(users.values())))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)
