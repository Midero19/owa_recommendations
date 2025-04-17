import streamlit as st
import pandas as pd

# --- Chargement des données ---
df = pd.read_csv("final_owa.csv", sep=";", encoding="utf-8", on_bad_lines="skip", engine="python")

# --- Mapping des clusters ---
cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}
df["profil"] = df["cluster"].map(cluster_labels)

# --- Détection type d'interaction ---
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

# --- Recommandations comportementales générales ---
reco_map = {
    "💤 Volatile": {
        "objectif": "Réduire l’abandon à froid dès la première visite",
        "action": "Relancer par un email ou push dans l’heure avec un contenu percutant (type actu flash ou vidéo 30s)",
        "ton": "Intrigant, FOMO",
        "canal": "Push / Email",
        "cta": "⏱️ Découvrez ce que vous avez manqué en 60 secondes !"
    },
    "🧠 Lecteur curieux": {
        "objectif": "Transformer sa curiosité en interaction",
        "action": "Afficher un quiz, emoji ou bouton 'suivre ce thème' après 3 pages vues",
        "ton": "Complice, engageant",
        "canal": "Popup + email personnalisé",
        "cta": "📚 Activez les suggestions selon vos lectures"
    },
    "⚡ Engagé silencieux": {
        "objectif": "Lever les freins invisibles à l’action",
        "action": "Ajouter un bouton de réaction ou une question douce en fin de contenu + email de valorisation",
        "ton": "Encourageant, chaleureux",
        "canal": "Interface + email à J+1",
        "cta": "👍 Vous avez aimé ce contenu ? Faites-le savoir en un clic"
    },
    "💥 Interactif actif": {
        "objectif": "Prévenir la frustration d’un utilisateur très impliqué",
        "action": "Offrir un contenu VIP, un badge ou une invitation à s’exprimer sur les futures fonctionnalités",
        "ton": "Valorisant, exclusif",
        "canal": "Email personnalisé + interface",
        "cta": "🏅 Merci pour votre activité ! Voici un avant-goût en exclusivité"
    },
    "📌 Standard": {
        "objectif": "Créer un déclic d’intérêt chez les profils indécis",
        "action": "Envoyer une sélection personnalisée des contenus populaires",
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

# --- Filtres UI ---
st.sidebar.header("🎯 Filtres")
selected_profil = st.sidebar.multiselect("Profil utilisateur", df['profil'].dropna().unique())
selected_interaction = st.sidebar.multiselect("Type d'interaction", df['interaction_type'].unique())
selected_risk = st.sidebar.selectbox("Niveau de risque", [1, 2, 3])
selected_user = st.sidebar.selectbox("Nom utilisateur", ["Tous"] + sorted(df['user_name'].dropna().unique()))
score_min, score_max = st.sidebar.slider("Score d'engagement", float(df['engagement_score'].min()), float(df['engagement_score'].max()), (float(df['engagement_score'].min()), float(df['engagement_score'].max())))

# --- Filtrage des données ---
filtered_df = df.copy()
if selected_profil:
    filtered_df = filtered_df[filtered_df['profil'].isin(selected_profil)]
if selected_interaction:
    filtered_df = filtered_df[filtered_df['interaction_type'].isin(selected_interaction)]
if selected_risk:
    filtered_df = filtered_df[filtered_df['risk_level'] == selected_risk]
if selected_user != "Tous":
    filtered_df = filtered_df[filtered_df['user_name'] == selected_user]
filtered_df = filtered_df[(filtered_df['engagement_score'] >= score_min) & (filtered_df['engagement_score'] <= score_max)]

# --- Résultats utilisateurs filtrés ---
st.markdown("## 👥 Résultats")
st.dataframe(filtered_df[['visitor_id', 'user_name', 'profil', 'interaction_type', 'risk_level', 'engagement_score']])

# --- Recommandation personnalisée ---
if len(filtered_df) == 1:
    user = filtered_df.iloc[0]
    st.markdown("## ✅ Recommandation personnalisée")
    if user['risk_level'] == 1:
        reco = reco_map.get(user['interaction_type'], {})
        st.markdown("### 🎯 Basée sur son comportement global")
        st.markdown(f"**Objectif :** {reco.get('objectif')}")
        st.markdown(f"**Action :** {reco.get('action')}")
        st.markdown(f"**Ton :** {reco.get('ton')}")
        st.markdown(f"**Canal :** {reco.get('canal')}")
        st.markdown(f"**CTA :** {reco.get('cta')}")

        # --- DOM element le plus fréquent pour ce user ---
        dom_clicks = df[df['visitor_id'] == user['visitor_id']]['dom_element_id'].dropna()
        if not dom_clicks.empty:
            top_dom = dom_clicks.mode().iloc[0]
            if top_dom in dom_reco_map:
                dom_reco = dom_reco_map[top_dom]
                st.markdown("---")
                st.markdown("### 🔍 Recommandation basée sur clic spécifique")
                st.markdown(f"**Élément cliqué :** `{top_dom}`")
                st.markdown(f"**Objectif :** {dom_reco.get('objectif')}")
                st.markdown(f"**Action :** {dom_reco.get('action')}")
                st.markdown(f"**Ton :** {dom_reco.get('ton')}")
                st.markdown(f"**Canal :** {dom_reco.get('canal')}")
                st.markdown(f"**CTA :** {dom_reco.get('cta')}")
    else:
        st.info("ℹ️ Cet utilisateur n’est pas considéré comme à risque élevé.")
else:
    st.info("🔍 Sélectionnez un seul utilisateur pour voir les recommandations complètes.")
