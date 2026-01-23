import streamlit as st
import PyPDF2
import pandas as pd
import qrcode
from io import BytesIO
import base64

# 1. CONFIGURATION & SÉCURITÉ
st.set_page_config(page_title="English Lab FWB Pro", layout="wide")
api_key = st.secrets.get("OPENAI_API_KEY", "")

# Initialisation de la base de données fictive
if "scores_db" not in st.session_state:
    st.session_state.scores_db = []

# Paramètres par défaut de la classe
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "persona": "A friendly British teacher",
        "grammar": "Present Continuous",
        "vocab": "morning, breakfast, school"
    }

# --- LOGIQUE DU PONT (PYTHON) ---
# Cette fonction traite les données envoyées par le bouton STOP en JS
def save_score(data_string):
    try:
        if "|" in data_string:
            name, score, words = data_string.split("|")
            st.session_state.scores_db.append({
                "Élève": name,
                "Score": score,
                "Mots": words,
                "Date": pd.Timestamp.now().strftime("%H:%M:%S")
            })
            st.success(f"Résultat de {name} enregistré !")
    except:
        pass

# --- GESTION DE L'AUTHENTIFICATION ---
# On vérifie si l'URL contient des paramètres (scan QR Code)
url_params = st.query_params
if "mode" in url_params and url_params["mode"] == "student":
    st.session_state.authenticated = True
    st.session_state.role = "Élève"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- ECRAN DE CONNEXION ---
if not st.session_state.authenticated:
    st.title("🚀 English Lab FWB - Plateforme Pro")
    role = st.radio("Je suis :", ["Élève", "Professeur"], horizontal=True)
    password = st.text_input("Code d'accès :", type="password")
    if st.button("Lancer la session"):
        if role == "Élève" and password == "ELEC2024":
            st.session_state.authenticated = True
            st.session_state.role = "Élève"
            st.rerun()
        elif role == "Professeur" and password == "ADMIN123":
            st.session_state.authenticated = True
            st.session_state.role = "Professeur"
            st.rerun()
        else:
            st.error("Code incorrect.")

# --- ESPACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Centre de Commande & QR Code")
    
    col_left, col_right = st.columns([1, 1.5])
    
    with col_left:
        st.subheader("⚙️ Configurer la leçon")
        with st.form("settings"):
            pers = st.text_input("IA Persona :", value=st.session_state.class_settings["persona"])
            gram = st.text_input("Grammaire :", value=st.session_state.class_settings["grammar"])
            voc = st.text_area("Lexique (mots-clés) :", value=st.session_state.class_settings["vocab"])
            if st.form_submit_button("Diffuser à la classe"):
                st.session_state.class_settings.update({"persona": pers, "grammar": gram, "vocab": voc})
                st.success("Paramètres mis à jour !")

        st.subheader("📲 Partager avec les élèves")
        # Génération du QR Code
        app_url = "https://ton-app.streamlit.app" # REMPLACE PAR TON URL REELLE
        student_url = f"{app_url}/?mode=student"
        
        qr = qrcode.make(student_url)
        buf = BytesIO()
        qr.save(buf)
        st.image(buf, caption="Faites scanner ce code aux élèves", width=250)
        st.code(student_url)

    with col_right:
        st.subheader("📊 Résultats en direct")
        # On affiche un input invisible qui sert de pont pour les données
        bridge_data = st.text_input("Bridge", key="bridge_input", label_visibility="collapsed")
        if bridge_data:
            save_score(bridge_data)
        
        if st.session_state.scores_db:
            st.table(pd.DataFrame(st.session_state.scores_db))
        else:
            st.info("En attente des élèves...")

    if st.button("Déconnexion"):
        st.session_state.authenticated = False
        st.rerun()

# --- INTERFACE ÉLÈVE ---
else:
    st.title("🎯 English Session")
    user_name = st.sidebar.text_input("Ton Prénom & Nom :")
    
    if not user_name:
        st.info("Entre ton nom dans la barre latérale pour activer le micro.")
    else:
        # Récupération des réglages prof
        s = st.session_state.class_settings
        v_list = str([w.strip().lower() for w in s["vocab"].split(",") if len(w.strip()) > 2]).replace("'", '"')

        # Code HTML/JS
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f6; padding: 20px; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
                #chat {{ height: 300px; overflow-y: auto; border: 1px solid #eee; padding: 10px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 10px; }}
                .msg {{ padding: 10px; border-radius: 10px; max-width: 80%; }}
                .user {{ align-self: flex-end; background: #007bff; color: white; }}
                .ai {{ align-self: flex-start; background: #f1f1f1; }}
                .btn {{ width: 100%; padding: 15px; border: none; border-radius: 10px; cursor: pointer; font-weight: bold; margin-bottom: 10px; }}
                #mic {{ background: #dc3545; color: white; font-size: 1.2rem; }}
                #stop {{ background: #28a745; color: white; }}
                .listening {{ animation: pulse 1.5s infinite; }}
                @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} 100% {{ opacity: 1; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3>Hello {user_name}!</h3>
                <p style="font-size: 0.8rem; color: #666;">Goal: {s['grammar']}</p>
                <div id="chat"><div class="msg ai">I am your {s['persona']}. Click the mic to start!</div></div>
                <button id="mic" class="btn">🎤 CLIQUE POUR PARLER</button>
                <button id="stop" class="btn">🛑 ENVOYER AU PROF</button>
            </div>

            <script>
                const API_KEY = "{api_key}";
                const VOCAB = {v_list};
                let score = 0; let found = new Set();

                const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                rec.lang = 'en-US';

                document.getElementById('mic').onclick = () => {{ try {{ rec.start(); }} catch(e) {{ rec.stop(); }} }};
                rec.onstart = () => document.getElementById('mic').classList.add('listening');
                rec.onend = () => document.getElementById('mic').classList.remove('listening');

                rec.onresult = async (e) => {{
                    const text = e.results[0][0].transcript;
                    addMsg(text, 'user');
                    
                    // Scoring
                    VOCAB.forEach(w => {{ if(text.toLowerCase().includes(w)) {{ found.add(w); score += 50; }} }});
                    score += 10;

                    // AI Response
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{
                            model: "gpt-4o-mini",
                            messages: [
                                {{role: "system", content: "You are {s['persona']}. Target grammar: {s['grammar']}. Respond in 1 sentence + 1 question."}},
                                {{role: "user", content: text}}
                            ]
                        }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    addMsg(reply, 'ai');
                    const u = new SpeechSynthesisUtterance(reply); u.lang = 'en-US'; window.speechSynthesis.speak(u);
                }};

                function addMsg(t, c) {{
                    const d = document.createElement('div'); d.className = 'msg ' + c; d.innerText = t;
                    const chat = document.getElementById('chat'); chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}

                document.getElementById('stop').onclick = () => {{
                    const data = "{user_name}|" + score + "|" + Array.from(found).join(', ');
                    const inputs = window.parent.document.querySelectorAll('input');
                    for (let i of inputs) {{
                        if (i.type === "text") {{
                            i.value = data;
                            i.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            i.dispatchEvent(new KeyboardEvent('keydown', {{ keyCode: 13, bubbles: true }}));
                            break;
                        }}
                    }}
                    alert("Résultats envoyés !");
                }};
            </script>
        </body>
        </html>
        """
        st.components.v1.html(html_code, height=600)

    if st.sidebar.button("Déconnexion"):
        st.session_state.authenticated = False
        st.query_params.clear()
        st.rerun()
