import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template,  request, redirect, url_for, session
from flask_socketio import SocketIO
import subprocess
import threading
import os
import signal

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

process = None

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simple authentication check (replace with your logic)
        if username == "admin" and password == "1234":
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

# Index page
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

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
