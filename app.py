import streamlit as st
import qrcode
from io import BytesIO
from fpdf import FPDF
from openai import OpenAI

# 1. CONFIGURATION & MOTEUR
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

# Initialisation de la mémoire session
if "class_settings" not in st.session_state:
    st.session_state.class_settings = {
        "language": "English", 
        "level": "Primaire (Initiation/A1)",
        "mode": "Tuteur (Dialogue IA)",
        "topic": "Food and Drinks", 
        "session_code": "LAB2026",
        "teacher_email": "", 
        "vocab": "Apple, Banana, Milk, I like",
        "custom_prompt": "Fais semblant d'être un serveur dans un café."
    }

# --- FONCTION PDF (CONFORME PAGE 4 - GRILLE ABCD) ---
def create_pdf(user_name, level, topic, evaluation_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Bilan d'Evaluation Officiel - FWB", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 8, txt=f"Eleve : {user_name} | Niveau : {level} | Sujet : {topic}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    clean_text = evaluation_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# --- LOGIQUE DES ROLES ---
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Configuration du Laboratoire")
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(st.session_state.class_settings["level"]))
        lang = col1.selectbox("Langue :", ["English", "Nederlands"])
        mode = col1.selectbox("Mode d'activité :", ["Tuteur (Dialogue IA)", "Solo (Expression continue)", "Jeu de rôle", "Examen oral"])
        
        topic = col2.text_input("Thème de la séance :", value=st.session_state.class_settings["topic"])
        sess_code = col2.text_input("Code secret session :", value=st.session_state.class_settings["session_code"])
        mail = col2.text_input("Email enseignant :", value=st.session_state.class_settings["teacher_email"])
        
        st.divider()
        voc = st.text_area("Vocabulaire attendu :", value=st.session_state.class_settings["vocab"])
        mission = st.text_area("🎯 MISSION DU TUTEUR :", value=st.session_state.class_settings["custom_prompt"])
        
        # LE BOUTON DE VALIDATION (OBLIGATOIRE DANS LE FORM)
        submitted = st.form_submit_button("✅ Enregistrer et Publier la session")
        if submitted:
            st.session_state.class_settings.update({
                "language": lang, "level": lvl, "topic": topic, "session_code": sess_code,
                "teacher_email": mail, "vocab": voc, "custom_prompt": mission, "mode": mode
            })
            st.success(f"Session publiée ! Code : {sess_code}")

    st.divider()
    col_a, col_b = st.columns([1, 2])
    with col_a:
        qr = qrcode.make("https://tuteur-anglais-fwb.streamlit.app") 
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150, caption="Scan QR Code")
    with col_b:
        st.info(f"### 🔑 Code Élève : **{st.session_state.class_settings['session_code']}**")

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    st.title(f"🗣️ Labo : {s['topic']}")
    
    user_name = st.sidebar.text_input("Ton Prénom :")
    input_code = st.sidebar.text_input("Code de session (donné par le prof) :")
    
    if not user_name or input_code != s['session_code']:
        st.warning("👈 Entre ton prénom et le code de session correct pour activer le micro.")
    else:
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        tts_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        adapt_prompt = f"Tu es un tuteur de {s['language']} ({s['level']}). MISSION: {s['custom_prompt']}. PARLE UNIQUEMENT EN {s['language']}. Sois bienveillant."

        html_code = f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; text-align:center;">
            <div id="status" style="color:blue; font-weight:bold; margin-bottom:10px;">Pret</div>
            <div id="chat" style="height:250px; overflow-y:auto; margin-bottom:10px; padding:10px; background:white; text-align:left;"></div>
            <button id="go" style="width:100%; padding:20px; background:#dc3545; color:white; border:none; border-radius:10px; font-weight:bold;">🎤 CLIQUE ET PARLE</button>
        </div>
        <script>
            const API_KEY = "{st.secrets['OPENAI_API_KEY']}";
            let msgs = [{{role: "system", content: `{adapt_prompt}`}}];
            const btn = document.getElementById('go');
            const chat = document.getElementById('chat');
            const status = document.getElementById('status');
            const synth = window.speechSynthesis;
            const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            rec.lang = "{rec_l}";

            function speakText(text) {{
                synth.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.lang = "{tts_l}";
                u.rate = 0.9;
                setTimeout(() => {{ synth.speak(u); }}, 100);
            }}

            async function talk(txt) {{
                status.innerText = "L'IA reflechit...";
                if(txt) msgs.push({{role: "user", content: txt}});
                else msgs.push({{role: "user", content: "START MISSION."}});
                try {{
                    const r = await fetch('https://api.openai.com/v1/chat/completions', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY }},
                        body: JSON.stringify({{ model: "gpt-4o-mini", messages: msgs }})
                    }});
                    const d = await r.json();
                    const reply = d.choices[0].message.content;
                    msgs.push({{role: "assistant", content: reply}});
                    chat.innerHTML += `<p><b>Tuteur:</b> ${{reply.replace('Correction:', '<br><small style="color:red;">Correction:</small>')}}</p>`;
                    chat.scrollTop = chat.scrollHeight;
                    speakText(reply.split('Correction:')[0]);
                    status.innerText = "A toi !";
                }} catch(e) {{ status.innerText = "Erreur IA."; }}
            }}

            btn.onclick = () => {{
                const unlock = new SpeechSynthesisUtterance("");
                synth.speak(unlock);
                if(msgs.length === 1) talk(null);
                else {{ try {{ rec.start(); status.innerText = "Ecoute..."; }} catch(e) {{}} }}
            }};

            rec.onresult = (e) => {{
                const t = e.results[0][0].transcript;
                chat.innerHTML += `<p style="text-align:right; color:blue;"><b>Moi:</b> ${{t}}</p>`;
                talk(t);
            }};
        </script>
        """
        st.components.v1.html(html_code, height=480)

        st.divider()
        trans = st.text_area("Copie le dialogue pour l'évaluation :", height=150)
        if st.button("🏁 Générer mon Bilan Officiel FWB"):
            with st.spinner("Analyse SEGEC / Tronc Commun..."):
                est_solo = s['mode'] == "Solo (Expression continue)"
                type_oral = "CONTINU (EOC)" if est_solo else "INTERACTION (EOI)"
                eval_p = f"Expert Tronc Commun & SEGEC. Evalue {user_name} ({s['level']}) pour Expression Orale {type_oral}. BIENVEILLANCE: Note > 10/20 si communication reussie (ignore erreurs micro). Bareme Page 4: 1xC=8/20, 2xC=6/20."
                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": f"{eval_p} Texte: {trans}"}])
                bilan_final = res.choices[0].message.content
                st.markdown(bilan_final)
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan_final)
                st.download_button("📥 Télécharger mon PDF", pdf, f"Bilan_{user_name}.pdf")arkdown(bilan_final)
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan_final)
                st.download_button("📥 Télécharger mon PDF", pdf, f"Bilan_{user_name}.pdf")
