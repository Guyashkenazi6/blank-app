import random
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Semantle Football", page_icon="⚽", layout="centered")

# -----------------------------
# Demo player pool (replace/extend)
# -----------------------------
TOP_LEAGUE_PLAYERS = [
    "Bukayo Saka", "Cole Palmer", "Mohamed Salah", "Alexander Isak",
    "Vinícius Júnior", "Jude Bellingham", "Kylian Mbappé", "Erling Haaland",
    "Lautaro Martínez", "Rafael Leão", "Florian Wirtz", "Jamal Musiala",
    "Victor Osimhen", "Rodrygo", "Phil Foden", "Antoine Semenyo",
]

# -----------------------------
# Mock similarity function
# Replace with your real semantic engine later
# -----------------------------
def compute_similarity(secret: str, guess: str) -> int:
    g = guess.strip().lower()
    s = secret.strip().lower()
    if not g:
        return 0
    if g == s:
        return 100
    # Toy scoring: closer if they share initials/letters
    overlap = len(set(g) & set(s))
    base = min(90, 10 + overlap * 4)
    # Add small deterministic wobble
    wobble = (len(g) * 7 + len(s) * 3) % 10
    score = min(99, base + wobble)
    return max(0, int(score))

def new_game():
    st.session_state["secret"] = random.choice(TOP_LEAGUE_PLAYERS)
    st.session_state["history"] = []
    st.session_state["last_score"] = None

# -----------------------------
# State init
# -----------------------------
if "secret" not in st.session_state:
    new_game()

# -----------------------------
# UI
# -----------------------------
st.title("⚽ Semantle Football")
st.caption("נחש שחקן ותקבל ציון קרבה 0–100. עובד מצוין מהטלפון.")

with st.sidebar:
    st.subheader("Game")
    if st.button("New Game", use_container_width=True):
        new_game()
        st.rerun()

    # Optional admin reveal toggle (off by default)
    reveal = st.toggle("Admin: reveal secret", value=False)
    if reveal:
        st.info(f"SECRET: {st.session_state['secret']}")

guess = st.text_input("ניחוש (שם שחקן):", placeholder="לדוגמה: Mohamed Salah / סאלח")
submit = st.button("בדוק ציון", use_container_width=True)

if submit:
    secret = st.session_state["secret"]
    score = compute_similarity(secret, guess)

    st.session_state["last_score"] = score
    st.session_state["history"].insert(
        0,
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "guess": guess.strip(),
            "score": score,
        },
    )

# Score panel
if st.session_state.get("last_score") is not None:
    score = st.session_state["last_score"]
    st.subheader(f"ציון קרבה: {score} / 100")
    st.progress(score / 100.0)

    st.markdown(
        f"""
        <div style="
            margin-top: 8px;
            padding: 14px 16px;
            border-radius: 12px;
            background: rgba(0, 200, 0, 0.12);
            border: 1px solid rgba(0, 200, 0, 0.35);
            font-size: 18px;
            font-weight: 700;
            text-align: center;">
            ✅ {score} / 100
        </div>
        """,
        unsafe_allow_html=True
    )

# History table
st.divider()
st.subheader("היסטוריית ניחושים")
if st.session_state["history"]:
    st.dataframe(st.session_state["history"], use_container_width=True, hide_index=True)
else:
    st.write("עדיין אין ניחושים.")