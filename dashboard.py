from flask import Flask, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from datetime import datetime
from datetime import timedelta


app = Flask(__name__)

CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")

SCOPE = "user-read-recently-played user-top-read user-read-playback-state"

auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri="http://localhost/", 
    scope=SCOPE
)

def get_spotify_client():
    token_info = auth_manager.refresh_access_token(REFRESH_TOKEN)
    return spotipy.Spotify(auth=token_info["access_token"])

def get_current_track():
    try:
        sp = get_spotify_client()
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
    return "saka yaptim dinlemiyorum", "", ""


def get_top_artists(limit=5):
    try:
        sp = get_spotify_client()
        data = sp.current_user_top_artists(limit=limit, time_range="short_term")
        return [(i + 1, a["name"]) for i, a in enumerate(data["items"])]
    except:
        return []

def get_top_tracks(limit=10):
    try:
        sp = get_spotify_client()
        data = sp.current_user_top_tracks(limit=limit, time_range="short_term")
        return [(i + 1, t["name"]) for i, t in enumerate(data["items"])]
    except:
        return []

def get_recent_tracks(limit=5):
    try:
        print("recently played isteniyor...")
        sp = get_spotify_client()
        data = sp.current_user_recently_played(limit=limit)

        print("recent raw data:", data)

        tracks = []
        for i, item in enumerate(data["items"]):
            played_at = item["played_at"]
            time_str = datetime.fromisoformat(
                played_at.replace("Z", "+00:00")
            ).strftime("%H:%M")

            tracks.append((
                i + 1,
                item["track"]["name"],
                item["track"]["artists"][0]["name"],
                time_str
            ))

        return tracks
    except Exception as e:
        print("recent error:", e)
        return []

@app.route("/")
def dashboard():
    track_name, track_artist, track_embed = get_current_track()
    top_artists = get_top_artists()
    top_tracks = get_top_tracks()
    recent_tracks = get_recent_tracks()

    last_updated = (datetime.utcnow() + timedelta(hours=3)).strftime("%H:%M")




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
            .card h2 {
                font-size: 0.75rem;
                letter-spacing: 1px;
                opacity: 0.6;
                margin-bottom: 6px;
                text-transform: uppercase;
            }
            .card.hero {
                    border: 1px solid rgba(255,255,255,0.25);
                    transform: scale(1.02);
            }
            table { width:100% }
            td { padding:4px }
            .profile-link {
                color: #1DB954;
                text-decoration: none;
                font-weight: 500;
            }

            .profile-link:hover {
                text-decoration: underline;
            }
            .desc {
                margin: 3px 0;
                font-size: 12.5px;
                line-height: 1.35;
                color: #cfcfcf;
            }
            .title {
                font-size: 1.9em;
                line-height: 1.15;
                margin-bottom: 6px;
                letter-spacing: -0.5px;
            }

            @media (max-width: 480px) {
                .title {
                    font-size: 1.45em;
                }
            }
            .footer {
                margin-top: 40px;
                text-align: center;
                font-size: 11px;
                color: #9a9a9a;
                opacity: 0.6;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title" style="background:linear-gradient(90deg,#1DB954,#1ed760);
                -webkit-background-clip:text;color:transparent;">
                Spotify Dashboard of Elif Naz
        </h1>


            <p style="font-style: italic; font-size: 1.1em;">
                vsco but make it spotify
            </p>
            <p style="margin-top:10px; font-size:14px; opacity:0.85;">
                <a href="https://open.spotify.com/user/yk69xlqfyypx701kxqnbhb3v4"
                    target="_blank"
                    class="profile-link"
                    title="spotify profilim">
                    spotify profilim
                </a>
            </p>
            <p class="desc">haftalık veri anlık cekiliyor, olabildigince</p>
            <p class="desc">embed hata veriyorsa local/unlisted dinliyorumdur</p>

            <div class="card hero">
                <h2>Currently Playing</h2>
                <p>{{track_name}} {{track_artist}}</p>
                {% if track_embed %}
                <iframe src="{{track_embed}}" width="100%" height="80"
                        frameborder="0" allow="encrypted-media"></iframe>
                {% endif %}
            </div>

            <div class="card">
                <h2>Top 5 Artists</h2>
                <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:8px;">
                    most listened - short term (4 weeks)
                </p>
                <table>
                {% for n, a in top_artists %}
                    <tr><td>{{n}}.</td><td>{{a}}</td></tr>
                {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>Top 10 Songs</h2>
                <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:8px;">
                    most listened - short term (4 weeks)
                </p>
                <table>
                {% for n, t in top_tracks %}
                    <tr><td>{{n}}.</td><td>{{t}}</td></tr>
                {% endfor %}
                </table>
            </div>
            <div class="card">
                <h2>Recently Played</h2>
                <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:8px;">
                    last 5 listens
                </p>
                <table>
                {% for n, t, a, time in recent_tracks %}
                    <tr>
                        <td>{{n}}.</td>
                        <td>
                            {{t}} – <span style="opacity:0.7">{{a}}</span><br>
                            <span style="font-size:11px; opacity:0.5;">{{time}}</span>
                        </td>
                    </tr>
                {% endfor %}
                </table>
            </div>
            <p style="
                text-align:center;
                font-size:11px;
                color:#9a9a9a;
                opacity:0.6;
                margin-top:20px;
            ">
                last updated · {{ last_updated }}
            </p>
            <div class="footer">
                made for fun, provides none • spotinaz.com
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
    recent_tracks=recent_tracks,
    last_updated=last_updated,
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
