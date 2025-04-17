import streamlit as st
import pandas as pd
import os
import gdown

# --- Téléchargement du fichier depuis Google Drive ---
file_id = "1ygyiExXkF-pDxwNmxyX_MPev4znvnY8Y"
output_path = "final_owa.csv"

if not os.path.exists(output_path):
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# --- Chargement des données ---
df = pd.read_csv(output_path, sep=";", encoding="utf-8", on_bad_lines="skip", engine="python")

# --- Mapping des clusters ---
cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}
df["profil"] = df["cluster"].map(cluster_labels)

# --- Typologie comportementale ---
def classify_interaction(row):
    if row['is_bounce'] == 1 or row['bounce_rate'] > 80:
        return "💤 Volatile"
    elif row['num_pageviews'] > 10 and row['num_actions'] < 3:
        return "🧠 Lecteur curieux"
    elif row['avg_session_duration'] > 300 and row['num_actions'] < 3:
        return "⚡ Engagé silencieux"
    elif row['num_actions'] > 10 or row['num_comments'] > 3:
        return "💥 Interactif actif"
    else:
        return "📌 Standard"

df['interaction_type'] = df.apply(classify_interaction, axis=1)

# --- Recommandations comportementales ---
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
    "💥 Interactif actif": {
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

# --- Recommandations DOM ---
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

# --- Filtres contextuels basés sur la date ---
st.sidebar.header("📅 Filtres par activité utilisateur")

# Convertir yyyymmdd_click en datetime
df['yyyymmdd_click'] = pd.to_datetime(df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce')
available_dates = df['yyyymmdd_click'].dt.date.dropna().unique()

selected_date = st.sidebar.date_input(
    "Sélectionnez une date de clic :", 
    min_value=min(available_dates), 
    max_value=max(available_dates)
)

# Filtrage par date
filtered_by_date = df[df['yyyymmdd_click'].dt.date == selected_date]

# Session ID
available_sessions = filtered_by_date['session_id'].dropna().unique()
selected_session = st.sidebar.selectbox(
    "Session ID :", ["Tous"] + sorted(map(str, available_sessions))
)

# Visitor ID
available_visitors = filtered_by_date['visitor_id'].dropna().unique()
selected_visitor = st.sidebar.selectbox(
    "Visitor ID :", ["Tous"] + sorted(map(str, available_visitors))
)

# User name
available_users = filtered_by_date['user_name'].dropna().unique()
selected_user = st.sidebar.selectbox(
    "Nom d'utilisateur :", ["Tous"] + sorted(available_users)
)

# Risk level
available_risks = sorted(filtered_by_date['risk_level'].dropna().unique())
selected_risk = st.sidebar.selectbox(
    "Niveau de risque (1 = élevé)", ["Tous"] + available_risks
)

# --- Application des filtres cumulés ---
filtered_df = filtered_by_date.copy()

if selected_session != "Tous":
    filtered_df = filtered_df[filtered_df['session_id'].astype(str) == selected_session]

if selected_visitor != "Tous":
    filtered_df = filtered_df[filtered_df['visitor_id'].astype(str) == selected_visitor]

if selected_user != "Tous":
    filtered_df = filtered_df[filtered_df['user_name'] == selected_user]

if selected_risk != "Tous":
    filtered_df = filtered_df[filtered_df['risk_level'] == selected_risk]

# --- Affichage des résultats ---
st.markdown(f"### 👥 {len(filtered_df)} utilisateur(s) trouvé(s) pour le {selected_date.strftime('%Y-%m-%d')}")
if filtered_df.empty:
    st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
else:
    st.dataframe(filtered_df[['visitor_id', 'user_name', 'profil', 'interaction_type', 'risk_level', 'engagement_score']])

# --- Recommandation individuelle si un seul utilisateur sélectionné ---
if len(filtered_df) == 1:
    user = filtered_df.iloc[0]
    st.markdown("## ✅ Recommandation personnalisée")
    if user['risk_level'] == 1:
        reco = reco_map.get(user['interaction_type'], {})
        st.markdown("### 🎯 Basée sur le comportement général")
        st.markdown(f"**Objectif :** {reco.get('objectif')}")
        st.markdown(f"**Action :** {reco.get('action')}")
        st.markdown(f"**Ton :** {reco.get('ton')}")
        st.markdown(f"**Canal :** {reco.get('canal')}")
        st.markdown(f"**CTA :** {reco.get('cta')}")

        dom_clicks = df[df['visitor_id'] == user['visitor_id']]['dom_element_id'].dropna()
        if not dom_clicks.empty:
            top_dom = dom_clicks.mode().iloc[0]
            if top_dom in dom_reco_map:
                dom_reco = dom_reco_map[top_dom]
                st.markdown("---")
                st.markdown("### 🔍 Basée sur le comportement spécifique (DOM)")
                st.markdown(f"**Élément cliqué :** `{top_dom}`")
                st.markdown(f"**Objectif :** {dom_reco.get('objectif')}")
                st.markdown(f"**Action :** {dom_reco.get('action')}")
                st.markdown(f"**Ton :** {dom_reco.get('ton')}")
                st.markdown(f"**Canal :** {dom_reco.get('canal')}")
                st.markdown(f"**CTA :** {dom_reco.get('cta')}")
    else:
        st.info("ℹ️ Cet utilisateur n’est pas à risque élevé.")
