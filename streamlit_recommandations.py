# Statistiques + graphique engagement
st.markdown("## 📊 Statistiques filtrées")
with st.expander("ℹ Légende profils / interactions"):
    st.markdown("""
*Profils utilisateurs*  
🔥 Utilisateurs actifs • 🟠 Visiteurs occasionnels  
🟣 Engagement moyen • 🔴 Nouveaux utilisateurs • 🟢 Explorateurs passifs

*Types d'interactions*  
😴 Volatile : visite très courte ou abandonnée  
🧠 Lecteur curieux : consulte beaucoup de pages sans agir  
⚡ Engagé silencieux : reste longtemps sans interagir  
💥 Utilisateur très actif : agit beaucoup ou commente  
📌 Standard : comportement moyen sans traits distinctifs
""")

st.markdown("### 📈 Évolution du taux d'engagement moyen")

daily_engagement = (
    filtered_df.dropna(subset=["yyyymmdd_click", "engagement_score"])
    .groupby(filtered_df['yyyymmdd_click'].dt.date)["engagement_score"]
    .mean()
    .reset_index()
)

if not daily_engagement.empty:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(daily_engagement["yyyymmdd_click"], daily_engagement["engagement_score"], marker='o')
    ax.set_xlabel("Date")
    ax.set_ylabel("Score d'engagement moyen")
    ax.set_title("Évolution du taux d'engagement dans le temps")
    ax.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("Pas de données disponibles pour afficher l'évolution.")

# Résultats utilisateurs
st.markdown("## 📋 Résultats utilisateurs")
if selected_date == "Toutes":
    st.markdown("### 👥 Toutes les dates")
else:
    st.markdown(f"### 👥 Résultats pour le {selected_date}")

st.write(f"Nombre de clics : {len(filtered_df)}")
st.write(f"Nombre d'utilisateurs uniques (visitor_id) : {filtered_df['visitor_id'].nunique()}")

if not filtered_df.empty:
    grouped_df = filtered_df.groupby(['visitor_id', 'user_name_click']).agg({
        'yyyymmdd_click': 'min',
        'profil': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'interaction_type': lambda x: x.mode().iloc[0] if not x.mode().empty else None,
        'risk_level': 'max',
        'engagement_score': 'mean'
    }).reset_index()

    max_rows = st.sidebar.slider("Nombre max de lignes à afficher :", 10, 500, 100)
    st.dataframe(grouped_df.head(max_rows))

    # Condition : afficher les recommandations uniquement si un filtre est appliqué
    filters_applied = (
        selected_date != "Toutes"
        or selected_session != "Tous"
        or selected_visitor != "Tous"
        or selected_user != "Tous"
        or selected_risk != "Tous"
    )

    if filters_applied:
        st.markdown("## ✅ Recommandations personnalisées")
        unique_users = filtered_df.drop_duplicates(subset=['visitor_id', 'user_name_click', 'interaction_type', 'profil'])
        dom_by_visitor = get_dom_by_visitor(df)

        max_recos = st.sidebar.slider("Nombre de recommandations à afficher :", 1, 20, 10)
        display_users = unique_users.head(max_recos)

        for _, user in display_users.iterrows():
            if user['interaction_type'] in reco_map:
                reco = reco_map[user['interaction_type']]
                with st.expander(f"👤 {user['user_name_click']} – {user['interaction_type']} (profil : {user['profil']}, risque : {user['risk_level']})"):
                    st.markdown("### 🎯 Comportement général")
                    st.markdown(f"*Objectif :* {reco['objectif']}")
                    st.markdown(f"*Action :* {reco['action']}")
                    st.markdown(f"*Ton :* {reco['ton']}")
                    st.markdown(f"*Canal :* {reco['canal']}")
                    st.markdown(f"*CTA :* {reco['cta']}")

                    top_dom = dom_by_visitor.get(user['visitor_id'])
                    if pd.notna(top_dom) and top_dom in dom_reco_map:
                        dom = dom_reco_map[top_dom]
                        st.markdown("### 🔍 Élément DOM principal")
                        st.markdown(f"*Élément :* {top_dom}")
                        st.markdown(f"*Objectif :* {dom['objectif']}")
                        st.markdown(f"*Action :* {dom['action']}")
                        st.markdown(f"*Ton :* {dom['ton']}")
                        st.markdown(f"*Canal :* {dom['canal']}")
                        st.markdown(f"*CTA :* {dom['cta']}")
    else:
        st.info("🔎 Appliquez au moins un filtre pour afficher des recommandations personnalisées.")
else:
    st.warning("Aucun utilisateur trouvé avec les filtres appliqués.")
