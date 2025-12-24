from flask import Flask, render_template_string, session, redirect, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import datetime
import os

# =========================
# APP
# =========================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback")

SCOPE = "user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played"

# =========================
# DASHBOARD ROUTE
# =========================
@app.route("/")
def dashboard():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )

    token_info = session.get("token_info", None)
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

    sp = spotipy.Spotify(auth=token_info["access_token"])

    # ---------- CURRENTLY PLAYING ----------
    current = sp.current_user_playing_track()
    if current and current.get("item"):
        track_name = current["item"]["name"]
        track_artist = current["item"]["artists"][0]["name"]
        track_embed = f"https://open.spotify.com/embed/track/{current['item']['id']}"
        progress_ms = current["progress_ms"]
        duration_ms = current["item"]["duration_ms"]
        progress_percent = int(progress_ms / duration_ms * 100)
    else:
        track_name = "Şu an çalan parça yok"
        track_artist = ""
        track_embed = ""
        progress_percent = 0

    # ---------- TOP ARTISTS 1-5 ----------
    top_artists_data = sp.current_user_top_artists(limit=5, time_range="medium_term")
    top_artists = [(i+1, artist["name"]) for i, artist in enumerate(top_artists_data["items"])]

    # ---------- TOP SONGS 1-10 ----------
    top_tracks_data = sp.current_user_top_tracks(limit=10, time_range="medium_term")
    top_tracks = [(i+1, track["name"], track["artists"][0]["name"]) for i, track in enumerate(top_tracks_data["items"])]

    # ---------- LISTENING TIME ----------
    user_profile = sp.current_user()
    total_played_ms = 0
    recent_tracks = sp.current_user_recently_played(limit=50)
    for item in recent_tracks["items"]:
        total_played_ms += item["track"]["duration_ms"]
    total_played_hours = total_played_ms // (1000 * 60 * 60)

    return render_template_string("""
<html>
<head>
<title>Spotify Dashboard of Elif Naz</title>
<style>
body {background:#121212; color:white; font-family:sans-serif; text-align:center; margin:0; padding:0;}
header {padding:30px 0;}
h1 {font-size:36px; background:linear-gradient(90deg,#1DB954,#1ed760); -webkit-background-clip:text; color:transparent;}
h3 {margin:5px 0; color:#b3b3b3;}
section {margin:20px auto; width:90%; max-width:500px; background:#1e1e1e; padding:15px; border-radius:10px; box-shadow:0 4px 8px rgba(0,0,0,0.2);}
table {width:100%; border-collapse:collapse; margin-top:10px;}
td {padding:8px; text-align:left; border-bottom:1px solid #333;}
.embed-container {margin-top:10px;}
.progress-bar {background:#333; border-radius:10px; height:15px; margin-top:5px;}
.progress {background:#1DB954; height:15px; border-radius:10px;}
</style>
</head>
<body>
<header>
<h1>Spotify Dashboard of Elif Naz</h1>
<h3>çöplüğüme hoş geldin</h3>
</header>

<!-- CURRENTLY PLAYING -->
<section>
<h2>Şu anda bunu dinliyorum</h2>
<p>{{track_name}} - {{track_artist}}</p>
{% if track_embed %}
<div class="embed-container">
<iframe src="{{track_embed}}" width="100%" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>
<div class="progress-bar">
<div class="progress" style="width:{{progress_percent}}%;"></div>
</div>
</div>
{% endif %}
</section>

<!-- TOP ARTISTS -->
<section>
<h2>Top Artists</h2>
<table>
{% for num, artist in top_artists %}
<tr><td>{{num}}.</td><td>{{artist}}</td></tr>
{% endfor %}
</table>
</section>

<!-- TOP SONGS -->
<section>
<h2>Top Songs</h2>
<table>
{% for num, name, artist in top_tracks %}
<tr><td>{{num}}.</td><td>{{name}}</td><td>{{artist}}</td></tr>
{% endfor %}
</table>
</section>

<!-- LISTENING TIME -->
<section>
<h2>Toplam Dinleme Sürem</h2>
<p>{{total_played_hours}} saat</p>
</section>

</body>
</html>
""", track_name=track_name, track_artist=track_artist, track_embed=track_embed, progress_percent=progress_percent,
       top_artists=top_artists, top_tracks=top_tracks, total_played_hours=total_played_hours)

# =========================
# CALLBACK (OAUTH)
# =========================
@app.route("/spotify_callback")
def spotify_callback():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )
    from flask import request
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code, check_cache=False)
    session["token_info"] = token_info
    return redirect(url_for("dashboard"))

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
