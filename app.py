import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
import urllib.parse
import json

# 1. CONFIGURATION
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", "level": "S1-S2", "topic": "Daily Routine",
        "min_turns": 3, "session_code": "LAB2024", "teacher_email": "votre@email.com",
        "vocab": "wake up, breakfast, then", "grammar": "Present Simple"
    }

# --- INTERFACE PROFESSEUR ---
if st.session_state.get("role") == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    with st.form("config"):
        c1, c2 = st.columns(2)
        lang = c1.selectbox("Langue :", ["English", "Nederlands"])
        lvl = c1.selectbox("Niveau FWB :", ["S1-S2", "S3-S4", "Primaire"])
        topic = c2.text_input("Sujet :", value=st.session_state.class_settings["topic"])
        mail = c2.text_input("Email de réception :", value=st.session_state.class_settings["teacher_email"])
        voc = st.text_area("Lexique/Grammaire cibles :", value=st.session_state.class_settings["vocab"])
        if st.form_submit_button("Enregistrer"):
            st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc})
            st.success("Configuré !")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    st.sidebar.title("👤 Profil")
    user_name = st.sidebar.text_input("Ton Prénom :")

    if not user_name:
        st.warning("👈 Indique ton prénom dans la barre latérale pour commencer.")
    else:
        st.title(f"🗣️ Entraînement : {s['language']}")
        st.info(f"**Mission :** Parle de '{s['topic']}' (Niveau {s['level']})")

        # LOGIQUE MICRO + IA + SYNTHÈSE VOCALE
        # Note : On passe l'historique dans un composant caché pour le récupérer en Python
        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
            <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif; border-bottom:1px solid #eee;"></div>
            <button id="btn-mic" style="width:100%; padding:20px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; font-size:18px; cursor:pointer;">🎤 CLIQUE POUR PARLER</button>
        </div>

        <script>
            const API_KEY = "{api_key}";
            let messages = [{{role: "system", content: "Tu es un tuteur de langue {s['language']} pour un élève de niveau {s['level']}. Sujet: {s['topic']}. Utilise le vocabulaire: {s['vocab']}. Fais des phrases courtes."}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');

            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{'en-US' if s['language']=='English' else 'nl-BE'}";

            btn.onclick = () => {{ rec.start(); btn.style.background="#28a745"; btn.innerText="Je t'écoute..."; }};

            rec.onresult = async (e) => {{
                const text = e.results[0][0].transcript;
                btn.style.background="#dc3545"; btn.innerText="🎤 CLIQUE POUR PARLER";
                
                box.innerHTML += `<p style="text-align:right;"><b>Moi:</b> ${{text}}</p>`;
                messages.push({{role: "user", content: text}});

                const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                    body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                }});
                
                const d = await r.json();
                const reply = d.choices[0].message.content;
                messages.push({{role: "assistant", content: reply}});
                
                box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;"><b>IA:</b> ${{reply}}</p>`;
                box.scrollTop = box.scrollHeight;

                const u = new SpeechSynthesisUtterance(reply);
                u.lang = "{'en-US' if s['language']=='English' else 'nl-NL'}";
                window.speechSynthesis.speak(u);
                
                // On envoie l'historique au parent Streamlit
                window.parent.postMessage({{type: 'chat_history', data: messages}}, "*");
            }};
        </script>
        """
        st.components.v1.html(html_code, height=450)

        # BOUTON FINAL : ANALYSE FWB + MAIL
        st.write("---")
        if st.button("🏁 Terminer et générer mon évaluation FWB"):
            with st.spinner("Analyse de tes compétences en cours..."):
                # Ici, on simule l'appel de synthèse finale (on peut l'automatiser via GPT aussi)
                crit_text = "S1-S2" if s['level'] == "S1-S2" else "S3-S4"
                
                evaluation_finale = f"""RAPPORT D'ÉVALUATION (Normes FWB)
Élève : {user_name}
Niveau : {s['level']}
Langue : {s['language']}

1. Intention de communication : [A/B/C/D]
2. Lexique ({s['vocab']}) : [A/B/C/D]
3. Structures grammaticales : [A/B/C/D]
4. Aisance orale : [A/B/C/D]

TRANSCRIPTION DISPONIBLE SUR LE SMARTPHONE DE L'ÉLÈVE."""

                mail_link = f"mailto:{s['teacher_email']}?subject=Evaluation {user_name}&body={urllib.parse.quote(evaluation_finale)}"
                
                st.success("✅ Analyse terminée !")
                st.markdown(f'<a href="{mail_link}" target="_blank" style="text-decoration:none;"><div style="background:#28a745; color:white; padding:20px; border-radius:10px; text-align:center; font-weight:bold;">📧 ENVOYER MES RÉSULTATS AU PROFESSEUR</div></a>', unsafe_allow_html=True)

# --- LOGIN ---
else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Rôle :", ["Élève", "Professeur"], horizontal=True)
    if st.text_input("Code :", type="password") in ["ADMIN123", "ELEC2024"]:
        if st.button("Entrer"):
            st.session_state.role = role
            st.rerun()
