from flask import Flask, request, jsonify, render_template
import yt_dlp  # ← ここが必須（yt-dlp パッケージ）
import os
import re
import tempfile

app = Flask(__name__, template_folder="../templates")


def normalize_url(url: str, replace_x: bool = True) -> str:
    if replace_x:
        url = re.sub(r"https?://(www\.)?x\.com", "https://twitter.com", url)
    return url


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST"])
def download_api():
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

        return jsonify({
            "status": "ok",
            "filename": os.path.basename(filename)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Vercel用
app = app
