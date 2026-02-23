# app.py
import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Semantle Football", page_icon="⚽", layout="centered")

PLAYERS_FILE = Path("players.json")

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
            "league": str(p.get("league", "")).strip(),
            "team": str(p.get("team", "")).strip(),
            "position": str(p.get("position", "")).strip(),
            "nationality": str(p.get("nationality", "")).strip(),
        })
    return players

def new_game(players: list[dict]):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None
    st.session_state["last_guess"] = None

def compute_similarity(secret: dict, guess: dict) -> int:
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

st.title("⚽ Semantle Football")
st.caption("תתחיל להקליד שם שחקן, ותבחר מהרשימה שנפתחת. בלי ליגות, בלי קבוצות.")

players = load_players()
if not players:
    st.error("לא נמצא players.json ליד app.py")
    st.stop()

# init state
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

# ---- Autocomplete-like picker ----
query = st.text_input("חיפוש שם שחקן", placeholder="לדוגמה: haa / haaland / salah").strip().lower()

# אם אין טקסט, נציג מעט שחקנים רנדומליים כדי שיהיה מה לבחור
if query:
    matches = [p for p in players if query in p["name"].lower()]
else:
    # 50 אקראיים כדי לא להעמיס
    matches = random.sample(players, k=min(50, len(players)))

# הגבלה כדי שיטען מהר בטלפון
MAX_OPTIONS = 300
matches = matches[:MAX_OPTIONS]

if not matches:
    st.warning("לא נמצאו שחקנים שמתאימים למה שהקלדת.")
    st.stop()

# dropdown מציג רק שמות (כמו שביקשת)
names = [p["name"] for p in matches]

chosen_name = st.selectbox("בחר שחקן", names)

# למצוא את האובייקט המלא לפי שם (אם יש כפילויות שם, ניקח את הראשון)
chosen_player = next(p for p in matches if p["name"] == chosen_name)

if st.button("בדוק ציון", use_container_width=True):
    secret = st.session_state["secret"]
    score = compute_similarity(secret, chosen_player)

    st.session_state["last_score"] = score
    st.session_state["last_guess"] = chosen_player["name"]
    st.session_state["history"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "guess": chosen_player["name"],
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