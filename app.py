@app.route('/download', methods=['POST'])
def download():
    url = request.form['url']
    file_format = request.form['format']
    try:
        unique_id = str(uuid.uuid4())
        ext = 'mp4' if file_format == 'mp4' else 'mp3'
        output_template = os.path.join(DOWNLOAD_FOLDER, f"{unique_id}.%(ext)s")

        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestaudio/best' if ext == 'mp3' else 'bestvideo+bestaudio/best',
            'merge_output_format': ext,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if ext == 'mp3' else []
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return render_template('index.html', message=f"Error: {str(e)}")
