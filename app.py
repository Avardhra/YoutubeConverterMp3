import os
import uuid
import zipfile
import json
import threading
import time
import shutil
import subprocess
import sys
from flask import Flask, request, send_from_directory, jsonify, Response
from flask_cors import CORS
import yt_dlp

# Paksa update yt-dlp agar engine selalu terbaru
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
except Exception as e:
    print(f"Update error: {e}")

app = Flask(__name__, static_url_path='', static_folder='.', template_folder='.')
CORS(app, resources={r"/*": {"origins": "*"}})

# Konfigurasi Path untuk Railway
BASE_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.chmod(DOWNLOAD_DIR, 0o777)

# LOGIKA COOKIES
env_cookies = os.environ.get("YT_COOKIES")
cookie_path = os.path.join(BASE_DIR, 'cookies.txt')

if env_cookies:
    with open(cookie_path, 'w') as f:
        f.write(env_cookies)
    print(f"✅ Cookies file created: {cookie_path}")
else:
    print("⚠️ Warning: YT_COOKIES environment variable is not set!")

active_sessions = {}

class ProgressTracker:
    def __init__(self, session_id, total_files):
        self.session_id = session_id
        self.total = total_files
        self.current = 0
        self.files = []
        self.status = "Menyiapkan..."
        self.title = ""
        self.is_complete = False

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/process', methods=['POST'])
def process_videos():
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({"error": "Tidak ada URL"}), 400

    session_id = str(uuid.uuid4())
    session_path = os.path.join(DOWNLOAD_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    tracker = ProgressTracker(session_id, len(urls))
    active_sessions[session_id] = tracker

    def download_worker():
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '128', # 128kbps lebih hemat RAM daripada 192kbps
                }],
                'nocheckcertificate': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'source_address': '0.0.0.0', # Penting untuk stabilitas IP di Railway/HF
                'quiet': True,
                'no_warnings': True,
            }

            if os.path.exists(cookie_path):
                ydl_opts['cookiefile'] = cookie_path

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                for i, url in enumerate(urls):
                    tracker.title = f"Lagu {i+1}/{len(urls)}"
                    tracker.status = "Mengunduh..."
                    try:
                        for attempt in range(3):
                            try:
                                ydl.download([url])
                                break
                            except Exception as e:
                                print(f"Retry {attempt+1}: {e}")
                                time.sleep(3)
                        tracker.current += 1
                    except Exception as e:
                        print(f"Error downloading {url}: {e}")
                        tracker.current += 1 

            time.sleep(3)
            mp3_files = [f for f in os.listdir(session_path) if f.endswith('.mp3')]
            tracker.files = [{"name": f, "url": f"/get-file/{session_id}/{f}"} for f in mp3_files]
            
            if tracker.files:
                create_zip(session_id, tracker.files)
                time.sleep(3) # Beri napas ke server untuk nulis file ke disk
            tracker.status = "✅ Selesai!"
            tracker.is_complete = True

        except Exception as e:
            tracker.status = f"❌ Error: {str(e)}"
            tracker.is_complete = True
        finally:
            threading.Timer(600.0, cleanup_session, args=[session_id]).start()

    thread = threading.Thread(target=download_worker)
    thread.daemon = True
    thread.start()

    return Response(process_session(session_id), mimetype='text/event-stream')

def progress_hook(d, tracker):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '0%')
        tracker.status = f"📥 Mengunduh: {percent}"
    elif d['status'] == 'finished':
        tracker.status = "🎵 Mengonversi ke MP3..."

def process_session(session_id):
    while True:
        tracker = active_sessions.get(session_id)
        if not tracker: break
        progress_data = {'type': 'progress', 'current': tracker.current, 'total': tracker.total, 'title': tracker.title, 'status': tracker.status}
        yield f"data: {json.dumps(progress_data)}\n\n"
        if tracker.is_complete:
            final_data = {'type': 'complete', 'files': tracker.files, 'zip_url': f'/download-zip/{session_id}', 'total': tracker.total}
            yield f"data: {json.dumps(final_data)}\n\n"
            break
        time.sleep(1)

@app.route('/get-file/<session_id>/<path:filename>')
def get_file(session_id, filename):
    return send_from_directory(os.path.join(DOWNLOAD_DIR, session_id), filename, as_attachment=True)

@app.route('/download-zip/<session_id>')
def download_zip(session_id):
    zip_path = os.path.join(DOWNLOAD_DIR, f"{session_id}.zip")
    if os.path.exists(zip_path):
        return send_from_directory(DOWNLOAD_DIR, f"{session_id}.zip", as_attachment=True)
    return "File ZIP tidak ditemukan", 404

def create_zip(session_id, files):
    zip_path = os.path.join(DOWNLOAD_DIR, f"{session_id}.zip")
    session_path = os.path.join(DOWNLOAD_DIR, session_id)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in files:
            file_path = os.path.join(session_path, file_info['name'])
            if os.path.exists(file_path):
                zipf.write(file_path, file_info['name'])

def cleanup_session(session_id):
    try:
        if session_id in active_sessions: del active_sessions[session_id]
        shutil.rmtree(os.path.join(DOWNLOAD_DIR, session_id), ignore_errors=True)
        zip_file = os.path.join(DOWNLOAD_DIR, f"{session_id}.zip")
        if os.path.exists(zip_file): os.remove(zip_file)
    except Exception as e: print(f"Cleanup error: {e}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port)