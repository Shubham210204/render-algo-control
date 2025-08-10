from flask import Flask, render_template
from flask_socketio import SocketIO
import subprocess
import threading
import os
import signal

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

process = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_script')
def start_script():
    global process
    if process is None or process.poll() is not None:
        process = subprocess.Popen(
            ["python", "algo.py"],
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
