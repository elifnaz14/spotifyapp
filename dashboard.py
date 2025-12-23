from flask import Flask, redirect, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os, json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

TOKEN_FILE = "token.json"

sp_oauth = SpotifyOAuth(
    client_id=os.environ.get("9f51e301cf594158b80107b2b4bf54ce"),
    client_secret=os.environ.get("ff7a063fc03c4086a05f1a05f511fa40"),
    redirect_uri=os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback"),
    scope="""
    user-read-currently-playing
    user-read-recently-played
    user-top-read
    """
)

def save_token(t): open(TOKEN_FILE,"w").write(json.dumps(t))
def load_token(): return json.loads(open(TOKEN_FILE).read()) if os.path.exists(TOKEN_FILE) else None
def safe(fn, fallback=None):
    try: return fn()
    except: return fallback

@app.route("/")
def index():
    if load_token(): return redirect("/dashboard")
    return f"""
    <html>
    <body style="background:#121212;color:white;
    display:flex;align-items:center;justify-content:center;height:100vh">
    <a href="{sp_oauth.get_authorize_url()}"
       style="background:#1DB954;color:black;
       padding:16px 32px;border-radius:40px;
       font-weight:600;text-decoration:none">
       Spotify ile giriş
    </a>
    </body>
    </html>
    """

@app.route("/spotify_callback")
def spotify_callback():
    save_token(sp_oauth.get_access_token(request.args.get("code")))
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    token = load_token()
    if not token: return redirect("/")

    sp = spotipy.Spotify(auth=token["access_token"])

    current = safe(lambda: sp.current_user_playing_track())
    recent = safe(lambda: sp.current_user_recently_played(limit=50), {"items":[]})
    top_tracks = safe(lambda: sp.current_user_top_tracks(limit=10, time_range="short_term"), {"items":[]})
    top_artists = safe(lambda: sp.current_user_top_artists(limit=5, time_range="short_term"), {"items":[]})

    # şu anda / son dinlenen
    track_id = None
    track_name = ""
    artist_name = ""

    if current and current.get("item"):
        item = current["item"]
        track_id = item["id"]
        track_name = item["name"]
        artist_name = ", ".join(a["name"] for a in item["artists"])
    elif recent["items"]:
        item = recent["items"][0]["track"]
        track_id = item["id"]
        track_name = item["name"]
        artist_name = ", ".join(a["name"] for a in item["artists"])

    # dinleme süresi (yaklaşık, bu hafta)
    total_ms = sum(i["track"]["duration_ms"] for i in recent["items"])
    total_minutes = round(total_ms / 60000)

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Spotify Dashboard of Elif Naz</title>

<style>
body {{
    margin:0;
    font-family:-apple-system,BlinkMacSystemFont;
    background:#121212;
    color:#eaeaea;
}}
.container {{
    max-width:900px;
    margin:auto;
    padding:24px;
}}
h1 {{
    margin-bottom:6px;
}}
.subtitle {{
    color:#b3b3b3;
    margin-bottom:32px;
}}
.card {{
    background:#181818;
    border-radius:16px;
    padding:20px;
    margin-bottom:24px;
    transition:transform .2s;
}}
.card:hover {{
    transform:translateY(-2px);
}}
table {{
    width:100%;
    border-collapse:collapse;
}}
td {{
    padding:10px 6px;
    border-bottom:1px solid #2a2a2a;
    font-size:14px;
}}
.small {{
    color:#b3b3b3;
    font-size:13px;
}}
iframe {{
    border-radius:12px;
    width:100%;
    height:80px;
    border:none;
}}
</style>
</head>

<body>
<div class="container">

<h1>Spotify Dashboard of Elif Naz</h1>
<div class="subtitle">çöplüğüme hoş geldin</div>

<div class="card">
<b>Şu anda bunu dinliyorum</b>
<div class="small">{track_name} – {artist_name}</div><br>
{"<iframe src='https://open.spotify.com/embed/track/"+track_id+"'></iframe>" if track_id else ""}
</div>

<div class="card">
<b>Bu hafta en çok dinlediğim sanatçılar</b>
<table>
{''.join(f"<tr><td>{i+1}. {a['name']}</td></tr>" for i,a in enumerate(top_artists["items"]))}
</table>
</div>

<div class="card">
<b>Bu hafta en çok dinlediğim parçalar</b>
<table>
{''.join(f"<tr><td>{i+1}. {t['name']} – {t['artists'][0]['name']}</td></tr>" for i,t in enumerate(top_tracks["items"]))}
</table>
</div>

<div class="card">
<b>Bu hafta Spotify’da geçirdiğim süre</b>
<div class="small">{total_minutes} dakika</div>
</div>

</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True)
