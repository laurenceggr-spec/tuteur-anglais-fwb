import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import qrcode
from io import BytesIO
import time

# 1. CONFIGURATION
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 2. CONNEXION GOOGLE SHEETS (Le pont réel)
# Note: L'URL doit être configurée dans vos secrets Streamlit ou ici pour le test
url = "VOTRE_URL_GOOGLE_SHEET_ICI" # <--- METTEZ VOTRE LIEN SHEETS ICI
conn = st.connection("gsheets", type=GSheetsConnection)

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
            if st.form_submit_button("Mettre à jour"):
                st.session_state.class_settings.update({"language": lang, "topic": topic, "min_turns": turns, "session_code": sess_code})
        
        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150)

    with tab2:
        st.subheader("📥 Résultats centralisés (Cloud)")
        if st.button("🔄 Actualiser les données"):
            st.cache_data.clear()
            st.rerun()
        
        try:
            # On lit directement la base de données partagée
            df = conn.read(spreadsheet=url, worksheet="Sheet1")
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.info("La feuille est vide. En attente des élèves...")
        except:
            st.error("Erreur de connexion au Google Sheet. Vérifiez l'URL.")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    if not st.session_state.get("session_verified"):
        st.title("🚀 Accès au cours")
        code_in = st.text_input("Code Session :")
        if st.button("Valider"):
            if code_in == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
    else:
        user_name = st.sidebar.text_input("Ton Prénom :")
        if user_name:
            # [Ici votre bloc html_code habituel pour le chat IA]
            st.write(f"Sujet : {s['topic']}")
            
            if st.button("📤 Envoyer au professeur"):
                # CRÉATION DE LA LIGNE DE RÉSULTAT
                new_data = {
                    "Heure": time.strftime("%H:%M"),
                    "Élève": user_name,
                    "Langue": s['language'],
                    "Sujet": s['topic'],
                    "Score": "15/20",
                    "Évaluation": "Très bonne session orale !"
                }
                
                # ENVOI AU CLOUD
                try:
                    existing_df = conn.read(spreadsheet=url, worksheet="Sheet1")
                    updated_df = pd.concat([existing_df, pd.DataFrame([new_data])], ignore_index=True)
                    conn.update(spreadsheet=url, data=updated_df)
                    st.success("✅ Données synchronisées avec l'ordinateur du prof !")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erreur d'envoi : {e}")

# --- LOGIN ---
else:
    st.title("🚀 Language Lab FWB")
    role = st.radio("Rôle :", ["Élève", "Professeur"], horizontal=True)
    pw = st.text_input("Mot de passe :", type="password")
    if st.button("Entrer"):
        if role == "Professeur" and pw == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        elif role == "Élève" and pw == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
