import streamlit as st
import pandas as pd
import numpy as np
import os
import gdown
import re

# --- Header ---
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #4CAF50; font-size: 3rem;'>🧠 Moteur de recommandations utilisateurs</h1>
    <p style='color: grey;'>Analyse comportementale et suggestions personnalisées en un clic</p>
</div>
""", unsafe_allow_html=True)

# --- Data loading ---
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
    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(
        df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce'
    )
    return df

# Load once and cache
df = load_data(output_path, file_id)

# --- Profil mapping ---
cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}
df['profil'] = df['cluster'].map(cluster_labels)

# --- Interaction classification (vectorized) ---
conds = [
    (df['is_bounce'] == 1) | (df['bounce_rate'] > 80),
    (df['num_pageviews'] > 10) & (df['num_actions'] < 3),
    (df['avg_session_duration'] > 300) & (df['num_actions'] < 3),
    (df['num_actions'] > 10) | (df['num_comments'] > 3),
]
choices = [
    "💤 Volatile",
    "🧠 Lecteur curieux",
    "⚡ Engagé silencieux",
    "💥 Utilisateur très actif"
]
df['interaction_type'] = np.select(conds, choices, default="📌 Standard")

# --- Recommendation mappings ---
reco_map = {
    "💤 Volatile": {
        "objectif": "Réduire l’abandon à froid dès la première visite",
        "action": "Relancer par un email ou push dans l’heure avec un contenu percutant",
        "ton": "Intrigant, FOMO",
        "canal": "Push / Email",
        "cta": "⏱️ Découvrez ce que vous avez manqué en 60 secondes !"
    },
    "🧠 Lecteur curieux": {
        "objectif": "Transformer sa curiosité en interaction",
        "action": "Afficher un quiz, emoji ou bouton 'suivre ce thème'",
        "ton": "Complice, engageant",
        "canal": "Popup + email",
        "cta": "📚 Activez les suggestions selon vos lectures"
    },
    "⚡ Engagé silencieux": {
        "objectif": "Lever les freins invisibles à l’action",
        "action": "Ajouter un bouton de réaction ou une question douce",
        "ton": "Encourageant, chaleureux",
        "canal": "Interface + email",
        "cta": "👍 Vous avez aimé ce contenu ? Faites-le savoir en un clic"
    },
    "💥 Utilisateur très actif": {
        "objectif": "Prévenir la frustration d’un utilisateur très impliqué",
        "action": "Offrir un contenu VIP ou une invitation à contribuer",
        "ton": "Valorisant, exclusif",
        "canal": "Email personnalisé + interface",
        "cta": "🏅 Merci pour votre activité ! Voici un avant-goût en exclusivité"
    },
    "📌 Standard": {
        "objectif": "Créer un déclic d’intérêt",
        "action": "Envoyer une sélection des contenus populaires",
        "ton": "Positif, informatif",
        "canal": "Email hebdomadaire",
        "cta": "📬 Voici les contenus qui font vibrer notre communauté"
    }
}

dom_reco_map = {
    "nav_menu_link": {"objectif": "Faciliter l'accès rapide aux contenus", "action": "Adapter la navigation aux rubriques préférées", "ton": "Clair, organisé", "canal": "Interface + email", "cta": "🔎 Naviguez plus vite dans vos contenus favoris"},
    "read_more_btn": {"objectif": "Proposer du contenu approfondi", "action": "Recommander des articles longs ou des séries", "ton": "Éditorial, expert", "canal": "Email dossier", "cta": "📘 Découvrez notre série spéciale"},
    "search_bar": {"objectif": "Anticiper ses recherches", "action": "Créer des suggestions ou alertes", "ton": "Pratique, rapide", "canal": "Interface + notification", "cta": "🔔 Activez les alertes sur vos sujets préférés"},
    "video_player": {"objectif": "Fidéliser via les vidéos", "action": "Playlist ou suggestions vidéos", "ton": "Visuel, immersif", "canal": "Interface vidéo", "cta": "🎬 Votre sélection vidéo vous attend"},
    "comment_field": {"objectif": "Encourager l’expression", "action": "Mettre en avant les débats en cours", "ton": "Communautaire", "canal": "Email + interface", "cta": "💬 Rejoignez la discussion du moment"},
    "cta_banner_top": {"objectif": "Transformer l’intérêt en fidélité", "action": "Offre ou teaser exclusif", "ton": "Promo, VIP", "canal": "Email", "cta": "🎁 Votre avant-première vous attend"},
    "footer_link_about": {"objectif": "Comprendre son besoin discret", "action": "Sondage simple ou assistant guidé", "ton": "Curieux, bienveillant", "canal": "Popup", "cta": "🤔 On vous aide à trouver ce que vous cherchez ?"}
}

# --- Sidebar filters ---
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))

# Apply filters early
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

# --- Main content ---
st.markdown("""
<div style='text-align: center;'>
    <h2 style='color: #F4B400;'>📋 Résultats utilisateurs</h2>
