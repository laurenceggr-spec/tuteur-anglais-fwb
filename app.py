import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
from fpdf import FPDF
from openai import OpenAI
import urllib.parse

# 1. CONFIGURATION & MOTEUR (Validé)
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
        "custom_prompt": "Fais semblant d'être un serveur dans un café. Demande à l'élève ce qu'il veut manger."
    }

# --- FONCTION PDF (Barème Strict Page 4 - Validé) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - FWB", ln=True, align='C')
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    pdf.cell(200, 8, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 8, txt=f"Niveau : {level} | Sujet : {topic}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Ton Coaching (ABCD & Bienveillance) :", ln=True)
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
    st.title("👨‍🏫 Configuration")
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        topic = col2.text_input("Sujet :", value=st.session_state.class_settings["topic"])
        mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
        st.divider()
        voc = st.text_area("Attendus :", value=st.session_state.class_settings["vocab"])
        mission = st.text_area("🎯 MISSION DU TUTEUR :", value=st.session_state.class_settings["custom_prompt"])
        if st.form_submit_button("✅ Publier"):
            st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc, "custom_prompt": mission})
            st.rerun()

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    user_name = st.sidebar.text_input("Ton Prénom :")
    
    if not user_name:
        st.info("👈 Entre ton prénom pour commencer.")
    else:
        st.title(f"🗣️ Thème : {s['topic']}")
        
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        adapt_prompt = f"""Tu es un tuteur de {s['language']} niveau {s['level']}. 
        MISSION: {s['custom_prompt']}. 
        IMPORTANT: Ne dis jamais 'Hello how are you'. Entre directement dans le vif du sujet via ta MISSION.
        Niveau Primaire A1: uniquement des mots simples.
        CORRECTIONS: Écris après 'Correction:', mais ne les lis pas oralement."""

        html_code = f"""
        <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff; text-align:center;">
            <div id="status" style="margin-bottom:10px; font-weight:bold; color:blue;">Appuie sur le bouton pour démarrer</div>
            <div id="chatbox" style="height:250px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif; text-align:left; border:1px solid #eee; padding:10px;"></div>
            <button id="btn-mic" style="width:100%; padding:25px; background:#dc3545; color:white; border:none; border-radius:15px; font-weight:bold; cursor:pointer; font-size:1.3em;">🎤 ACTIVER LE TUTEUR</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let messages = [{{role: "system", content: "{adapt_prompt}"}}];
            const box = document.getElementById('chatbox');
            const btn = document.getElementById('btn-mic');
            const status = document.getElementById('status');
            const synth = window.speechSynthesis;
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            let rec = SpeechRec ? new SpeechRec() : null;
            if(rec) {{ rec.lang = "{rec_l}"; rec.continuous = false; }}

            async function callIA(txt) {{
                status.innerText = "L'IA prépare sa question...";
                try {{
                    if(txt) messages.push({{role: "user", content: txt}});
                    else messages.push({{role: "user", content: "Action: Lance ta mission directement."}});

                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    messages.push({{role: "assistant", content: reply}});
                    
                    box.innerHTML += `<p style="background:#f1f1f1; padding:10px; border-radius:10px; margin:5px 0;"><b>Tuteur:</b> ${{reply.replace('Correction:', '<br><i style="color:red;">Correction:</i>')}}</p>`;
                    box.scrollTop = box.scrollHeight;

                    const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                    u.lang = "{tts_l}";
                    u.onend = () => {{
                        status.innerText = "À toi de parler !";
                        status.style.color = "green";
                        btn.innerText = "🎤 CLIQUE ET RÉPONDS";
                        btn.style.background = "#dc3545";
                    }};
                    synth.speak(u);
                }} catch (e) {{ status.innerText = "Erreur IA. Vérifie ta clé API."; }}
            }}

            btn.onclick = () => {{
                // 1. Débloquer l'audio immédiatement
                synth.cancel();
                synth.speak(new SpeechSynthesisUtterance("")); 
                
                if (messages.length === 1) {{
                    // Lancement initial
                    btn.style.background = "#6c757d";
                    btn.innerText = "INITIALISATION...";
                    callIA(null);
                }} else {{
                    // Tour de parole élève
                    try {{
                        rec.start();
                        btn.innerText = "JE T'ÉCOUTE...";
                        btn.style.background = "#28a745";
                        status.innerText = "Micro activé...";
                    }} catch(err) {{ callIA(null); }}
                }}
            }};

            if(rec) {{
                rec.onresult = (e) => {{
                    const t = e.results[0][0].transcript;
                    box.innerHTML += `<p style="text-align:right; margin:5px 0;"><b>Moi:</b> ${{t}}</p>`;
                    callIA(t);
                }};
                rec.onerror = () => {{ 
                    status.innerText = "Micro non capté, l'IA continue..."; 
                    callIA("L'élève a un souci de micro, continue la mission."); 
                }};
            }}
        </script>
        """
        st.components.v1.html(html_code, height=520)

        # --- EVALUATION (Validé - Strict Page 4) ---
        st.divider()
        trans = st.text_area("Copie ton dialogue ici pour ton bilan :")
        if st.button("🏁 Générer mon Rapport Officiel"):
            with st.spinner("Analyse..."):
                eval_p = f"""Examine {user_name} (Niveau {s['level']}) via ABCD. 
                BARÈME STRICT : $1 \\times C = 8/20$, $2 \\times C$ ou $1 \\times D = 6/20$.
                Tutoie l'élève, sois encourageant et donne 3 pistes concrètes."""
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Dialogue: {trans}"}])
                bilan = res.choices[0].message.content
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan)
                st.download_button("📥 Télécharger mon PDF", pdf, f"Bilan_{user_name}.pdf")
                m = s['teacher_email']
                link = f"mailto:{m}?subject=Bilan%20Labo%20-%20{user_name}&body=Voici%20mon%20bilan."
                st.markdown(f'<a href="{link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center;">📧 Envoyer au professeur ({m})</div></a>', unsafe_allow_html=True)
