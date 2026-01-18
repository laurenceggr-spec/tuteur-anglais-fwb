import streamlit as st
from openai import OpenAI

# Vérification de la clé dans les secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Clé API manquante dans les Secrets !")
    st.stop()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.title("Test de Connexion")

try:
    # Test simple
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello in English"}]
    )
    st.success("La connexion fonctionne parfaitement !")
    st.write(f"Réponse de l'IA : {response.choices[0].message.content}")
except Exception as e:
    st.error("La clé est là, mais OpenAI la refuse.")
    st.info("Vérifiez si vous avez bien ajouté 5$ de crédit sur votre compte API OpenAI.")
    st.exception(e)
