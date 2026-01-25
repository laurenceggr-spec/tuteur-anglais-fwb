import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
from fpdf import FPDF
from openai import OpenAI
import urllib.parse

# 1. CONFIGURATION & MOTEUR
st.set_page_config(page_title="Language Lab FWB", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

# Initialisation des réglages session
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", "level": "S1-S2", "mode": "Tuteur (Dialogue IA)",
        "topic": "Daily Routine", "session_code": "LAB2024", 
        "teacher_email": "prof@ecole.be", "vocab": "wake up, breakfast",
        "custom_prompt": "Sois un tuteur patient et encourageant."
    }

# --- FONCTION PDF (Notation /5 + Tutoiement) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - Language Lab FWB", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 10, txt=f"Niveau : {level} | Sujet : {topic}", ln=True)
    pdf.cell(200, 10, txt=f"Date : {time.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Ton Analyse Detaillee :", ln=True)
    pdf.set_font("Arial", size=11)
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- CHOIX DU RÔLE ---
if "role" not in st.session_state:
    st.title("🚀 Bienvenue au Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR (Rétabli avec Modes + Mission Custom) ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    if st.text_input("Code Admin :", type="password") == "ADMIN123":
        with st.form("config"):
            col1, col2 = st.columns(2)
            mode = col1.selectbox("Mode d'activité :", ["Tuteur (Dialogue IA)", "Solo (IA écoute et évalue)", "Duo (IA écoute 2 élèves)"])
            lang = col1.selectbox("Langue :", ["English", "Nederlands"])
            lvl = col1.selectbox("Niveau FWB :", ["S1-S2", "S3-S4", "Primaire"])
            
            topic = col2.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            mail = col2.text_input("Ton Email (pour réception) :", value=st.session_state.class_settings["teacher_email"])
            voc = col2.text_area("Objectifs (Lexique/Grammaire) :", value=st.session_state.class_settings["vocab"])
            
            # NOUVEAU : Champ pour modeler le rôle de l'IA
            custom_p = st.text_area("Mission / Rôle précis de l'IA :", 
                                   placeholder="Ex: Tu es un serveur, demande à l'élève de commander. Insiste sur les formules de politesse.",
                                   value=st.session_state.class_settings["custom_prompt"])
            
            if st.form_submit_button("Lancer la session"):
                st.session_state.class_settings.update({
                    "language": lang, "level": lvl, "mode": mode, 
                    "topic": topic, "teacher_email": mail, "vocab": voc,
                    "custom_prompt": custom_p
                })
        
        st.divider()
        st.subheader("📲 Partage avec tes élèves")
        cA, cB = st.columns([1, 2])
        with cA:
            qr = qrcode.make("https://tuteur-anglais.streamlit.app") # URL réelle ici
            buf = BytesIO(); qr.save(buf); st.image(buf, width=200)
        with cB:
            st.metric("CODE SESSION", st.session_state.class_settings["session_code"])

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    if not st.session_state.get("session_verified"):
        st.title("🚀 Entre dans le Labo")
        if st.text_input("Code Session donné par le prof :") == s['session_code']:
            if st.button("Valider"): st.session_state.session_verified = True; st.rerun()
    else:
        st.sidebar.title("👤 Ton Profil")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if not user_name:
            st.warning("👈 Écris ton prénom à gauche pour activer ton tuteur.")
        else:
            st.title(f"🗣️ Mode {s['mode']}")
            st.write(f"Sujet : **{s['topic']}** | Niveau : **{s['level']}**")

            # CONSTRUCTION DU PROMPT IA (Incorpore la Mission du prof)
            mode_prompt = f"Tu es un tuteur de {s['language']} niveau {s['level']}. Sujet: {s['topic']}. Mission: {s['custom_prompt']}."
            if "Solo" in s['mode']: mode_prompt += " Donne la consigne, puis écoute l'élève sans l'interrompre."
            elif "Duo" in s['mode']: mode_prompt += " Présente l'activité pour 2 élèves, puis écoute-les."

            # INTERFACE CHAT IA PARLANTE
            rec_l = "en-US" if s['language'] == "English" else "nl-BE"
            tts_l = "en-US" if s['language'] == "English" else "nl-NL"
            
            html_code = f"""
            <div style="background:#f8f9fa; padding:20px; border-radius:15px; border: 2px solid #007bff;">
                <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
            </div>
            <script>
                const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
                let messages = [{{role: "system", content: "{mode_prompt} Réponds toujours oralement. Si tu corriges une faute, fais-le par écrit à la fin de ta réponse."}}];
                const box = document.getElementById('chatbox');
                const btn = document.getElementById('btn-mic');
                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_l}";

                btn.onclick = () => {{ rec.start(); btn.style.background="#28a745"; btn.innerText="Je t'écoute..."; }};

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    btn.style.background="#dc3545"; btn.innerText="🎤 CLIQUE ET PARLE";
                    box.innerHTML += `<p style="text-align:right; color:#007bff;"><b>Moi:</b> ${{text}}</p>`;
                    messages.push({{role: "user", content: text}});

                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    
                    messages.push({{role: "assistant", content: reply}});
                    box.innerHTML += `<p style="text-align:left; background:#e9ecef; padding:10px; border-radius:10px;"><b>IA:</b> ${{reply}}</p>`;
                    box.scrollTop = box.scrollHeight;

                    const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                    u.lang = "{tts_l}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=450)

            # --- EVALUATION FWB + PDF + EMAIL ---
            st.divider()
            transcription = st.text_area("Copie-colle ici ton dialogue pour l'évaluation :")
            
            if st.button("🏁 Générer mon Bilan & Envoyer au Prof"):
                with st.spinner("Analyse selon les référentiels FWB..."):
                    prompt_eval = f"""Evalue cette session . Elève: {user_name}, Niveau: {s['level']}.
                    Analyse cet historique: {transcription}.
                    Note sur 5 (Critères FWB) : 1. Intention, 2. Lexique ({s['vocab']}), 3. Grammaire, 4. Aisance.
                    Sois juste et encourageant."""
                    
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt_eval}])
                    bilan_ia = res.choices[0].message.content
                    
                    pdf_bytes = create_pdf(user_name, s['level'], s['topic'], bilan_ia)
                    st.success("✅ Ton rapport PDF est prêt !")
                    st.download_button("📥 Télécharger mon PDF", pdf_bytes, f"Bilan_{user_name}.pdf", "application/pdf")
                    
                    # Email pré-rempli
                    sujet = f"Evaluation Labo - {user_name}"
                    corps = f"Bonjour, voici mon bilan PDF pour la session {s['topic']}."
                    mail_link = f"mailto:{s['teacher_email']}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
                    st.markdown(f'<a href="{mail_link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">📧 ENVOYER L\'ALERTE AU PROFESSEUR</div></a>', unsafe_allow_html=True)
