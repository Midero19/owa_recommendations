import streamlit as st
import pandas as pd
import numpy as np
import os
import gdown

# Désactive le reload de fichiers pour gagner du temps
os.environ["STREAMLIT_WATCH_DISABLE"] = "true"

# --- Configuration de la page ---
st.set_page_config(page_title="Moteur de recommandations", layout="wide")

# --- Chargement et prétraitement des données (caché) ---
FILE_ID = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
OUTPUT_PATH = "final_owa.csv"

@st.cache_data(show_spinner=False)
def load_data(path: str, file_id: str) -> pd.DataFrame:
    if not os.path.exists(path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=True)
    df = pd.read_csv(
        path, sep=";", encoding="utf-8", on_bad_lines="skip",
        engine="python", dtype={"visitor_id": str}
    )
    df.fillna(0, inplace=True)
    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(
        df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce'
    )
    cluster_labels = {
        0: "Utilisateurs actifs",
        1: "Visiteurs occasionnels",
        3: "Engagement moyen",
        4: "Nouveaux utilisateurs",
        6: "Explorateurs passifs"
    }
    df['profil'] = df['cluster'].map(cluster_labels)
    conds = [
        (df['is_bounce'] == 1) | (df['bounce_rate'] > 80),
        (df['num_pageviews'] > 10) & (df['num_actions'] < 3),
        (df['avg_session_duration'] > 300) & (df['num_actions'] < 3),
        (df['num_actions'] > 10) | (df['num_comments'] > 3)
    ]
    choices = [
        "💤 Volatile",
        "🧠 Lecteur curieux",
        "⚡ Engagé silencieux",
        "💥 Utilisateur très actif"
    ]
    df['interaction_type'] = np.select(conds, choices, default="📌 Standard")
    return df

with st.spinner("Chargement et prétraitement des données..."):
    df = load_data(OUTPUT_PATH, FILE_ID)

reco_map = {
    "💤 Volatile": {...},
    "🧠 Lecteur curieux": {...},
    "⚡ Engagé silencieux": {...},
    "💥 Utilisateur très actif": {...},
    "📌 Standard": {...}
}
dom_reco_map = {...}

# --- Barre latérale : filtres ---
st.sidebar.header("🎯 Filtres utilisateur")
filters = {
    "Date de clic": ["Toutes"] + sorted(df['yyyymmdd_click'].dt.date.unique()),
    "Session ID": ["Tous"] + sorted(df['session_id'].unique()),
    "Visitor ID": ["Tous"] + sorted(df['visitor_id'].unique()),
    "Nom d'utilisateur": ["Tous"] + sorted(df['user_name_click'].astype(str).unique()),
    "Niveau de risque": ["Tous"] + sorted(df['risk_level'].astype(str).unique())
}
selected = {k: st.sidebar.selectbox(f"{k} :", v) for k, v in filters.items()}

# --- Application des filtres ---
fd = df.copy()
if selected["Date de clic"] != "Toutes":
    fd = fd[fd['yyyymmdd_click'].dt.date == selected["Date de clic"]]
for key, col in [
    ("Session ID", 'session_id'),
    ("Visitor ID", 'visitor_id'),
    ("Nom d'utilisateur", 'user_name_click'),
    ("Niveau de risque", 'risk_level')
]:
    val = selected[key]
    if val != "Tous":
        fd = fd[fd[col].astype(str) == val]
if fd.empty:
    st.warning("Aucun résultat pour ces filtres.")
    st.stop()

@st.cache_data(show_spinner=False)
def compute_grouped(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby(['visitor_id', 'user_name_click']).agg(
        first_click=('yyyymmdd_click','min'),
        profil=('profil', lambda x: x.mode().iat[0]),
        interaction=('interaction_type', lambda x: x.mode().iat[0]),
        risk=('risk_level','max'),
        engagement=('engagement_score','mean')
    ).reset_index()

gg = compute_grouped(fd)

st.markdown(f"**Clics :** {len(fd)} • **Utilisateurs :** {fd['visitor_id'].nunique()}")
cols = st.columns(2)
cols[0].bar_chart(gg['profil'].value_counts())
if selected["Visitor ID"] == "Tous":
    ser = fd.groupby('yyyymmdd_click')['engagement_score'].mean()
else:
    ser = fd[fd['visitor_id'] == selected["Visitor ID"]]['engagement_score']
cols[1].line_chart(ser)
st.dataframe(gg)

st.header("✅ Recommandations personnalisées")
dom_mode = df.groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iat[0] if not x.mode().empty else None)
for i, row in gg.iterrows():
    rec = reco_map.get(row['interaction'])
    if not rec:
        continue
    with st.expander(f"👤 {row['user_name_click']} – {row['interaction']} (profil: {row['profil']})"):
        st.write(f"**Objectif :** {rec['objectif']}")
        st.write(f"**Action :** {rec['action']}")
        st.write(f"**Ton :** {rec['ton']}")
        st.write(f"**Canal :** {rec['canal']}")
        st.write(f"**CTA :** {rec['cta']}")
        dom = dom_mode.get(row['visitor_id'])
        if pd.notna(dom) and dom in dom_reco_map:
            d = dom_reco_map[dom]
            st.write(f"🔍 DOM : {dom} – {d['objectif']}, {d['action']}")
