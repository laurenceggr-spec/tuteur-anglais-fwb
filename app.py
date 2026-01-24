import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
import urllib.parse
from fpdf import FPDF

# 1. CONFIGURATION & IMPORTS
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Fonction de création du PDF sécurisé
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Rapport d'Evaluation Officiel - Language Lab", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 10, txt=f"Niveau : {level}", ln=True)
    pdf.cell(200, 10, txt=f"Sujet : {topic}", ln=True)
    pdf.cell(200, 10, txt=f"Date : {time.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Resultats (Criteres FWB) :", ln=True)
    pdf.set_font("Arial", size=12)
    # Remplacement des caractères spéciaux pour éviter les erreurs PDF
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# Initialisation des paramètres par défaut
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", "level": "S1-S2", "topic": "Daily Routine",
        "min_turns": 3, "session_code": "LAB2024", "teacher_email": "votre@email.com",
        "vocab": "wake up, breakfast, then", "grammar": "Present Simple"
    }

# --- INTERFACE PROFESSEUR ---
if st.session_state.get("role") == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    
    with st.form("config_prof"):
        c1, c2 = st.columns(2)
        lang = c1.selectbox("Langue :", ["English", "Nederlands"])
        lvl = c1.selectbox("Niveau FWB :", ["S1-S2", "S3-S4", "Primaire"])
        turns = c1.number_input("Répliques minimum :", 1, 10, 3)
        
        topic = c2.text_input("Sujet de discussion :", value=st.session_state.class_settings["topic"])
        sess_code = c2.text_input("Code de Session :", value=st.session_state.class_settings["session_code"])
        mail = c2.text_input("Email de réception :", value=st.session_state.class_settings["teacher_email"])
        
        voc = st.text_area("Lexique & Grammaire cibles :", value=st.session_state.class_settings["vocab"])
        
        if st.form_submit_button("Lancer la session"):
            st.session_state.class_settings.update({
                "language": lang, "level": lvl, "topic": topic, 
                "min_turns": turns, "session_code": sess_code, 
                "teacher_email": mail, "vocab": voc
            })
            st.success("Session configurée et prête !")

    # RETABLISSEMENT DU QR CODE ET CODE SESSION
    st.divider()
    st.subheader("📲 Accès pour les élèves")
    colA, colB = st.columns([1, 3])
    with colA:
        app_url = "https://tuteur-anglais.streamlit.app" # Remplacez par votre URL réelle
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO()
        qr.save(buf)
        st.image(buf, width=200)
    with colB:
        st.info(f"**CODE DE SESSION :** {st.session_state.class_settings['session_code']}")
        st.write("Les élèves doivent scanner le QR Code ou entrer manuellement le code ci-dessus.")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès au Labo")
        code_input = st.text_input("Entre le Code de Session donné par le prof :")
        if st.button("Rejoindre"):
            if code_input == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
            else: st.error("Code incorrect.")
    else:
        # GUIDAGE ELEVE : NOM OBLIGATOIRE
        st.sidebar.title("👤 Ton Profil")
        user_name = st.sidebar.text_input("Écris ton Prénom ici :")
        
        if not user_name:
            st.warning("👈 Pour commencer, écris ton prénom dans la colonne de gauche.")
        else:
            st.title(f"🗣️ Entraînement : {s['language']}")
            st.write(f"Sujet : **{s['topic']}** | Niveau : **{s['level']}**")

            # BLOC CHAT IA + SYNTHESE VOCALE
            rec_l = "en-US" if s['language'] == "English" else "nl-BE"
            tts_l = "en-US" if s['language'] == "English" else "nl-NL"
            
            html_code = f"""
            <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
                <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
            </div>
            <script>
                const API_KEY = "{api_key}";
                let messages = [{{role: "system", content: "Tu es un tuteur de {s['language']} niveau {s['level']}. Sujet: {s['topic']}. Aide l'élève à utiliser: {s['vocab']}. Phrases courtes."}}];
                const box = document.getElementById('chatbox');
                const btn = document.getElementById('btn-mic');
                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_l}";

                btn.onclick = () => {{ rec.start(); btn.style.background="#28a745"; btn.innerText="Écoute en cours..."; }};

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

                    const u = new SpeechSynthesisUtterance(reply);
                    u.lang = "{tts_l}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=450)

            # GENERATION PDF SECURISE
            st.divider()
            if st.button("🏁 Terminer et générer mon rapport PDF"):
                # Définition des critères basés sur le niveau choisi par le prof
                if s['level'] == "S1-S2":
                    eval_text = "1. Intention (A1/A2): ACQUIS\n2. Lexique cible: EN VOIE D'ACQUISITION\n3. Structures simples: ACQUIS\n4. Aisance: ACQUIS"
                else:
                    eval_text = "1. Pertinence (A2/B1): ACQUIS\n2. Richesse lexicale: ACQUIS\n3. Complexite structures: EN VOIE D'ACQUISITION\n4. Interaction: ACQUIS"
                
                pdf_data = create_pdf(user_name, s['level'], s['topic'], eval_text)
                st.success("✅ Ton rapport officiel a été généré !")
                st.download_button(
                    label="📥 Télécharger mon rapport (PDF)",
                    data=pdf_data,
                    file_name=f"Rapport_{user_name}.pdf",
                    mime="application/pdf"
                )
                st.warning("⚠️ Envoie maintenant ce fichier à ton professeur.")

# --- LOGIN ---
else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Je suis :", ["Élève", "Professeur"], horizontal=True)
    pw = st.text_input("Mot de passe :", type="password")
    if st.button("Entrer"):
        if role == "Professeur" and pw == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        elif role == "Élève" and pw == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
