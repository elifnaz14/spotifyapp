from flask import Flask, redirect, request, render_template_string, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objs as go
from plotly.offline import plot
import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")

# ⚡ Spotify Credentials
CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback")

SCOPE = 'user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played'

# =========================
# Helper: get Spotify client with refreshed token
# =========================
def get_spotify_client():
    token_info = session.get("token_info", None)
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)
    if token_info:
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session["token_info"] = token_info
    return spotipy.Spotify(auth=token_info['access_token'] if token_info else None), token_info

# =========================
# Routes
# =========================
@app.route("/")
def login():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return render_template_string("""
    <html>
    <head><title>Spotify Dashboard</title></head>
    <body style="background:#121212;color:white;text-align:center;font-family:sans-serif;">
        <h1>Spotify Dashboard of Elif Naz</h1>
        <p>Çöplüğüme hoş geldin!</p>
        <a href="{{auth_url}}">
            <button style="padding:15px 30px;font-size:18px;background-color:#1DB954;border:none;border-radius:25px;color:white;cursor:pointer;">
                Spotify ile Giriş Yap
            </button>
        </a>
    </body>
    </html>
    """, auth_url=auth_url)

@app.route("/spotify_callback")
def spotify_callback():
    code = request.args.get("code")
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    sp, token_info = get_spotify_client()
    if not token_info:
        return redirect(url_for("login"))

    # -------------------
    # Kullanıcı Bilgileri
    # -------------------
    user = sp.current_user()
    display_name = user['display_name']
    email = user['email']
    profile_img = user['images'][0]['url'] if user['images'] else ''

    # -------------------
    # Top Artists
    # -------------------
    top_artists_data = sp.current_user_top_artists(limit=5, time_range='medium_term')
    top_artists = []
    artist_names = []
    artist_popularity = []

    for artist in top_artists_data['items']:
        top_artists.append(artist['images'][0]['url'])
        artist_names.append(artist['name'])
        artist_popularity.append(artist['popularity'])

    artist_pairs = list(zip(top_artists, artist_names))

    # -------------------
    # Şu anda çalan
    # -------------------
    current_playing = sp.current_user_playing_track()
    if current_playing and current_playing.get("item"):
        track_name = current_playing['item']['name']
        track_artist = current_playing['item']['artists'][0]['name']
        track_embed_url = f"https://open.spotify.com/embed/track/{current_playing['item']['id']}"
        progress_ms = current_playing['progress_ms']
        duration_ms = current_playing['item']['duration_ms']
        is_playing = current_playing['is_playing']
        progress_percent = int(progress_ms / duration_ms * 100)
        now_playing_prefix = "Şu anda bunu dinliyorum:"
    else:
        track_name = "Şu an çalan parça yok"
        track_artist = ""
        track_embed_url = ""
        progress_percent = 0
        is_playing = False
        now_playing_prefix = ""

    # -------------------
    # Top 10 parçalar
    # -------------------
    recent_tracks_data = sp.current_user_recently_played(limit=10)
    recent_tracks = []
    for item in recent_tracks_data['items']:
        name = item['track']['name']
        artist = item['track']['artists'][0]['name']
        time_played = datetime.datetime.strptime(item['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        recent_tracks.append((name, artist, time_played.strftime("%d %b %H:%M")))

    # -------------------
    # HTML Render
    # -------------------
    return render_template_string("""
    <html>
    <head>
        <title>Spotify Dashboard</title>
        <style>
            body {background:#121212;color:white;font-family:sans-serif;margin:0;padding:0;}
            .container {display:flex; flex-wrap:wrap; justify-content:center;margin-top:20px;}
            .card {background:#1e1e1e;border-radius:10px;padding:15px;margin:10px;width:250px;text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.3);}
            img {width:100%; border-radius:10px;}
            table {width:100%; border-collapse: collapse; margin-top:10px;}
            th, td {padding:8px; text-align:left; border-bottom:1px solid #333;}
            iframe {border-radius:10px;}
        </style>
    </head>
    <body>
        <h1 style="text-align:center;background:linear-gradient(90deg,#1DB954,#1ed760);-webkit-background-clip:text;color:transparent;">
            Spotify Dashboard
        </h1>
        <div class="container">
            <!-- Kullanıcı -->
            <div class="card">
                <h2>{{display_name}}</h2>
                <p>{{email}}</p>
                {% if profile_img %}<img src="{{profile_img}}">{% endif %}
            </div>

            <!-- Top Artists -->
            {% for artist_img, artist_name in artist_pairs %}
            <div class="card">
                <img src="{{artist_img}}">
                <h3>{{artist_name}}</h3>
            </div>
            {% endfor %}

            <!-- Şu anda çalan -->
            <div class="card">
                <h3>{{now_playing_prefix}}</h3>
                <p>{{track_name}} - {{track_artist}}</p>
                {% if track_embed_url %}
                <iframe src="{{track_embed_url}}" width="300" height="80"></iframe>
                <div style="background:#333;border-radius:10px;">
                    <div style="background:#1DB954;width:{{progress_percent}}%;height:15px;border-radius:10px;"></div>
                </div>
                <p>{{'Çalıyor' if is_playing else 'Duraklatıldı'}}</p>
                {% endif %}
            </div>

            <!-- Top 10 parçalar -->
            <div class="card">
                <h3>Bu hafta en çok dinlediğim parçalar</h3>
                <table>
                    <tr><th>Parça</th><th>Sanatçı</th><th>Zaman</th></tr>
                    {% for name, artist, time in recent_tracks %}
                    <tr>
                        <td>{{name}}</td><td>{{artist}}</td><td>{{time}}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>
    </body>
    </html>
    """,
    display_name=display_name,
    email=email,
    profile_img=profile_img,
    artist_pairs=artist_pairs,
    track_name=track_name,
    track_artist=track_artist,
    track_embed_url=track_embed_url,
    progress_percent=progress_percent,
    is_playing=is_playing,
    now_playing_prefix=now_playing_prefix,
    recent_tracks=recent_tracks
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
