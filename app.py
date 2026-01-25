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

# --- FONCTION PDF (Notation FWB ABCD Strict) ---
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
        mission = st.text_area("🎯 MISSION DU TUTEUR :", value=st.session_state.class_settings["custom_prompt"])
        
        if st.form_submit_button("✅ Enregistrer et Publier"):
            st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc, "custom_prompt": mission})
            st.success(f"Session publiée : Niveau {lvl}")
            st.rerun()
    st.divider()
    qr = qrcode.make("https://tuteur-anglais.streamlit.app")
    buf = BytesIO(); qr.save(buf); st.image(buf, width=150)

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.info("👈 Entre ton prénom pour commencer.")
    else:
        st.title(f"🗣️ Activité : {s['topic']}")
        
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        adapt_prompt = f"""Tu es un tuteur de {s['language']} niveau {s['level']}. 
        MISSION: {s['custom_prompt']}. 
        IMPORTANT: Ne dis jamais 'Hello how are you'. Entre directement dans le sujet avec ta MISSION.
        Niveau Primaire: phrases de 3-4 mots.
        CORRECTIONS: Écris après 'Correction:', mais ne les lis pas."""

        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff; text-align:center;">
            <div id="status-mic" style="margin-bottom:10px; font-weight:bold; color:#dc3545;">Micro Inactif</div>
            <div id="chatbox" style="height:250px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif; text-align:left; border-bottom:1px solid #eee;">
                <p style="color:gray;">Clique sur le gros bouton pour lancer la discussion avec l'IA.</p>
            </div>
            <button id="btn-mic" style="width:100%; padding:25px; background:#dc3545; color:white; border:none; border-radius:15px; font-weight:bold; cursor:pointer; font-size:1.3em; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let messages = [{{role: "system", content: "{adapt_prompt}"}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');
            const status = document.getElementById('status-mic');
            const synth = window.speechSynthesis;
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (!SpeechRecognition) {{
                btn.innerText = "Navigateur non compatible (Utilise Chrome)";
            }}

            const rec = new SpeechRecognition();
            rec.lang = "{rec_l}";
            rec.continuous = false;

            async function askIA(userInput) {{
                if (userInput) {{
                    messages.push({{role: "user", content: userInput}});
                }} else {{
                    messages.push({{role: "user", content: "Bonjour, lance la mission."}});
                }}

                const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                    body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                }});
                const d = await r.json();
                const reply = d.choices[0].message.content;
                messages.push({{role: "assistant", content: reply}});
                
                box.innerHTML += `<p style="background:#f1f1f1; padding:10px; border-radius:10px; margin:5px 0;">IA: ${{reply.replace('Correction:', '<br><b style="color:red;">Correction:</b>')}}</p>`;
                box.scrollTop = box.scrollHeight;

                synth.cancel();
                const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                u.lang = "{tts_l}";
                synth.speak(u);
            }}

            btn.onclick = () => {{
                // Unlock Audio
                synth.speak(new SpeechSynthesisUtterance(""));
                
                // Si c'est le tout premier clic, on lance l'IA directement
                if (messages.length === 1) {{
                    status.innerText = "Lancement de la mission...";
                    status.style.color = "blue";
                    askIA(null);
                }}

                try {{
                    rec.start();
                    status.innerText = "Micro Activé : Je t'écoute...";
                    status.style.color = "#28a745";
                    btn.style.background = "#28a745";
                }} catch(e) {{
                    console.log("Rec déjà actif");
                }}
            }};

            rec.onresult = (e) => {{
                const text = e.results[0][0].transcript;
                box.innerHTML += `<p style="text-align:right; margin:5px 0;"><b>${{text}}</b></p>`;
                status.innerText = "Analyse en cours...";
                status.style.color = "orange";
                btn.style.background = "#dc3545";
                askIA(text);
            }};

            rec.onerror = (event) => {{
                btn.style.background = "#dc3545";
                if(event.error === 'not-allowed') {{
                    status.innerText = "ERREUR : Micro bloqué par le navigateur !";
                }} else {{
                    status.innerText = "Micro en attente...";
                }}
            }};

            rec.onend = () => {{
                btn.style.background = "#dc3545";
                if(status.innerText.includes("écoute")) status.innerText = "Micro en attente...";
            }};
        </script>
        """
        st.components.v1.html(html_code, height=500)

        # --- EVALUATION STRICTE PAGE 4 ---
        st.divider()
        transcription = st.text_area("Copie ton dialogue ici pour ton bilan final :")
        if st.button("🏁 Générer mon Rapport Officiel"):
            with st.spinner("Analyse pédagogique..."):
                eval_p = f"""Tu es un examinateur FWB. Tutoie l'élève (Niveau {s['level']}).
                Applique ABCD. BARÈME MATHÉMATIQUE STRICT (PAGE 4) :
                - Si A ou B partout : Note entre 10 et 20/20.
                - 1 x C = 8/20.
                - 2 x C ou 1 x D = 6/20.
                - 3 x C ou 2 x D = 4/20.
                Sois bienveillant et donne 3 pistes concrètes de travail."""
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {transcription}"}])
                bilan = res.choices[0].message.content
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan)
                st.download_button("📥 Télécharger mon Bilan PDF", pdf, f"Bilan_{user_name}.pdf")
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20Labo%20-%20{user_name}&body=Voici%20mon%20bilan."
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center;">📧 Envoyer au professeur ({m})</div></a>', unsafe_allow_html=True)
