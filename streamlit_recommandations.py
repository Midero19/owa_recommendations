import streamlit as st
import pandas as pd
import os
import gdown
import matplotlib.pyplot as plt

# 🎨 Config de page Streamlit
st.set_page_config(
    page_title="OWA – Recommandations Utilisateurs",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<h1 style='text-align: center;'>📊 OWA – Moteur de recommandations</h1>
""", unsafe_allow_html=True)
st.markdown("---")

# 🗖️ Téléchargement des données
os.environ["STREAMLIT_WATCH_DISABLE"] = "true"
file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

@st.cache_data
def load_data():
    if not os.path.exists(output_path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)
    df = pd.read_csv(
        output_path,
        sep=";",
        encoding="utf-8",
        on_bad_lines="skip",
        engine="python",
        dtype={"visitor_id": str}
    )
    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce')
    df['user_name_click'] = df['user_name_click'].fillna("Inconnu")
    df['profil'] = df['cluster'].map(cluster_labels)
    df['interaction_type'] = df.apply(classify_interaction, axis=1)
    return df

@st.cache_data
def get_dom_by_visitor(df):
    return df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

def safe_mode(series):
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else "Non défini"

def classify_interaction(row):
    if row['is_bounce'] == 1 or row['bounce_rate'] > 80:
        return "🛌 Volatile"
    elif row['num_pageviews'] > 10 and row['num_actions'] < 3:
        return "🧠 Lecteur curieux"
    elif row['avg_session_duration'] > 300 and row['num_actions'] < 3:
        return "⚡ Engagé silencieux"
    elif row['num_actions'] > 10 or row['num_comments'] > 3:
        return "💥 Utilisateur très actif"
    else:
        return "📌 Standard"

# Données utilisateur
cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}

# Recommandations
interaction_types = ["💥 Utilisateur très actif", "⚡ Engagé silencieux", "🧠 Lecteur curieux", "🛌 Volatile", "📌 Standard"]
profils = ["Utilisateurs actifs", "Visiteurs occasionnels", "Engagement moyen", "Nouveaux utilisateurs", "Explorateurs passifs"]
dom_elements = ["default", "nav_menu_link", "read_more_btn", "search_bar", "video_player", "comment_field", "cta_banner_top", "footer_link_about"]

reco_map = {}

# Recommandations personnalisées spécifiques (10 exemples)
reco_map.update({
    ("💥 Utilisateur très actif", "Utilisateurs actifs", "video_player"): {
        "objectif": "Valoriser la fidélité avec du contenu riche",
        "action": "Proposer une série vidéo exclusive",
        "ton": "VIP et immersif",
        "canal": "Interface + Email",
        "cta": "🎥 Nouvelle série exclusive pour vous"
    },
    ("🧠 Lecteur curieux", "Explorateurs passifs", "read_more_btn"): {
        "objectif": "Encourager à aller plus loin",
        "action": "Suggérer des formats longs ou des séries thématiques",
        "ton": "Éditorial",
        "canal": "Interface",
        "cta": "📘 Continuez votre lecture avec notre série"
    },
    ("🛌 Volatile", "Nouveaux utilisateurs", "nav_menu_link"): {
        "objectif": "Structurer leur découverte",
        "action": "Activer un menu contextuel simplifié",
        "ton": "Guidé",
        "canal": "Interface",
        "cta": "🧱 Commencez par un parcours rapide"
    },
    ("⚡ Engagé silencieux", "Utilisateurs actifs", "comment_field"): {
        "objectif": "Encourager l’interaction",
        "action": "Mettre en avant les commentaires récents",
        "ton": "Chaleureux",
        "canal": "Interface",
        "cta": "💬 Et vous, qu’en pensez-vous ?"
    },
    ("📌 Standard", "Nouveaux utilisateurs", "footer_link_about"): {
        "objectif": "Créer un accompagnement",
        "action": "Déclencher un assistant d’accueil",
        "ton": "Bienveillant",
        "canal": "Interface",
        "cta": "👋 Suivez notre guide de démarrage"
    },
    ("💥 Utilisateur très actif", "Visiteurs occasionnels", "comment_field"): {
        "objectif": "Créer une habitude de contribution",
        "action": "Proposer un système de badges",
        "ton": "Communautaire",
        "canal": "Interface + Email",
        "cta": "🏋️ Participez et débloquez des récompenses !"
    },
    ("⚡ Engagé silencieux", "Explorateurs passifs", "search_bar"): {
        "objectif": "Accompagner la recherche",
        "action": "Pré-remplir la barre avec suggestions personnalisées",
        "ton": "Pratique",
        "canal": "Interface",
        "cta": "🔍 Découvrez ce que les autres explorent"
    },
    ("🛌 Volatile", "Visiteurs occasionnels", "cta_banner_top"): {
        "objectif": "Captiver dès l’arrivée",
        "action": "Afficher un message FOMO personnalisé",
        "ton": "Intrigant",
        "canal": "Interface",
        "cta": "⚡ Ne passez pas à côté des temps forts"
    },
    ("🧠 Lecteur curieux", "Engagement moyen", "read_more_btn"): {
        "objectif": "Créer de la continuité",
        "action": "Afficher un bouton 'lire aussi' dynamique",
        "ton": "Suggéré",
        "canal": "Interface",
        "cta": "📚 Voir les articles similaires"
    },
    ("📌 Standard", "default", "default"): {
        "objectif": "Envoyer les meilleurs contenus",
        "action": "Email hebdo avec articles les plus lus",
        "ton": "Neutre",
        "canal": "Email",
        "cta": "📬 Découvrez ce qui a retenu l'attention cette semaine"
    }
})

def get_recommendation(interaction, profil, dom):
    if pd.isna(dom):
        dom = "default"
    keys_to_try = [
        (interaction, profil, dom),
        (interaction, profil, "default"),
        (interaction, "default", "default"),
        ("📌 Standard", "default", "default")
    ]
    for key in keys_to_try:
        if key in reco_map:
            return reco_map[key]
    return {
        "objectif": "Aucune recommandation trouvée",
        "action": "Analyser davantage le comportement utilisateur",
        "ton": "Neutre",
        "canal": "Email",
        "cta": "📩 Contactez-nous pour en savoir plus"
    }

# 📊 Visualisation de l'engagement utilisateur
st.markdown("## 📊 Évolution de l'engagement utilisateur")
df = load_data()
daily_engagement = (
    df.dropna(subset=["yyyymmdd_click", "engagement_score"])
    .groupby(df['yyyymmdd_click'].dt.date)["engagement_score"]
    .mean()
    .reset_index()
)

if not daily_engagement.empty:
    fig, ax = plt.subplots(figsize=(6, 3), constrained_layout=True)
    ax.plot(daily_engagement["yyyymmdd_click"], daily_engagement["engagement_score"], marker='o')
    ax.set_xlabel("Date")
    ax.set_ylabel("Score d'engagement moyen")
    ax.set_title("Évolution du taux d'engagement dans le temps")
    ax.grid(True)
    plt.xticks(rotation=45)
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.pyplot(fig)
else:
    st.info("Pas de données disponibles pour afficher l'évolution.")

# 📋 Tableau des utilisateurs
st.markdown("## 📋 Résumé des utilisateurs")
if not df.empty:
    resume = df.groupby(["visitor_id", "user_name_click"]).agg({
        "profil": safe_mode,
        "interaction_type": safe_mode,
        "risk_level": safe_mode
    }).reset_index()
    st.dataframe(resume.head(100), use_container_width=True)
else:
    st.warning("Aucune donnée utilisateur disponible.")
