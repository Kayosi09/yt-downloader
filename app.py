from flask import Flask, render_template, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

# Ensure download folder exists
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html', message='')

@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    try:
        unique_id = str(uuid.uuid4())
        output_template = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s")
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return render_template('index.html', message=f"Error: {str(e)}")

# Entry point for Gunicorn & development server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
