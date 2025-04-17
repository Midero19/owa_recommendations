import streamlit as st
import pandas as pd
import numpy as np
import os
import gdown

# 📥 Télécharger le fichier final_owa.csv depuis Google Drive si non présent
file_id = "1ygyiExXkF-pDxwNmxyX_MPev4znvnY8Y"
output_path = "final_owa.csv"

if not os.path.exists(output_path):
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Dashboard DG - Segments utilisateurs", layout="wide")
st.title("\U0001F4CA Dashboard DG – Segmentation utilisateurs Management & Datascience")
st.markdown("#### \U0001F501 Basé sur clustering préexistant (final_owa.csv)")
st.markdown("---")

# CHARGEMENT DES DONNÉES
try:
    df = pd.read_csv("final_owa.csv")
except FileNotFoundError:
    st.error("Le fichier 'final_owa.csv' est introuvable.")
    st.stop()

# MAPPING DES PROFILS
mapping = {
    0: "\U0001F7E0 Visiteurs occasionnels",
    1: "\U0001F7E3 Engagement moyen",
    3: "\U0001F525 Utilisateurs actifs",
    4: "\U0001F7E2 Explorateurs passifs",
    6: "\U0001F534 Nouveaux utilisateurs"
}
df['profil'] = df['cluster'].map(mapping)

usernames = df['user_name_click'].dropna().unique() if 'user_name_click' in df.columns else []

# --- FILTRES DYNAMIQUES ---
st.sidebar.header("\U0001F50D Filtres utilisateurs")

selected_profil = st.sidebar.multiselect("Filtrer par profil:", df['profil'].dropna().unique())
selected_actif = st.sidebar.selectbox("Actif récemment:", ["Tous", "Oui", "Non"])
score_min, score_max = st.sidebar.slider("Score d'engagement:", float(df['engagement_score'].min()), float(df['engagement_score'].max()), (float(df['engagement_score'].min()), float(df['engagement_score'].max())))

selected_username = st.sidebar.selectbox("Filtrer par nom d'utilisateur:", options=["Tous"] + sorted(usernames)) if len(usernames) > 0 else "Tous"

filtered_df = df.copy()
if selected_profil:
    filtered_df = filtered_df[filtered_df['profil'].isin(selected_profil)]
if selected_actif != "Tous":
    filtered_df = filtered_df[filtered_df['is_recent_active'] == (1 if selected_actif == "Oui" else 0)]
filtered_df = filtered_df[(filtered_df['engagement_score'] >= score_min) & (filtered_df['engagement_score'] <= score_max)]
if selected_username != "Tous":
    filtered_df = filtered_df[filtered_df['user_name_click'] == selected_username]

# --- AFFICHAGE ---

# KPIs GÉNÉRAUX
nb_total = len(df)
nb_actifs = len(df[df["profil"] == "🔥 Utilisateurs actifs"])
nb_passifs = len(df[df["profil"].isin(["🟠 Visiteurs occasionnels", "🟢 Explorateurs passifs"])])
pct_actifs = round(nb_actifs / nb_total * 100, 1)
pct_passifs = round(nb_passifs / nb_total * 100, 1)

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total utilisateurs", f"{nb_total:,}")
col2.metric("✅ Actifs", f"{nb_actifs:,} ({pct_actifs}%)")
col3.metric("⚠️ À risque", f"{nb_passifs:,} ({pct_passifs}%)")

# AFFICHAGE DU TABLEAU FILTRÉ
st.markdown("## 👤 Profils utilisateurs filtrés")
st.dataframe(filtered_df[['visitor_id', 'profil', 'user_name_click', 'engagement_score', 'rfm_frequency', 'avg_session_duration']])

