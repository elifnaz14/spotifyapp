from flask import Flask, redirect, request, render_template_string, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objs as go
from plotly.offline import plot
import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ba25b99ecf49effc559dc21a257d35631ad0429c73e09571a664f619c5347d99")  # <-- env'den okunuyor

# 🔹 TEST LOGIN ROUTE
@app.route("/test_login")
def test_login():
    sp_oauth = SpotifyOAuth(
        client_id=os.environ.get("9f51e301cf594158b80107b2b4bf54ce"),
        client_secret=os.environ.get("ff7a063fc03c4086a05f1a05f511fa40"),
        redirect_uri=os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback"),
        scope='user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played'
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# 🔹 DEBUG ROUTE (SECRET_KEY test için)
@app.route("/debug")
def debug():
    return str(app.config["SECRET_KEY"])

# ⚡ Scope
SCOPE = 'user-read-private user-read-email user-top-read user-read-currently-playing user-read-playback-state user-read-recently-played'

# 🔹 LOGIN ROUTE
@app.route('/')
def login():
    sp_oauth = SpotifyOAuth(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        redirect_uri=os.environ.get("REDIRECT_URI"),
        scope=SCOPE
    )
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

# 🔹 SPOTIFY CALLBACK
@app.route('/spotify_callback')
def spotify_callback():
    sp_oauth = SpotifyOAuth(
        client_id=os.environ.get("CLIENT_ID"),
        client_secret=os.environ.get("CLIENT_SECRET"),
        redirect_uri=os.environ.get("REDIRECT_URI"),
        scope=SCOPE
    )

    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('dashboard'))

# 🔹 DASHBOARD
@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    user = sp.current_user()
    display_name = user['display_name']
    email = user['email']
    profile_img = user['images'][0]['url'] if user['images'] else ''

    top_artists_data = sp.current_user_top_artists(limit=5, time_range='medium_term')
    top_artists = []
    artist_names = []
    artist_popularity = []

    for artist in top_artists_data['items']:
        top_artists.append(artist['images'][0]['url'])
        artist_names.append(artist['name'])
        artist_popularity.append(artist['popularity'])

    artist_pairs = list(zip(top_artists, artist_names))

    current_playing = sp.current_user_playing_track()
    if current_playing and current_playing.get("item"):
        track_name = current_playing['item']['name']
        track_artist = current_playing['item']['artists'][0]['name']
        track_embed_url = f"https://open.spotify.com/embed/track/{current_playing['item']['id']}"
        progress_ms = current_playing['progress_ms']
        duration_ms = current_playing['item']['duration_ms']
        is_playing = current_playing['is_playing']
        progress_percent = int(progress_ms / duration_ms * 100)
    else:
        track_name = "Şu an çalan parça yok"
        track_artist = ""
        track_embed_url = ""
        progress_percent = 0
        is_playing = False

    recent_tracks_data = sp.current_user_recently_played(limit=5)
    recent_tracks = []

    for item in recent_tracks_data['items']:
        name = item['track']['name']
        artist = item['track']['artists'][0]['name']
        time_played = datetime.datetime.strptime(item['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        recent_tracks.append((name, artist, time_played.strftime("%d %b %H:%M")))

    bar_fig = go.Figure([go.Bar(x=artist_names, y=artist_popularity, marker_color='green')])
    bar_fig.update_layout(
        title="Top 5 Artist Popülerliği",
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='white'
    )
    bar_div = plot(bar_fig, output_type='div', include_plotlyjs=False)

    pie_fig = go.Figure([go.Pie(labels=artist_names, values=artist_popularity)])
    pie_fig.update_layout(
        title="Top Artist Dağılımı",
        plot_bgcolor='#121212',
        paper_bgcolor='#121212',
        font_color='white'
    )
    pie_div = plot(pie_fig, output_type='div', include_plotlyjs=False)

    return render_template_string("""
    <html>
    <head>
        <title>Spotify Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {background:#121212;color:white;font-family:sans-serif;}
            .container {display:flex; flex-wrap:wrap; justify-content:center;margin-top:20px;}
            .card {background:#1e1e1e;border-radius:10px;padding:15px;margin:10px;width:250px;text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.3);}
            img {width:100%; border-radius:10px;}
        </style>
    </head>
    <body>
        <h1 style="text-align:center;background:linear-gradient(90deg,#1DB954,#1ed760);-webkit-background-clip:text;color:transparent;">
            Spotify Dashboard
        </h1>
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
                <h3>Şu An Çalan</h3>
                <p>{{track_name}} - {{track_artist}}</p>
                {% if track_embed_url %}
                <iframe src="{{track_embed_url}}" width="300" height="80"></iframe>
                <div style="background:#333;border-radius:10px;">
                    <div style="background:#1DB954;width:{{progress_percent}}%;height:15px;border-radius:10px;"></div>
                </div>
                <p>{{'Çalıyor' if is_playing else 'Duraklatıldı'}}</p>
                {% endif %}
            </div>

            <div class="card">{{bar_div | safe}}</div>
            <div class="card">{{pie_div | safe}}</div>
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
    recent_tracks=recent_tracks,
    bar_div=bar_div,
    pie_div=pie_div
    )

# 🔹 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
