import streamlit as st
import requests
import random
from difflib import SequenceMatcher

# -----------------------------
# הגדרות API
# -----------------------------
API_KEY = "9548331b90cece4ee37fdd93ad6a0edb"
SEASON = 2025  # 2025/2026

HEADERS = {
    "x-apisports-key": API_KEY
}

# ליגות בכירות (ID של API-Football)
LEAGUES = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Bundesliga": 78,
    "Ligue 1": 61
}

# -----------------------------
# פונקציות API
# -----------------------------
@st.cache_data
def fetch_players():
    players = []

    for league_id in LEAGUES.values():
        page = 1
        while True:
            url = "https://v3.football.api-sports.io/players"
            params = {
                "league": league_id,
                "season": SEASON,
                "page": page
            }
            r = requests.get(url, headers=HEADERS, params=params)
            data = r.json()

            for item in data["response"]:
                p = item["player"]
                s = item["statistics"][0]

                players.append({
                    "name": p["name"],
                    "team": s["team"]["name"],
                    "league": s["league"]["name"],
                    "position": p["position"],
                    "nationality": p["nationality"]
                })

            if page >= data["paging"]["total"]:
                break
            page += 1

    return players

players = fetch_players()

# -----------------------------
# בחירת שחקן סודי
# -----------------------------
if "secret_player" not in st.session_state:
    st.session_state.secret_player = random.choice(players)

secret = st.session_state.secret_player

# -----------------------------
# פונקציות ניקוד
# -----------------------------
def normalize(text):
    return text.lower().strip()

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def calculate_score(guess, target):
    score = 0

    score += similarity(
        normalize(guess["name"]),
        normalize(target["name"])
    ) * 40

    if guess["league"] == target["league"]:
        score += 20

    if guess["team"] == target["team"]:
        score += 20

    if guess["position"] == target["position"]:
        score += 10

    if guess["nationality"] == target["nationality"]:
        score += 10

    return round(score)

# -----------------------------
# UI
# -----------------------------
st.title("⚽ Football Semantle (API Version)")

query = st.text_input(
    "כתוב שם של שחקן",
    placeholder="לדוגמה: haaland"
)

matches = []
if query:
    q = normalize(query)
    matches = [
        p for p in players
        if q in normalize(p["name"])
    ][:10]

selected_player = None
if matches:
    selected_name = st.radio(
        "השלמות אפשריות",
        [p["name"] for p in matches]
    )
    selected_player = next(p for p in matches if p["name"] == selected_name)

# -----------------------------
# בדיקת ניחוש
# -----------------------------
if selected_player:
    score = calculate_score(selected_player, secret)
    st.success(f"🔥 ציון קרבה: {score}/100")

    if score == 100:
        st.balloons()
        st.success("🎉 מצאת את השחקן!")

# -----------------------------
# Debug
# -----------------------------
with st.expander("🛠 Debug"):
    st.json(secret)

# -----------------------------
# ריסט
# -----------------------------
if st.button("🔄 שחקן חדש"):
    st.session_state.secret_player = random.choice(players)
    st.experimental_rerun()