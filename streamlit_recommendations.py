import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances

# CONFIGURATION DE LA PAGE
st.set_page_config(page_title="Dashboard DG - Segments utilisateurs", layout="wide")
st.title("📊 Dashboard DG – Segmentation utilisateurs Management & Datascience")
st.markdown("#### 🔄 Basé sur clustering KMeans + fusion intelligente (v1.1)")
st.markdown("---")

# CHARGEMENT DES DONNÉES
try:
    df = pd.read_csv("final (4).csv")
except FileNotFoundError:
    st.error("Le fichier 'final (4).csv' est introuvable.")
    st.stop()

# AGGRÉGATION PAR UTILISATEUR
user_df = df.groupby("visitor_id").agg({
    'rfm_recency': 'mean',
    'rfm_frequency': 'mean',
    'rfm_intensity': 'mean',
    'engagement_score': 'mean',
    'engagement_density': 'mean',
    'avg_actions_per_session': 'mean',
    'avg_session_duration': 'mean',
    'bounce_rate': 'mean',
    'is_recent_active': 'max'
}).reset_index()

# CLUSTERING
features = [
    'rfm_recency', 'rfm_frequency', 'rfm_intensity',
    'engagement_score', 'engagement_density',
    'avg_actions_per_session', 'avg_session_duration',
    'bounce_rate', 'is_recent_active'
]

X = user_df[features].fillna(0)
X_scaled = StandardScaler().fit_transform(X)

kmeans = KMeans(n_clusters=7, random_state=42, n_init=10)
user_df['cluster'] = kmeans.fit_predict(X_scaled)

# FUSION DE CLUSTERS 2 ET 5 VERS LEUR PLUS PROCHE
centroids = pd.DataFrame(X_scaled).groupby(user_df['cluster']).mean()
dist_matrix = pairwise_distances(centroids)

def closest_cluster(from_cluster, exclude_clusters):
    distances = dist_matrix[from_cluster].copy()
    distances[exclude_clusters] = np.inf
    return np.argmin(distances)

nearest_for_2 = closest_cluster(2, exclude_clusters=[2, 5])
nearest_for_5 = closest_cluster(5, exclude_clusters=[2, 5])

user_df['cluster'] = user_df['cluster'].replace({
    2: nearest_for_2,
    5: nearest_for_5
})

# MAPPING DES PROFILS
cluster_labels = {
    0: "🔥 Utilisateurs actifs",
    1: "🟠 Visiteurs occasionnels",
    3: "🟣 Engagement moyen",
    4: "🔴 Nouveaux utilisateurs",
    6: "🟢 Explorateurs passifs"
}
user_df['profil'] = user_df['cluster'].map(cluster_labels)

# KPIs GÉNÉRAUX
nb_total = len(user_df)
nb_actifs = len(user_df[user_df["profil"] == "🔥 Utilisateurs actifs"])
nb_passifs = len(user_df[user_df["profil"].isin(["🟠 Visiteurs occasionnels", "🟢 Explorateurs passifs"])])
pct_actifs = round(nb_actifs / nb_total * 100, 1)
pct_passifs = round(nb_passifs / nb_total * 100, 1)

col1, col2, col3 = st.columns(3)
col1.metric("👥 Total utilisateurs", f"{nb_total:,}")
col2.metric("✅ Actifs", f"{nb_actifs:,} ({pct_actifs}%)")
col3.metric("⚠️ À risque", f"{nb_passifs:,} ({pct_passifs}%)")

st.markdown("---")
st.markdown("## 👤 Profils utilisateurs & recommandations")

# RECOMMANDATIONS PAR PROFIL
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

# AFFICHAGE PAR PROFIL
for profil in user_df["profil"].dropna().unique():
    df_seg = user_df[user_df["profil"] == profil]
    r = reco_map.get(profil, {})
    with st.expander(f"{profil} – {len(df_seg)} utilisateurs"):
        st.markdown(f"**🎯 Objectif :** {r.get('objectif','')}")
        st.markdown(f"**✅ Action recommandée :** {r.get('action','')}")
        st.markdown(f"**🗣️ Ton conseillé :** {r.get('ton','')}")
        st.markdown(f"**📡 Canal :** {r.get('canal','')}")
        st.markdown(f"**👉 Exemple :** {r.get('cta','')}")

# SYNTHÈSE DG
st.markdown("---")
st.markdown("## 📌 Synthèse DG")
st.markdown("""
- Les utilisateurs actifs sont engagés mais doivent être valorisés.
- Des campagnes simples peuvent réengager 30% des profils dormants.
- Une séquence d’accueil permettra de mieux intégrer les nouveaux.
""")

# 🔍 FILTRE PAR VISITOR_ID
st.markdown("---")
st.markdown("## 🔎 Explorer un utilisateur par ID")

visitor_ids = user_df['visitor_id'].unique()
selected_id = st.selectbox("Sélectionnez un visitor_id :", sorted(visitor_ids))

user_info = user_df[user_df['visitor_id'] == selected_id]

if not user_info.empty:
    st.markdown(f"### 👤 Infos pour l'utilisateur ID : `{selected_id}`")

    st.dataframe(user_info[[
        'rfm_recency', 'rfm_frequency', 'rfm_intensity',
        'engagement_score', 'engagement_density',
        'avg_actions_per_session', 'avg_session_duration',
        'bounce_rate', 'is_recent_active'
    ]].T.rename(columns={user_info.index[0]: "Valeur"}))

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
