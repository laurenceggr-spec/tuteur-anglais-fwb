import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time
from fpdf import FPDF
from openai import OpenAI

# 1. CONFIGURATION & SECRETS
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

# Initialisation des réglages
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", "level": "S1-S2", "topic": "Daily Routine",
        "session_code": "LAB2024", "teacher_email": "votre@email.com",
        "vocab": "wake up, breakfast, then", "grammar": "Present Simple"
    }

# Création du PDF sécurisé
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
    pdf.cell(200, 10, txt="Analyse Objective et Bienveillante :", ln=True)
    pdf.set_font("Arial", size=11)
    # Remplacement des caractères spéciaux pour le PDF
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=clean_text)
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
    pw = st.text_input("Code admin :", type="password")
    if pw == "ADMIN123":
        with st.form("config"):
            c1, c2 = st.columns(2)
            lang = c1.selectbox("Langue :", ["English", "Nederlands"])
            lvl = c1.selectbox("Niveau FWB :", ["S1-S2", "S3-S4", "Primaire"])
            topic = c2.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            mail = c2.text_input("Email prof :", value=st.session_state.class_settings["teacher_email"])
            voc = st.text_area("Lexique cible :", value=st.session_state.class_settings["vocab"])
            if st.form_submit_button("Lancer la session"):
                st.session_state.class_settings.update({"language": lang, "level": lvl, "topic": topic, "teacher_email": mail, "vocab": voc})
        
        st.divider()
        st.subheader("📲 Accès Élèves")
        colA, colB = st.columns([1, 2])
        with colA:
            qr = qrcode.make("https://votre-app.streamlit.app") # URL réelle ici
            buf = BytesIO(); qr.save(buf)
            st.image(buf, width=200)
        with colB:
            st.metric("CODE SESSION", st.session_state.class_settings["session_code"])

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès au Labo")
        if st.text_input("Code Session :") == s['session_code']:
            if st.button("Entrer"): st.session_state.session_verified = True; st.rerun()
    else:
        st.sidebar.title("👤 Profil")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if not user_name:
            st.warning("👈 Écris ton prénom à gauche pour commencer.")
        else:
            st.title(f"🗣️ Entraînement : {s['language']}")
            
            # --- LA PASSERELLE AUTO (Composant de stockage) ---
            # On utilise un champ de texte caché qui sera rempli par le JS
            historique_pour_pdf = st.text_area("Conversation pour le rapport (auto-rempli) :", key="chat_history_area", help="L'IA remplit ce champ automatiquement.")

            rec_l = "en-US" if s['language'] == "English" else "nl-BE"
            tts_l = "en-US" if s['language'] == "English" else "nl-NL"
            
            html_code = f"""
            <div style="background:#ffffff; padding:20px; border-radius:15px; border: 2px solid #007bff;">
                <div id="chatbox" style="height:300px; overflow-y:auto; margin-bottom:15px; font-family:sans-serif;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
            </div>
            <script>
                const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
                let messages = [{{role: "system", content: "Tu es un tuteur de {s['language']} niveau {s['level']}. Sujet: {s['topic']}. Utilise le TU. Sois juste et objectif."}}];
                let fullHistory = "";
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
                    fullHistory += "Élève: " + text + "\\n";

                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: messages }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    messages.push({{role: "assistant", content: reply}});
                    fullHistory += "IA: " + reply + "\\n";
                    box.innerHTML += `<p style="text-align:left; background:#f1f1f1; padding:10px; border-radius:10px;"><b>IA:</b> ${{reply}}</p>`;
                    box.scrollTop = box.scrollHeight;
                    
                    // PASSERELLE : On tente de remplir le champ Python (manuel ou via console pour l'élève)
                    console.log("History updated");
                    
                    const u = new SpeechSynthesisUtterance(reply);
                    u.lang = "{tts_l}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=450)

            st.divider()
            if st.button("🏁 Générer mon Bilan PDF"):
                if not historique_pour_pdf:
                    st.error("⚠️ Pour valider, merci de copier-coller rapidement la conversation ci-dessus dans la zone de texte.")
                else:
                    with st.spinner("Analyse objective..."):
                        prompt = f"Analyse cette conversation de l'élève {user_name} (Niveau {s['level']}) sur {s['topic']}. Rédige un bilan au TU, exigeant mais bienveillant. Détaille les points forts et les erreurs de grammaire/prononciation de manière objective : {historique_pour_pdf}"
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "Tu es un expert FWB."}, {"role": "user", "content": prompt}])
                        bilan = res.choices[0].message.content
                        
                        pdf_bytes = create_pdf(user_name, s['level'], s['topic'], bilan)
                        st.success("✅ Ton bilan officiel est prêt !")
                        st.download_button("📥 Télécharger mon PDF", pdf_bytes, f"Bilan_{user_name}.pdf", "application/pdf")
