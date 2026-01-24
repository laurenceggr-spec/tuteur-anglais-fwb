import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
from fpdf import FPDF
import openai

# 1. CONFIGURATION INITIALE
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Initialisation des réglages par défaut
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", "level": "S1-S2", "topic": "Daily Routine",
        "min_turns": 3, "session_code": "LAB2024", "teacher_email": "votre@email.com",
        "vocab": "wake up, breakfast, then", "grammar": "Present Simple"
    }

# Fonction pour créer le PDF (version finale avec encodage sécurisé)
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation - Language Lab FWB", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Eleve : {user_name}", ln=True)
    pdf.cell(200, 10, txt=f"Niveau : {level}", ln=True)
    pdf.cell(200, 10, txt=f"Sujet : {topic}", ln=True)
    pdf.cell(200, 10, txt=f"Date : {time.strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analyse Pedagogue et Objective :", ln=True)
    pdf.set_font("Arial", size=12)
    # Nettoyage pour éviter les crashs de caractères spéciaux
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIQUE DES ROLES ---
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Je suis ELEVE"):
            st.session_state.role = "Élève"
            st.rerun()
    with col2:
        if st.button("Je suis PROFESSEUR"):
            st.session_state.role = "Professeur"
            st.rerun()

# --- INTERFACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    pw = st.text_input("Code d'accès admin :", type="password")
    
    if pw == "ADMIN123":
        with st.form("config_prof"):
            c1, c2 = st.columns(2)
            lang = c1.selectbox("Langue :", ["English", "Nederlands"])
            lvl = c1.selectbox("Niveau FWB :", ["S1-S2", "S3-S4", "Primaire"])
            topic = c2.text_input("Sujet de discussion :", value=st.session_state.class_settings["topic"])
            mail = c2.text_input("Email de réception :", value=st.session_state.class_settings["teacher_email"])
            voc = st.text_area("Lexique & structures cibles :", value=st.session_state.class_settings["vocab"])
            code = c1.text_input("Code de session pour élèves :", value="LAB2024")
            
            if st.form_submit_button("Mettre à jour la session"):
                st.session_state.class_settings.update({
                    "language": lang, "level": lvl, "topic": topic, 
                    "teacher_email": mail, "vocab": voc, "session_code": code
                })
        
        st.divider()
        st.subheader("📲 Accès Élèves")
        colA, colB = st.columns([1, 2])
        with colA:
            # QR CODE
            qr = qrcode.make(f"https://tuteur-anglais.streamlit.app") # URL à adapter
            buf = BytesIO(); qr.save(buf)
            st.image(buf, width=200)
        with colB:
            st.metric("CODE SESSION", st.session_state.class_settings["session_code"])
            st.info("Affichez ce code au tableau. Les élèves devront le saisir pour entrer.")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès au Labo")
        c_in = st.text_input("Entre le Code Session :")
        if st.button("Valider"):
            if c_in == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
            else: st.error("Code erroné.")
    else:
        st.sidebar.title("👤 Ton Profil")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if not user_name:
            st.warning("👈 Écris ton prénom à gauche pour activer le micro.")
        else:
            st.title(f"🗣️ Entraînement : {s['language']}")
            st.write(f"Mission : Parler de **{s['topic']}** (Niveau {s['level']})")

            # BLOC CHAT INTERACTIF (JS)
            rec_l = "en-US" if s['language'] == "English" else "nl-BE"
            tts_l = "en-US" if s['language'] == "English" else "nl-NL"
            
            html_code = f"""
            <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
                <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif; border-bottom: 1px solid #eee;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer; font-size:16px;">🎤 CLIQUE ET PARLE</button>
            </div>
            <script>
                const API_KEY = "{api_key}";
                let messages = [{{role: "system", content: "Tu es un tuteur de {s['language']} niveau {s['level']}. Sujet: {s['topic']}. Utilise: {s['vocab']}. Sois encourageant mais note les erreurs."}}];
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
                    box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;"><b>IA:</b> ${{reply}}</p>`;
                    box.scrollTop = box.scrollHeight;

                    const u = new SpeechSynthesisUtterance(reply);
                    u.lang = "{tts_l}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=450)

            # ZONE DE SECURITE POUR LE PDF
            st.divider()
            st.subheader("🏁 Fin de session")
            transcription = st.text_area("Copie-colle ici ton dernier message ou un résumé pour l'évaluation :")
            
            if st.button("📄 Générer mon Bilan PDF Officiel"):
                if not transcription:
                    st.error("S'il te plaît, écris un petit mot ou colle ta conversation ci-dessus pour que l'IA puisse t'évaluer.")
                else:
                    with st.spinner("Analyse objective en cours..."):
                        # Appel à l'IA pour un feedback juste (Tutoiement + Objectivité)
                        prompt_eval = f"L'élève {user_name} a fini sa session sur {s['topic']}. Voici ce qu'il a dit : {transcription}. Rédige un bilan au TU, avec une section '🌟 Points forts' et une section '🚀 Défis'. Sois juste et objectif sur la grammaire et l'effort."
                        
                        try:
                            client = openai.OpenAI(api_key=api_key)
                            res = client.chat.completions.create(
                                model="gpt-4o-mini",
                                messages=[{"role": "system", "content": "Tu es un expert FWB en évaluation de langues."},
                                          {"role": "user", "content": prompt_eval}]
                            )
                            bilan_ia = res.choices[0].message.content
                        except:
                            bilan_ia = "Bilan généré : Tu as fait des efforts de communication. Travaille encore la fluidité."

                        pdf_bytes = create_pdf(user_name, s['level'], s['topic'], bilan_ia)
                        st.success("Ton rapport PDF est prêt !")
                        st.download_button("📥 Télécharger mon Rapport", pdf_bytes, f"Bilan_{user_name}.pdf", "application/pdf")
