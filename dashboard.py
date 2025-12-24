from flask import Flask, redirect, request, render_template_string, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
import os

# =========================
# APP
# =========================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")  # Heroku'dan alacak

# ⚡ Spotify Env
CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback")

SCOPE = "user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played"

# =========================
# ROUTES
# =========================
@app.route("/")
def login():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=None)  # Heroku'da terminal input istemez
    auth_url = sp_oauth.get_authorize_url()
    return render_template_string("""
    <html>
    <head><title>Spotify Dashboard</title></head>
    <body style="background:#121212;color:white;font-family:sans-serif;text-align:center;">
        <h1 style="color:#1DB954;">Spotify Dashboard of Elif Naz</h1>
        <p style="color:#b3b3b3;">Çöplüğüme hoş geldin</p>
        <a href="{{auth_url}}">
            <button style="padding:12px 25px;font-size:16px;background-color:#1DB954;border:none;border-radius:20px;color:white;cursor:pointer;">
                Spotify ile Giriş Yap
            </button>
        </a>
    </body>
    </html>
    """, auth_url=auth_url)

@app.route("/spotify_callback")
def spotify_callback():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE,
                            cache_path=None)
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code, check_cache=False)
    session["token_info"] = token_info
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    token_info = session.get("token_info")
    if not token_info:
        return redirect(url_for("login"))

    sp = spotipy.Spotify(auth=token_info["access_token"])

    # =========================
    # Şu anda çalan parça
    # =========================
    current_playing = sp.current_user_playing_track()
    if current_playing and current_playing.get("item"):
        track_name = current_playing["item"]["name"]
        track_artist = current_playing["item"]["artists"][0]["name"]
        track_embed = f"https://open.spotify.com/embed/track/{current_playing['item']['id']}"
        progress_ms = current_playing["progress_ms"]
        duration_ms = current_playing["item"]["duration_ms"]
        progress_min_sec = f"{int(progress_ms/60000)}:{int((progress_ms%60000)/1000):02d}"
        duration_min_sec = f"{int(duration_ms/60000)}:{int((duration_ms%60000)/1000):02d}"
        now_playing_text = f"Şu anda bunu dinliyorum: {track_name} - {track_artist}"
    else:
        track_name = ""
        track_artist = ""
        track_embed = ""
        progress_min_sec = "0:00"
        duration_min_sec = "0:00"
        now_playing_text = "Şu anda çalan parça yok"

    # =========================
    # Top Artists
    # =========================
    top_artists_data = sp.current_user_top_artists(limit=10, time_range="medium_term")
    top_artists = [artist["name"] for artist in top_artists_data["items"]]

    # =========================
    # Top Songs
    # =========================
    top_tracks_data = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    top_tracks = [(track["name"], track["artists"][0]["name"]) for track in top_tracks_data["items"]]

    # =========================
    # Dashboard HTML
    # =========================
    return render_template_string("""
    <html>
    <head>
        <title>Spotify Dashboard</title>
        <style>
            body {background:#121212;color:white;font-family:sans-serif;margin:0;padding:0;}
            .container {max-width:700px;margin:auto;padding:20px;}
            h1 {color:#1DB954;text-align:center;}
            p.subtitle {color:#b3b3b3;text-align:center;}
            h2 {border-bottom:1px solid #333;padding-bottom:5px;}
            ul {list-style:none;padding-left:0;}
            li {padding:4px 0;}
            .track {margin:15px 0;padding:10px;background:#1e1e1e;border-radius:10px;}
            iframe {border:none;border-radius:10px;width:100%;height:80px;}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Spotify Dashboard of Elif Naz</h1>
            <p class="subtitle">Çöplüğüme hoş geldin</p>

            <h2>Şu Anda Çalan Parça</h2>
            <div class="track">
                <p>{{now_playing_text}}</p>
                {% if track_embed %}
                <iframe src="{{track_embed}}" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
                <p>Dinleme süresi: {{progress_min_sec}} / {{duration_min_sec}}</p>
                {% endif %}
            </div>

            <h2>Top Artists</h2>
            <ul>
            {% for artist in top_artists %}
                <li>{{artist}}</li>
            {% endfor %}
            </ul>

            <h2>Bu Haftanın Top 10 Parçaları</h2>
            <ul>
            {% for name, artist in top_tracks %}
                <li>{{name}} - {{artist}}</li>
            {% endfor %}
            </ul>
        </div>
    </body>
    </html>
    """, top_artists=top_artists, top_tracks=top_tracks, track_embed=track_embed,
         now_playing_text=now_playing_text, progress_min_sec=progress_min_sec, duration_min_sec=duration_min_sec)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
