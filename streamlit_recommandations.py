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
    # Téléchargement si nécessaire
    if not os.path.exists(path):
        gdown.download(f"https://drive.google.com/uc?id={file_id}", path, quiet=True)
    # Lecture du CSV
    df = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8",
        on_bad_lines="skip",
        engine="python",
        dtype={"visitor_id": str}
    )
    # Nettoyage de base
    df.fillna(0, inplace=True)
    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(
        df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce'
    )
    # Mapping de profil
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
        (df['num_actions'] > 10) | (df['num_comments'] > 3),
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
    df = load_data(output_path, file_id)

# --- Mappages de recommandations statiques ---
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
    "nav_menu_link": {
        "objectif": "Faciliter l'accès rapide aux contenus",
        "action": "Adapter la navigation aux rubriques préférées",
        "ton": "Clair, organisé",
        "canal": "Interface + email",
        "cta": "🔎 Naviguez plus vite dans vos contenus favoris"
    },
    "read_more_btn": {
        "objectif": "Proposer du contenu approfondi",
        "action": "Recommander des articles longs ou des séries",
        "ton": "Éditorial, expert",
        "canal": "Email dossier",
        "cta": "📘 Découvrez notre série spéciale"
    },
    "search_bar": {
        "objectif": "Anticiper ses recherches",
        "action": "Créer des suggestions ou alertes",
        "ton": "Pratique, rapide",
        "canal": "Interface + notification",
        "cta": "🔔 Activez les alertes sur vos sujets préférés"
    },
    "video_player": {
        "objectif": "Fidéliser via les vidéos",
        "action": "Playlist ou suggestions vidéos",
        "ton": "Visuel, immersif",
        "canal": "Interface vidéo",
        "cta": "🎬 Votre sélection vidéo vous attend"
    },
    "comment_field": {
        "objectif": "Encourager l’expression",
        "action": "Mettre en avant les débats en cours",
        "ton": "Communautaire",
        "canal": "Email + interface",
        "cta": "💬 Rejoignez la discussion du moment"
    },
    "cta_banner_top": {
        "objectif": "Transformer l’intérêt en fidélité",
        "action": "Offre ou teaser exclusif",
        "ton": "Promo, VIP",
        "canal": "Email",
        "cta": "🎁 Votre avant-première vous attend"
    },
    "footer_link_about": {
        "objectif": "Comprendre son besoin discret",
        "action": "Sondage simple ou assistant guidé",
        "ton": "Curieux, bienveillant",
        "canal": "Popup",
        "cta": "🤔 On vous aide à trouver ce que vous cherchez ?"
    }
}

# --- Barre latérale : filtres ---
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
filters = {
    "Date de clic": ["Toutes"] + all_dates,
    "Session ID": ["Tous"] + sorted(df['session_id'].unique()),
    "Visitor ID": ["Tous"] + sorted(df['visitor_id'].unique()),
    "Nom d'utilisateur": ["Tous"] + sorted(df['user_name_click'].unique()),
    "Niveau de risque": ["Tous"] + sorted(df['risk_level'].unique())
}
selected = {label: st.sidebar.selectbox(f"{label} :", options) for label, options in filters.items()}

# --- Application des filtres ---
filtered_df = df.copy()
for label, val in selected.items():
    if val not in ["Toutes", "Tous"]:
        key = label.lower().replace(" ", "_")
        if key in ["date_de_clic", "yyyymmdd_click"]:
            filtered_df = filtered_df[filtered_df['yyyymmdd_click'].dt.date == val]
        else:
            filtered_df = filtered_df[filtered_df[key] == val]

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

# Chart engagement
if selected['Visitor ID'] == 'Tous':
    series_eng = filtered_df.groupby('yyyymmdd_click')['engagement_score'].mean()
else:
    series_eng = filtered_df[filtered_df['visitor_id'] == selected['Visitor ID']]['engagement_score']
col2.line_chart(series_eng, use_container_width=True)

# Tableau des données
st.dataframe(grouped_df, use_container_width=True)

# --- Recommandations ---
st.header("✅ Recommandations personnalisées")
# Calcul du mode DOM par visiteur
dom_mode = df.groupby('visitor_id')['dom_element_id'] \
              .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

for idx, row in enumerate(grouped_df.itertuples()):
    with st.expander(f"👤 {row.user_name_click} – {row.interaction_type} (profil: {row.profil}, risque: {row.risk_level})"):
        rec = reco_map[row.interaction_type]
        st.write(f"**Objectif :** {rec['objectif']}")
        st.write(f"**Action :** {rec['action']}")
        st.write(f"**Ton :** {rec['ton']}")
        st.write(f"**Canal :** {rec['canal']}")
        st.write(f"**CTA :** {rec['cta']}")
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
