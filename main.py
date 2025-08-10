from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import subprocess
import sys

app = Flask(__name__)
app.secret_key = "yoursecretkey"  # Change to a strong secret
socketio = SocketIO(app)

# Dummy credentials (replace with database check if needed)
USERNAME = "admin"
PASSWORD = "1234"

process = None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Your existing socket.io event handlers go here...

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