</div>
""", unsafe_allow_html=True)
if selected_date == "Toutes":
    st.markdown("<div style='text-align: center;'><h3>👥 Toutes les dates</h3></div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div style='text-align: center;'><h3>👥 Résultats pour le {selected_date}</h3></div>", unsafe_allow_html=True)

st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>📊 <strong>Nombre de clics</strong> : {len(filtered_df)}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align: center; font-size: 1.2rem;'>🧍‍♂️ <strong>Utilisateurs uniques</strong> : {filtered_df['visitor_id'].nunique()}</div>", unsafe_allow_html=True)

if not filtered_df.empty:
    @st.cache_data(show_spinner=False)
    def compute_grouped(df: pd.DataFrame) -> pd.DataFrame:
        return df.groupby(['visitor_id', 'user_name_click']).agg({
            'yyyymmdd_click': 'min',
            'profil': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
            'interaction_type': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
            'risk_level': 'max',
            'engagement_score': 'mean'
        }).reset_index()

    grouped_df = compute_grouped(filtered_df)

    # Profiles distribution
    profil_counts = grouped_df['profil'].value_counts()
    st.bar_chart(profil_counts, use_container_width=True)

    # Engagement over time
    if selected_visitor != "Tous":
        chart_data = filtered_df[filtered_df['visitor_id'] == selected_visitor][['yyyymmdd_click', 'engagement_score']]
        title = f"Score d'engagement pour {selected_visitor}"
    else:
        chart_data = filtered_df.groupby('yyyymmdd_click')['engagement_score'].mean().reset_index()
        title = "Score d'engagement global (moyenne quotidienne)"
    st.line_chart(chart_data.set_index('yyyymmdd_click')['engagement_score'], use_container_width=True)

    # Data table
    st.dataframe(grouped_df, use_container_width=True)

    # Recommendations
    st.markdown("""
<div style='text-align: center; margin-top: 2rem;'>
    <h2 style='color: #43A047;'>✅ Recommandations personnalisées</h2>
</div>
""", unsafe_allow_html=True)

    dom_by_visitor = df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'] \
        .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

    for _, user in filtered_df.drop_duplicates(subset=['visitor_id', 'user_name_click', 'interaction_type', 'profil']).iterrows():
        reco = reco_map.get(user['interaction_type'])
        if reco:
            with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']} (profil : {user['profil']}, risque : {user['risk_level']})"):
                st.markdown("### 🎯 Comportement général")
                st.markdown(f"**Objectif :** {reco['objectif']}")
                st.markdown(f"**Action :** {reco['action']}")
                st.markdown(f"**Ton :** {reco['ton']}")
                st.markdown(f"**Canal :** {reco['canal']}")
                st.markdown(f"**CTA :** {reco['cta']}")

                if st.checkbox("🔍 Voir la recommandation DOM", key=f"dom_{user['visitor_id']}"):
                    top_dom = dom_by_visitor.get(user['visitor_id'])
                    dom = dom_reco_map.get(top_dom)
                    if dom:
                        st.markdown("### 🔍 Élément DOM principal")
                        st.markdown(f"**Élément :** {top_dom}")
                        st.markdown(f"**Objectif :** {dom['objectif']}")
                        st.markdown(f"**Action :** {dom['action']}")
                        st.markdown(f"**Ton :** {dom['ton']}")
                        st.markdown(f"**Canal :** {dom['canal']}")
                        st.markdown(f"**CTA :** {dom['cta']}")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
