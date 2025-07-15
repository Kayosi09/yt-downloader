from flask import Flask, request, send_file, render_template, jsonify
import yt_dlp
import os
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        filename = str(uuid.uuid4()) + '.mp4'
        filepath = os.path.join(DOWNLOAD_DIR, filename)

        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[ext=mp4]/best',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up downloaded file after serving
        try:
            os.remove(filepath)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
