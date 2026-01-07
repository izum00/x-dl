from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import re
import tempfile
import threading

app = Flask(__name__, template_folder="../templates")

# 直近のファイルパスを保持
LAST_FILE_PATH = None


def normalize_url(url: str, replace_x: bool = True) -> str:
    if replace_x:
        url = re.sub(r"https?://(www\.)?x\.com", "https://twitter.com", url)
    return url


def delete_file_later(path: str, delay: int = 120):
    def _delete():
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f"[AUTO DELETE] deleted: {path}")
        except Exception as e:
            print(f"[AUTO DELETE ERROR] {e}")

    timer = threading.Timer(delay, _delete)
    timer.start()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def download_api():
    global LAST_FILE_PATH

    data = request.json
    url = data.get("url")
    replace_x = data.get("replace_x", True)

    if not url:
        return jsonify({"error": "url is required"}), 400

    url = normalize_url(url, replace_x)

    tmp_dir = tempfile.mkdtemp()

    ydl_opts = {
        "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
        "format": "best",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        LAST_FILE_PATH = filename

        # ★ ここで 60秒後削除を予約
        delete_file_later(filename, delay=60)

        return jsonify({
            "status": "ok",
            "filename": os.path.basename(filename),
            "download_url": "/api/file",
            "expire_seconds": 120
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/file", methods=["GET"])
def get_file():
    global LAST_FILE_PATH

    if not LAST_FILE_PATH or not os.path.exists(LAST_FILE_PATH):
        return jsonify({"error": "file not found or expired"}), 404

    return send_file(LAST_FILE_PATH, as_attachment=True)


# Vercel用
app = app
