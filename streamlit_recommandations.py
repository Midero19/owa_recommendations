import streamlit as st
import pandas as pd
import os
import gdown
import matplotlib.pyplot as plt

os.environ["STREAMLIT_WATCH_DISABLE"] = "true"

file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

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

cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}
df["profil"] = df["cluster"].map(cluster_labels)

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

df['interaction_type'] = df.apply(classify_interaction, axis=1)

reco_map = {
    "💤 Volatile": {"objectif": "Réduire l’abandon à froid dès la première visite", "action": "Relancer par un email ou push dans l’heure avec un contenu percutant", "ton": "Intrigant, FOMO", "canal": "Push / Email", "cta": "⏱️ Découvrez ce que vous avez manqué en 60 secondes !"},
    "🧠 Lecteur curieux": {"objectif": "Transformer sa curiosité en interaction", "action": "Afficher un quiz, emoji ou bouton 'suivre ce thème'", "ton": "Complice, engageant", "canal": "Popup + email", "cta": "📚 Activez les suggestions selon vos lectures"},
    "⚡ Engagé silencieux": {"objectif": "Lever les freins invisibles à l’action", "action": "Ajouter un bouton de réaction ou une question douce", "ton": "Encourageant, chaleureux", "canal": "Interface + email", "cta": "👍 Vous avez aimé ce contenu ? Faites-le savoir en un clic"},
    "💥 Utilisateur très actif": {"objectif": "Prévenir la frustration d’un utilisateur très impliqué", "action": "Offrir un contenu VIP ou une invitation à contribuer", "ton": "Valorisant, exclusif", "canal": "Email personnalisé + interface", "cta": "🏅 Merci pour votre activité ! Voici un avant-goût en exclusivité"},
    "📌 Standard": {"objectif": "Créer un déclic d’intérêt", "action": "Envoyer une sélection des contenus populaires", "ton": "Positif, informatif", "canal": "Email hebdomadaire", "cta": "📬 Voici les contenus qui font vibrer notre communauté"}
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

st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))

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

st.markdown("## 📊 Statistiques filtrées")
with st.expander("ℹ️ Légende profils / interactions"):
    st.markdown("""
**Profils utilisateurs**  
🔥 Utilisateurs actifs • 🟠 Visiteurs occasionnels  
🟣 Engagement moyen • 🔴 Nouveaux utilisateurs • 🟢 Explorateurs passifs

**Types d'interactions**  
😴 Volatile : visite très courte ou abandonnée  
🧠 Lecteur curieux : consulte beaucoup de pages sans agir  
⚡ Engagé silencieux : reste longtemps sans interagir  
💥 Utilisateur très actif : agit beaucoup ou commente  
📌 Standard : comportement moyen sans traits distinctifs
""")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### Profils")
    profil_counts = filtered_df['profil'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(6, 6))
    if not profil_counts.empty:
        ax1.pie(profil_counts, labels=profil_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)
    else:
        st.info("Aucun profil à afficher.")

with col2:
    st.markdown("#### Interactions")
    interaction_counts = filtered_df['interaction_type'].value_counts()
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    if not interaction_counts.empty:
        ax2.bar(interaction_counts.index, interaction_counts.values)
        ax2.set_ylabel("Utilisateurs")
        ax2.tick_params(axis='x', rotation=45)
        st.pyplot(fig2)
    else:
        st.info("Aucune interaction à afficher.")



st.markdown("## 📋 Résultats utilisateurs")
if selected_date == "Toutes":
    st.markdown("### 👥 Toutes les dates")
else:
    st.markdown(f"### 👥 Résultats pour le {selected_date}")

st.write(f"Nombre d’utilisateurs : {len(filtered_df)}")

if not filtered_df.empty:
    st.dataframe(filtered_df[[
        'yyyymmdd_click', 'visitor_id', 'user_name_click',
        'profil', 'interaction_type', 'risk_level', 'engagement_score'
    ]])

st.markdown("## ✅ Recommandations personnalisées")
    unique_users = filtered_df.drop_duplicates(subset=['visitor_id', 'interaction_type', 'profil'])
    dom_by_visitor = df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

    for _, user in unique_users.iterrows():
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
                    st.markdown(f"**Élément :** `{top_dom}`")
                    st.markdown(f"**Objectif :** {dom['objectif']}")
                    st.markdown(f"**Action :** {dom['action']}")
                    st.markdown(f"**Ton :** {dom['ton']}")
                    st.markdown(f"**Canal :** {dom['canal']}")
                    st.markdown(f"**CTA :** {dom['cta']}")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
