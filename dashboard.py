from flask import Flask, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import os

app = Flask(__name__)

# ---------------------
# Spotify API setup
# ---------------------
CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = "https://spotinaz-695626b39531.herokuapp.com/spotify_callback"

SCOPE = "user-read-recently-played user-top-read user-read-playback-state"

auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_handler=MemoryCacheHandler()  # <<< TEK VE KRİTİK DÜZELTME
)

sp = spotipy.Spotify(auth_manager=auth_manager)

# ---------------------
# Helper functions
# ---------------------
def get_current_track():
    try:
        current = sp.current_playback()
        if current and current.get("item"):
            track = current["item"]
            return (
                track["name"],
                track["artists"][0]["name"],
                f"https://open.spotify.com/embed/track/{track['id']}"
            )
    except:
        pass
    return "Şu anda çalan parça yok", "", ""

def get_top_artists(limit=5):
    try:
        data = sp.current_user_top_artists(limit=limit, time_range="short_term")
        return [(i + 1, a["name"]) for i, a in enumerate(data["items"])]
    except:
        return []

def get_top_tracks(limit=10):
    try:
        data = sp.current_user_top_tracks(limit=limit, time_range="short_term")
        return [(i + 1, t["name"]) for i, t in enumerate(data["items"])]
    except:
        return []

def get_daily_average_listening():
    return "2 saat 45 dakika"

# ---------------------
# Routes
# ---------------------
@app.route("/")
def dashboard():
    track_name, track_artist, track_embed = get_current_track()
    top_artists = get_top_artists()
    top_tracks = get_top_tracks()
    daily_avg = get_daily_average_listening()

    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spotify Dashboard</title>
        <style>
            body { background:#121212; color:white; font-family:sans-serif; margin:0 }
            .container { max-width:600px; margin:auto; padding:20px }
            .card { background:#1e1e1e; margin:12px 0; padding:15px;
                    border-radius:10px; box-shadow:0 4px 8px rgba(0,0,0,.3) }
            table { width:100% }
            td { padding:4px }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="background:linear-gradient(90deg,#1DB954,#1ed760);
                       -webkit-background-clip:text;color:transparent;">
                Spotify Dashboard of Elif Naz
            </h1>
            <p>Çöplüğüme hoş geldin</p>

            <div class="card">
                <h2>Şu anda çalıyor</h2>
                <p>{{track_name}} {{track_artist}}</p>
                {% if track_embed %}
                <iframe src="{{track_embed}}" width="100%" height="80"
                        frameborder="0" allow="encrypted-media"></iframe>
                {% endif %}
            </div>

            <div class="card">
                <h2>Top 5 Artists</h2>
                <table>
                {% for n, a in top_artists %}
                    <tr><td>{{n}}.</td><td>{{a}}</td></tr>
                {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>Top 10 Songs</h2>
                <table>
                {% for n, t in top_tracks %}
                    <tr><td>{{n}}.</td><td>{{t}}</td></tr>
                {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>Günlük Ortalama Dinleme Süresi</h2>
                <p>{{daily_avg}}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(
        html,
        track_name=track_name,
        track_artist=track_artist,
        track_embed=track_embed,
        top_artists=top_artists,
        top_tracks=top_tracks,
        daily_avg=daily_avg
    )

# ---------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
