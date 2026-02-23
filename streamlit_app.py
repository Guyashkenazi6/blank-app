# app.py
import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Semantle Football", page_icon="⚽", layout="centered")

PLAYERS_FILE = Path("players.json")

# -----------------------------
# League filtering (auto detect top 7)
# -----------------------------
TOP7_TOKENS = {
    "premier league",
    "la liga",
    "serie a",
    "bundesliga",
    "ligue 1",
    "primeira liga",
    "eredivisie",
}

def is_top7_league(league: str) -> bool:
    l = (league or "").strip().lower()
    return any(tok in l for tok in TOP7_TOKENS)

# -----------------------------
# Position grouping
# -----------------------------
def pos_group(pos: str) -> str:
    p = (pos or "").strip().upper()
    if not p:
        return "UNK"
    # Data often has: GK, DF, MF, FW or similar
    if "GK" in p or p == "G":
        return "GK"
    if "DF" in p or "D" == p:
        return "DEF"
    if "MF" in p or "M" == p:
        return "MID"
    if "FW" in p or "F" == p:
        return "FWD"
    # Fallback: try common words
    if "DEF" in p:
        return "DEF"
    if "MID" in p:
        return "MID"
    if "FOR" in p or "STR" in p or "WING" in p:
        return "FWD"
    return "UNK"

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

        league = str(p.get("league", "")).strip()
        if not is_top7_league(league):
            continue

        team = str(p.get("team", "")).strip()
        position = str(p.get("position", "")).strip()
        nationality = str(p.get("nationality", "")).strip()

        players.append(
            {
                "name": name,
                "league": league,
                "team": team,
                "position": position,
                "pos_group": pos_group(position),
                "nationality": nationality,
            }
        )

    # Dedup by (name, team, league)
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

# -----------------------------
# Scoring
# -----------------------------
def compute_similarity(secret: dict, guess: dict) -> int:
    # Exact hit
    if secret["name"].strip().lower() == guess["name"].strip().lower():
        return 100

    score = 0

    same_league = secret["league"] and secret["league"] == guess["league"]
    same_team = secret["team"] and secret["team"] == guess["team"]
    same_nat = secret["nationality"] and secret["nationality"] == guess["nationality"]

    # Strongest signal
    if same_team:
        score += 55
    elif same_league:
        score += 28
    else:
        score += 0

    # Positions
    if secret["position"] and guess["position"] and secret["position"] == guess["position"]:
        score += 20
    elif secret["pos_group"] != "UNK" and secret["pos_group"] == guess["pos_group"]:
        score += 14
    else:
        score += 0

    # Nationality
    if same_nat:
        score += 12

    # Small club-name related bonus (helps when strings are similar)
    # Example: "Manchester City" vs "Manchester United"
    s_team = (secret["team"] or "").lower()
    g_team = (guess["team"] or "").lower()
    if s_team and g_team and not same_team:
        s_words = set(w for w in s_team.replace("-", " ").split() if len(w) >= 4)
        g_words = set(w for w in g_team.replace("-", " ").split() if len(w) >= 4)
        inter = len(s_words & g_words)
        score += min(5, inter * 2)

    # Small name overlap bonus (never a main signal)
    s = secret["name"].lower()
    g = guess["name"].lower()
    score += min(4, len(set(s) & set(g)) // 4)

    # Keep 99 max if not exact
    return max(0, min(99, int(score)))

# -----------------------------
# Game state
# -----------------------------
def new_game(players: list[dict]):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

# -----------------------------
# UI
# -----------------------------
st.title("⚽ Semantle Football")
st.caption("חפש שחקן והניחוש יחזיר ציון קרבה 0–100. השחקן הסודי נבחר רק מהטופ 7 ליגות.")

players = load_players()
if not players:
    st.error("לא הצלחתי לטעון שחקנים מהטופ 7 ליגות מתוך players.json. בדוק שהקובץ קיים ושיש בו נתונים.")
    st.stop()

# Handle duplicate names: show team only for duplicates
name_counts = {}
for p in players:
    name_counts[p["name"]] = name_counts.get(p["name"], 0) + 1

def option_label(p: dict) -> str:
    if name_counts.get(p["name"], 0) > 1 and p["team"]:
        return f'{p["name"]} ({p["team"]})'
    return p["name"]

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
        st.info(f'SECRET: {s["name"]} | {s["team"]} | {s["league"]}')

guess_player = st.selectbox(
    "חפש ובחר שחקן",
    players,
    format_func=option_label,
)

if st.button("בדוק ציון", use_container_width=True):
    secret = st.session_state["secret"]
    score = compute_similarity(secret, guess_player)
    st.session_state["last_score"] = score
    st.session_state["history"].insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guess": option_label(guess_player),
            "score": score,
        },
    )

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
        unsafe_allow_html=True,
    )

st.divider()
st.subheader("היסטוריית ניחושים")
if st.session_state["history"]:
    st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין ניחושים.")