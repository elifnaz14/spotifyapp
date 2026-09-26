from flask import Flask, render_template_string, request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from datetime import datetime
from datetime import timedelta


app = Flask(__name__)

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID") or os.environ.get("9f51e301cf594158b80107b2b4bf54ce") or "9f51e301cf594158b80107b2b4bf54ce"
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET") or os.environ.get("ff7a063fc03c4086a05f1a05f511fa40") or "bce0ae1bc6f04a2eb5975774a942e57b"
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN") or "AQBleAjlzWYAUy0twq4eYgyOHRTwfhSkHWoGYANgRsygpsjrEcjl3nsnlFQnJUqR7UV8d_jzF3j5_vNOUJgDM7bzkmiDp_UNiCrH41J3B_t7v_49MEvLlW3zRPk5Lvs0ZCU"

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
    sp = get_spotify_client()
    current = sp.current_playback()

    if current and current.get("item"):
        track = current["item"]
        return (
            track["name"],
            track["artists"][0]["name"],
            f"https://open.spotify.com/embed/track/{track['id']}"
        )
    else:
        html_message = (
            '<span style="font-family:sans-serif; font-size:0.95em; opacity:0.7;">'
            'not listening rn, but maybe </span>'
            '<a href="https://lichess-damage-report-f5e4b5271a78.herokuapp.com" '
            'target="_blank" style="color:#1DB954; font-weight:500; text-decoration:underline;">'
            'playing</a>'
        )
        return html_message, "", ""
    
@app.route("/current-track")
def current_track_api():
    track_name, track_artist, track_embed = get_current_track()

    if track_embed:
        return {
            "status": "playing",
            "embed": track_embed
        }
    else:
        return {
            "status": "idle"
        }

def get_top_artists(limit=5, time_range="short_term"):
    try:
        sp = get_spotify_client()
        data = sp.current_user_top_artists(limit=limit, time_range=time_range)
        return [(i + 1, a["name"]) for i, a in enumerate(data["items"])]
    except:
        return []

def get_top_tracks(limit=10, time_range="short_term"):
    try:
        sp = get_spotify_client()
        data = sp.current_user_top_tracks(limit=limit, time_range=time_range)
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
            played_time = datetime.fromisoformat(
                played_at.replace("Z", "+00:00")
            ) + timedelta(hours=3)

            time_str = played_time.strftime("%H:%M")

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

_timeline_cache = {"timestamp": None, "data": None}

def get_timeline_data():
    now = datetime.utcnow()
    if _timeline_cache["data"] and _timeline_cache["timestamp"]:
        if (now - _timeline_cache["timestamp"]).total_seconds() < 300:
            return _timeline_cache["data"]

    try:
        sp = get_spotify_client()
        if not sp:
            return _timeline_cache.get("data") or {}

        timeline = {}
        for term in ["long_term", "medium_term", "short_term"]:
            res = sp.current_user_top_artists(limit=10, time_range=term)
            timeline[term] = [{"rank": i + 1, "name": a["name"]} for i, a in enumerate(res.get("items", []))]

        _timeline_cache["data"] = timeline
        _timeline_cache["timestamp"] = now
        return timeline
    except Exception as e:
        print("[Spotinaz] Timeline fetch error:", e)
        return _timeline_cache.get("data") or {}


VALID_RANGES = {"short_term", "medium_term", "long_term"}
RANGE_LABELS = {
    "short_term": "last 4 weeks",
    "medium_term": "last 6 months",
    "long_term": "all time"
}


