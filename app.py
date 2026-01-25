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
        "topic": "Food and Drinks", 
        "session_code": "LAB2024", 
        "teacher_email": "", 
        "vocab": "Apple, Banana, Milk, I like, I don't like",
        "custom_prompt": "Fais semblant d'être un serveur dans un café. Demande à l'élève ce qu'il veut manger et boire pour son petit-déjeuner."
    }

# --- FONCTION PDF (Notation FWB ABCD) ---
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
    pdf.cell(200, 10, txt="Ton Coaching (Juste & Encourageant) :", ln=True)
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
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        topic = col2.text_input("Sujet thématique :", value=st.session_state.class_settings["topic"])
        mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
        
        st.divider()
        voc = st.text_area("Attendus spécifiques (Lexique/Grammaire) :", value=st.session_state.class_settings["vocab"])
        mission = st.text_area("🎯 MISSION DU TUTEUR (L'IA l'utilisera pour lancer le dialogue) :", 
                               value=st.session_state.class_settings["custom_prompt"])
        
        if st.form_submit_button("✅ Enregistrer et Publier"):
            st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc, "custom_prompt": mission})
            st.success(f"Session publiée : Niveau {lvl}")
            st.rerun()
    st.divider()
    qr = qrcode.make("https://tuteur-anglais.streamlit.app")
    buf = BytesIO(); qr.save(buf); st.image(buf, width=150, caption="Scanner pour l'élève")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.info("👈 Entre ton prénom pour commencer.")
    else:
        st.title(f"🗣️ Sujet : {s['topic']}")
        
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        adapt_prompt = f"""Tu es un tuteur de {s['language']} niveau {s['level']}. 
        MISSION: {s['custom_prompt']}. 
        RÈGLE: Utilise ta MISSION pour poser une question TRÈS COURTE sur {s['topic']}.
        Si Niveau=Primaire: phrases de 3-4 mots max.
        CORRECTIONS: Écris après 'Correction:', mais ne les lis pas oralement."""

        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
            <div id="chatbox" style="height:250px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif; border-bottom:1px solid #eee;">
                <p style="color:blue;"><b>Système:</b> Clique sur le micro pour que l'IA te parle !</p>
            </div>
            <button id="btn-mic" style="width:100%; padding:20px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:1.2em;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let messages = [{{role: "system", content: "{adapt_prompt}"}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');
            const synth = window.speechSynthesis;
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";
            rec.continuous = false;
            rec.interimResults = false;

            async function askIA(userInput) {{
                if(userInput) messages.push({{role: "user", content: userInput}});
                else messages.push({{role: "user", content: "Lance la mission stp."}});

                const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                    body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                }});
                const d = await r.json();
                const reply = d.choices[0].message.content;
                messages.push({{role: "assistant", content: reply}});
                
                box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px; margin:5px 0;">IA: ${{reply.replace('Correction:', '<br><i style="color:red;">Correction:</i>')}}</p>`;
                box.scrollTop = box.scrollHeight;

                synth.cancel();
                const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                u.lang = "{tts_l}";
                synth.speak(u);
            }}

            btn.onclick = () => {{
                synth.speak(new SpeechSynthesisUtterance("")); // Débloque l'audio
                btn.style.background = "#28a745";
                btn.innerText = "ÉCOUTE EN COURS...";
                try {{
                    rec.start();
                }} catch(e) {{
                    console.log("Re-clic");
                }}
            }};

            rec.onresult = (e) => {{
                const text = e.results[0][0].transcript;
                box.innerHTML += `<p style="text-align:right; margin:5px 0;"><b>${{text}}</b></p>`;
                btn.style.background = "#dc3545";
                btn.innerText = "🎤 CLIQUE ET PARLE";
                askIA(text);
            }};

            rec.onerror = (err) => {{
                btn.style.background = "#dc3545";
                btn.innerText = "🎤 ERREUR MICRO (Réessaye)";
                // Si c'est le premier clic et que ça rate, on lance quand même l'IA
                if(messages.length === 1) askIA(null);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=450)

        # --- EVALUATION ---
        st.divider()
        transcription = st.text_area("Copie ton dialogue ici pour le bilan :")
        if st.button("🏁 Générer mon Bilan Officiel"):
            with st.spinner("Analyse..."):
                eval_p = f"""Tu es un examinateur FWB. Tutoie l'élève (Niveau {s['level']}).
                Applique ABCD. BARÈME STRICT : $1 \\times C = 8/20$, $2 \\times C$ ou $1 \\times D = 6/20$.
                Sois encourageant."""
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {transcription}"}])
                bilan = res.choices[0].message.content
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan)
                st.download_button("📥 Télécharger le PDF", pdf, f"Bilan_{user_name}.pdf")
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20{user_name}&body=Mon%20bilan%20en%20annexe."
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center;">📧 Envoyer au professeur ({m})</div></a>', unsafe_allow_html=True)
