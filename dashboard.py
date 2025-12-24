from flask import Flask, redirect, request, render_template_string, session, url_for
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

SCOPE = 'user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played'

# =========================
# ROUTES
# =========================
@app.route('/')
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

@app.route('/spotify_callback')
def spotify_callback():
    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code, check_cache=False)

    # Token bilgisini session'a kaydet
    session['token_info'] = token_info
    return redirect(url_for('dashboard'))

def get_spotify_client():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    sp_oauth = SpotifyOAuth(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            redirect_uri=REDIRECT_URI,
                            scope=SCOPE)
    # Token süresi dolmuşsa yenile
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])
    return sp

@app.route('/dashboard')
def dashboard():
    sp = get_spotify_client()
    if not sp:
        return redirect(url_for('login'))

    user = sp.current_user()
    display_name = user['display_name']
    email = user['email']
    profile_img = user['images'][0]['url'] if user['images'] else ''

    # =========================
    # Top Artists
    # =========================
    top_artists_data = sp.current_user_top_artists(limit=5, time_range='medium_term')
    artist_names = [artist['name'] for artist in top_artists_data['items']]
    artist_imgs = [artist['images'][0]['url'] for artist in top_artists_data['items']]
    artist_pairs = list(zip(artist_imgs, artist_names))

    # =========================
    # Şu anda çalan
    # =========================
    current_playing = sp.current_user_playing_track()
    if current_playing and current_playing.get("item"):
        track_name = current_playing['item']['name']
        track_artist = current_playing['item']['artists'][0]['name']
        track_embed_url = f"https://open.spotify.com/embed/track/{current_playing['item']['id']}"
        progress_ms = current_playing['progress_ms']
        duration_ms = current_playing['item']['duration_ms']
        is_playing = current_playing['is_playing']
        progress_percent = int(progress_ms / duration_ms * 100)
        listened_time = str(datetime.timedelta(milliseconds=progress_ms))
    else:
        track_name = "Şu an çalan parça yok"
        track_artist = ""
        track_embed_url = ""
        progress_percent = 0
        is_playing = False
        listened_time = "0:00"

    # =========================
    # Bu haftanın top 10 parçaları
    # =========================
    recent_tracks_data = sp.current_user_top_tracks(limit=10, time_range='short_term')
    top_tracks = []
    for item in recent_tracks_data['items']:
        name = item['name']
        artist = item['artists'][0]['name']
        duration_ms = item['duration_ms']
        duration = str(datetime.timedelta(milliseconds=duration_ms))
        top_tracks.append((name, artist, duration))

    # =========================
    # Dashboard render
    # =========================
    return render_template_string("""
    <html>
    <head>
        <title>Spotify Dashboard</title>
        <style>
            body {background:#121212;color:white;font-family:sans-serif;margin:0;padding:0;}
            .container {display:flex; flex-wrap:wrap; justify-content:center;margin-top:20px;}
            .card {background:#1e1e1e;border-radius:10px;padding:15px;margin:10px;width:250px;text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.3);}
            img {width:100%; border-radius:10px;}
            table {width:100%; border-collapse:collapse;}
            th, td {padding:8px;text-align:left;border-bottom:1px solid #333;}
        </style>
    </head>
    <body>
        <h1 style="text-align:center;background:linear-gradient(90deg,#1DB954,#1ed760);-webkit-background-clip:text;color:transparent;">
            Spotify Dashboard of Elif Naz
        </h1>
        <p style="text-align:center;">Çöplüğüme hoş geldin!</p>
        <div class="container">
            <div class="card">
                <h2>{{display_name}}</h2>
                <p>{{email}}</p>
                {% if profile_img %}<img src="{{profile_img}}">{% endif %}
            </div>

            {% for artist_img, artist_name in artist_pairs %}
            <div class="card">
                <img src="{{artist_img}}">
                <h3>{{artist_name}}</h3>
            </div>
            {% endfor %}

            <div class="card">
                <h3>Şu anda bunu dinliyorum</h3>
                <p>{{track_name}} - {{track_artist}}</p>
                <p>Dinlediğim süre: {{listened_time}}</p>
                {% if track_embed_url %}
                <iframe src="{{track_embed_url}}" width="300" height="80" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
                <div style="background:#333;border-radius:10px;">
                    <div style="background:#1DB954;width:{{progress_percent}}%;height:15px;border-radius:10px;"></div>
                </div>
                <p>{{'Çalıyor' if is_playing else 'Duraklatıldı'}}</p>
                {% endif %}
            </div>

            <div class="card" style="width:520px;">
                <h3>Bu haftanın top 10 parçaları</h3>
                <table>
                    <tr><th>Parça</th><th>Sanatçı</th><th>Süre</th></tr>
                    {% for name, artist, duration in top_tracks %}
                    <tr><td>{{name}}</td><td>{{artist}}</td><td>{{duration}}</td></tr>
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
    listened_time=listened_time,
    top_tracks=top_tracks
    )

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
