import streamlit as st
import pandas as pd
import os
import gdown
import re
import traceback

# Afficher la pile d'erreurs complètes dans l'app
st.set_option('server.showErrorDetails', True)

def main():
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

    df = pd.read_csv(
        output_path,
        sep=";",
        encoding="utf-8",
        on_bad_lines="skip",
        engine="python",
        dtype={"visitor_id": str}
    )

    df['session_id'] = df['session_id'].astype(str)
    df['yyyymmdd_click'] = pd.to_datetime(
        df['yyyymmdd_click'].astype(str),
        format="%Y%m%d",
        errors='coerce'
    )

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

    # Cartes de recommandations
    reco_map = {
        "💤 Volatile": {
            "objectif": "Réduire l’abandon à froid dès la première visite",
            "action": "Relancer par un email ou push dans l’heure avec un contenu percutant",
            "ton": "Intrigant, FOMO",
            "canal": "Push / Email",
            "cta": "⏱️ Découvrez ce que vous avez manqué en 60 secondes !"
        },
        # … idem pour les autres clés …
    }
    dom_reco_map = {
        "nav_menu_link": {
            "objectif": "Faciliter l'accès rapide aux contenus",
            "action": "Adapter la navigation aux rubriques préférées",
            "ton": "Clair, organisé",
            "canal": "Interface + email",
            "cta": "🔎 Naviguez plus vite dans vos contenus favoris"
        },
        # … etc …
    }

    # Sidebar filtres
    st.sidebar.header("🎯 Filtres utilisateur")
    all_dates = sorted(df['yyyymmdd_click'].dt.date.dropna().unique())
    selected_date = st.sidebar.selectbox("Date de clic :", ["Toutes"] + list(all_dates))
    selected_session = st.sidebar.selectbox("Session ID :", ["Tous"] + sorted(df['session_id'].dropna().unique()))
    selected_visitor = st.sidebar.selectbox("Visitor ID :", ["Tous"] + sorted(df['visitor_id'].dropna().unique()))
    selected_user = st.sidebar.selectbox("Nom d'utilisateur :", ["Tous"] + sorted(df['user_name_click'].dropna().unique()))
    selected_risk = st.sidebar.selectbox("Niveau de risque :", ["Tous"] + sorted(df['risk_level'].dropna().unique()))

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

    # Affichage des stats globales
    st.markdown("""
    <div style='text-align: center;'>
        <h2 style='color: #F4B400;'>📋 Résultats utilisateurs</h2>
    </div>
    """, unsafe_allow_html=True)
    date_label = "Toutes les dates" if selected_date == "Toutes" else f"le {selected_date}"
    st.markdown(f"<div style='text-align: center;'><h3>👥 {date_label}</h3></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size:1.2rem;'>📊 <strong>Nombre de clics</strong> : {len(filtered_df)}</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align: center; font-size:1.2rem;'>🧍‍♂️ <strong>Utilisateurs uniques</strong> : {filtered_df['visitor_id'].nunique()}</div>", unsafe_allow_html=True)

    if filtered_df.empty:
        st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
        return

    # Regroupements et graphiques…
    # … (reste de votre code pour les bar_chart, altair, dataframe, expander, etc.) …

    # Exemple pour le safe_name dans la boucle des recommandations :
    for idx, user in filtered_df.drop_duplicates(subset=['visitor_id','user_name_click','interaction_type','profil']).iterrows():
        reco = reco_map.get(user['interaction_type'])
        if not reco:
            continue
        with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']}"):
            st.markdown(f"**CTA :** {reco['cta']}")
            try:
                safe_name = re.sub(r'\W+', '_', str(user['user_name_click']))
                checkbox_key = f"{user['visitor_id']}_{safe_name}_{idx}"
                if st.checkbox("🔍 Voir la recommandation DOM", key=checkbox_key):
                    top_dom = df[df['visitor_id']==user['visitor_id']]['dom_element_id'].mode().iloc[0]
                    dom = dom_reco_map.get(top_dom)
                    if dom:
                        st.markdown(f"**Élément DOM :** {top_dom}")
            except Exception:
                st.error("Erreur lors de la génération du safe_name:")
                st.text(traceback.format_exc())

if __name__ == "__main__":
    try:
        main()
    except Exception:
        st.error("🔥 Une erreur inattendue est survenue :")
        st.text(traceback.format_exc())
