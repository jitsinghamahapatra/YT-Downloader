from flask import Flask, request, jsonify, send_file, send_from_directory, after_this_request
from flask_cors import CORS
import yt_dlp
import os
import re

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

COOKIE_FILE = "cookies.txt"  # optional


# === Serve frontend ===
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# === URL detector ===
def detect_url_type(url: str):
    """Detect whether it's a YouTube video, playlist, or invalid URL."""
    if not url or not isinstance(url, str):
        return "invalid"

    url = url.strip()

    # YouTube playlist link
    if "list=" in url and ("youtube.com" in url or "youtu.be" in url):
        return "playlist"

    # YouTube normal video link
    if re.search(r"(youtu\.be/|youtube\.com/watch\?v=)", url):
        return "video"

    # Not a YouTube URL
    return "invalid"


# === Get formats ===
@app.route('/api/formats')
def get_formats():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    url_type = detect_url_type(url)
    if url_type == "playlist":
        return jsonify({'error': 'Playlists are not supported. Please use a single video URL.'}), 400
    elif url_type == "invalid":
        return jsonify({'error': 'Invalid or unsupported URL. Please enter a YouTube video link.'}), 400

    # Clean URL (remove junk parameters like ?si= or &pp=)
    url = url.split('&')[0].split('?si=')[0]

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'retries': 2,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/141.0.0.0 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not info or 'formats' not in info:
            return jsonify({'error': 'Could not fetch formats. Try another link.'}), 400

        formats = []
        seen = set()
        for f in info.get('formats', []):
            if not f:
                continue
            res = f.get('height')
            ext = f.get('ext')
            fps = f.get('fps')
            codec = f.get('vcodec')
            if codec != 'none' and (res, ext) not in seen:
                seen.add((res, ext))
                formats.append({
                    'format_id': f.get('format_id'),
                    'ext': ext,
                    'resolution': f"{res}p" if res else 'unknown',
                    'fps': fps,
                    'vcodec': codec
                })

        # Add audio-only
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

    except yt_dlp.utils.DownloadError as e:
        print("YT_DLP ERROR:", e)
        return jsonify({'error': 'Invalid or private YouTube URL.'}), 400
    except Exception as e:
        print("FORMAT ERROR:", e)
        return jsonify({'error': f'Failed to fetch formats: {str(e)}'}), 500


# === Download route ===
@app.route('/api/download')
def download_video():
    url = request.args.get('url')
    format_id = request.args.get('format_id')

    if not url or not format_id:
        return jsonify({'error': 'Missing URL or format_id'}), 400

    if detect_url_type(url) != "video":
        return jsonify({'error': 'Only single YouTube video URLs are supported.'}), 400

    url = url.split('&')[0]

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
            'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        }
    else:
        ydl_opts = {
            'format': f'{format_id}+bestaudio/best',
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
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
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
