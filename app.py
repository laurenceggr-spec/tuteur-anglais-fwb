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

# Initialisation des réglages session (Adaptés au Référentiel)
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", 
        "level": "S1-S2 (A1/A2.1)", # Précision du niveau cible
        "mode": "Tuteur (Dialogue IA)",
        "topic": "Daily Routine", 
        "session_code": "LAB2024", 
        "teacher_email": "prof@ecole.be", 
        "vocab": "wake up, breakfast, then, after",
        "custom_prompt": "Sois un tuteur patient. Encourage l'élève à faire des phrases complètes."
    }

# --- FONCTION PDF (Notation FWB ABCD + Traduction chiffrée) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - Tronc Commun FWB", ln=True, align='C')
    
    pdf.set_font("Arial", size=11)
    pdf.ln(10)
    pdf.cell(200, 8, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 8, txt=f"Niveau Cible : {level} | Sujet : {topic}", ln=True)
    pdf.cell(200, 8, txt=f"Date : {time.strftime('%d/%m/%Y %H:%M')}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Analyse des competences (Grille ABCD) :", ln=True)
    
    pdf.set_font("Arial", size=10)
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=clean_text)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 5, txt="Ce bilan est base sur le Referentiel des Langues Modernes du Tronc Commun (FWB).")
    
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIQUE DES ROLES ---
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR (Niveaux du Tronc Commun) ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    if st.text_input("Code Admin :", type="password") == "ADMIN123":
        with st.form("config"):
            col1, col2 = st.columns(2)
            mode = col1.selectbox("Mode d'activité :", ["Tuteur (Dialogue IA)", "Solo (IA écoute et évalue)", "Duo (IA écoute 2 élèves)"])
            lang = col1.selectbox("Langue :", ["English", "Nederlands"])
            # Niveaux calqués sur le Référentiel
            lvl = col1.selectbox("Degré / Niveau Cible :", [
                "Primaire (Initiation/A1)", 
                "S1-S2 (Vers A2.1)", 
                "S3-S4 (Vers A2.2/B1)"
            ])
            
            topic = col2.text_input("Sujet thématique :", value=st.session_state.class_settings["topic"])
            mail = col2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
            voc = col2.text_area("Attendus spécifiques (Lexique/Grammaire) :", value=st.session_state.class_settings["vocab"])
            
            custom_p = st.text_area("Mission du tuteur (Prompt pédagogique) :", 
                                   value=st.session_state.class_settings["custom_prompt"])
            
            if st.form_submit_button("Mettre à jour la session"):
                st.session_state.class_settings.update({"language": lang, "level": lvl, "mode": mode, "topic": topic, "teacher_email": mail, "vocab": voc, "custom_prompt": custom_p})
        
        st.divider()
        st.subheader("📲 Accès Élèves")
        cA, cB = st.columns([1, 2])
        with cA:
            qr = qrcode.make("https://tuteur-anglais.streamlit.app/")
            buf = BytesIO(); qr.save(buf); st.image(buf, width=200)
        with cB:
            st.metric("CODE SESSION", st.session_state.class_settings["session_code"])

# --- INTERFACE ÉLÈVE (IA Adaptée au Référentiel) ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès Labo")
        if st.text_input("Code Session :") == s['session_code']:
            if st.button("Valider"): st.session_state.session_verified = True; st.rerun()
    else:
        st.sidebar.title("👤 Profil")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if not user_name:
            st.warning("👈 Écris ton prénom à gauche pour commencer.")
        else:
            st.title(f"🗣️ Activité : {s['topic']}")
            
            # ADAPTATION DU PROMPT SELON LE REFERENTIEL
            target_desc = "Phrases simples, vocabulaire de base." if "Primaire" in s['level'] else "Echanges structurés, utilisation de connecteurs."
            mode_prompt = f"""Tu es un tuteur de {s['language']}. 
            Niveau cible Référentiel FWB: {s['level']}. 
            Attentes: {target_desc}. 
            Mission: {s['custom_prompt']}. 
            Mode: {s['mode']}.
            Respecte scrupuleusement le niveau: ne sois pas trop complexe si c'est du Primaire."""

            # INTERFACE CHAT IA PARLANTE
            rec_l = "en-US" if s['language'] == "English" else "nl-BE"
            tts_l = "en-US" if s['language'] == "English" else "nl-NL"

            html_code = f"""
            <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
                <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
            </div>
            <script>
                const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
                let messages = [{{role: "system", content: "{mode_prompt} Réponds oralement. Ecris les corrections après la mention 'Correction:'."}}];
                const box = document.getElementById('chatbox');
                const btn = document.getElementById('btn-mic');
                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_l}";

                btn.onclick = () => {{ rec.start(); btn.style.background="#28a745"; btn.innerText="Écoute..."; }};

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
                    box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;"><b>IA:</b> ${{reply}}</p>`;
                    box.scrollTop = box.scrollHeight;

                    const u = new SpeechSynthesisUtterance(reply.split('Correction:')[0]);
                    u.lang = "{tts_l}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=450)

            # --- EVALUATION FWB BASÉE SUR LE RÉFÉRENTIEL ---
            st.divider()
            transcription = st.text_area("Copie ton dialogue ici pour le bilan final :")
            
            if st.button("🏁 Générer mon Rapport Officiel (Référentiel FWB)"):
                with st.spinner("Analyse des attendus du Tronc Commun..."):
                    prompt_fwb = f"""Tu es un examinateur expert du Référentiel Langues Modernes FWB. 
                    Analyse la session de {user_name} (Niveau {s['level']}) sur {s['topic']}.
                    Dialogue: {transcription}.
                    
                    Evalue selon la grille ABCD (Réalisation, Adéquation, Langue, Rythme).
                    Vérifie spécifiquement si les attendus pour {s['level']} sont rencontrés (ex: lexique {s['vocab']}).
                    
                    Calcule la note selon le barème strict :
                    - Si A ou B partout: Cote sur 5 par critère (Total >= 10/20).
                    - Si C ou D : Applique les pénalités (1xC=8/20, 1xD=6/20, etc.).
                    
                    Rédige au TU, avec bienveillance mais objectivité pédagogique."""
                    
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt_fwb}])
                    bilan_ia = res.choices[0].message.content
                    
                    pdf_bytes = create_pdf(user_name, s['level'], s['topic'], bilan_ia)
                    st.success("✅ Ton rapport PDF aux normes du Tronc Commun est prêt !")
                    st.download_button("📥 Télécharger mon Rapport PDF", pdf_bytes, f"Bilan_FWB_{user_name}.pdf", "application/pdf")
                    
                    # Email pré-rempli
                    sujet = f"Evaluation Labo FWB - {user_name}"
                    corps = f"Bonjour, voici mon bilan officiel (PDF) basé sur le référentiel du tronc commun pour la session : {s['topic']}."
                    mail_link = f"mailto:{s['teacher_email']}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps)}"
                    st.markdown(f'<a href="{mail_link}" target="_blank"><div style="background:#28a745; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">📧 SIGNALER L\'ENVOI AU PROFESSEUR</div></a>', unsafe_allow_html=True)
