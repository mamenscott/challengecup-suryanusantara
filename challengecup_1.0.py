import streamlit as st
import random
import math
import pandas as pd
import json
import os

STATE_FILE = "tournament_state.json"

PERATURAN_TEXT = """
## ♟️ Penjelasan Sistem Skor & Peringkat Turnamen

Untuk menghindari kebingungan dalam membaca klasemen, berikut kami sampaikan penjelasan sistem penilaian yang digunakan pada turnamen ini.

### 1. Sistem Turnamen
Turnamen ini menggunakan Sistem Swiss, di mana:
- Semua peserta bermain di setiap ronde (tidak ada sistem gugur).
- Lawan di setiap ronde ditentukan berdasarkan perolehan skor sementara.

### 2. Sistem Skor
Perolehan poin ditentukan sebagai berikut:

| Hasil | Poin |
|------|------|
| Menang | 1 poin |
| Seri | 0,5 poin |
| Kalah | 0 poin |

Kolom Skor pada klasemen menunjukkan jumlah total poin yang diperoleh dari seluruh ronde.

### 3. Sistem Tie-Break
Apabila terdapat dua atau lebih peserta dengan Skor yang sama, maka peringkat ditentukan menggunakan nilai Tie-Break.

Tie-Break yang digunakan adalah **Buchholz**, yaitu jumlah total skor dari seluruh lawan yang pernah dihadapi oleh peserta tersebut.

Artinya:
- Peserta yang menghadapi lawan dengan performa lebih kuat akan memiliki nilai Tie-Break yang lebih tinggi.
- Tie-Break tidak menambah poin, tetapi hanya digunakan untuk membedakan peringkat apabila skor sama.

### 4. Skala Tie-Break
Nilai Tie-Break ditampilkan dalam skala kecil (misalnya 0,5; 0,8; 0,9) agar tidak mengganggu nilai Skor utama dan hanya berfungsi sebagai pembeda.

### 5. Urutan Penentuan Peringkat
Peringkat ditentukan berdasarkan urutan berikut:
1. Skor tertinggi
2. Jika skor sama → Tie-Break tertinggi

### 6. Contoh

| Nama | Skor | Tie-Break |
|------|------|-----------|
| A | 3 | 0,8 |
| B | 3 | 0,6 |

Peserta A berada di atas peserta B karena meskipun skor sama, A menghadapi lawan yang secara keseluruhan lebih kuat.

---

Dengan sistem ini diharapkan peringkat dapat mencerminkan tidak hanya jumlah kemenangan, tetapi juga tingkat kesulitan lawan yang dihadapi oleh masing-masing peserta.

Terima kasih atas partisipasi Bapak/Ibu sekalian, dan selamat mengikuti turnamen. Semoga kegiatan ini berjalan lancar dan menyenangkan ♟️
"""


st.set_page_config(page_title="Challenge Cup Turnamen", layout="centered")

