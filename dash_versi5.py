# === Cement Quality Recorder | SIG – Product Quality Assurance ===
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import os

# =================== Konfigurasi Halaman ====================
st.set_page_config(page_title="Cement Quality Recorder | SIG – PQA", layout="wide")

# Logo ----------------------------------------------------------------------
if os.path.exists("SIG_logo.png"):
    st.image("SIG_logo.png", width=120)

# =================== CSS ====================================================
st.markdown(
    """
    <style>
    html, body {font-family: 'Inter', sans-serif; background: linear-gradient(90deg,#f8f8f8 0%, #ffffff 50%);}    
    .block-container {background:#fff;padding:2rem;border-radius:16px;
                      box-shadow:0 8px 24px rgba(0,0,0,.07);}    
    .stButton>button{background:#d71920;color:#fff;font-weight:600;border:none;border-radius:8px;padding:10px 20px}
    .stButton>button:hover{background:#b3161c}
    .stDownloadButton>button{color:#d71920;border:1px solid #d71920;background:#fff}
    .stDownloadButton>button:hover{background:#d71920;color:#fff}
    </style>""",
    unsafe_allow_html=True,
)

# =================== Utilitas ===============================================

def _clean_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Ganti koma → titik & konversi kolom numerik ke float."""
    num_cols = df.columns.difference(["Tanggal", "Silo", "Peneliti"])
    for col in num_cols:
        df[col] = (
            df[col].astype(str)
            .str.replace(r"\s", "", regex=True)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# =================== Session State ==========================================
if "data_list" not in st.session_state:
    st.session_state.data_list = []

# =================== HEADER =================================================
st.title("📈 Cement Quality Recorder | SIG – Product Quality Assurance")
st.markdown("""<small>Proyek Kerja Praktek – PT Semen Indonesia (Persero) Tbk & Institut Teknologi Sepuluh Nopember</small>""", unsafe_allow_html=True)
st.markdown("---")

# =================== Sidebar Input ==========================================
st.sidebar.header("✍️ Input Data Manual")
Tanggal  = st.sidebar.date_input("Tanggal")
Silo     = st.sidebar.text_input("Silo")
Peneliti = st.sidebar.text_input("Peneliti")

cols = st.sidebar.columns(2)
num_fields = [
    "SiO2","Al2O3","Fe2O3","CaO","MgO","SO3","C3S","C2S","C3A","C4AF",
    "FL","LOI","Residu","Blaine","Insoluble","Na2O","K2O",
    "Kuat Tekan 1 Hari","Kuat Tekan 3 Hari","Kuat Tekan 7 Hari","Kuat Tekan 28 Hari",
    "Setting Time Awal","Setting Time Akhir"
]
values = {}
for i, field in enumerate(num_fields):
    col = cols[i % 2]
    values[field] = col.number_input(field, step=0.01)

if st.sidebar.button("✅ Simpan Data"):
    st.session_state.data_list.append([
        Tanggal, Silo, Peneliti, *[values[f] for f in num_fields]
    ])
    st.sidebar.success("Data tersimpan!")

# -------------------- Upload Excel ---------------------
st.sidebar.markdown("---")
st.sidebar.header("📥 Upload Excel (.xlsx)")
up_file = st.sidebar.file_uploader("Pilih file", type=["xlsx"])
if up_file is not None:
    up_df = pd.read_excel(up_file)
    up_df = _clean_numeric(up_df)
    st.session_state.data_list.extend(up_df.values.tolist())
    st.sidebar.success("Data Excel ditambahkan!")

# =================== DataFrame ==============================================
cols_all = ["Tanggal","Silo","Peneliti",*num_fields]
df = pd.DataFrame(st.session_state.data_list, columns=cols_all)
if not df.empty:
    df = _clean_numeric(df)

# =================== Tabs ====================================================
view_data, view_stats, view_viz, view_about = st.tabs([
    "📋 Data","📈 Statistik","📊 Visualisasi","👥 Tentang Kami"
])

# ===== DATA =====
with view_data:
    st.subheader("📋 Data Tersimpan")
    if not df.empty:
        for i in range(len(df)):
            col1, col2 = st.columns([10, 1])
            col1.write(df.iloc[i:i+1])
            if col2.button("🗑️", key=f"del_{i}"):
                st.session_state.data_list.pop(i)
                st.rerun()
        buff = io.BytesIO()
        with pd.ExcelWriter(buff, engine="xlsxwriter") as w:
            pd.DataFrame(st.session_state.data_list, columns=cols_all).to_excel(w, index=False, sheet_name="Data")
        st.download_button("⬇️ Download Excel", buff.getvalue(), "cement_quality.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Belum ada data.")
        
# ===== STATISTIK =====
with view_stats:
    st.subheader("📈 Statistik Deskriptif")
    if df.empty:
        st.info("Belum ada data.")
    else:
        st.dataframe(df.describe(), use_container_width=True)

# ===== VISUALISASI =====
with view_viz:
    st.subheader("📊 Visualisasi Data")
    if df.empty:
        st.info("Belum ada data.")
    else:
        df["Tanggal"] = pd.to_datetime(df["Tanggal"], errors="coerce")
        df.sort_values("Tanggal", inplace=True)
        df["Bulan"] = df["Tanggal"].dt.to_period("M").astype(str)

        X_vars  = df.columns[3:19]
        Y_tekan = [f"Kuat Tekan {i} Hari" for i in (1,3,7,28)]
        Y_set   = ["Setting Time Awal","Setting Time Akhir"]

        # ---------- 1) Boxplot X ----------
        st.markdown("#### 1. Distribusi Variabel X per Bulan")
        var_x = st.selectbox("Pilih Variabel X", X_vars, key="box")
        fig1 = px.box(df, x="Bulan", y=var_x, color="Bulan", title=f"Distribusi {var_x} per Bulan")
        st.plotly_chart(fig1, use_container_width=True)

        # ---------- 2) Setting Time (Bar) + Overlay X (Line) ----------
        st.markdown("#### 2. Setting Time + Overlay Variabel X")
        var_overlay = st.selectbox("Pilih Variabel X untuk overlay", X_vars, key="overlay")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        for y in Y_set:
            fig2.add_trace(go.Bar(x=df["Tanggal"], y=df[y], name=y), secondary_y=False)
        fig2.add_trace(
            go.Scatter(x=df["Tanggal"], y=df[var_overlay], mode="lines+markers", name=var_overlay, line=dict(width=2)),
            secondary_y=True
        )
        fig2.update_layout(title="Setting Time vs " + var_overlay, barmode="group")
        fig2.update_yaxes(title_text="Setting Time (menit)", secondary_y=False)
        fig2.update_yaxes(title_text=var_overlay, secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

        # ---------- 3) Trend Kuat Tekan ----------
        st.markdown("#### 3. Trend Kuat Tekan 1, 3, 7, 28 Hari")
        fig3 = go.Figure()
        for y in Y_tekan:
            fig3.add_trace(go.Scatter(x=df["Tanggal"], y=df[y], mode="lines+markers", name=y))
        fig3.update_layout(title="Kuat Tekan per Tanggal", xaxis_title="Tanggal", yaxis_title="Kuat Tekan (MPa)")
        st.plotly_chart(fig3, use_container_width=True)

# ===== TENTANG KAMI =====
with view_about:
    st.subheader("👥 Tim & Pembimbing")

    # ---------- Pembimbing ----------
    col_sup, col_ad = st.columns([1, 2])
    with col_sup:
        st.markdown("#### Pembimbing Lapangan")
        st.markdown("Heru Enggar Triantoro, S.T., M.Eng.")
    with col_ad:
        st.markdown("#### Dosen Pembimbing")
        st.markdown("1. Prof. Dr. Muhammad Mashuri, M.T.  ")
        st.markdown("2. Diaz Fitra Aksioma, S.Si., M.Si.")

    st.markdown("---")
    st.markdown("#### Tim Kolaborator Mahasiswa")

    cols_pic = st.columns(2, gap="large")
    # Foto Fitri
    if os.path.exists("fitri.jpg"):
        cols_pic[0].image("fitri.jpg", width=160, caption="Fitri Fatma Dewi (5003221031)")
    else:
        cols_pic[0].markdown("Fitri Fatma Dewi (5003221031)")

    # Foto Devi
    if os.path.exists("devi.jpg"):
        cols_pic[1].image("devi.jpg", width=160, caption="Devi Sagita Rachman (5003221172)")
    else:
        cols_pic[1].markdown("Devi Sagita Rachman (5003221172)")
