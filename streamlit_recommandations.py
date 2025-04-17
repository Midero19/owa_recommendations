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

# 📦 Téléchargement des données
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
    return df

@st.cache_data
def get_dom_by_visitor(df):
    return df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

def safe_mode(series):
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else "Non défini"

def classify_interaction(row):
    if row['is_bounce'] == 1 or row['bounce_rate'] > 80:
        return "💤 Volatile"
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

# Recommandation selon interaction x profil x DOM
interaction_types = ["💥 Utilisateur très actif", "⚡ Engagé silencieux", "🧠 Lecteur curieux", "💤 Volatile", "📌 Standard"]
profils = ["Utilisateurs actifs", "Visiteurs occasionnels", "Engagement moyen", "Nouveaux utilisateurs", "Explorateurs passifs"]
dom_elements = ["default", "nav_menu_link", "read_more_btn", "search_bar", "video_player", "comment_field", "cta_banner_top", "footer_link_about"]

reco_map = {}

for interaction in interaction_types:
    for profil in profils:
        for dom in dom_elements:
            reco_map[(interaction, profil, dom)] = {
                "objectif": f"Stimuler l'engagement pour un profil '{profil}' avec un comportement '{interaction}' sur l'élément '{dom}'",
                "action": f"Suggérer un contenu ou une interaction adaptée. Exemple : personnaliser l'expérience utilisateur via '{dom}' en fonction du profil et du comportement",
                "ton": "Adapté au contexte utilisateur",
                "canal": "Email / Interface selon fréquence",
                "cta": f"📥 Découvrez nos suggestions pour {profil}"
            }

# Recos spécifiques
reco_map.update({
    ("💥 Utilisateur très actif", "Utilisateurs actifs", "default"): {
        "objectif": "Valoriser leur implication continue",
        "action": "Proposer un accès à du contenu VIP ou à des bêtas fermées. Exemple : envoyer un email avec des contenus premium débloqués",
        "ton": "Exclusif et gratifiant",
        "canal": "Email personnalisé + interface",
        "cta": "🏅 Vous avez débloqué l’accès à notre contenu premium !"
    },
    ("🧠 Lecteur curieux", "Explorateurs passifs", "read_more_btn"): {
        "objectif": "Encourager à approfondir une lecture",
        "action": "Recommander des articles connexes ou longs formats. Exemple : afficher une suggestion d’article expert juste après un clic sur 'lire plus'",
        "ton": "Éditorial",
        "canal": "Email ou interface",
        "cta": "📘 Explorez nos analyses approfondies sur ce thème"
    },
    ("💤 Volatile", "Visiteurs occasionnels", "cta_banner_top"): {
        "objectif": "Réduire l’abandon rapide",
        "action": "Afficher une accroche exclusive dès l’arrivée. Exemple : bandeau haut avec un message FOMO + offre découverte",
        "ton": "FOMO / Intrigant",
        "canal": "Interface + Push",
        "cta": "⚡ Ce que vous avez manqué en 60 secondes !"
    },
    ("⚡ Engagé silencieux", "Explorateurs passifs", "search_bar"): {
        "objectif": "Faciliter la recherche personnalisée",
        "action": "Pré-remplir des suggestions basées sur ses intérêts. Exemple : afficher des requêtes populaires personnalisées dans la barre de recherche",
        "ton": "Pratique",
        "canal": "Interface + suggestions",
        "cta": "🔍 Découvrez ce que d’autres explorent en ce moment"
    },
    ("📌 Standard", "Nouveaux utilisateurs", "footer_link_about"): {
        "objectif": "Créer un accompagnement doux",
        "action": "Proposer une découverte guidée. Exemple : activer un assistant visuel expliquant la plateforme après clic sur 'à propos'",
        "ton": "Bienveillant",
        "canal": "Interface",
        "cta": "🤝 On vous aide à bien démarrer ?"
    },
    ("📌 Standard", "default", "default"): {
        "objectif": "Contenu standard",
        "action": "Sélection hebdo des contenus. Exemple : email hebdo automatique avec articles les plus lus",
        "ton": "Neutre",
        "canal": "Email",
        "cta": "📬 Nos contenus les plus lus cette semaine"
    }
})

