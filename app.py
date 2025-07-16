from flask import Flask, render_template, request, send_file, jsonify, Response
import yt_dlp
import uuid
import os
import threading
import json

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
progress_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.json.get('url')
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({'title': info.get('title'), 'thumbnail': info.get('thumbnail')})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download_progress')
def download_progress():
    url = request.args.get('url')
    file_format = request.args.get('format')
    download_id = str(uuid.uuid4())
    progress_data[download_id] = {'progress': 0}

    def download_and_stream():
        output_file = os.path.join(DOWNLOAD_FOLDER, f"{download_id}.%(ext)s")
        opts = {
            'outtmpl': output_file,
            'format': 'bestaudio/best' if file_format == 'mp3' else 'bestvideo+bestaudio/best',
            'merge_output_format': file_format,
            'progress_hooks': [lambda d: update_progress(download_id, d)],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }] if file_format == 'mp3' else []
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                final_filename = filename if file_format == 'mp4' else filename.rsplit('.', 1)[0] + '.mp3'
                progress_data[download_id]['status'] = 'done'
                progress_data[download_id]['filename'] = final_filename
        except Exception as e:
            progress_data[download_id]['status'] = 'error'
            progress_data[download_id]['message'] = str(e)

    threading.Thread(target=download_and_stream).start()

    def event_stream():
        while True:
            data = progress_data[download_id]
            yield f"data: {json.dumps(data)}\n\n"
            if data.get('status') in ['done', 'error']:
                break
            import time; time.sleep(1)

    return Response(event_stream(), mimetype='text/event-stream')

def update_progress(download_id, d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        downloaded = d.get('downloaded_bytes', 0)
        percent = int((downloaded / total) * 100) if total else 0
        progress_data[download_id]['progress'] = percent

@app.route('/download_file')
def download_file():
    filename = request.args.get('filename')
    try:
        response = send_file(filename, as_attachment=True)
        threading.Thread(target=lambda: (os.remove(filename) if os.path.exists(filename) else None)).start()
        return response
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
