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

    names = []
    for p in data:
        name = str(p.get("name", "")).strip()
        if name:
            names.append(name)

    # מסדר ומנקה כפילויות
    names = sorted(set(names), key=lambda x: x.lower())
    return names

def new_game(names):
    st.session_state["secret"] = random.choice(names)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

def compute_similarity(secret_name: str, guess_name: str) -> int:
    s = secret_name.lower().strip()
    g = guess_name.lower().strip()
    if s == g:
        return 100

    # ניקוד דמה בסיסי, אפשר לשפר אחר כך עם דאטה נוסף
    score = 10
    overlap = len(set(s) & set(g))
    score += min(60, overlap * 4)

    # בונוס על prefix
    if s.startswith(g) or g.startswith(s):
        score += 15

    return max(0, min(99, int(score)))

st.title("⚽ Semantle Football")
st.caption("לחץ על השדה, תתחיל להקליד, ותבחר שחקן. זה autocomplete אמיתי במובייל.")

names = load_players()
if not names:
    st.error("לא נמצא players.json ליד app.py")
    st.stop()

if "secret" not in st.session_state:
    new_game(names)

with st.sidebar:
    st.subheader("Game")
    if st.button("New Game", use_container_width=True):
        new_game(names)
        st.rerun()

    reveal = st.toggle("Admin: reveal secret", value=False)
    if reveal:
        st.info(f'SECRET: {st.session_state["secret"]}')

# שדה אחד בלבד עם חיפוש מובנה
guess_name = st.selectbox("חפש ובחר שחקן", names)

if st.button("בדוק ציון", use_container_width=True):
    score = compute_similarity(st.session_state["secret"], guess_name)
    st.session_state["last_score"] = score
    st.session_state["history"].insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "guess": guess_name,
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