@app.route("/")
def dashboard():
    time_range = request.args.get("time_range", "short_term")
    if time_range not in VALID_RANGES:
        time_range = "short_term"

    track_name, track_artist, track_embed = get_current_track()
    top_artists = get_top_artists(time_range=time_range)
    top_tracks = get_top_tracks(time_range=time_range)
    recent_tracks = get_recent_tracks()
    timeline_data = get_timeline_data()

    last_updated = (datetime.utcnow() + timedelta(hours=3)).strftime("%H:%M")




    html = """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spotify Dashboard of Elif Naz</title>
        <style>
            body { background:#121212; color:white; font-family:sans-serif; margin:0 }
            .container { max-width:600px; margin:auto; padding:20px }
            .card { background:#1e1e1e; margin:24px 0; padding:24px;
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
            .meta {
                font-size: 11px;
                opacity: 0.5;
            }
            .secondary {
                opacity: 0.7;
            }
            .footer {
                margin-top: 40px;
                text-align: center;
                font-size: 11px;
                color: #9a9a9a;
                opacity: 0.6;
            }
                        .tabs {
                display: flex;
                gap: 8px;
                margin: 20px 0 -6px;
            }
            .tab {
                flex: 1;
                text-align: center;
                padding: 8px 0;
                border-radius: 8px;
                font-size: 12px;
                text-decoration: none;
                color: #cfcfcf;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.08);
                transition: all 0.2s ease;
            }
            .tab.active {
                background: rgba(29,185,84,0.15);
                color: #1DB954;
                border-color: #1DB954;
                font-weight: 600;
            }
            .readme-card {
                cursor: pointer;
                overflow: hidden;
                border-radius: 16px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                background: rgba(255,255,255,0.05);
                transition: all 0.3s ease;
                border: 1px solid rgba(255,255,255,0.1);
            }

            .readme-header {
                font-weight: 700;
                font-size: 0.95em;
                padding: 10px 14px;
                text-align: center;
                user-select: none;
                color: #e0e0e0;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                background: rgba(255,255,255,0.02);
                border-radius: 12px 12px 0 0;
                transition: background 0.3s ease;
            }
            .readme-card:hover .readme-header {
                background: rgba(255,255,255,0.05);
            }
            .readme-card:hover {
                background: rgba(29, 185, 84, 0.08); /* hafif spotify yeşili */
            }
            .readme-content {
                max-height: 0;
                opacity: 0;
                padding: 0 14px;
                transition: max-height 0.35s ease, opacity 0.35s ease, padding 0.35s ease;
                font-size: 0.9em;
                color: #dcdcdc;
                line-height: 1.45;
            }
            .readme-card.active .readme-content {
                max-height: 500px;
                opacity: 1;
                padding: 12px 14px;
            }

            /* Minimal 2D Timeline */
            .timeline-card {
                user-select: none;
            }
            .timeline-2d {
                position: relative;
                height: 220px;
                background: #161616;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                overflow: hidden;
                margin-bottom: 14px;
                cursor: ew-resize;
            }
            .timeline-2d::before {
                content: "";
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: rgba(255, 255, 255, 0.03);
                pointer-events: none;
            }
            .timeline-y-guide {
                position: absolute;
                left: 8px;
                font-size: 9px;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                color: rgba(255, 255, 255, 0.18);
                font-family: monospace;
                pointer-events: none;
                z-index: 1;
            }
            .timeline-y-guide.top { top: 8px; }
            .timeline-y-guide.mid { top: calc(50% - 6px); }
            .timeline-y-guide.bot { bottom: 8px; }

            .t-node {
                position: absolute;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                white-space: nowrap;
                color: #cfcfcf;
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.07);
                transform: translate(-50%, -50%);
                transition: top 0.28s cubic-bezier(0.2, 0.8, 0.3, 1), opacity 0.25s ease, border-color 0.2s ease, background 0.2s ease;
                pointer-events: none;
            }
            .t-node.rank-1 {
                color: #ffffff;
                font-weight: 600;
                border-color: rgba(29, 185, 84, 0.4);
                background: rgba(29, 185, 84, 0.12);
                z-index: 3;
            }
            .t-node.rank-top {
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.16);
                z-index: 2;
            }
            .t-node .t-rank {
                font-size: 9.5px;
                color: rgba(255, 255, 255, 0.35);
                margin-right: 4px;
                font-family: monospace;
            }
            .t-node.rank-1 .t-rank {
                color: #1DB954;
                opacity: 1;
            }

            .timeline-controls {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .timeline-scrubber {
                -webkit-appearance: none;
                width: 100%;
                height: 3px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
                outline: none;
                cursor: pointer;
                margin: 4px 0;
            }
            .timeline-scrubber::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #1DB954;
                cursor: pointer;
                transition: transform 0.1s ease;
            }
            .timeline-scrubber::-webkit-slider-thumb:hover {
                transform: scale(1.3);
            }
            .timeline-ticks {
                display: flex;
                justify-content: space-between;
                font-size: 11px;
                color: #777;
            }
            .timeline-ticks .tick {
                cursor: pointer;
                transition: color 0.15s ease;
            }
            .timeline-ticks .tick:hover {
                color: #ccc;
            }
            .timeline-ticks .tick.active {
                color: #1DB954;
                font-weight: 500;
            }
        </style>
        <style>
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.85; }
            100% { opacity: 1; }
        }

        .playing-pulse {
            animation: pulse 2.5s ease-in-out infinite;
        }
        </style>

        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-K5K6CCE7CS"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'G-K5K6CCE7CS');
        </script>
    </head>
    <body>
    <div class="container">
        <h1 class="title" style="background:linear-gradient(90deg,#1DB954,#1ed760);
            -webkit-background-clip:text;color:transparent;">
            Spotify Dashboard of Elif Naz
        </h1>

        <p class="desc" style="text-transform: uppercase; opacity: 0.55; font-size: 0.75rem; letter-spacing: 1px; margin-top:0; margin-bottom:6px;">
            vsco but make it spotify
        </p>
        <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:8px;">
            used beats rather than filters
        </p>

        <div class="card hero">
            <h2>Currently Listening</h2>
            <div id="current-playing-area">
            {% if track_embed %}
                <iframe src="{{track_embed}}" width="100%" height="80"
                        frameborder="0" allow="encrypted-media"></iframe>
            {% else %}
                <p style="font-family:sans-serif; font-size:0.95em; opacity:0.7; margin:0;">
                    not listening rn, but maybe
                    <a href="https://lichess-damage-report-f5e4b5271a78.herokuapp.com"
                    target="_blank"
                    style="color:#1DB954; font-weight:500; text-decoration:underline;">
                    playing
                    </a>
                </p>
            {% endif %}
            </div>
        </div>

        <div class="card timeline-card">
            <h2>timeline</h2>
            <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:12px;">
                drag to see artist frequency across time
            </p>

            <div class="timeline-2d" id="timeline-2d">
                <div class="timeline-y-guide top">frequent</div>
                <div class="timeline-y-guide mid">moderate</div>
                <div class="timeline-y-guide bot">occasional</div>
                <div id="timeline-nodes"></div>
            </div>

            <div class="timeline-controls">
                <input type="range" id="timeline-range" min="0" max="2" step="0.01" value="2" class="timeline-scrubber">
                <div class="timeline-ticks">
                    <span class="tick" data-val="0">all time</span>
                    <span class="tick" data-val="1">last 6 months</span>
                    <span class="tick active" data-val="2">last 4 weeks</span>
                </div>
            </div>
        </div>

        <div class="tabs">
            <a href="/?time_range=short_term" class="tab {{ 'active' if current_range == 'short_term' }}">last 4 weeks</a>
            <a href="/?time_range=medium_term" class="tab {{ 'active' if current_range == 'medium_term' }}">last 6 months</a>
            <a href="/?time_range=long_term" class="tab {{ 'active' if current_range == 'long_term' }}">all time</a>
        </div>

        <div class="card">
            <h2>Top 5 Artists</h2>
            <p style="font-size:11px; opacity:0.55; margin-top:-6px; margin-bottom:8px;">
                most listened - {{ range_label }}
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
                most listened - {{ range_label }}
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
                        {{t}} – <span class="secondary">{{a}}</span>
                        <span class="meta">{{time}}</span>
                    </td>
                </tr>
            {% endfor %}
            </table>
        </div>

        <div class="card readme-card">
            <div class="readme-header">alakasız linkler</div>
            <div class="readme-content">
                <p>
                    <a href="https://strava.app.link/yP1KWcOj0Zb" target="_blank" style="color:#FC5200;">strava</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">my strava profile</span>
                </p>
                <p>
                    <a href="https://open.spotify.com/user/yk69xlqfyypx701kxqnbhb3v4" target="_blank" style="color:#1DB954;">spotify</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">my spotify profile</span>
                </p>
                <p>
                    <a href="https://lichess-damage-report-f5e4b5271a78.herokuapp.com" target="_blank" style="color:#1DB954;">lichess</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">personalized lichess damage reports</span>
                </p>
                <p>
                    <a href="https://www.linkedin.com/in/elif-naz-mutlu-634915216/" target="_blank" style="color:#1DB954;">linkedin</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">my linkedin profile</span>
                </p>
                <p>
                    <a href="https://go2mid.com" target="_blank" style="color:#1DB954;">go2mid.com</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">start from the midgame</span>
                </p>
                <p>
                    <a href="https://github.com/elifnaz14" target="_blank" style="color:#1DB954;">github</a>
                    <span style="opacity:0.6; font-size:0.85em; font-style:italic;">my github profile</span>
                </p>
            </div>
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

    
    <script>
    document.querySelectorAll('.readme-card').forEach(card => {
        card.addEventListener('click', () => {
            card.classList.toggle('active');
        });
    });

    // 2D Timeline Engine
    const timelineData = {{ timeline_json|safe }};
    const nodesContainer = document.getElementById("timeline-nodes");
    const slider = document.getElementById("timeline-range");
    const ticks = document.querySelectorAll(".timeline-ticks .tick");
    const canvas = document.getElementById("timeline-2d");

    if (timelineData && Object.keys(timelineData).length > 0 && nodesContainer && slider) {
        const artistMap = {};
        const terms = ["long_term", "medium_term", "short_term"];
        
        terms.forEach(term => {
            (timelineData[term] || []).forEach(item => {
                if (!artistMap[item.name]) {
                    artistMap[item.name] = { long_term: null, medium_term: null, short_term: null };
                }
                artistMap[item.name][term] = item.rank;
            });
        });

        const artistNames = Object.keys(artistMap);
        const totalCols = 4;
        const colWidth = 100 / totalCols;

        const domNodes = {};
        artistNames.forEach((name, idx) => {
            const el = document.createElement("div");
            el.className = "t-node";
            el.innerHTML = '<span class="t-rank"></span>' + name;
            nodesContainer.appendChild(el);
            
            const col = idx % totalCols;
            const xPercent = (col * colWidth) + (colWidth / 2);
            domNodes[name] = {
                el: el,
                rankEl: el.querySelector(".t-rank"),
                x: xPercent,
                ranks: artistMap[name]
            };
        });

        function renderTimeline(v) {
            let eraA, eraB, f;
            if (v <= 1) {
                eraA = "long_term";
                eraB = "medium_term";
                f = v;
            } else {
                eraA = "medium_term";
                eraB = "short_term";
                f = v - 1;
            }

            const activeStep = Math.round(v);
            ticks.forEach(t => {
                t.classList.toggle("active", parseInt(t.dataset.val) === activeStep);
            });

            artistNames.forEach(name => {
                const node = domNodes[name];
                const rA = node.ranks[eraA] !== null ? node.ranks[eraA] : 13;
                const rB = node.ranks[eraB] !== null ? node.ranks[eraB] : 13;

                const rank = rA * (1 - f) + rB * f;

                if (rank > 11.2) {
                    node.el.style.opacity = "0";
                    node.el.style.top = "115%";
                    node.el.style.left = node.x + "%";
                } else {
                    const roundedRank = Math.max(1, Math.min(10, Math.round(rank)));
                    const yPercent = 14 + (rank - 1) * 7.2;
                    const opacity = Math.max(0, Math.min(1, (11.5 - rank) / 3.5));

                    node.el.style.opacity = opacity.toFixed(2);
                    node.el.style.top = yPercent.toFixed(1) + "%";
                    node.el.style.left = node.x + "%";
                    node.rankEl.textContent = roundedRank + ".";

                    node.el.classList.toggle("rank-1", roundedRank === 1);
                    node.el.classList.toggle("rank-top", roundedRank <= 3 && roundedRank > 1);
                }
            });
        }

        slider.addEventListener("input", () => {
            renderTimeline(parseFloat(slider.value));
        });

        ticks.forEach(t => {
            t.addEventListener("click", () => {
                const target = parseFloat(t.dataset.val);
                animateSlider(target);
            });
        });

        let isDragging = false;
        function onDrag(clientX) {
            const rect = canvas.getBoundingClientRect();
            let ratio = (clientX - rect.left) / rect.width;
            ratio = Math.max(0, Math.min(1, ratio));
            const val = ratio * 2;
            slider.value = val;
            renderTimeline(val);
        }

        canvas.addEventListener("mousedown", (e) => { isDragging = true; onDrag(e.clientX); });
        window.addEventListener("mousemove", (e) => { if (isDragging) onDrag(e.clientX); });
        window.addEventListener("mouseup", () => { isDragging = false; });
        canvas.addEventListener("touchstart", (e) => { isDragging = true; onDrag(e.touches[0].clientX); }, { passive: true });
        window.addEventListener("touchmove", (e) => { if (isDragging) onDrag(e.touches[0].clientX); }, { passive: true });
        window.addEventListener("touchend", () => { isDragging = false; });

        function animateSlider(targetVal) {
            let current = parseFloat(slider.value);
            const step = (targetVal - current) / 10;
            let count = 0;
            function anim() {
                count++;
                current += step;
                if (count >= 10 || Math.abs(current - targetVal) < 0.03) {
                    slider.value = targetVal;
                    renderTimeline(targetVal);
                } else {
                    slider.value = current;
                    renderTimeline(current);
                    requestAnimationFrame(anim);
                }
            }
            requestAnimationFrame(anim);
        }

        renderTimeline(2);
    }

    let lastEmbed = null;

    async function refreshCurrentTrack() {
        const res = await fetch("/current-track");
        const data = await res.json();
        const area = document.getElementById("current-playing-area");

        if (data.status === "playing") {
            if (data.embed !== lastEmbed) {
                lastEmbed = data.embed;
                area.innerHTML = `
                    <iframe src="${data.embed}" width="100%" height="80"
                        frameborder="0" allow="encrypted-media"></iframe>
                `;
            }
        } else {
            if (lastEmbed !== null) {
                lastEmbed = null;
                area.innerHTML = `
                    <p style="font-family:sans-serif; font-size:0.95em; opacity:0.7; margin:0;">
                        not listening rn
                    </p>
                `;
            }
        }
    }

    setInterval(refreshCurrentTrack, 15000);
    </script>
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
    current_range=time_range,
    range_label=RANGE_LABELS[time_range],
    timeline_json=json.dumps(timeline_data),
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
