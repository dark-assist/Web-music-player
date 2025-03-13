from flask import Flask, request, render_template_string, jsonify, send_file
import yt_dlp
import requests
import re
import os

app = Flask(__name__)

# 🔎 YouTube Search Function
def youtube_search(query):
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers)
    
    # Extract video IDs
    video_ids = re.findall(r'"videoId":"(.*?)"', response.text)
    unique_ids = list(set(video_ids))

    # Extract titles
    titles = re.findall(r'"title":{"runs":\[{"text":"(.*?)"}\]', response.text)
    
    if not unique_ids or not titles:
        return []

    results = [{"title": titles[i], "videoId": unique_ids[i]} for i in range(min(len(titles), len(unique_ids)))]
    return results[:5]  # Sirf top 5 results bhejne ke liye

# 🎵 Home Page (Search Form)
@app.route("/")
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Free Music Player</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #f8f8f8;
            }
            button, input {
                margin: 10px;
                padding: 8px;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background: white;
                margin: 5px;
                padding: 10px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
            }
        </style>
    </head>
    <body>
        <h1>🎵 Free Music Player</h1>
        <input type="text" id="search-box" placeholder="Search for a song...">
        <button onclick="searchSongs()">Search</button>
        <ul id="song-list"></ul>
        <audio id="player" controls></audio>

        <script>
            async function searchSongs() {
                const query = document.getElementById("search-box").value;
                const response = await fetch(`/search?q=${query}`);
                const data = await response.json();
                const songList = document.getElementById("song-list");
                songList.innerHTML = "";

                data.forEach(song => {
                    const li = document.createElement("li");
                    li.innerHTML = `
                        ${song.title} 
                        <button onclick="playSong('${song.videoId}')">▶ Play</button>
                        <a href="/download/${song.videoId}" download>⬇ Download</a>
                    `;
                    songList.appendChild(li);
                });
            }

            async function playSong(videoId) {
                const response = await fetch(`/stream/${videoId}`);
                const data = await response.json();
                document.getElementById("player").src = data.url;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)

# 🎶 Search API
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "Query is required"}), 400

    results = youtube_search(query)
    return jsonify(results)

# 🎧 Stream Song
@app.route("/stream/<video_id>")
def stream(video_id):
    ydl_opts = {"format": "bestaudio/best", "quiet": True, "noplaylist": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        audio_url = info.get("url")

        if not audio_url:
            return jsonify({"error": "Audio not found"}), 404

        return jsonify({"url": audio_url})

# ⬇️ Download Song
@app.route("/download/<video_id>")
def download(video_id):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"downloads/{video_id}.mp3",
        "quiet": True,
    }

    os.makedirs("downloads", exist_ok=True)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    return send_file(f"downloads/{video_id}.mp3", as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