# ================= CSS =================
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1, h2, h3 { text-align:center; }
    .stButton>button { width:100%; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ================= CONFIG =================
BUCHHOLZ_SCALE = 0.1
USERS = {
    "panitia": {"password": "123456789", "role": "panitia"},
    "peserta": {"password": "1234", "role": "peserta"}
}

# ================= DATA =================
class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0.0
        self.opponents = set()
        self.buchholz = 0.0

def save_state():
    data = {
        "players": [
            {
                "name": p.name,
                "score": p.score,
                "opponents": list(p.opponents),
                "buchholz": p.buchholz
            }
            for p in st.session_state.players
        ],
        "round": st.session_state.round,
        "total_rounds": st.session_state.total_rounds,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(data, f)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            data = json.load(f)

        players = []
        for p in data.get("players", []):
            pl = Player(p["name"])
            pl.score = p["score"]
            pl.opponents = set(p["opponents"])
            pl.buchholz = p.get("buchholz", 0.0)
            players.append(pl)

        st.session_state.players = players
        st.session_state.round = data.get("round", 0)
        st.session_state.total_rounds = data.get("total_rounds", 0)

# ================= FUNCTIONS =================
def choose_rounds(n, rmin, rmax):
    return max(rmin, min(rmax, math.ceil(math.log2(n))))

def random_pair(players):
    p = players[:]
    random.shuffle(p)
    return [(p[i], p[i+1]) for i in range(0, len(p), 2)]

def swiss_pair(players):
    sorted_players = sorted(players, key=lambda x: (-x.score, x.name))
    paired, pairs = set(), []
    for p in sorted_players:
        if p.name in paired: continue
        for q in sorted_players:
            if q.name not in paired and q.name != p.name and q.name not in p.opponents:
                pairs.append((p,q))
                paired.add(p.name)
                paired.add(q.name)
                break
    return pairs

def buchholz(player, players):
    lookup = {p.name:p for p in players}
    return sum(lookup[o].score for o in player.opponents)

# ================= STATE =================
for k,v in {"players":[], "round":0, "total_rounds":0, "pairs":[], "user":None, "role":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================= LOGIN =================
if st.session_state.user is None:
    st.title("Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.user = u
            st.session_state.role = USERS[u]["role"]
            load_state()
            st.rerun()
        else:
            st.error("Login gagal")
    st.stop()

# ================= SIDEBAR =================
if st.session_state.role == "panitia":
    menu = st.sidebar.radio("Navigasi", ["Setup", "Ronde", "Klasemen", "Peraturan"])
else:
    menu = st.sidebar.radio("Navigasi", ["Klasemen", "Peraturan"])


# ================= SETUP =================
if menu == "Setup":
    if st.session_state.role != "panitia":
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        st.stop()
    st.header("🛠 Setup Turnamen")
    n = st.number_input("Jumlah peserta", 2, step=1)
    names = [st.text_input(f"Nama peserta {i+1}", key=f"n{i}") for i in range(n)]
    rmin = st.number_input("Ronde minimum", 1, step=1)
    rmax = st.number_input("Ronde maksimum", 1, step=1)

    if st.button("Mulai Turnamen"):
        st.session_state.players = [Player(nm) for nm in names]
        st.session_state.round = 1
        st.session_state.total_rounds = choose_rounds(len(names), rmin, rmax)
        st.session_state.pairs = []
        save_state()
# ================= RONDE =================
elif menu == "Ronde":
    if st.session_state.role != "panitia":
        st.warning("Anda tidak memiliki akses ke halaman ini.")
        st.stop()
    st.header("♟ Ronde Pertandingan")
    if st.session_state.round == 0:
        st.info("Turnamen belum dimulai")
    elif st.session_state.round > st.session_state.total_rounds:
        st.success("Turnamen selesai")
    else:
        st.write(f"Ronde {st.session_state.round}/{st.session_state.total_rounds}")
        if not st.session_state.pairs:
            st.session_state.pairs = random_pair(st.session_state.players) if st.session_state.round==1 else swiss_pair(st.session_state.players)

        for i,(p,q) in enumerate(st.session_state.pairs):
            st.write(f"{p.name} vs {q.name}")
            st.selectbox("Hasil", ["Belum", f"{p.name} menang", "Seri", f"{q.name} menang"], key=f"res_{i}")

        if st.button("Simpan hasil"):
            for i,(p,q) in enumerate(st.session_state.pairs):
                res = st.session_state[f"res_{i}"]
                if res == f"{p.name} menang": p.score +=1
                elif res == "Seri": p.score +=0.5; q.score +=0.5
                elif res == f"{q.name} menang": q.score +=1
                p.opponents.add(q.name); q.opponents.add(p.name)
            st.session_state.round +=1
            st.session_state.pairs = []
            save_state()
            st.rerun()

# ================= KLASMEN =================
elif menu == "Klasemen":
    st.header("🏆 Klasemen Challange Cup Surya Nusantara")
    for p in st.session_state.players:
        p.buchholz = round(buchholz(p, st.session_state.players)*BUCHHOLZ_SCALE,2)
    data = [{"Nama":p.name,"Skor":p.score,"Tie-Break":p.buchholz} for p in sorted(st.session_state.players, key=lambda x:(-x.score,-x.buchholz))]
    st.dataframe(pd.DataFrame(data), use_container_width=True)

# ================= PERATURAN =================

elif menu == "Peraturan":
    st.header("Peraturan")
    st.markdown(PERATURAN_TEXT, unsafe_allow_html=True)

st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"user":None}))

