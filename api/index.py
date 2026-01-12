from flask import Flask, request, jsonify, render_template, send_file
import yt_dlp
import os
import re
import tempfile
import threading
from flask_cors import CORS

app = Flask(__name__, template_folder="../templates")
CORS(app)


def normalize_url(url: str, replace_x: bool = True) -> str:
    if replace_x:
        url = re.sub(r"https?://(www\.)?x\.com", "https://twitter.com", url)
    return url


def delete_dir_later(path: str, delay: int = 120):
    def _delete():
        try:
            if os.path.exists(path):
                for f in os.listdir(path):
                    os.remove(os.path.join(path, f))
                os.rmdir(path)
                print(f"[AUTO DELETE] deleted dir: {path}")
        except Exception as e:
            print(f"[AUTO DELETE ERROR] {e}")

    threading.Timer(delay, _delete).start()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def download_api():
    data = request.json or {}
    url = data.get("url")
    replace_x = data.get("replace_x", True)
    audio_only = int(data.get("audio_only", 0))

    if not url:
        return jsonify({"error": "url is required"}), 400

    url = normalize_url(url, replace_x)
    tmp_dir = tempfile.mkdtemp()

    if audio_only == 1:
        format_selector = "bestaudio[ext=m4a]/bestaudio"
    else:
        format_selector = (
            "best[ext=mp4][acodec!=none]/"
            "bestvideo[ext=mp4]/"
            "best"
        )

    ydl_opts = {
        "outtmpl": os.path.join(tmp_dir, "%(title)s.%(ext)s"),
        "format": format_selector,
        "merge_output_format": None,  # FFmpeg禁止
        "quiet": True,
        "no_warnings": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        delete_dir_later(tmp_dir, delay=60)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Vercel用
app = app
