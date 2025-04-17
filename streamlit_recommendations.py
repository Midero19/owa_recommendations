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
st.markdown("""
    <h1 style='text-align: center;'>📊 Dashboard DG – Segmentation utilisateurs</h1>
    <h4 style='text-align: center;'>🔄 Basé sur clustering préexistant (final_owa.csv)</h4>
    <hr style='margin-top: 0;'>
""", unsafe_allow_html=True)

# CHARGEMENT DES DONNÉES
try:
    df = pd.read_csv("final_owa.csv", sep=None, engine="python", encoding="utf-8", on_bad_lines="skip")
except FileNotFoundError:
    st.error("Le fichier 'final_owa.csv' est introuvable.")
    st.stop()

# MAPPING DES PROFILS
mapping = {
    0: "🟠 Visiteurs occasionnels",
    1: "🟣 Engagement moyen",
    3: "🔥 Utilisateurs actifs",
    4: "🟢 Explorateurs passifs",
    6: "🔴 Nouveaux utilisateurs"
}
df['profil'] = df['cluster'].map(mapping)

usernames = df['user_name_click'].dropna().unique() if 'user_name_click' in df.columns else []

# --- FILTRES DYNAMIQUES ---
st.sidebar.header("🔍 Filtres utilisateurs")

selected_profil = st.sidebar.multiselect("Filtrer par profil:", df['profil'].dropna().unique())
selected_actif = st.sidebar.selectbox("Actif récemment:", ["Tous", "Oui", "Non"])
score_min, score_max = st.sidebar.slider("Score d'engagement:", float(df['engagement_score'].min()), float(df['engagement_score'].max()), (float(df['engagement_score'].min()), float(df['engagement_score'].max())))

usernames_filtered = df[df['profil'].isin(selected_profil)]['user_name_click'].dropna().unique() if selected_profil else usernames
selected_username = st.sidebar.selectbox("Filtrer par nom d'utilisateur:", options=["Tous"] + sorted(usernames_filtered)) if len(usernames_filtered) > 0 else "Tous"

# Filtre connecté pour visitor_id
visitor_ids_filtered = df[df['profil'].isin(selected_profil)]['visitor_id'].unique() if selected_profil else df['visitor_id'].unique()
selected_visitor_id = st.sidebar.selectbox("Filtrer par visitor_id:", options=["Tous"] + sorted(visitor_ids_filtered.astype(str)))

filtered_df = df.copy()
if selected_profil:
    filtered_df = filtered_df[filtered_df['profil'].isin(selected_profil)]
if selected_visitor_id != "Tous":
    filtered_df = filtered_df[filtered_df['visitor_id'] == int(selected_visitor_id)]
if selected_actif != "Tous":
    filtered_df = filtered_df[filtered_df['is_recent_active'] == (1 if selected_actif == "Oui" else 0)]
filtered_df = filtered_df[(filtered_df['engagement_score'] >= score_min) & (filtered_df['engagement_score'] <= score_max)]
if selected_username != "Tous":
    filtered_df = filtered_df[filtered_df['user_name_click'] == selected_username]

# --- KPIs ---
nb_total = len(df)
nb_actifs = len(df[df["profil"] == "🔥 Utilisateurs actifs"])
nb_passifs = len(df[df["profil"].isin(["🟠 Visiteurs occasionnels", "🟢 Explorateurs passifs"])])
pct_actifs = round(nb_actifs / nb_total * 100, 1)
pct_passifs = round(nb_passifs / nb_total * 100, 1)

st.markdown("""
<div style='display: flex; justify-content: space-around;'>
  <div><h3>👥 Total utilisateurs</h3><p style='font-size: 24px;'>""" + f"{nb_total:,}" + "</p></div>
  <div><h3>✅ Actifs</h3><p style='font-size: 24px;'>""" + f"{nb_actifs:,} ({pct_actifs}%)" + "</p></div>
  <div><h3>⚠️ À risque</h3><p style='font-size: 24px;'>""" + f"{nb_passifs:,} ({pct_passifs}%)" + "</p></div>
</div>
""", unsafe_allow_html=True)

# --- INFO PROFIL DÉTAILLÉ ---
st.markdown("---")
st.markdown("## 🔎 Détail d'un utilisateur")

if selected_visitor_id != "Tous":
    selected_info = df[df['visitor_id'] == int(selected_visitor_id)]
    if not selected_info.empty:
        profil = selected_info['profil'].values[0]
        st.markdown(f"### 👤 Profil détecté : **{profil}**")
        st.dataframe(selected_info[[
            'rfm_recency', 'rfm_frequency', 'rfm_intensity',
            'engagement_score', 'engagement_density',
            'avg_actions_per_session', 'avg_session_duration',
            'bounce_rate', 'is_recent_active'
        ]].T.rename(columns={selected_info.index[0]: "Valeur"}))

# --- RECOMMANDATIONS ---
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

# --- SYNTHÈSE DG ---
st.markdown("---")
st.markdown("## 📌 Synthèse DG")
st.markdown("""
- Les utilisateurs actifs sont engagés mais doivent être valorisés.
- Des campagnes simples peuvent réengager 30% des profils dormants.
- Une séquence d’accueil permettra de mieux intégrer les nouveaux.
""")
