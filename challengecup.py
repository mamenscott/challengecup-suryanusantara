import streamlit as st
import random
import math

st.set_page_config(page_title="Challenge Cup Tournament", layout="centered")

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0.0
        self.opponents = set()

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

# ================= STATE INIT =================
if "players" not in st.session_state:
    st.session_state.players = []
if "round" not in st.session_state:
    st.session_state.round = 0
if "total_rounds" not in st.session_state:
    st.session_state.total_rounds = 0
if "pairs" not in st.session_state:
    st.session_state.pairs = []
if "results" not in st.session_state:
    st.session_state.results = {}

# ================= UI =================
st.title("♟️ Challenge Cup Tournament Surya Nusantara")

st.header("Setup")
n = st.number_input("Jumlah peserta", min_value=2, step=1)
names = [st.text_input(f"Nama peserta {i+1}", key=f"name_{i}") for i in range(int(n))]
rmin = st.number_input("Ronde minimum", min_value=1, step=1)
rmax = st.number_input("Ronde maksimum", min_value=1, step=1)

if st.button("Mulai Turnamen"):
    st.session_state.players = [Player(nm) for nm in names]
    st.session_state.round = 1
    st.session_state.total_rounds = choose_rounds(len(names), rmin, rmax)
    st.session_state.pairs = []
    st.session_state.results = {}

st.divider()

# ================= TURNAMEN =================
if st.session_state.round > 0 and st.session_state.round <= st.session_state.total_rounds:

    st.subheader(f"Ronde {st.session_state.round} / {st.session_state.total_rounds}")

    if not st.session_state.pairs:
        if st.session_state.round == 1:
            st.session_state.pairs = random_pair(st.session_state.players)
        else:
            st.session_state.pairs = swiss_pair(st.session_state.players)

    for i, (p, q) in enumerate(st.session_state.pairs):
        key = f"res_{st.session_state.round}_{i}"
        st.write(f"**{p.name} vs {q.name}**")
        st.selectbox(
            "Hasil",
            ["Belum", f"{p.name} menang", "Seri", f"{q.name} menang"],
            key=key
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
    table = sorted(st.session_state.players, key=lambda p: (-p.score, p.name))
    st.table([[p.name, p.score] for p in table])
