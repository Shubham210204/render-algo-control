import eventlet
eventlet.monkey_patch()

import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import subprocess
import threading
import os
import signal

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
app.secret_key = "your-secret-key"

process = None
logs = []  # Store logs in memory
is_running = False

# ---------------- LOGIN ROUTES ---------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Simple hardcoded login check
        if username == os.getenv("username") and password == os.getenv("password"):
            session["user"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")
    
    return render_template("login.html")

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ---------------- SOCKET.IO EVENTS ---------------- #
@socketio.on('connect')
def on_connect():
    """When a user connects, send all stored logs."""
    for log in logs:
        socketio.emit('log', log)

@socketio.on('start_script')
def start_script():
    global process, is_running
    if process is None or process.poll() is not None:
        # Do not clear logs here — they persist until user manually clears
        is_running = True
        log_message("✅ Script started...")

        process = subprocess.Popen(
            ["python", "-u", "algo.py"],  # Unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        threading.Thread(target=stream_logs, args=(process.stdout,), daemon=True).start()
    else:
        log_message("⚠ Script is already running.")

def stream_logs(pipe):
    """Read process output line-by-line, store and send."""
    for line in pipe:
        log_message(line.strip())

@socketio.on('stop_script')
def stop_script():
    global process, is_running
    if process and process.poll() is None:
        os.kill(process.pid, signal.SIGTERM)
        is_running = False
        log_message("🛑 Script stopped.")
    else:
        log_message("⚠ No running script.")

@socketio.on('clear_logs')
def clear_logs():
    """Clear all stored logs and notify clients."""
    global logs
    logs = []
    socketio.emit('clear_logs')  # Let frontend know to clear display

# ---------------- HELPER FUNCTION ---------------- #
def log_message(message):
    """Store logs in memory and emit to clients."""
    logs.append(message)
    socketio.emit('log', message)

# ---------------- MAIN ---------------- #
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
