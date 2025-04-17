import streamlit as st
import pandas as pd
import numpy as np
import os
import gdown
import re

# --- Configuration de la page ---
st.set_page_config(page_title="Moteur de recommandations", layout="wide")

# --- En-tête ---
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #4CAF50; font-size: 3rem;'>🧠 Moteur de recommandations utilisateurs</h1>
    <p style='color: grey;'>Analyse comportementale et suggestions personnalisées en un clic</p>
</div>
""", unsafe_allow_html=True)

# --- Chargement et prétraitement des données (caché) ---
file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

@st.cache_data(show_spinner=False)
def load_data(path: str, file_id: str) -> pd.DataFrame:
    if not os.path.exists(path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=True)
    df = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8",
        on_bad_lines="skip",
        engine="python",
        dtype={"visitor_id": str}
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
        (df['num_actions'] > 10) | (df['num_comments'] > 3),
    ]
    choices = ["💤 Volatile", "🧠 Lecteur curieux", "⚡ Engagé silencieux", "💥 Utilisateur très actif"]
    df['interaction_type'] = np.select(conds, choices, default="📌 Standard")
    return df

with st.spinner("Chargement et prétraitement des données..."):
    df = load_data(output_path, file_id)

# --- Mappages de recommandations statiques ---
reco_map = { ... }  # inchangé
dom_reco_map = { ... }  # inchangé

# --- Barre latérale : filtres dynamiques ---
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
filters = {
    "Date de clic": ["Toutes"] + all_dates,
    "Session ID": ["Tous"] + sorted(df['session_id'].dropna().astype(str).unique()),
    "Visitor ID": ["Tous"] + sorted(df['visitor_id'].dropna().astype(str).unique()),
    "Niveau de risque": ["Tous"] + sorted(df['risk_level'].dropna().astype(str).unique())
}
# Ajouter le filtre Nom d'utilisateur seulement si la colonne existe
def add_user_filter():
    if 'user_name_click' in df.columns:
        uniques = sorted(df['user_name_click'].dropna().astype(str).unique())
        filters["Nom d'utilisateur"] = ["Tous"] + uniques
add_user_filter()
selected = {label: st.sidebar.selectbox(f"{label} :", opts) for label, opts in filters.items()}

# --- Application des filtres ---
filtered_df = df.copy()
for label, val in selected.items():
    if val not in ["Toutes", "Tous"]:
        if label == "Date de clic":
            filtered_df = filtered_df[filtered_df['yyyymmdd_click'].dt.date == val]
        else:
            col_key = 'user_name_click' if label == "Nom d'utilisateur" else label.lower().replace(' ', '_')
            filtered_df = filtered_df[filtered_df[col_key].astype(str) == str(val)]
if filtered_df.empty:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
    st.stop()

# --- Calcul groupé (caché) ---
@st.cache_data(show_spinner=False)
def compute_grouped(df_grp: pd.DataFrame) -> pd.DataFrame:
    return df_grp.groupby(['visitor_id', 'user_name_click']).agg({
        'yyyymmdd_click': 'min',
        'profil': lambda x: x.mode().iloc[0],
        'interaction_type': lambda x: x.mode().iloc[0],
        'risk_level': 'max',
        'engagement_score': 'mean'
    }).reset_index()

grouped_df = compute_grouped(filtered_df)

# --- Affichage des métriques et graphiques ---
st.markdown(f"**Nombre de clics :** {len(filtered_df)}  |  **Utilisateurs uniques :** {filtered_df['visitor_id'].nunique()}")
col1, col2 = st.columns(2)
col1.bar_chart(grouped_df['profil'].value_counts(), use_container_width=True)
series_eng = (
    filtered_df.groupby('yyyymmdd_click')['engagement_score'].mean()
    if selected['Visitor ID'] == 'Tous'
    else filtered_df[filtered_df['visitor_id'].astype(str) == selected['Visitor ID']]['engagement_score']
)
col2.line_chart(series_eng, use_container_width=True)

# --- Tableau des données ---
st.dataframe(grouped_df, use_container_width=True)

# --- Recommandations personnalisées ---
st.header("✅ Recommandations personnalisées")
dom_mode = df.groupby('visitor_id')['dom_element_id'] \
             .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)
for idx, row in enumerate(grouped_df.itertuples()):
    with st.expander(f"👤 {row.user_name_click} – {row.interaction_type} (profil: {row.profil}, risque: {row.risk_level})"):
        rec = reco_map[row.interaction_type]
        st.write(f"**Objectif :** {rec['objectif']}")
        # ... autres champs
        key = f"dom_{row.visitor_id}_{idx}"
        if st.checkbox("🔍 Voir recommandation DOM", key=key):
            dom = dom_reco_map.get(dom_mode[row.visitor_id])
            if dom:
                st.write(f"**Élément :** {dom_mode[row.visitor_id]}")
                st.write(f"**Objectif :** {dom['objectif']}")
                st.write(f"**Action :** {dom['action']}")
                st.write(f"**Ton :** {dom['ton']}")
                st.write(f"**Canal :** {dom['canal']}")
                st.write(f"**CTA :** {dom['cta']}")

else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
