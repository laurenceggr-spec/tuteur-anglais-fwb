import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import qrcode
from io import BytesIO
import time

# 1. CONFIGURATION & SÉCURITÉ
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 2. CONNEXION CLOUD (Le pont entre appareils)
# Remplace par l'URL de ton Google Sheet (Partagé en "Éditeur" pour tous)
SQL_URL = "https://docs.google.com/spreadsheets/d/1QycENconwTyJB8iaF4rccfvwnIyfnqg2_qHHXl_ZaC8/edit?gid=0#gid=0" 

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("Connexion Cloud non configurée.")

# Initialisation des paramètres par défaut
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English",
        "topic": "Daily Routine",
        "min_turns": 3,
        "session_code": "LAB2024",
        "teacher_email": "votre@email.com",
        "grammar": "Present Simple",
        "vocab": "wake up, breakfast"
    }

# --- AUTHENTIFICATION ---
url_params = st.query_params
if "mode" in url_params and url_params["mode"] == "student":
    st.session_state.role = "Élève"
    st.session_state.authenticated = True

# --- INTERFACE PROFESSEUR ---
if st.session_state.get("role") == "Professeur":
    st.title("👨‍🏫 Dashboard Enseignant")
    tab1, tab2 = st.tabs(["⚙️ Configuration", "📊 Suivi en Direct"])
    
    with tab1:
        with st.form("settings"):
            c1, c2 = st.columns(2)
            lang = c1.selectbox("Langue :", ["English", "Nederlands"])
            turns = c1.number_input("Répliques min. :", 1, 10, 3)
            sess_code = c2.text_input("Code Session :", value=st.session_state.class_settings["session_code"])
            topic = st.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            voc = st.text_area("Lexique cible :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Mettre à jour la classe"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "min_turns": turns, 
                    "session_code": sess_code, "vocab": voc
                })
                st.success("Session configurée !")

        st.subheader("📲 Accès pour les élèves")
        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150, caption=f"Code Manuel : {sess_code}")

    with tab2:
        st.subheader("📥 Résultats centralisés (Cloud)")
        if st.button("🔄 Rafraîchir les scores"):
            st.cache_data.clear()
            st.rerun()
        
        try:
            df = conn.read(spreadsheet=SQL_URL, worksheet="Sheet1")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                sel = st.selectbox("Détail évaluation :", df['Élève'].tolist())
                eval_text = df[df['Élève'] == sel]['Évaluation'].values[0]
                st.info(eval_text)
            else:
                st.info("Aucune donnée reçue.")
        except:
            st.warning("En attente de la première soumission d'élève...")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès au cours")
        code_in = st.text_input("Code Session :")
        if st.button("Rejoindre"):
            if code_in == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
            else: st.error("Code incorrect.")
    else:
        st.title(f"🎯 Pratique : {s['language']}")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if user_name:
            rec_lang = "en-US" if s['language'] == "English" else "nl-BE"
            
            # BLOC CHAT IA
            html_code = f"""
            <div style="background:#fff; padding:15px; border-radius:10px; border:1px solid #ddd;">
                <p><b>Sujet:</b> {s['topic']}</p>
                <div id="chatbox" style="height:200px; overflow-y:auto; background:#f9f9f9; padding:10px; margin-bottom:10px; border-radius:5px; font-size:14px; border:1px solid #eee;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
                <input type="hidden" id="transcript-input">
            </div>

            <script>
                const API_KEY = "{api_key}";
                let fullTranscript = "";
                const box = document.getElementById('chatbox');
                const btn = document.getElementById('btn-mic');

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_lang}";

                btn.onclick = () => {{ try {{ rec.start(); btn.style.background="#28a745"; }} catch(e) {{ rec.stop(); }} }};

                rec.onresult = async (e) => {{
                    btn.style.background="#dc3545";
                    const text = e.results[0][0].transcript;
                    box.innerHTML += "<div style='text-align:right; color:#007bff;'><b>Moi:</b> "+text+"</div>";
                    fullTranscript += "Student: " + text + "\\n";

                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ 
                            model: "gpt-4o-mini", 
                            messages: [
                                {{role: "system", content: "Short {s['language']} tutor. One sentence response."}},
                                {{role: "user", content: text}}
                            ] 
                        }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    box.innerHTML += "<div style='text-align:left; color:#333;'><b>IA:</b> "+reply+"</div>";
                    fullTranscript += "IA: " + reply + "\\n";
                    box.scrollTop = box.scrollHeight;
                    window.parent.postMessage({{type: 'transcript', data: fullTranscript}}, "*");
                    
                    const u = new SpeechSynthesisUtterance(reply);
                    u.lang = "{'en-US' if s['language']=='English' else 'nl-NL'}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=350)
            
            st.divider()
            st.subheader("🏁 Fin de session")
            
            # 1. On prépare le contenu du mail
            prof_email = s['teacher_email']
            sujet = f"Evaluation Anglais - {user_name}"
            corps_du_mail = f"""Bonjour Monsieur, 
            
Voici mes résultats pour la session sur : {s['topic']}.
Nom de l'élève : {user_name}
Langue : {s['language']}
Score estimé : 15/20

Commentaire : L'élève a bien participé à la conversation orale."""

            # 2. On encode le message pour qu'il soit lisible par un lien web (URL Encoding)
            import urllib.parse
            mail_link = f"mailto:{prof_email}?subject={urllib.parse.quote(sujet)}&body={urllib.parse.quote(corps_du_mail)}"

            # 3. On crée un bouton stylé qui ouvre l'application mail du smartphone
            st.markdown(f"""
                <a href="{mail_link}" target="_blank" style="text-decoration: none;">
                    <div style="
                        background-color: #007bff;
                        color: white;
                        padding: 15px;
                        text-align: center;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 18px;
                        cursor: pointer;
                        border: none;">
                        📧 Cliquer ici pour envoyer mes résultats
                    </div>
                </a>
                """, unsafe_allow_html=True)
            
            st.info("💡 Une fois que tu as cliqué, ton application mail s'ouvrira. Appuie simplement sur 'Envoyer' dans ton mail.")
# --- LOGIN ---
else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Rôle :", ["Élève", "Professeur"], horizontal=True)
    pw = st.text_input("Code :", type="password")
    if st.button("Entrer"):
        if role == "Professeur" and pw == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        elif role == "Élève" and pw == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
