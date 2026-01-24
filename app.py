import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time

# 1. CONFIGURATION
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Initialisation de la base de données "Cloud" simulée pour la démo
# Note: Pour une vraie mise en production, on utiliserait st.connection("gsheets") 
if "cloud_results" not in st.session_state:
    st.session_state.cloud_results = []

if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English",
        "level": "S1-S2",
        "topic": "Daily Routine",
        "mode": "Tuteur IA",
        "min_turns": 3,
        "session_code": "CLASSE2024", # Code manuel
        "teacher_email": "votre@email.com",
        "grammar": "Present Simple",
        "vocab": "wake up, breakfast"
    }

# --- INTERFACE PROFESSEUR ---
if st.session_state.get("role") == "Professeur":
    st.title("👨‍🏫 Dashboard Enseignant")
    tab1, tab2 = st.tabs(["⚙️ Configuration", "📊 Monitoring de la Classe"])
    
    with tab1:
        with st.form("settings"):
            c1, c2 = st.columns(2)
            lang = c1.selectbox("Langue :", ["English", "Nederlands"])
            turns = c1.number_input("Répliques min. :", min_value=1, value=3)
            sess_code = c2.text_input("Code Session (si pas de QR) :", value="CLASSE2024")
            mail = c2.text_input("Votre Email (pour réception) :", value=st.session_state.class_settings["teacher_email"])
            
            topic = st.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            voc = st.text_area("Lexique cible :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Lancer la session"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "min_turns": turns,
                    "session_code": sess_code, "teacher_email": mail, "vocab": voc
                })
                st.success("Session configurée !")

        st.subheader("📲 Accès Élèves")
        col_qr, col_info = st.columns([1, 2])
        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        col_qr.image(buf, width=150)
        col_info.write(f"**URL :** `{app_url}`")
        col_info.write(f"**Code Session :** `{sess_code}`")

    with tab2:
        st.subheader("📥 Résultats reçus en temps réel")
        if st.button("🔄 Actualiser les scores"):
            st.rerun()
            
        if st.session_state.cloud_results:
            df = pd.DataFrame(st.session_state.cloud_results)
            st.table(df[['Élève', 'Langue', 'Score', 'Heure']])
            sel = st.selectbox("Détail de l'évaluation :", [r['Élève'] for r in st.session_state.cloud_results])
            res = next(item for item in st.session_state.cloud_results if item["Élève"] == sel)
            st.info(res['Évaluation'])
        else:
            st.info("Aucun élève n'a encore terminé.")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    st.title(f"🎯 Labo : {s['language']}")
    
    # Vérification du code session si on arrive manuellement
    if "session_verified" not in st.session_state:
        st.session_state.session_verified = False

    if not st.session_state.session_verified:
        code_input = st.text_input("Entre le CODE SESSION donné par le prof :")
        if st.button("Valider"):
            if code_input == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
            else: st.error("Code incorrect")
    else:
        user_name = st.sidebar.text_input("Ton Prénom :")
        if not user_name:
            st.warning("⚠️ Écris ton prénom à gauche.")
        else:
            # Code HTML identique à la version 8.0 mais SANS le Bridge JS
            # À la place, on utilise un bouton final Streamlit pour envoyer les données
            
            # (Simulation de l'interface de chat pour l'élève via HTML)
            v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')
            
            st.markdown(f"**Sujet :** {s['topic']} | **Objectif :** {s['min_turns']} répliques.")
            
            # --- COMPOSANT CHAT ---
            # Ici, pour garantir la réception, une fois le chat fini en JS, 
            # on demande à l'élève de copier son évaluation ou on utilise un bouton spécial.
            
            html_code = f"""
            <div id="status" style="padding:10px; background:#e3f2fd; border-radius:10px; margin-bottom:10px;">
                Statut : Prêt. Parle en anglais !
            </div>
            <button onclick="startRec()" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold;">🎤 PARLER</button>
            <div id="chat-box" style="height:200px; overflow-y:auto; background:#f9f9f9; border:1px solid #ddd; margin-top:10px; padding:10px; font-size:14px;"></div>
            
            <script>
                // Logique simplifiée pour la démonstration
                let t = ""; let count = 0;
                async function startRec() {{
                    const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    rec.lang = "{'en-US' if s['language']=='English' else 'nl-BE'}";
                    rec.start();
                    rec.onresult = async (e) => {{
                        let text = e.results[0][0].transcript;
                        t += "Student: " + text + "\\n";
                        document.getElementById('chat-box').innerHTML += "<b>Moi:</b> "+text+"<br>";
                        
                        // Appel IA
                        const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                            method: 'POST', headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                            body: JSON.stringify({{ model: "gpt-4o-mini", messages: [{{role:"system", content:"Short English tutor."}, {{role:"user", content:text}}] }})
                        }});
                        const d = await r.json(); const reply = d.choices[0].message.content;
                        t += "IA: " + reply + "\\n";
                        document.getElementById('chat-box').innerHTML += "<b>IA:</b> "+reply+"<br>";
                        window.speechSynthesis.speak(new SpeechSynthesisUtterance(reply));
                    }}
                }}
            </script>
            """
            st.components.v1.html(html_code + f"<script>const API_KEY='{api_key}';</script>", height=350)

            # --- SOLUTION DE SECOURS FIABLE : L'ENVOI MANUEL ---
            st.divider()
            st.subheader("Fin de session")
            st.write("Une fois que tu as fini de parler, clique ci-dessous :")
            
            if st.button("📤 Envoyer mes résultats au prof"):
                # Ici on simule l'envoi au cloud (st.session_state est partagé si sur le même serveur)
                # Dans une version réelle, on enregistrerait ici dans une base de données
                st.session_state.cloud_results.append({
                    "Élève": user_name,
                    "Langue": s['language'],
                    "Score": "75/100",
                    "Heure": time.strftime("%H:%M"),
                    "Évaluation": f"Bravo {user_name}, tu as bien pratiqué le sujet {s['topic']}."
                })
                st.success("✅ Résultats envoyés ! Le prof peut les voir sur son écran.")
                
                # Option Email
                body = f"Rapport de {user_name}. Sujet: {s['topic']}. Score: 75/100"
                mail_link = f"mailto:{s['teacher_email']}?subject=Rapport Anglais - {user_name}&body={body}"
                st.markdown(f'<a href="{mail_link}" style="text-decoration:none; background:#007bff; color:white; padding:10px; border-radius:5px;">📧 Envoyer aussi par Email</a>', unsafe_allow_html=True)

# --- LOGIN ---
else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Je suis :", ["Élève", "Professeur"], horizontal=True)
    pw = st.text_input("Code d'accès :", type="password")
    if st.button("Entrer"):
        if role == "Professeur" and pw == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        if role == "Élève" and pw == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
