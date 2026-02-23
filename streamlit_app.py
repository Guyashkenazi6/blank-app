# app.py
import json
import random
from datetime import datetime
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Semantle Football", page_icon="⚽", layout="centered")
PLAYERS_FILE = Path("players.json")

# -----------------------------
# Settings (you can tweak)
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

# Reduce player pool:
EXCLUDE_GK = True
MIN_MINUTES = 450  # 5 games of 90min; set to 0 to disable minutes filtering

def is_top7_league(league: str) -> bool:
    l = (league or "").strip().lower()
    return any(tok in l for tok in TOP7_TOKENS)

def pos_group(pos: str) -> str:
    p = (pos or "").strip().upper()
    if not p:
        return "UNK"
    if "GK" in p:
        return "GK"
    if "DF" in p:
        return "DEF"
    if "MF" in p:
        return "MID"
    if "FW" in p:
        return "FWD"
    if "DEF" in p:
        return "DEF"
    if "MID" in p:
        return "MID"
    if "FOR" in p or "STR" in p or "WING" in p:
        return "FWD"
    return "UNK"

def safe_int(x, default=0):
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return int(x)
        s = str(x).strip()
        if not s:
            return default
        # handle "1,234"
        s = s.replace(",", "")
        return int(float(s))
    except Exception:
        return default

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

        g = pos_group(position)
        if EXCLUDE_GK and g == "GK":
            continue

        # Minutes: try common keys if present, otherwise 0
        minutes = (
            safe_int(p.get("minutes", None), 0)
            or safe_int(p.get("Min", None), 0)
            or safe_int(p.get("Minutes", None), 0)
            or safe_int(p.get("min", None), 0)
        )

        # If minutes exist and MIN_MINUTES > 0, filter
        if MIN_MINUTES > 0 and minutes > 0 and minutes < MIN_MINUTES:
            continue

        players.append(
            {
                "name": name,
                "league": league,
                "team": team,
                "position": position,
                "pos_group": g,
                "nationality": nationality,
                "minutes": minutes,
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

def compute_similarity(secret: dict, guess: dict) -> int:
    if secret["name"].strip().lower() == guess["name"].strip().lower():
        return 100

    score = 0

    same_league = secret["league"] and secret["league"] == guess["league"]
    same_team = secret["team"] and secret["team"] == guess["team"]
    same_nat = secret["nationality"] and secret["nationality"] == guess["nationality"]

    # Strong signal
    if same_team:
        score += 55
    elif same_league:
        score += 28

    # Position
    if secret["position"] and guess["position"] and secret["position"] == guess["position"]:
        score += 20
    elif secret["pos_group"] != "UNK" and secret["pos_group"] == guess["pos_group"]:
        score += 14

    # Nationality
    if same_nat:
        score += 12

    # Small club-name overlap bonus
    s_team = (secret["team"] or "").lower()
    g_team = (guess["team"] or "").lower()
    if s_team and g_team and not same_team:
        s_words = set(w for w in s_team.replace("-", " ").split() if len(w) >= 4)
        g_words = set(w for w in g_team.replace("-", " ").split() if len(w) >= 4)
        score += min(5, len(s_words & g_words) * 2)

    # Tiny name overlap bonus
    s = secret["name"].lower()
    g = guess["name"].lower()
    score += min(4, len(set(s) & set(g)) // 4)

    return max(0, min(99, int(score)))

def new_game(players: list[dict]):
    st.session_state["secret"] = random.choice(players)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

# -----------------------------
# UI
# -----------------------------
st.title("⚽ Semantle Football")
st.caption("חפש שחקן והניחוש יחזיר ציון קרבה 0–100. המאגר מצומצם לשחקנים פעילים בטופ 7.")

players = load_players()
if not players:
    st.error("המאגר יצא ריק אחרי הסינון. נסה להוריד MIN_MINUTES או לבטל EXCLUDE_GK.")
    st.stop()

# Duplicate names: show team only if needed
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

# Single search-select field
guess_player = st.selectbox(
    "חפש ובחר שחקן",
    players,
    format_func=option_label,
)

col1, col2 = st.columns([1, 1])
with col1:
    check = st.button("בדוק ציון", use_container_width=True)
with col2:
    reveal_btn = st.button("Reveal secret (בדיקה)", use_container_width=True)

if reveal_btn:
    s = st.session_state["secret"]
    st.info(f'סודי: {s["name"]} | {s["team"]} | {s["league"]}')

if check:
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
st.caption(f"סה״כ שחקנים במאגר המצומצם: {len(players)}")

if st.session_state["history"]:
    st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין ניחושים.")