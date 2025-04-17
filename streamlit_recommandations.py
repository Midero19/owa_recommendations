import streamlit as st
import pandas as pd
import os
import gdown
import matplotlib.pyplot as plt

# Eviter les erreurs sur Streamlit Cloud
os.environ["STREAMLIT_WATCH_DISABLE"] = "true"

# --- TELECHARGEMENT DU FICHIER ---
file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

if not os.path.exists(output_path):
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# --- CHARGEMENT DU FICHIER ---
df = pd.read_csv(
    output_path,
    sep=";",
    encoding="utf-8",
    on_bad_lines="skip",
    engine="python",
    dtype={"visitor_id": str}
)

# --- PRETRAITEMENT ---
df['session_id'] = df['session_id'].astype(str)
df['yyyymmdd_click'] = pd.to_datetime(df['yyyymmdd_click'].astype(str), format="%Y%m%d", errors='coerce')

# --- MAPPING DES CLUSTERS ---
cluster_labels = {
    0: "Utilisateurs actifs",
    1: "Visiteurs occasionnels",
    3: "Engagement moyen",
    4: "Nouveaux utilisateurs",
    6: "Explorateurs passifs"
}
df["profil"] = df["cluster"].map(cluster_labels)

# --- TYPOLOGIE COMPORTEMENTALE ---
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

# --- BARRE LATERALE (FILTRES) ---
st.sidebar.header("🌟 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))

with st.sidebar.expander("ℹ️ Légende profils / interactions"):
    st.markdown("""
**Profils utilisateurs**  
🔥 Utilisateurs actifs • 🟠 Visiteurs occasionnels  
🔸 Engagement moyen • 🔴 Nouveaux utilisateurs • 🔵 Explorateurs passifs

**Types d'interactions**  
😪 Volatile • 🧠 Lecteur curieux • ⚡ Engagé silencieux  
💥 Interactif actif • 📌 Standard
""")

# --- APPLICATION DES FILTRES ---
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

# --- GRAPHIQUES DYNAMIQUES ---
st.markdown("## 📊 Statistiques filtrées")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Profils")
    profil_counts = filtered_df['profil'].value_counts()
    fig1, ax1 = plt.subplots(figsize=(4, 4))
    if not profil_counts.empty:
        ax1.pie(profil_counts, labels=profil_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.axis('equal')
        st.pyplot(fig1)
    else:
        st.info("Aucun profil à afficher.")

with col2:
    st.markdown("### Durée moyenne (s)")
    avg_duration = filtered_df.groupby('profil')['avg_session_duration'].mean().sort_values()
    fig2, ax2 = plt.subplots(figsize=(4, 4))
    if not avg_duration.empty:
        ax2.barh(avg_duration.index, avg_duration.values)
        ax2.set_xlabel("Secondes")
        st.pyplot(fig2)
    else:
        st.info("Pas de durée moyenne dispo.")

with col3:
    st.markdown("### Interactions")
    interaction_counts = filtered_df['interaction_type'].value_counts()
    fig3, ax3 = plt.subplots(figsize=(4, 4))
    if not interaction_counts.empty:
        ax3.bar(interaction_counts.index, interaction_counts.values)
        ax3.set_ylabel("Utilisateurs")
        ax3.tick_params(axis='x', rotation=45)
        st.pyplot(fig3)
    else:
        st.info("Aucune interaction à afficher.")

# --- TABLEAU RESULTATS ---
st.markdown("## 📅 Résultats utilisateurs")
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
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