def get_recommendation(interaction, profil, dom):
    key = (interaction, profil, dom if pd.notna(dom) else "default")
    if key in reco_map:
        return reco_map[key]
    fallback = (interaction, profil, "default")
    if fallback in reco_map:
        return reco_map[fallback]
    return reco_map.get(("📌 Standard", "default", "default"))

# Chargement des données
st.info("Chargement des données en cours...")
df = load_data()
df["profil"] = df["cluster"].map(cluster_labels)
df["interaction_type"] = df.apply(classify_interaction, axis=1)
st.success("Données chargées !")

# Filtres utilisateurs
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("📅 Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("🧾 Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("🆔 Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("👤 Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("⚠️ Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))
max_rows = st.sidebar.slider("📄 Nombre de lignes visibles :", 10, 500, 100)
max_recos = st.sidebar.slider("🤖 Nb de recommandations :", 1, 20, 10)

# Application des filtres
filtered_df = df.copy()
if selected_date != "Toutes":
    filtered_df = filtered_df[filtered_df['yyyymmdd_click'].dt.date == selected_date]
if selected_session != "Tous":
    filtered_df = filtered_df[filtered_df['session_id'] == selected_session]
if selected_visitor != "Tous":
    filtered_df = filtered_df[filtered_df['visitor_id'] == selected_visitor]
if selected_user != "Tous":
    filtered_df = filtered_df[filtered_df['user_name_click'] == selected_user]
if selected_risk != "Tous":
    filtered_df = filtered_df[filtered_df['risk_level'] == selected_risk]

# Graphique engagement
st.markdown("## 📈 Évolution de l'engagement utilisateur")
daily_engagement = (
    filtered_df.dropna(subset=["yyyymmdd_click", "engagement_score"])
    .groupby(filtered_df['yyyymmdd_click'].dt.date)["engagement_score"]
    .mean()
    .reset_index()
)

if not daily_engagement.empty:
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(daily_engagement["yyyymmdd_click"], daily_engagement["engagement_score"], marker='o')
    ax.set_xlabel("Date")
    ax.set_ylabel("Score d'engagement moyen")
    ax.set_title("Évolution du taux d'engagement dans le temps")
    ax.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("Pas de données disponibles pour afficher l'évolution.")

# Résumé utilisateurs
st.markdown("## 👥 Résultats des utilisateurs filtrés")
if not filtered_df.empty:
    grouped_df = filtered_df.groupby(['visitor_id', 'user_name_click']).agg({
        'yyyymmdd_click': 'min',
        'profil': safe_mode,
        'interaction_type': safe_mode,
        'risk_level': 'max'
    }).reset_index()

    st.dataframe(grouped_df.head(max_rows), use_container_width=True)

    filters_applied = any([
        selected_date != "Toutes",
        selected_session != "Tous",
        selected_visitor != "Tous",
        selected_user != "Tous",
        selected_risk != "Tous"
    ])

    if filters_applied:
        st.markdown("## ✅ Recommandations personnalisées")
        unique_users = filtered_df.drop_duplicates(subset=['visitor_id', 'user_name_click', 'interaction_type', 'profil'])
        dom_by_visitor = get_dom_by_visitor(df)
        display_users = unique_users.head(max_recos)

        for _, user in display_users.iterrows():
            top_dom = dom_by_visitor.get(user['visitor_id'])
            reco = get_recommendation(user['interaction_type'], user['profil'], top_dom)

            with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']} (profil : {user['profil']})"):
                st.markdown("### 🎯 Recommandation personnalisée")
                st.markdown(f"**Objectif :** {reco['objectif']}")
                st.markdown(f"**Action :** {reco['action']}")
                st.markdown(f"**Ton :** {reco['ton']}")
                st.markdown(f"**Canal :** {reco['canal']}")
                st.markdown(f"**CTA :** {reco['cta']}")

                if pd.notna(top_dom):
                    st.markdown("### 🔍 Élément DOM principal")
                    st.markdown(f"**DOM utilisé :** {top_dom}")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
