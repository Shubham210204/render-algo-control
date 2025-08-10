import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO
import subprocess
import threading
import os
import signal

app = Flask(__name__)
app.secret_key = "your-secret-key"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

process = None

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "your-secret-key"  # needed for sessions

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Simple hardcoded login check
        if username == "admin" and password == "1234":
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


@socketio.on('start_script')
def start_script():
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            ["python", "-u", "algo.py"],  # Unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        threading.Thread(target=stream_logs, args=(process.stdout,), daemon=True).start()
        socketio.emit('log', '✅ Script started...')
    else:
        socketio.emit('log', '⚠ Script is already running.')

def stream_logs(pipe):
    for line in pipe:
        socketio.emit('log', line.strip())

@socketio.on('stop_script')
def stop_script():
    global process
    if process and process.poll() is None:
        os.kill(process.pid, signal.SIGTERM)
        socketio.emit('log', '🛑 Script stopped.')
    else:
        socketio.emit('log', '⚠ No running script.')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
