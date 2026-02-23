# app.py
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

    # שם קטן אבל חשוב: רשימה ממוינת נותנת השלמות יציבות
    players.sort(key=lambda x: x["name"].lower())
    return players

def new_game(players):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

def compute_similarity(secret, guess):
    if secret["name"].lower() == guess["name"].lower():
        return 100

    score = 10
    if secret.get("league") and secret["league"] == guess.get("league"):
        score += 25
    if secret.get("team") and secret["team"] == guess.get("team"):
        score += 30
    if secret.get("position") and secret["position"] == guess.get("position"):
        score += 10
    if secret.get("nationality") and secret["nationality"] == guess.get("nationality"):
        score += 8

    overlap = len(set(secret["name"].lower()) & set(guess["name"].lower()))
    score += min(15, overlap)

    return max(0, min(99, int(score)))

# ---------- UI ----------
st.title("⚽ Semantle Football")
st.caption("תתחיל להקליד שם שחקן, ותקבל הצעות ללחיצה כמו autocomplete.")

players = load_players()
if not players:
    st.error("לא נמצא players.json ליד app.py")
    st.stop()

# Session init
if "secret" not in st.session_state:
    new_game(players)

if "query" not in st.session_state:
    st.session_state["query"] = ""

if "selected_name" not in st.session_state:
    st.session_state["selected_name"] = ""

with st.sidebar:
    st.subheader("Game")
    if st.button("New Game", use_container_width=True):
        new_game(players)
        st.rerun()

    reveal = st.toggle("Admin: reveal secret", value=False)
    if reveal:
        st.info(f'SECRET: {st.session_state["secret"]["name"]}')

# --- Search input ---
st.session_state["query"] = st.text_input(
    "חיפוש שחקן",
    value=st.session_state["query"],
    placeholder="לדוגמה: haa / haaland / salah"
).strip()

q = st.session_state["query"].lower()

# --- Build suggestions ---
SUGGESTIONS_LIMIT = 8

def matches(p):
    return q in p["name"].lower()

suggestions = []
if q:
    suggestions = [p["name"] for p in players if matches(p)]
    suggestions = suggestions[:SUGGESTIONS_LIMIT]

# --- Suggestions UI (clickable) ---
if q and suggestions:
    st.markdown("**השלמות:**")
    for name in suggestions:
        # כפתור לכל הצעה
        if st.button(name, key=f"sug_{name}", use_container_width=True):
            st.session_state["selected_name"] = name
            st.session_state["query"] = name
            st.rerun()
elif q and not suggestions:
    st.warning("לא נמצאו השלמות למה שהקלדת.")

# --- Selected player (must be exact match) ---
chosen_name = st.session_state["selected_name"] or st.session_state["query"]

# חיפוש exact match במאגר
chosen_player = next((p for p in players if p["name"].lower() == chosen_name.lower()), None)

col1, col2 = st.columns([1, 1])
with col1:
    check = st.button("בדוק ציון", use_container_width=True)
with col2:
    clear = st.button("נקה", use_container_width=True)

if clear:
    st.session_state["query"] = ""
    st.session_state["selected_name"] = ""
    st.rerun()

if check:
    if not chosen_player:
        st.error("כדי לבדוק ציון, תבחר שחקן מההשלמות (או תרשום שם בדיוק כמו במאגר).")
    else:
        secret = st.session_state["secret"]
        score = compute_similarity(secret, chosen_player)

        st.session_state["last_score"] = score
        st.session_state.setdefault("history", []).insert(0, {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guess": chosen_player["name"],
            "score": score
        })

# --- Score display ---
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
if st.session_state.get("history"):
    st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין ניחושים.")