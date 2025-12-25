import streamlit as st
import random
import math
import pandas as pd

st.set_page_config(page_title="Challenge Cup Tournament", layout="centered")

# ================= CONFIG =================
BUCHHOLZ_SCALE = 0.1  # 8.0 → 0.8

# ================= DATA =================
class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0.0
        self.opponents = set()
        self.buchholz = 0.0

# ================= LOGIC =================
def choose_rounds(n, rmin, rmax):
    ideal = math.ceil(math.log2(n))
    return max(rmin, min(rmax, ideal))

def random_pair(players):
    lst = players[:]
    random.shuffle(lst)
    return [(lst[i], lst[i+1]) for i in range(0, len(lst), 2)]

def swiss_pair(players):
    sorted_players = sorted(players, key=lambda p: (-p.score, p.name))
    paired = set()
    pairs = []

    for p in sorted_players:
        if p.name in paired:
            continue
        for q in sorted_players:
            if q.name not in paired and q.name != p.name and q.name not in p.opponents:
                pairs.append((p, q))
                paired.add(p.name)
                paired.add(q.name)
                break
    return pairs

def buchholz(player, all_players):
    lookup = {p.name: p for p in all_players}
    return sum(lookup[o].score for o in player.opponents)

# ================= STATE =================
if "players" not in st.session_state:
    st.session_state.players = []
if "round" not in st.session_state:
    st.session_state.round = 0
if "total_rounds" not in st.session_state:
    st.session_state.total_rounds = 0
if "pairs" not in st.session_state:
    st.session_state.pairs = []

# ================= UI =================
st.title("♟️ Challenge Cup Tournament Surya Nusantara")

st.header("Setup Turnamen")
n = st.number_input("Jumlah peserta", min_value=2, step=1)
names = [st.text_input(f"Nama peserta {i+1}", key=f"name_{i}") for i in range(int(n))]
rmin = st.number_input("Ronde minimum", min_value=1, step=1)
rmax = st.number_input("Ronde maksimum", min_value=1, step=1)

if st.button("Mulai Turnamen"):
    st.session_state.players = [Player(nm) for nm in names]
    st.session_state.round = 1
    st.session_state.total_rounds = choose_rounds(len(names), rmin, rmax)
    st.session_state.pairs = []

st.divider()

# ================= TURNAMEN =================
if 0 < st.session_state.round <= st.session_state.total_rounds:

    st.subheader(f"Ronde {st.session_state.round} / {st.session_state.total_rounds}")

    if not st.session_state.pairs:
        if st.session_state.round == 1:
            st.session_state.pairs = random_pair(st.session_state.players)
        else:
            st.session_state.pairs = swiss_pair(st.session_state.players)

    for i, (p, q) in enumerate(st.session_state.pairs):
        st.write(f"**{p.name} vs {q.name}**")
        st.selectbox(
            "Hasil",
            ["Belum", f"{p.name} menang", "Seri", f"{q.name} menang"],
            key=f"res_{st.session_state.round}_{i}"
        )

    if st.button("Simpan hasil ronde"):
        for i, (p, q) in enumerate(st.session_state.pairs):
            res = st.session_state.get(f"res_{st.session_state.round}_{i}")
            if res == f"{p.name} menang":
                p.score += 1
            elif res == "Seri":
                p.score += 0.5
                q.score += 0.5
            elif res == f"{q.name} menang":
                q.score += 1
            p.opponents.add(q.name)
            q.opponents.add(p.name)

        st.session_state.round += 1
        st.session_state.pairs = []
        st.rerun()

# ================= KLASMEN =================
if st.session_state.players:
    st.divider()
    st.subheader("Klasemen")

    players = st.session_state.players

    for p in players:
        raw = buchholz(p, players)
        p.buchholz = round(raw * BUCHHOLZ_SCALE, 2)

    table = sorted(players, key=lambda p: (-p.score, -p.buchholz, p.name))

    rows = []
    rank = 1
    for p in table:
        rows.append({
            "Rank": rank,
            "Nama": p.name,
            "Skor": round(p.score, 1),
            "Tie-Break": round(p.buchholz, 2)
        })
        rank += 1

    df = pd.DataFrame(rows)

    # Pastikan tipe numerik benar
    df["Rank"] = df["Rank"].astype(int)
    df["Skor"] = df["Skor"].astype(float)
    df["Tie-Break"] = df["Tie-Break"].map(lambda x: f"{x:.2f}".rstrip("0").rstrip("."))
    df["Skor"] = df["Skor"].map(lambda x: int(x) if x.is_integer() else x)

    styled = df.style.set_properties(**{
        "text-align": "center"
    }).set_table_styles([
        {"selector": "th", "props": [("text-align", "center")]}
    ])

    st.dataframe(styled, hide_index=True, use_container_width=True)