# RECOMMANDATIONS PAR PROFIL
st.markdown("---")
st.markdown("## 💬 Recommandations par profil")
reco_map = {
    "🟠 Visiteurs occasionnels": {
        "objectif": "Réengager avec contenu court & pertinent",
        "action": "2 emails à J+2 & J+5 avec articles courts + invitation à découvrir les nouveautés.",
        "ton": "Curieux, accrocheur",
        "canal": "Email ou notification",
        "cta": "Découvrez nos actus les plus vues cette semaine"
    },
    "🔥 Utilisateurs actifs": {
        "objectif": "Les fidéliser avec valorisation",
        "action": "Badge ambassadeur, classement, contenus premium",
        "ton": "Engageant, valorisant",
        "canal": "Email + interface personnalisée",
        "cta": "Bravo ! Vous êtes parmi nos membres les plus actifs 👏"
    },
    "🟣 Engagement moyen": {
        "objectif": "Stimuler avec événement ou défi",
        "action": "Inviter à un webinaire ou défi de la semaine",
        "ton": "Challenge, interactif",
        "canal": "Email + popup",
        "cta": "Relancez votre activité avec notre prochain webinaire"
    },
    "🔴 Nouveaux utilisateurs": {
        "objectif": "Accompagner dans les 7 premiers jours",
        "action": "Tutoriel vidéo, onboarding 3 étapes",
        "ton": "Pédagogique, bienveillant",
        "canal": "Email à J+1 & J+3",
        "cta": "Bienvenue ! Découvrez comment tirer le meilleur de la plateforme"
    },
    "🟢 Explorateurs passifs": {
        "objectif": "Comprendre leurs attentes",
        "action": "Popup 'Que recherchez-vous ?' + contenus ciblés",
        "ton": "Curieux, empathique",
        "canal": "Popup + email",
        "cta": "Dites-nous ce qui vous intéresse et on vous guide"
    }
}
for profil, group in df.groupby("profil"):
    reco = reco_map.get(profil, {})
    with st.expander(f"{profil} – {len(group)} utilisateurs"):
        st.markdown(f"**🎯 Objectif :** {reco.get('objectif', '')}")
        st.markdown(f"**✅ Action recommandée :** {reco.get('action', '')}")
        st.markdown(f"**🗣️ Ton conseillé :** {reco.get('ton', '')}")
        st.markdown(f"**📡 Canal :** {reco.get('canal', '')}")
        st.markdown(f"**👉 Exemple :** {reco.get('cta', '')}")

# SYNTHÈSE DG
st.markdown("---")
st.markdown("## 📌 Synthèse DG")
st.markdown("""
- Les utilisateurs actifs sont engagés mais doivent être valorisés.
- Des campagnes simples peuvent réengager 30% des profils dormants.
- Une séquence d’accueil permettra de mieux intégrer les nouveaux.
""")

# RECHERCHE PAR VISITOR_ID
st.markdown("---")
st.markdown("## 🔎 Rechercher un utilisateur spécifique")
search_id = st.text_input("Entrer un visitor_id exact :")

if search_id:
    try:
        visitor_id_int = int(search_id)
        user_info = df[df['visitor_id'] == visitor_id_int]
        if not user_info.empty:
            st.markdown(f"### 👤 Infos pour l'utilisateur ID : `{visitor_id_int}`")
            st.dataframe(user_info.T.rename(columns={user_info.index[0]: "Valeur"}))
            profil = user_info['profil'].values[0]
            st.markdown(f"### 🧠 Profil détecté : **{profil}**")
            reco = reco_map.get(profil, {})
            st.markdown("#### ✅ Recommandation personnalisée")
            st.markdown(f"**🎯 Objectif :** {reco.get('objectif','')}")
            st.markdown(f"**📢 Action :** {reco.get('action','')}")
            st.markdown(f"**🗣️ Ton :** {reco.get('ton','')}")
            st.markdown(f"**📡 Canal :** {reco.get('canal','')}")
            st.markdown(f"**👉 Exemple de message :** {reco.get('cta','')}")
        else:
            st.warning("Aucun utilisateur trouvé avec cet ID.")
    except ValueError:
        st.warning("Veuillez entrer un ID valide (nombre entier).")
