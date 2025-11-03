from flask import Flask, request, jsonify, send_file, send_from_directory, after_this_request
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "cookies.txt"  # <-- your exported YouTube cookies


# === Serve frontend ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# === Get available formats ===
@app.route('/api/formats')
def get_formats():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    # Clean URL (remove extra params like ?si=)
    url = url.split('?')[0]

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'retries': 3,
        'nocheckcertificate': True,
        'cookiefile': COOKIE_FILE,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/141.0.0.0 Safari/537.36',
        'http_headers': {
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.youtube.com/',
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen = set()

            for f in info.get('formats', []):
                # Only include video-only or video+audio formats
                res = f.get('height') or f.get('resolution')
                ext = f.get('ext')
                fps = f.get('fps')
                codec = f.get('vcodec')
                if f.get('vcodec') != 'none' and (res, ext) not in seen:
                    seen.add((res, ext))
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': ext,
                        'resolution': f"{res}p" if res else 'unknown',
                        'fps': fps,
                        'vcodec': codec
                    })

            # Add audio-only option
            formats.append({
                'format_id': 'bestaudio',
                'ext': 'mp3',
                'resolution': 'Audio Only',
                'fps': None,
                'vcodec': 'none'
            })

            return jsonify({
                'title': info.get('title', 'Untitled'),
                'formats': formats
            })

    except Exception as e:
        print("FORMAT ERROR:", e)
        return jsonify({'error': str(e)}), 500


# === Download selected format ===
@app.route('/api/download')
def download_video():
    url = request.args.get('url')
    format_id = request.args.get('format_id')

    if not url or not format_id:
        return jsonify({'error': 'Missing URL or format_id'}), 400

    # Clean URL
    url = url.split('?')[0]

    # Force bestvideo+bestaudio for any video selection
    if format_id == 'bestaudio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'retries': 3,
            'nocheckcertificate': True,
            'cookiefile': COOKIE_FILE,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/141.0.0.0 Safari/537.36',
            'http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
            },
        }
    else:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'retries': 3,
            'nocheckcertificate': True,
            'cookiefile': COOKIE_FILE,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/141.0.0.0 Safari/537.36',
            'http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
            },
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_id == 'bestaudio':
                file_path = os.path.splitext(file_path)[0] + '.mp3'

        @after_this_request
        def cleanup(response):
            try:
                os.remove(file_path)
            except Exception:
                pass
            return response

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        print("DOWNLOAD ERROR:", e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

