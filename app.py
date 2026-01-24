import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import time

# 1. CONFIGURATION & SÉCURITÉ
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Initialisation des variables de session
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

if "cloud_results" not in st.session_state:
    st.session_state.cloud_results = []

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
            mail = c2.text_input("Email de réception :", value=st.session_state.class_settings["teacher_email"])
            topic = st.text_input("Sujet :", value=st.session_state.class_settings["topic"])
            voc = st.text_area("Lexique cible :", value=st.session_state.class_settings["vocab"])
            
            if st.form_submit_button("Mettre à jour la classe"):
                st.session_state.class_settings.update({
                    "language": lang, "topic": topic, "min_turns": turns, 
                    "session_code": sess_code, "teacher_email": mail, "vocab": voc
                })
                st.success("Session configurée avec succès !")

        st.subheader("📲 Accès pour les élèves")
        app_url = "https://tuteur-anglais.streamlit.app" 
        qr = qrcode.make(f"{app_url}/?mode=student")
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150, caption=f"Code Manuel : {sess_code}")

    with tab2:
        st.subheader("📥 Résultats de la classe")
        if st.button("🔄 Rafraîchir les scores"):
            st.rerun()
        
        if st.session_state.cloud_results:
            df = pd.DataFrame(st.session_state.cloud_results)
            st.table(df[['Heure', 'Élève', 'Score']])
            sel = st.selectbox("Détail évaluation :", [r['Élève'] for r in st.session_state.cloud_results])
            res = next(item for item in st.session_state.cloud_results if item["Élève"] == sel)
            st.info(res['Évaluation'])
        else:
            st.info("En attente de soumissions...")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.get("role") == "Élève":
    s = st.session_state.class_settings
    
    if not st.session_state.get("session_verified"):
        st.title("🚀 Bienvenue au Labo")
        code_in = st.text_input("Entre le CODE SESSION (au tableau) :")
        if st.button("Rejoindre le cours"):
            if code_in == s['session_code']:
                st.session_state.session_verified = True
                st.rerun()
            else: st.error("Code incorrect.")
    else:
        st.title(f"🎯 Pratique : {s['language']}")
        user_name = st.sidebar.text_input("Ton Prénom :")
        
        if user_name:
            v_json = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')
            rec_lang = "en-US" if s['language'] == "English" else "nl-BE"
            
            # Bloc HTML/JS avec DOUBLE ACCOLADES pour éviter l'erreur f-string
            html_code = f"""
            <div style="background:#fff; padding:15px; border-radius:10px; border:1px solid #ddd;">
                <p><b>Topic:</b> {s['topic']}</p>
                <div id="chatbox" style="height:200px; overflow-y:auto; background:#f9f9f9; padding:10px; margin-bottom:10px; border-radius:5px; font-size:14px; border:1px solid #eee;"></div>
                <button id="btn-mic" style="width:100%; padding:15px; background:#dc3545; color:white; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">🎤 CLIQUE ET PARLE</button>
            </div>

            <script>
                const API_KEY = "{api_key}";
                let transcript = "";
                const box = document.getElementById('chatbox');
                const btn = document.getElementById('btn-mic');

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = "{rec_lang}";

                btn.onclick = () => {{ try {{ rec.start(); btn.style.background="#28a745"; }} catch(e) {{ rec.stop(); }} }};

                rec.onresult = async (e) => {{
                    btn.style.background="#dc3545";
                    const text = e.results[0][0].transcript;
                    box.innerHTML += "<div style='text-align:right; color:#007bff;'><b>Moi:</b> "+text+"</div>";
                    transcript += "Student: " + text + "\\n";

                    // APPEL IA AVEC DOUBLES ACCOLADES
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
                    transcript += "IA: " + reply + "\\n";
                    box.scrollTop = box.scrollHeight;
                    
                    const u = new SpeechSynthesisUtterance(reply);
                    u.lang = "{'en-US' if s['language']=='English' else 'nl-NL'}";
                    window.speechSynthesis.speak(u);
                }};
            </script>
            """
            st.components.v1.html(html_code, height=350)
            
            if st.button("📤 Envoyer mes résultats au prof"):
                # Simulation d'envoi Cloud
                new_res = {
                    "Heure": time.strftime("%H:%M"),
                    "Élève": user_name,
                    "Langue": s['language'],
                    "Score": "15/20",
                    "Évaluation": f"Excellent travail sur le sujet {s['topic']} ! Tu as bien respecté les consignes."
                }
                st.session_state.cloud_results.append(new_res)
                st.success("✅ Envoyé ! Tu peux fermer l'application.")
                st.balloons()

# --- LOGIN INITIAL ---
else:
    st.title("🚀 Language Lab FWB")
    col1, col2 = st.columns(2)
    role = col1.radio("Je suis :", ["Élève", "Professeur"])
    pw = col2.text_input("Mot de passe :", type="password")
    if st.button("Entrer"):
        if role == "Professeur" and pw == "ADMIN123":
            st.session_state.role = "Professeur"; st.rerun()
        elif role == "Élève" and pw == "ELEC2024":
            st.session_state.role = "Élève"; st.rerun()
