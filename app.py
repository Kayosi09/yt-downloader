from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from yt_dlp import YoutubeDL
import threading
import os
import uuid
import validators

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return jsonify({"status": "API Running"})


@app.route('/get-thumbnail', methods=['POST'])
def get_thumbnail():
    url = request.form.get('url')
    if not url or not validators.url(url):
        return jsonify({'error': '❗ Invalid URL provided'}), 400

    try:
        ydl_opts = {'quiet': True, 'skip_download': True, 'forcejson': True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'thumbnail': info.get('thumbnail')})
    except Exception as e:
        return jsonify({'error': f'Failed to fetch thumbnail: {str(e)}'}), 500


@socketio.on('start_download')
def handle_start_download(data):
    url = data.get('url')
    format_choice = data.get('format', 'mp4')

    if not url or not validators.url(url):
        emit('progress_update', {'progress': 0, 'error': '❗ Invalid URL provided'})
        return

    download_id = str(uuid.uuid4())
    output_filename = f"{DOWNLOAD_FOLDER}/{download_id}.{format_choice}"

    def progress_hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').replace('%', '').strip()
            try:
                emit('progress_update', {'progress': float(percent)}, broadcast=False)
            except:
                pass
        elif d['status'] == 'finished':
            emit('progress_update', {'progress': 100}, broadcast=False)
            socketio.start_background_task(cleanup_and_notify, output_filename)

    ydl_opts = {
        'outtmpl': output_filename,
        'format': 'bestvideo+bestaudio/best' if format_choice == 'mp4' else 'bestaudio/best',
        'progress_hooks': [progress_hook],
        'merge_output_format': format_choice,
        'quiet': True,
        'noplaylist': True
    }

    def download_task():
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            emit('progress_update', {'progress': 0, 'error': f'❗ Download failed: {str(e)}'})

    threading.Thread(target=download_task).start()


def cleanup_and_notify(filepath):
    # Simulate serving file or notify completion
    socketio.sleep(1)
    # Optionally emit('file_ready', {'filename': os.path.basename(filepath)})
    socketio.sleep(10)
    if os.path.exists(filepath):
        os.remove(filepath)


@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
