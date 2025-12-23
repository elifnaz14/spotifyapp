from flask import Flask, redirect, request, render_template_string, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import plotly.graph_objs as go
from plotly.offline import plot
import datetime
import os

# =========================
# APP
# =========================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("ba25b99ecf49effc559dc21a257d35631ad0429c73e09571a664f619c5347d99")

# =========================
# ENV
# =========================
CLIENT_ID = os.environ.get("9f51e301cf594158b80107b2b4bf54ce")
CLIENT_SECRET = os.environ.get("ff7a063fc03c4086a05f1a05f511fa40")
REDIRECT_URI = os.environ.get("https://spotinaz-695626b39531.herokuapp.com/spotify_callback")

SCOPE = (
    "user-read-private user-read-email "
    "user-top-read user-read-currently-playing "
    "user-read-playback-state user-read-recently-played"
)

# =========================
# DEBUG (sonra silebilirsin)
# =========================
@app.route("/debug")
def debug():
    return f"""
    SECRET_KEY: {app.config["SECRET_KEY"]}<br>
    CLIENT_ID: {bool(CLIENT_ID)}<br>
    CLIENT_SECRET: {bool(CLIENT_SECRET)}<br>
    REDIRECT_URI: {REDIRECT_URI}
    """

# =========================
# LOGIN
# =========================
@app.route("/")
def login():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        show_dialog=True
    )
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# =========================
# CALLBACK
# =========================
@app.route("/spotify_callback")
def spotify_callback():
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE
    )

    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    session["token_info"] = token_info

    return redirect(url_for("dashboard"))

# =====
