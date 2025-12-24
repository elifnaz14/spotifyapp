from flask import Flask, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import datetime

app = Flask(__name__)

# Environment Variables (deploy'ta Heroku Config Vars'ta tanımlı olmalı)
CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback")  # Herhangi bir URL, token almak için gerekli ama login yok
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID,
                                                           client_secret=CLIENT_SECRET))

@app.route("/")
def dashboard():
    # 🎵 Şu anda çalan parça (Spotify API ile çalışmak için demo)
    try:
        current_track = sp.current_playback()
        if current_track and current_track.get("item"):
            track_name = current_track['item']['name']
            track_artist = current_track['item']['artists'][0]['name']
            track_embed_url = f"https://open.spotify.com/embed/track/{current_track['item']['id']}"
        else:
            track_name = "Şu an çalan parça yok"
            track_artist = ""
            track_embed_url = ""
    except:
        track_name = "Şu an çalan parça yok"
        track_artist = ""
        track_embed_url = ""

    # 🌟 Top Artists (son 1 hafta)
    top_artists_data = sp.current_user_top_artists(limit=5, time_range='short_term')
    top_artists = [(i+1, artist['name']) for i, artist in enumerate(top_artists_data['items'])]

    # 🎶 Top Songs (son 1 hafta)
    top_tracks_data = sp.current_user_top_tracks(limit=10, time_range='short_term')
    top_tracks = [(i+1, track['name']) for i, track in enumerate(top_tracks_data['items'])]

    # ⏱ Dinleme süresi (ortalama günlük)
    total_minutes = sum([track['duration_ms'] for track in top_tracks_data['items']]) / 60000
    avg_daily = round(total_minutes / 7, 1)

    return render_template_string("""
    <html>
    <head>
        <title>Spotify Dashboard of Elif Naz</title>
        <style>
            body {background:#121212; color:white; font-family:sans-serif; margin:0; padding:0;}
            .header {text-align:center; padding:30px;}
            h1 {background:linear-gradient(90deg,#1DB954,#1ed760); -webkit-background-clip:text; color:transparent; font-size:2.5em; margin:0;}
            p.subtitle {color:#AAAAAA; margin-top:5px;}
            .section {margin:30px auto; width:90%; max-width:600px; background:#1e1e1e; padding:20px; border-radius:12px; box-shadow:0 4px 10px rgba(0,0,0,0.3);}
            h2 {margin-top:0; margin-bottom:10px;}
            table {width:100%; border-collapse:collapse; margin-top:10px;}
            td {padding:8px;}
            tr:nth-child(even) {background: rgba(255,255,255,0.05);}
            .embed-container {position:relative; padding-bottom:80px; height:80px; overflow:hidden;}
            iframe {border:none; width:100%; height:80px;}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Spotify Dashboard of Elif Naz</h1>
            <p class="subtitle">Çöplüğüme hoş geldin</p>
        </div>

        <div class="section">
            <h2>Şu anda bunu dinliyorum</h2>
            <p>{{track_name}} - {{track_artist}}</p>
            {% if track_embed_url %}
            <div class="embed-container">
                <iframe src="{{track_embed_url}}" allow="encrypted-media"></iframe>
            </div>
            {% endif %}
        </div>

        <div class="section">
            <h2>Top Artists (son 1 hafta)</h2>
            <table>
                {% for num, artist in top_artists %}
                <tr><td>{{num}}.</td><td>{{artist}}</td></tr>
                {% endfor %}
            </table>
        </div>

        <div class="section">
            <h2>Top Songs (son 1 hafta)</h2>
            <table>
                {% for num, track in top_tracks %}
                <tr><td>{{num}}.</td><td>{{track}}</td></tr>
                {% endfor %}
            </table>
        </div>

        <div class="section">
            <h2>Ortalama Günlük Dinleme Süresi</h2>
            <p>{{avg_daily}} dakika</p>
        </div>
    </body>
    </html>
    """,
    track_name=track_name,
    track_artist=track_artist,
    track_embed_url=track_embed_url,
    top_artists=top_artists,
    top_tracks=top_tracks,
    avg_daily=avg_daily
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
