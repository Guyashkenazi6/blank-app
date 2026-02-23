import json
import random
from datetime import datetime
from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Semantle Football", page_icon="⚽", layout="centered")
PLAYERS_FILE = Path("players.json")

@st.cache_data
def load_players():
    if not PLAYERS_FILE.exists():
        return []
    with PLAYERS_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    players = []
    for p in data:
        name = str(p.get("name", "")).strip()
        if not name:
            continue
        players.append({
            "name": name,
            "league": str(p.get("league", "")).strip(),
            "team": str(p.get("team", "")).strip(),
            "position": str(p.get("position", "")).strip(),
            "nationality": str(p.get("nationality", "")).strip(),
        })

    # ניקוי כפילויות לפי (name, team, league)
    seen = set()
    dedup = []
    for p in players:
        key = (p["name"].lower(), p["team"].lower(), p["league"].lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(p)

    dedup.sort(key=lambda x: x["name"].lower())
    return dedup

def new_game(players):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

def compute_similarity(secret: dict, guess: dict) -> int:
    if secret["name"].strip().lower() == guess["name"].strip().lower():
        return 100

    score = 0
    W_LEAGUE = 30
    W_TEAM = 45
    W_POS = 15
    W_NATION = 10

    if secret["league"] and guess["league"] and secret["league"] == guess["league"]:
        score += W_LEAGUE
    if secret["team"] and guess["team"] and secret["team"] == guess["team"]:
        score += W_TEAM
    if secret["position"] and guess["position"] and secret["position"] == guess["position"]:
        score += W_POS
    if secret["nationality"] and guess["nationality"] and secret["nationality"] == guess["nationality"]:
        score += W_NATION

    s = secret["name"].lower()
    g = guess["name"].lower()
    overlap = len(set(s) & set(g))
    score += min(5, overlap // 3)

    return min(99, score)

st.title("⚽ Semantle Football")
st.caption("לחץ על השדה, תתחיל להקליד, ותבחר שחקן. הניקוד לפי ליגה/קבוצה/עמדה/לאום.")

players = load_players()
if not players:
    st.error("לא נמצא players.json ליד app.py")
    st.stop()

if "secret" not in st.session_state:
    new_game(players)

with st.sidebar:
    st.subheader("Game")
    if st.button("New Game", use_container_width=True):
        new_game(players)
        st.rerun()

    reveal = st.toggle("Admin: reveal secret", value=False)
    if reveal:
        s = st.session_state["secret"]
        st.info(f'SECRET: {s["name"]}')

# מציג רק שם, אבל שומר את כל האובייקט
guess_player = st.selectbox(
    "חפש ובחר שחקן",
    players,
    format_func=lambda p: p["name"]
)

if st.button("בדוק ציון", use_container_width=True):
    score = compute_similarity(st.session_state["secret"], guess_player)
    st.session_state["last_score"] = score
    st.session_state["history"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "guess": guess_player["name"],
        "score": score
    })

if st.session_state.get("last_score") is not None:
    score = st.session_state["last_score"]
    st.subheader(f"ציון קרבה: {score} / 100")
    st.progress(score / 100.0)
    st.markdown(
        f"""
        <div style="
            margin-top:10px;
            padding:14px;
            border-radius:12px;
            background:rgba(0,200,0,0.12);
            border:1px solid rgba(0,200,0,0.35);
            font-size:18px;
            font-weight:700;
            text-align:center;">
            ✅ {score} / 100
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()
st.subheader("היסטוריית ניחושים")
if st.session_state["history"]:
    st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין ניחושים.")