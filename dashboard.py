from flask import Flask, redirect, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objs as go
from plotly.offline import plot
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

TOKEN_FILE = "token.json"

sp_oauth = SpotifyOAuth(
    client_id=os.environ.get("9f51e301cf594158b80107b2b4bf54ce"),
    client_secret=os.environ.get("ff7a063fc03c4086a05f1a05f511fa40"),
    redirect_uri=os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback"),
    scope="user-top-read user-read-recently-played user-read-currently-playing"
)

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None

def safe(call, fallback=None):
    try:
        return call()
    except:
        return fallback

@app.route("/")
def index():
    token = load_token()
    if token:
        return redirect("/dashboard")

    auth_url = sp_oauth.get_authorize_url()
    return f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{
          background:#121212;
          color:white;
          display:flex;
          align-items:center;
          justify-content:center;
          height:100vh;
          font-family:Arial;
        }}
        a {{
          background:#1DB954;
          padding:18px 30px;
          border-radius:30px;
          text-decoration:none;
          color:black;
          font-weight:bold;
          font-size:18px;
        }}
      </style>
    </head>
    <body>
      <a href="{auth_url}">Spotify ile Giriş</a>
    </body>
    </html>
    """

@app.route("/spotify_callback")
def spotify_callback():
    token_info = sp_oauth.get_access_token(request.args.get("code"))
    save_token(token_info)
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    token = load_token()
    if not token:
        return redirect("/")

    sp = spotipy.Spotify(auth=token["access_token"])

    top_tracks = safe(lambda: sp.current_user_top_tracks(limit=10), {"items":[]})
    top_artists = safe(lambda: sp.current_user_top_artists(limit=5), {"items":[]})
    recent = safe(lambda: sp.current_user_recently_played(limit=1), {"items":[]})
    current = safe(lambda: sp.current_user_playing_track(), None)

    track_names = [t["name"] for t in top_tracks["items"]]
    track_pop = [t["popularity"] for t in top_tracks["items"]]

    bar = plot({
        "data":[go.Bar(x=track_names, y=track_pop)],
        "layout":go.Layout(
            title="Top 10 Şarkı",
            paper_bgcolor="#121212",
            plot_bgcolor="#121212",
            font=dict(color="white")
        )
    }, output_type="div", include_plotlyjs="cdn")

    artist_cards = ""
    for a in top_artists["items"]:
        img = a["images"][0]["url"] if a["images"] else ""
        artist_cards += f"""
        <div class="artist">
            <img src="{img}">
            <p>{a["name"]}</p>
        </div>
        """

    embed = ""
    if recent and recent["items"]:
        tid = recent["items"][0]["track"]["id"]
        embed = f"""
        <iframe src="https://open.spotify.com/embed/track/{tid}"
        width="100%" height="80" frameborder="0"></iframe>
        """

    now_playing = ""
    if current and current.get("item"):
        now_playing = f"""
        <p>🎧 Şu an çalıyor:</p>
        <strong>{current["item"]["name"]}</strong>
        """

    return f"""
    <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body {{
          background:#121212;
          color:white;
          font-family:Arial;
          margin:0;
          padding:15px;
        }}
        .card {{
          background:#181818;
          padding:15px;
          border-radius:18px;
          margin-bottom:20px;
        }}
        .artists {{
          display:flex;
          overflow-x:auto;
          gap:10px;
        }}
        .artist {{
          min-width:120px;
          text-align:center;
        }}
        .artist img {{
          width:100%;
          border-radius:10px;
        }}
        h2 {{ color:#1DB954; }}
      </style>
    </head>
    <body>

      <div class="card">
        <h2>Now</h2>
        {now_playing or "Şu an veri yok"}
        {embed}
      </div>

      <div class="card">
        <h2>Top Artists</h2>
        <div class="artists">
          {artist_cards}
        </div>
      </div>

      <div class="card">
        {bar}
      </div>

    </body>
    </html>
    """

if __name__ == "__main__":
    app.run()
