from flask import Flask, redirect, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objs as go
from plotly.offline import plot
import os, json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

TOKEN_FILE = "token.json"

sp_oauth = SpotifyOAuth(
    client_id=os.environ.get("9f51e301cf594158b80107b2b4bf54ce"),
    client_secret=os.environ.get("ff7a063fc03c4086a05f1a05f511fa40"),
    redirect_uri=os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback"),
    scope="user-top-read user-read-recently-played user-read-currently-playing"
)

def save_token(t): open(TOKEN_FILE,"w").write(json.dumps(t))
def load_token(): return json.loads(open(TOKEN_FILE).read()) if os.path.exists(TOKEN_FILE) else None
def safe(fn, fb=None):
    try: return fn()
    except: return fb

@app.route("/")
def index():
    if load_token(): return redirect("/dashboard")
    return f"""<html><body style="background:#121212;display:flex;justify-content:center;align-items:center;height:100vh;">
    <a style="background:#1DB954;padding:18px 30px;border-radius:30px;color:black;font-weight:bold;text-decoration:none"
    href="{sp_oauth.get_authorize_url()}">Spotify ile Giriş</a></body></html>"""

@app.route("/spotify_callback")
def spotify_callback():
    save_token(sp_oauth.get_access_token(request.args.get("code")))
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    token = load_token()
    if not token: return redirect("/")

    sp = spotipy.Spotify(auth=token["access_token"])

    recent = safe(lambda: sp.current_user_recently_played(limit=30), {"items":[]})
    top_tracks = safe(lambda: sp.current_user_top_tracks(limit=10, time_range="short_term"), {"items":[]})
    current = safe(lambda: sp.current_user_playing_track(), None)

    # 🎧 embed (şu an çalan > son dinlenen)
    track_id = None
    if current and current.get("item"):
        track_id = current["item"]["id"]
    elif recent["items"]:
        track_id = recent["items"][0]["track"]["id"]

    embed = f"<iframe src='https://open.spotify.com/embed/track/{track_id}' width='100%' height='80'></iframe>" if track_id else "—"

    # 🏆 bu hafta en çok dinlenen
    counts = {}
    for i in recent["items"]:
        name = i["track"]["name"]
        counts[name] = counts.get(name,0)+1
    top_week = max(counts, key=counts.get) if counts else "Veri yok"

    # ⏱️ dinleme süresi (tahmini)
    minutes = sum(i["track"]["duration_ms"] for i in recent["items"])//60000

    # 🎭 mood analysis
    track_ids = [i["track"]["id"] for i in recent["items"][:10]]
    features = safe(lambda: sp.audio_features(track_ids), [])
    if features:
        energy = sum(f["energy"] for f in features if f)/len(features)
        mood = "🔥 Enerjik" if energy > 0.7 else "😌 Chill" if energy > 0.4 else "🌧️ Melankolik"
    else:
        mood = "Analiz yok"

    # 📊 weekly chart
    names = [t["name"] for t in top_tracks["items"]]
    pops = [t["popularity"] for t in top_tracks["items"]]
    chart = plot({
        "data":[go.Bar(x=names, y=pops)],
        "layout":go.Layout(
            title="Bu Haftanın Top Şarkıları",
            paper_bgcolor="var(--bg)",
            plot_bgcolor="var(--bg)",
            font=dict(color="var(--text)")
        )
    }, output_type="div", include_plotlyjs="cdn")

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root {{
 --bg:#121212; --card:#181818; --text:white;
}}
.light {{
 --bg:#f2f2f2; --card:white; --text:#121212;
}}
body {{
 background:var(--bg); color:var(--text);
 font-family:Arial; margin:0; padding:15px;
}}
h1 {{ color:#1DB954; margin-bottom:5px; }}
.sub {{ opacity:.7; margin-bottom:15px; }}
.card {{
 background:var(--card); border-radius:16px;
 padding:12px; margin-bottom:15px;
}}
.toggle {{
 position:fixed; top:15px; right:15px;
 background:#1DB954; border:none;
 border-radius:20px; padding:8px 14px;
}}
</style>
<script>
function toggle(){{document.body.classList.toggle("light")}}
</script>
</head>
<body>

<button class="toggle" onclick="toggle()">🌓</button>

<h1>Spotify Dashboard of Elif Naz</h1>
<div class="sub">çöplüğüme hoş geldin</div>

<div class="card">{embed}</div>

<div class="card">⏱️ Bu hafta yaklaşık <b>{minutes} dk</b> dinledin</div>
<div class="card">🏆 Bu hafta en çok: <b>{top_week}</b></div>
<div class="card">🎭 Mood: <b>{mood}</b></div>

<div class="card">{chart}</div>

</body>
</html>
"""

if __name__ == "__main__":
    app.run()
