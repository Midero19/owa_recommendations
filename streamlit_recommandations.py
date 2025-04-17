import streamlit as st

st.title("🚀 Test Streamlit")
st.write("✅ L'app fonctionne correctement !")

# Bonus : test rapide des données
try:
    import pandas as pd
    df = pd.read_csv("final_owa.csv", sep=";", encoding="utf-8", on_bad_lines="skip", engine="python")
    st.success("✔ Fichier CSV chargé avec succès.")
    st.dataframe(df.head())
except Exception as e:
    st.error(f"Erreur lors du chargement du fichier : {e}")
