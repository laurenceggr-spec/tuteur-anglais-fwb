import streamlit as st
from openai import OpenAI

# 1. Configuration et style
st.set_page_config(page_title="Mon Tuteur d'Anglais FWB", page_icon="🇧🇪")
st.title("🇬🇧 English Speaking Partner")
st.subheader("Niveau A1-A2 (Référentiel FWB)")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 2. Définition de la mission de l'IA (Le Prompt)
SYSTEM_PROMPT = """
Tu es un tuteur d'anglais bienveillant pour un élève belge (référentiel FWB). 
Niveau : A1/A2. 
Mission : Réponds en UNE phrase courte. 
Si l'élève a fait une faute, corrige-le gentiment en disant 'You said... but it's better to say...'. 
Termine toujours par une question simple pour continuer la conversation.
Utilise un vocabulaire très simple (famille, école, loisirs, animaux).
"""

# 3. Interface Audio
audio_value = st.audio_input("Clique sur le micro et parle :")

if audio_value:
    # On donne un nom au fichier pour Whisper
    audio_value.name = "audio.wav"
    
    with st.spinner("Ton tuteur écoute..."):
        # A. Transcription (Oreille de l'IA)
        transcript = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_value
        )
        user_text = transcript.text
        st.info(f"Tu as dit : {user_text}")

        # B. Génération de la réponse (Cerveau de l'IA)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ]
        )
        ai_message = response.choices[0].message.content
        st.success(f"Tuteur : {ai_message}")

        # C. Synthèse Vocale (Voix de l'IA)
        # On utilise une voix claire pour des élèves (Alloy)
        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=ai_message
        )
        
        # L'option autoplay=True permet à l'IA de parler immédiatement
        st.audio(speech_response.content, autoplay=True)

st.divider()
st.caption("Conseil : Utilise des écouteurs pour une meilleure expérience.")
