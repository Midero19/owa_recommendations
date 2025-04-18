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

# 🧠 Titre centré et intro
st.markdown("""
<h1 style='text-align: center;'>📊 OWA – Moteur de recommandations</h1>
""", unsafe_allow_html=True)
st.markdown("---")

# 📦 Chargement des données
os.environ["STREAMLIT_WATCH_DISABLE"] = "true"
file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}

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
    df["profil"] = df["cluster"].map(cluster_labels)
    df['interaction_type'] = df.apply(classify_interaction, axis=1)
    return df

@st.cache_data
def get_dom_by_visitor(df):
    return df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

def safe_mode(series):
    mode = series.mode()
    return mode.iloc[0] if not mode.empty else "Non défini"

# 🔁 Recommandations
# 🔁 Recommandations
reco_map = {
    "💤 Volatile": {
        "objectif": "Réduire l’abandon rapide",
        "action": "Envoyer une relance email personnalisée avec un extrait du contenu non consulté + lien direct",
        "ton": "Urgent, intrigant (FOMO)",
        "canal": "Push / Email",
        "cta": "⏱ Vous êtes passé à côté d’un contenu sur-mesure ! Redécouvrez-le maintenant"
    },
    "🧠 Lecteur curieux": {
        "objectif": "Stimuler l’engagement",
        "action": "Proposer un bouton ‘Suivre ce thème’ ou ‘Recevoir plus de contenus similaires’ en bas d'article",
        "ton": "Curieux & complice",
        "canal": "Popup in-app + email de suivi personnalisé",
        "cta": "📚 Continuez sur votre lancée : suivez les contenus autour de ce thème !"
    },
    "⚡ Engagé silencieux": {
        "objectif": "Favoriser l’expression",
        "action": "Ajouter un micro-feedback (👍👎) ou un champ 'Vous avez aimé ce contenu ?' à la fin de l'article",
        "ton": "Chaleureux & bienveillant",
        "canal": "Interface + email",
        "cta": "👍 Vous l’avez lu, maintenant exprimez-vous !"
    },
    "💥 Utilisateur très actif": {
        "objectif": "Valoriser et retenir",
        "action": "Offrir un badge visible dans le profil ou une invitation à tester une fonctionnalité beta",
        "ton": "Exclusif & valorisant",
        "canal": "Email + interface",
        "cta": "🏅 Bravo pour votre activité ! Voici un accès VIP en avant-première"
    },
    "📌 Standard": {
        "objectif": "Créer un déclic",
        "action": "Envoyer une sélection de contenus populaires adaptés à leur dernier thème consulté",
        "ton": "Positif & incitatif",
        "canal": "Email hebdo + suggestion dans le flux",
        "cta": "📬 Découvrez ce que la communauté a le plus aimé cette semaine"
    }
}

dom_reco_map = {
    "nav_menu_link": {"objectif": "Navigation rapide", "action": "Adapter les rubriques", "ton": "Clair", "canal": "Interface", "cta": "🔎 Naviguez plus vite"},
    "read_more_btn": {"objectif": "Contenu long", "action": "Suggérer des séries", "ton": "Expert", "canal": "Email", "cta": "📘 Découvrez notre série"},
    "search_bar": {"objectif": "Anticiper", "action": "Créer des alertes", "ton": "Pratique", "canal": "Interface", "cta": "🔔 Activez les alertes"},
    "video_player": {"objectif": "Fidélisation vidéo", "action": "Playlist", "ton": "Immersif", "canal": "Interface", "cta": "🎬 Votre sélection vous attend"},
    "comment_field": {"objectif": "Encourager l’expression", "action": "Mettre en avant les débats", "ton": "Communautaire", "canal": "Email", "cta": "💬 Rejoignez la discussion"},
    "cta_banner_top": {"objectif": "Fidélisation", "action": "Teaser ou offre", "ton": "VIP", "canal": "Email", "cta": "🎁 Votre avant-première vous attend"},
    "footer_link_about": {"objectif": "Besoin discret", "action": "Assistant ou sondage", "ton": "Bienveillant", "canal": "Popup", "cta": "🤔 On vous aide ?"}
}

# 📥 Chargement
df = load_data()

# 🎛️ Filtres
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("📅 Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("🧾 Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("🆔 Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("👤 Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("⚠️ Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))
st.sidebar.markdown("---")
max_rows = st.sidebar.slider("📄 Nombre de lignes visibles :", 10, 500, 100)
max_recos = st.sidebar.slider("🤖 Nb de recommandations :", 1, 20, 10)

# 🔎 Application des filtres
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

st.markdown("## 📈 Évolution de l'engagement utilisateur")

daily_engagement = (
    filtered_df.dropna(subset=["yyyymmdd_click", "engagement_score"])
    .groupby(filtered_df['yyyymmdd_click'].dt.date)["engagement_score"]
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

# 📋 Résumé utilisateurs
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
            if user['interaction_type'] in reco_map:
                reco = reco_map[user['interaction_type']]
                with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']} (profil : {user['profil']}, risque : {user['risk_level']})"):
                    st.markdown("### 🎯 Comportement général")
                    st.markdown(f"**Objectif :** {reco['objectif']}")
                    st.markdown(f"**Action :** {reco['action']}")
                    st.markdown(f"**Ton :** {reco['ton']}")
                    st.markdown(f"**Canal :** {reco['canal']}")
                    st.markdown(f"**CTA :** {reco['cta']}")

                    top_dom = dom_by_visitor.get(user['visitor_id'])
                    if pd.notna(top_dom) and top_dom in dom_reco_map:
                        dom = dom_reco_map[top_dom]
                        st.markdown("### 🔍 Élément DOM principal")
                        st.markdown(f"**Élément :** {top_dom}")
                        st.markdown(f"**Objectif :** {dom['objectif']}")
                        st.markdown(f"**Action :** {dom['action']}")
                        st.markdown(f"**Ton :** {dom['ton']}")
                        st.markdown(f"**Canal :** {dom['canal']}")
                        st.markdown(f"**CTA :** {dom['cta']}")
    else:
        st.info("🔍 Appliquez au moins un filtre pour afficher des recommandations personnalisées.")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
