import streamlit as st
from openai import OpenAI
import os

# Configuration de la page
st.set_page_config(page_title="Mon Tuteur d'Anglais FWB", page_icon="🇧🇪")
st.title("🇬🇧 English Speaking Tutor (A1-A2)")
st.write("Clique sur le micro et parle à ton tuteur !")

# Initialisation du client OpenAI (Remplacez par votre clé ou utilisez les secrets Streamlit)
client = OpenAI(api_key="VOTRE_CLE_API_ICI")

# Le Prompt structuré pour le référentiel FWB
SYSTEM_PROMPT = """
Tu es un tuteur d'anglais bienveillant pour un élève belge (référentiel FWB). 
Niveau : A1/A2. 
Mission : Réponds en UNE phrase courte. 
Si l'élève fait une faute, dis 'You said... but it's better to say...'. 
Termine toujours par une question simple. 
Garde un vocabulaire très basique conforme au premier degré du secondaire.
"""

# Gestion de l'audio (Utilisation d'un composant de capture simple)
audio_value = st.audio_input("Parle à ton tuteur :")

if audio_value:
    # 1. Transcription (Audio vers Texte)
    transcript = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio_value
    )
    user_text = transcript.text
    st.write(f"**Toi :** {user_text}")

    # 2. Réponse de l'IA
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )
    ai_message = response.choices[0].message.content
    st.write(f"**Tuteur :** {ai_message}")

    # 3. Synthèse vocale (Texte vers Audio)
    speech_response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=ai_message
    )
    st.audio(speech_response.content, autoplay=True)
