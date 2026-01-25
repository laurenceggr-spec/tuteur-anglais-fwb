import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
from fpdf import FPDF
from openai import OpenAI
import urllib.parse

# 1. CONFIGURATION & MOTEUR
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

# Initialisation persistante
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", 
        "level": "Primaire (Initiation/A1)",
        "mode": "Tuteur (Dialogue IA)",
        "topic": "Daily Routine", 
        "session_code": "LAB2024", 
        "teacher_email": "", 
        "vocab": "Hello, Apple, Numbers",
        "custom_prompt": "Sois un tuteur pour enfants. Utilise des phrases de 3 mots maximum."
    }

# --- FONCTION PDF (Notation FWB ABCD + Tutoiement) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - FWB", ln=True, align='C')
    
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    pdf.cell(200, 8, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 8, txt=f"Niveau Cible : {level} | Sujet : {topic}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Ton Coaching Personnalise :", ln=True)
    
    pdf.set_font("Arial", size=10)
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIQUE DES ROLES ---
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    with st.form("config"):
        col1, col2 = st.columns(2)
        # Utilisation de index pour forcer la sélection actuelle
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau Cible :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        mode = col1.selectbox("Mode :", ["Tuteur (Dialogue IA)", "Solo (IA écoute)", "Duo"])
        
        topic = col2.text_input("Sujet :", value=st.session_state.class_settings["topic"])
        mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
        voc = col2.text_area("Attendus (Voc/Gramm) :", value=st.session_state.class_settings["vocab"])
        custom_p = col2.text_area("Mission IA :", value=st.session_state.class_settings["custom_prompt"])
        
        if st.form_submit_button("✅ Enregistrer la session"):
            st.session_state.class_settings.update({
                "language": lang, "level": lvl, "mode": mode, 
                "topic": topic, "teacher_email": mail, "vocab": voc, "custom_prompt": custom_p
            })
            st.success(f"Configuré sur : {lvl}")
            st.rerun()
    
    st.divider()
    qr = qrcode.make("https://tuteur-anglais.streamlit.app")
    buf = BytesIO(); qr.save(buf); st.image(buf, width=150, caption="Scanner pour l'élève")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    st.sidebar.title("👤 Profil")
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.warning("Écris ton prénom à gauche.")
    else:
        st.title(f"🗣️ Niveau : {s['level']}")
        st.caption(f"Sujet : {s['topic']}")
        
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        # PROMPT ADAPTÉ AU RÉFÉRENTIEL
        adapt_prompt = f"Tu es un tuteur {s['language']} niveau {s['level']}. TRÈS IMPORTANT: Si le niveau est Primaire A1, n'utilise que des mots très simples. Ne fais pas de phrases complexes."
        
        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
            <div id="chatbox" style="height:250px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;"></div>
            <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let messages = [{{role: "system", content: "{adapt_prompt} {s['custom_prompt']}. Réponds oralement. Ecris les corrections APRES 'Correction:'."}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');
            const synth = window.speechSynthesis;
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";

            btn.onclick = () => {{ 
                synth.speak(new SpeechSynthesisUtterance("")); 
                rec.start(); 
                btn.style.background = "#28a745"; 
            }};

            rec.onresult = async (e) => {{
                const text = e.results[0][0].transcript;
                btn.style.background = "#dc3545";
                box.innerHTML += `<p style="text-align:right;"><b>${{text}}</b></p>`;
                messages.push({{role: "user", content: text}});

                const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                    body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                }});
                const d = await r.json();
                const reply = d.choices[0].message.content;
                messages.push({{role: "assistant", content: reply}});
                box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;">${{reply.replace('Correction:', '<br><i>Correction:</i>')}}</p>`;
                box.scrollTop = box.scrollHeight;

                synth.cancel();
                const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                u.lang = "{tts_l}";
                synth.speak(u);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=400)

        # --- EVALUATION BIENVEILLANTE ---
        st.divider()
        transcription = st.text_area("Copie ton dialogue pour l'évaluation :")
        if st.button("🏁 Obtenir mon Bilan"):
            with st.spinner("Analyse bienveillante..."):
                eval_p = f"""Tu es un examinateur FWB pour le niveau {s['level']}. 
                Utilise la grille ABCD. L'élève est un débutant : sois indulgent. 
                S'il parvient à communiquer l'essentiel, il mérite A ou B.
                1. Réalisation (A-D) 2. Adéquation (A-D) 3. Langue (A-D) 4. Rythme (A-D).
                Barème : Si C ou D présent, applique : 1xC=8/20, 1xD=6/20, 2xC=6/20. Sinon note /20.
                Tutoie l'élève et donne 3 conseils concrets de progression."""
                
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {transcription}"}])
                bilan = res.choices[0].message.content
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan)
                st.download_button("📥 Télécharger le PDF", pdf, f"Bilan_{user_name}.pdf")
                
                # Mail pré-rempli
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20{user_name}&body=Voici%20mon%20bilan%20PDF%20joint."
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center;">📧 Envoyer au professeur ({m})</div></a>', unsafe_allow_html=True)
