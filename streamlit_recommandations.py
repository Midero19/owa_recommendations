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
    # Téléchargement si inexistant
    if not os.path.exists(path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=True)
    # Lecture
    df = pd.read_csv(
        path, sep=";", encoding="utf-8", on_bad_lines="skip",
        engine="python", dtype={"visitor_id": str}
    )
    # Nettoyage
    df.fillna(0, inplace=True)
    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(
        df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce'
    )
    # Mapping de profils
    cluster_labels = {
        0: "Utilisateurs actifs",
        1: "Visiteurs occasionnels",
        3: "Engagement moyen",
        4: "Nouveaux utilisateurs",
        6: "Explorateurs passifs"
    }
    df['profil'] = df['cluster'].map(cluster_labels)
    # Classification vectorisée des interactions
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

# --- Mappages de recommandations ---
reco_map = {
    "💤 Volatile": {
        "objectif": "Réduire l’abandon à froid dès la première visite",
        "action": "Relancer par email ou push dans l'heure avec un contenu percutant",
        "ton": "Intrigant, FOMO",
        "canal": "Push / Email",
        "cta": "⏱ Découvrez ce que vous avez manqué en 60s !"
    },
    "🧠 Lecteur curieux": {
        "objectif": "Transformer la curiosité en interaction",
        "action": "Afficher quiz ou bouton 'suivre le thème'",
        "ton": "Complice, engageant",
        "canal": "Popup + Email",
        "cta": "📚 Activez suggestions sur vos lectures"
    },
    "⚡ Engagé silencieux": {
        "objectif": "Lever les freins invisibles à l'action",
        "action": "Ajouter un bouton de réaction ou question douce",
        "ton": "Encourageant, chaleureux",
        "canal": "Interface + Email",
        "cta": "👍 Vous avez aimé ? Faites-le savoir"
    },
    "💥 Utilisateur très actif": {
        "objectif": "Prévenir frustration d'un utilisateur très impliqué",
        "action": "Offrir contenu VIP ou invitation à contribuer",
        "ton": "Valorisant, exclusif",
        "canal": "Email perso + Interface",
        "cta": "🏅 Merci pour votre activité ! Avant-goût exclusif"
    },
    "📌 Standard": {
        "objectif": "Créer un déclic d'intérêt",
        "action": "Envoyer sélection des contenus populaires",
        "ton": "Positif, informatif",
        "canal": "Email hebdo",
        "cta": "📬 Découvrez les contenus phares"
    }
}

dom_reco_map = {
    "nav_menu_link": {"objectif": "Faciliter accès rapide", "action": "Adapter nav selon préférences", "ton": "Clair", "canal": "Interface + Email", "cta": "🔎 Naviguez plus vite"},
    "read_more_btn": {"objectif": "Proposer contenu approfondi", "action": "Recommander articles longs", "ton": "Expert", "canal": "Email dossier", "cta": "📘 Découvrez la série"},
    "search_bar": {"objectif": "Anticiper recherches", "action": "Créer suggestions/alertes", "ton": "Pratique", "canal": "Interface + Notification", "cta": "🔔 Activez alertes"},
    "video_player": {"objectif": "Fidéliser via vidéo", "action": "Proposer playlist", "ton": "Immersif", "canal": "Interface Vidéo", "cta": "🎬 Votre sélection vidéo"},
    "comment_field": {"objectif": "Encourager expression", "action": "Promouvoir débats", "ton": "Communautaire", "canal": "Interface + Email", "cta": "💬 Rejoignez la discussion"}
}

# --- Barre latérale : filtres ---
st.sidebar.header("🎯 Filtres utilisateur")
filters = {
    'Date de clic': ['Toutes'] + sorted(df['yyyymmdd_click'].dt.date.unique()),
    'Session ID': ['Tous'] + sorted(df['session_id'].unique()),
    'Visitor ID': ['Tous'] + sorted(df['visitor_id'].unique()),
    'Nom d'utilisateur': ['Tous'] + sorted(df['user_name_click'].astype(str).unique()),
    'Niveau de risque': ['Tous'] + sorted(df['risk_level'].astype(str).unique())
}
selected = {k: st.sidebar.selectbox(f"{k} :", v) for k, v in filters.items()}

# --- Application des filtres ---
fd = df.copy()
# Date
if selected['Date de clic'] != 'Toutes':
    fd = fd[fd['yyyymmdd_click'].dt.date == selected['Date de clic']]
# Autres
for key, col in [('Session ID', 'session_id'), ('Visitor ID', 'visitor_id'), ('Nom d'utilisateur', 'user_name_click'), ('Niveau de risque', 'risk_level')]:
    val = selected[key]
    if val != 'Tous':
        fd = fd[fd[col].astype(str) == val]
if fd.empty:
    st.warning("Aucun résultat pour ces filtres.")
    st.stop()

# --- Calcul groupé (caché) ---
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

# --- Affichage ---
st.markdown(f"**Clics :** {len(fd)} • **Utilisateurs :** {fd['visitor_id'].nunique()}")
cols = st.columns(2)
cols[0].bar_chart(gg['profil'].value_counts())
# Engagement
if selected['Visitor ID'] == 'Tous':
    ser = fd.groupby('yyyymmdd_click')['engagement_score'].mean()
else:
    ser = fd[fd['visitor_id'] == selected['Visitor ID']]['engagement_score']
cols[1].line_chart(ser)
st.dataframe(gg)

# --- Recommandations ---
st.header("✅ Recommandations personnalisées")
dom_mode = df.groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iat[0] if not x.mode().empty else None)
for i, row in gg.iterrows():
    rec = reco_map.get(row['interaction'])
    if not rec: continue
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
