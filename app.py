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

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", 
        "level": "Primaire (Initiation/A1)",
        "mode": "Tuteur (Dialogue IA)",
        "topic": "Daily Routine", 
        "session_code": "LAB2024", 
        "teacher_email": "", 
        "vocab": "Breakfast, milk, bread",
        "custom_prompt": "Immersion directe."
    }

# --- FONCTION PDF (Barème Page 4 Strict) ---
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
    pdf.cell(200, 10, txt="Ton Coaching (Tutoiement & Bienveillance) :", ln=True)
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

# --- INTERFACE PROFESSEUR (Mise à jour Session) ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration")
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        topic = col2.text_input("Sujet thématique :", value=st.session_state.class_settings["topic"])
        mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
        voc = col2.text_area("Attendus spécifiques :", value=st.session_state.class_settings["vocab"])
        if st.form_submit_button("✅ Enregistrer et Publier"):
            st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc})
            st.success("Session synchronisée !")
            st.rerun()
    st.divider()
    qr = qrcode.make("https://tuteur-anglais.streamlit.app")
    buf = BytesIO(); qr.save(buf); st.image(buf, width=150)

# --- INTERFACE ÉLÈVE (Dialogue Immersif) ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.info("👈 Entre ton prénom pour commencer l'immersion.")
    else:
        st.title(f"🗣️ On parle de : {s['topic']}")
        st.write(f"Niveau : **{s['level']}**")

        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        # PROMPT : INTERDICTION DES BANALITÉS
        adapt_prompt = f"""Tu es un tuteur de {s['language']} pour un élève de niveau {s['level']}.
        SUJET: {s['topic']}. ATTENDUS: {s['vocab']}.
        RÈGLE D'OR: Ne commence JAMAIS par 'Hello, how are you?'. 
        Entre DIRECTEMENT dans le sujet en posant une question liée à {s['topic']}.
        Si Niveau=Primaire: utilise des phrases de 3-4 mots maximum.
        Si Niveau=Secondaire: utilise des phrases simples mais complètes.
        CORRECTIONS: Écris les corrections après 'Correction:', mais ne les DIS PAS oralement."""

        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
            <div id="chatbox" style="height:250px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;">
                <p style="color:gray;"><i>L'IA attend que tu parles pour lancer le sujet...</i></p>
            </div>
            <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let messages = [{{role: "system", content: "{adapt_prompt}"}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');
            const synth = window.speechSynthesis;
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";

            btn.onclick = () => {{ 
                synth.speak(new SpeechSynthesisUtterance("")); 
                rec.start(); 
                btn.style.background = "#28a745"; btn.innerText = "Je t'écoute...";
            }};

            rec.onresult = async (e) => {{
                const text = e.results[0][0].transcript;
                btn.style.background = "#dc3545"; btn.innerText = "🎤 CLIQUE ET PARLE";
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
                
                // Affichage avec correction visuelle
                box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;">${{reply.replace('Correction:', '<br><small style="color:red;">Correction:</small>')}}</p>`;
                box.scrollTop = box.scrollHeight;

                // Parole sans la correction
                synth.cancel();
                const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                u.lang = "{tts_l}";
                synth.speak(u);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=400)

        # --- EVALUATION STRICTE (BARÈME PAGE 4) ---
        st.divider()
        transcription = st.text_area("Copie ton dialogue ici pour obtenir ton bilan :")
        if st.button("🏁 Générer mon Bilan Officiel"):
            with st.spinner("Analyse du respect du Référentiel..."):
                eval_p = f"""Tu es un examinateur FWB pour {s['level']}. Tutoie l'élève.
                Applique la grille ABCD sur les critères : Réalisation, Adéquation, Langue, Rythme.
                BARÈME STRICT : 
                - Si A ou B partout : Donne une note entre 10 et 20.
                - 1 x C = $8/20$
                - 2 x C ou 1 x D = $6/20$
                - 3 x C ou 2 x D = $4/20$
                Ton ton doit être encourageant. Propose 3 pistes concrètes basées sur les savoirs (lexique/grammaire)."""
                
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {transcription}"}])
                bilan = res.choices[0].message.content
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan)
                st.download_button("📥 Télécharger ton Bilan PDF", pdf, f"Bilan_{user_name}.pdf")
                
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20Language%20Lab%20-%20{user_name}&body=Bonjour,%20voici%20mon%20bilan."
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">📧 Envoyer au professeur ({m})</div></a>', unsafe_allow_html=True)
