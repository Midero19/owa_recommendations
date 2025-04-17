import streamlit as st
import pandas as pd
import os
import gdown
import matplotlib.pyplot as plt

# 📦 Recommandations UX par interaction x profil x DOM

def get_recommendation(interaction, profil, dom):
    key = (interaction, profil, dom if pd.notna(dom) else "default")
    if key in reco_map:
        return reco_map[key]
    fallback = (interaction, profil, "default")
    if fallback in reco_map:
        return reco_map[fallback]
    return reco_map.get(("📌 Standard", "default", "default"))

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

# Ajout des recommandations spécifiques déjà définies ci-dessous
# (fusionnées et écrasent les valeurs génériques si mêmes clés)
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

# 🔁 Affichage des recommandations personnalisées dans la boucle utilisateur
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
