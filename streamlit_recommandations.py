import streamlit as st
import pandas as pd
import os
import gdown
import matplotlib.pyplot as plt
import altair as alt
import re

st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='color: #4CAF50; font-size: 3rem;'>🧠 Moteur de recommandations utilisateurs</h1>
    <p style='color: grey;'>Analyse comportementale et suggestions personnalisées en un clic</p>
</div>
""", unsafe_allow_html=True)

file_id = "1NMvtE9kVC2re36hK_YtvjOxybtYqGJ5Q"
output_path = "final_owa.csv"

if not os.path.exists(output_path):
    gdown.download(f"https://drive.google.com/uc?id={file_id}", output_path, quiet=False)

# Chargement des données
with st.spinner("Chargement des données en cours..."):
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

# Reco maps (inchangés ici)
reco_map = {...}  # raccourci

dom_reco_map = {...}  # raccourci

# Filtres utilisateur
st.sidebar.header("🎯 Filtres utilisateur")
all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
selected_date = st.sidebar.selectbox("Date de clic :", ["Toutes"] + list(all_dates))
selected_session = st.sidebar.selectbox("Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
selected_visitor = st.sidebar.selectbox("Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
selected_user = st.sidebar.selectbox("Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
selected_risk = st.sidebar.selectbox("Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))

# Filtrage
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

# Affichage résultats
st.markdown("""
<div style='text-align: center;'>
    <h2 style='color: #F4B400;'>📋 Résultats utilisateurs</h2>
</div>
""", unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center; font-size:1.2rem;'>📊 <strong>Nombre de clics</strong> : {len(filtered_df)}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center; font-size:1.2rem;'>🧍‍♂️ <strong>Utilisateurs uniques</strong> : {filtered_df['visitor_id'].nunique()}</p>", unsafe_allow_html=True)

if not filtered_df.empty:
    grouped_df = filtered_df.groupby(['visitor_id', 'user_name_click']).agg({
        'yyyymmdd_click': 'min',
        'profil': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'interaction_type': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'risk_level': 'max',
        'engagement_score': 'mean'
    }).reset_index()

    # Répartition profils
    st.markdown("""
    <div style='text-align: center; margin-top: 2rem;'>
        <h2 style='color: #1E88E5;'>📊 Répartition des profils utilisateurs</h2>
    </div>
    """, unsafe_allow_html=True)

    profil_counts = grouped_df['profil'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    profil_counts.plot(kind='bar', ax=ax)
    ax.set_ylabel("Nombre d'utilisateurs")
    ax.set_xlabel("Profil utilisateur")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

    # Tableau
    st.dataframe(grouped_df)

    # Graph engagement
    engagement_over_time = filtered_df[['yyyymmdd_click', 'engagement_score', 'visitor_id', 'user_name_click']].dropna()
    if selected_visitor != "Tous":
        title = f"Score d'engagement pour {selected_visitor}"
        chart_data = engagement_over_time[engagement_over_time['visitor_id'] == selected_visitor]
    else:
        title = "Score d'engagement global (moyenne quotidienne)"
        chart_data = engagement_over_time.groupby('yyyymmdd_click').agg({'engagement_score': 'mean'}).reset_index()

    st.markdown(f"""
    <div style='text-align: center; margin-top: 3rem;'>
        <h2 style='color: #1E88E5;'>📈 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

    line_chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x='yyyymmdd_click:T',
        y='engagement_score:Q'
    ).properties(width=700, height=400)
    st.altair_chart(line_chart, use_container_width=True)

    # Recommandations personnalisées
    st.markdown("""
    <div style='text-align: center; margin-top: 3rem;'>
        <h2 style='color: #43A047;'>✅ Recommandations personnalisées</h2>
    </div>
    """, unsafe_allow_html=True)

    unique_users = filtered_df.drop_duplicates(subset=['visitor_id', 'user_name_click', 'interaction_type', 'profil'])
    dom_by_visitor = df[['visitor_id', 'dom_element_id']].dropna().groupby('visitor_id')['dom_element_id'].agg(lambda x: x.mode().iloc[0] if not x.mode().empty else None)

    for idx, user in unique_users.iterrows():
        key_id = f"{user['visitor_id']}_{re.sub(r'\\W+', '_', str(user['user_name_click']))}_{idx}"
        with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']} (profil : {user['profil']}, risque : {user['risk_level']})"):
            reco = reco_map[user['interaction_type']]
            st.markdown(f"**Objectif :** {reco['objectif']}")
            st.markdown(f"**Action :** {reco['action']}")
            st.markdown(f"**Ton :** {reco['ton']}")
            st.markdown(f"**Canal :** {reco['canal']}")
            st.markdown(f"**CTA :** {reco['cta']}")

            if st.checkbox("🔍 Voir la recommandation DOM", key=key_id):
                top_dom = dom_by_visitor.get(user['visitor_id'])
                if pd.notna(top_dom) and top_dom in dom_reco_map:
                    dom = dom_reco_map[top_dom]
                    st.markdown(f"**Élément DOM :** `{top_dom}`")
                    st.markdown(f"**Objectif :** {dom['objectif']}")
                    st.markdown(f"**Action :** {dom['action']}")
                    st.markdown(f"**Ton :** {dom['ton']}")
                    st.markdown(f"**Canal :** {dom['canal']}")
                    st.markdown(f"**CTA :** {dom['cta']}")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
