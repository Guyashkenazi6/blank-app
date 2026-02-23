# app.py
import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Semantle Football",
    page_icon="⚽",
    layout="centered"
)

PLAYERS_FILE = Path("players.json")

# -----------------------------
# Load players
# -----------------------------
@st.cache_data
def load_players() -> list[dict]:
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
            "league": str(p.get("league", "")).strip() or "Unknown League",
            "team": str(p.get("team", "")).strip() or "Unknown Team",
            "position": str(p.get("position", "")).strip(),
            "nationality": str(p.get("nationality", "")).strip(),
        })
    return players

# -----------------------------
# Game logic
# -----------------------------
def new_game(players: list[dict]):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None
    st.session_state["last_guess"] = None

def compute_similarity(secret: dict, guess: dict) -> int:
    if secret["name"].lower() == guess["name"].lower():
        return 100

    score = 10

    if secret["league"] == guess["league"]:
        score += 25
    if secret["team"] == guess["team"]:
        score += 30
    if secret["position"] and secret["position"] == guess["position"]:
        score += 10
    if secret["nationality"] and secret["nationality"] == guess["nationality"]:
        score += 8

    # Name overlap bonus
    overlap = len(set(secret["name"].lower()) & set(guess["name"].lower()))
    score += min(15, overlap)

    return max(0, min(99, score))

# -----------------------------
# App start
# -----------------------------
st.title("⚽ Semantle Football")
st.caption("נחש שחקן מהליגות הבכירות וקבל ציון קרבה 0–100")

players = load_players()

if not players:
    st.error("לא נמצא players.json. ודא שהוא נמצא באותו Repo עם app.py")
    st.stop()

# Init session state
if "secret" not in st.session_state:
    new_game(players)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.subheader("Game")
    if st.button("New Game", use_container_width=True):
        new_game(players)
        st.rerun()

    reveal = st.toggle("Admin: reveal secret", value=False)
    if reveal:
        s = st.session_state["secret"]
        st.info(f'SECRET: {s["name"]} | {s["team"]} | {s["league"]}')

# -----------------------------
# Filters
# -----------------------------
leagues = sorted({p["league"] for p in players})
league = st.selectbox("ליגה", ["All"] + leagues)

filtered = players if league == "All" else [p for p in players if p["league"] == league]

teams = sorted({p["team"] for p in filtered})
team = st.selectbox("קבוצה", ["All"] + teams)

if team != "All":
    filtered = [p for p in filtered if p["team"] == team]

search = st.text_input("חיפוש שם").strip().lower()
if search:
    filtered = [p for p in filtered if search in p["name"].lower()]

if not filtered:
    st.warning("אין תוצאות לפי הסינון")
    st.stop()

# -----------------------------
# Dropdown
# -----------------------------
def label(p):
    return f'{p["name"]} | {p["team"]} | {p["league"]}'

selected = st.selectbox(
    "בחר שחקן מהמאגר",
    filtered[:8000],
    format_func=label
)

if st.button("בדוק ציון", use_container_width=True):
    secret = st.session_state["secret"]
    score = compute_similarity(secret, selected)

    st.session_state["last_score"] = score
    st.session_state["last_guess"] = selected

    st.session_state["history"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "guess": label(selected),
        "score": score
    })

# -----------------------------
# Score display
# -----------------------------
if st.session_state.get("last_score") is not None:
    score = st.session_state["last_score"]
    st.subheader(f"ציון קרבה: {score} / 100")

    st.progress(score / 100)

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

# -----------------------------
# History
# -----------------------------
st.divider()
st.subheader("היסטוריית ניחושים")

if st.session_state["history"]:
    st.dataframe(
        st.session_state["history"],
        use_container_width=True,
        hide_index=True
    )
else:
    st.write("עדיין אין ניחושים.")