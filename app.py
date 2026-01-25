import streamlit as st
import qrcode
from io import BytesIO
from fpdf import FPDF
from openai import OpenAI

# 1. CONFIGURATION & MOTEUR
st.set_page_config(page_title="Language Lab FWB Pro", layout="wide")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

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

# NAVIGATION
if "role" not in st.session_state:
    st.title("🚀 Language Lab FWB")
    c1, c2 = st.columns(2)
    if c1.button("Accès ÉLÈVE"): st.session_state.role = "Élève"; st.rerun()
    if c2.button("Accès PROFESSEUR"): st.session_state.role = "Professeur"; st.rerun()

# --- INTERFACE PROFESSEUR ---
elif st.session_state.role == "Professeur":
    st.title("👨‍🏫 Tableau de Bord Enseignant")
    
    # --- SECTION FIXE : ACCÈS ÉLÈVES (TOUJOURS VISIBLE) ---
    col_a, col_b = st.columns([1, 2])
    with col_a:
        # Remplacez par votre URL réelle une fois déployé
        qr = qrcode.make("https://tuteur-anglais-fwb.streamlit.app") 
        buf = BytesIO(); qr.save(buf)
        st.image(buf, width=150, caption="Scan pour rejoindre")
    with col_b:
        st.success(f"### 🔑 CODE DE SESSION : **{st.session_state.class_settings['session_code']}**")
        st.info(f"**Sujet actuel :** {st.session_state.class_settings['topic']} | **Mode :** {st.session_state.class_settings['mode']}")

    st.divider()

    # --- SECTION FORMULAIRE : CONFIGURATION ---
    st.subheader("⚙️ Modifier les paramètres de la classe")
    current = st.session_state.class_settings
    with st.form("config_pro"):
        col1, col2 = st.columns(2)
        levels = ["Primaire (Initiation/A1)", "S1-S2 (Vers A2.1)", "S3-S4 (Vers A2.2/B1)"]
        new_lvl = col1.selectbox("Degré / Niveau :", levels, index=levels.index(current["level"]))
        new_lang = col1.selectbox("Langue :", ["English", "Nederlands"], index=0 if current["language"]=="English" else 1)
        modes = ["Tuteur (Dialogue IA)", "Solo (Expression continue)", "Jeu de rôle", "Examen oral"]
        new_mode = col1.selectbox("Mode d'activité :", modes, index=modes.index(current["mode"]))
        
        new_topic = col2.text_input("Thème de la séance :", value=current["topic"])
        new_sess_code = col2.text_input("Code secret session :", value=current["session_code"])
        new_mail = col2.text_input("Email enseignant :", value=current["teacher_email"])
        
        new_voc = st.text_area("Vocabulaire attendu :", value=current["vocab"])
        new_mission = st.text_area("🎯 MISSION DU TUTEUR :", value=current["custom_prompt"])
        
        if st.form_submit_button("✅ APPLIQUER ET DIFFUSER"):
            st.session_state.class_settings = {
                "language": new_lang, "level": new_lvl, "topic": new_topic, 
                "session_code": new_sess_code, "teacher_email": new_mail, 
                "vocab": new_voc, "custom_prompt": new_mission, "mode": new_mode
            }
            st.rerun() # Rafraîchit tout pour mettre à jour le QR et le Code en haut

# --- INTERFACE ÉLÈVE ---
elif st.session_state.role == "Élève":
    s = st.session_state.class_settings
    st.title(f"🗣️ Labo : {s['topic']}")
    
    user_name = st.sidebar.text_input("Ton Prénom :")
    input_code = st.sidebar.text_input("Code de session :")
    
    if not user_name or input_code != s['session_code']:
        st.warning(f"👈 Entre ton prénom et le code affiché au tableau.")
    else:
        rec_l = "en-US" if s['language'] == "English" else "nl-BE"
        t_l = "en-US" if s['language'] == "English" else "nl-NL"
        
        adapt_prompt = (
            f"Tu es un tuteur de {s['language']} ({s['level']}). "
            f"THÈME: {s['topic']}. MISSION: {s['custom_prompt']}. "
            f"MODE: {s['mode']}. VOCABULAIRE: {s['vocab']}. "
            f"Parle UNIQUEMENT en {s['language']}. Sois bienveillant (Référentiel FWB)."
        )

        html_code = f"""
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; border:1px solid #ddd; text-align:center;">
            <div id="status" style="color:blue; font-weight:bold; margin-bottom:10px;">Prêt (Sujet : {s['topic']})</div>
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

            function speak(text) {{
                synth.cancel();
                const u = new SpeechSynthesisUtterance(text);
                u.lang = "{t_l}"; u.rate = 0.9;
                setTimeout(() => {{ synth.speak(u); }}, 100);
            }}

            async function talk(txt) {{
                status.innerText = "L'IA réfléchit...";
                if(txt) msgs.push({{role: "user", content: txt}});
                else msgs.push({{role: "user", content: "LANCE LA MISSION."}});
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
                    speak(reply.split('Correction:')[0]);
                    status.innerText = "À toi !";
                }} catch(e) {{ status.innerText = "Erreur IA."; }}
            }}

            btn.onclick = () => {{
                const unlock = new SpeechSynthesisUtterance("");
                synth.speak(unlock);
                if(msgs.length === 1) talk(null);
                else {{ try {{ rec.start(); status.innerText = "Écoute..."; }} catch(e) {{}} }}
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
        trans = st.text_area("Dialogue pour l'évaluation :", height=150)
        
        if st.button("🏁 Générer mon Bilan Officiel FWB"):
            with st.spinner("Analyse pédagogique en cours..."):
                est_solo = s['mode'] == "Solo (Expression continue)"
                t_oral = "CONTINU (EOC)" if est_solo else "INTERACTION (EOI)"
                
                eval_p = f"""Expert FWB (Tronc Commun). Évalue {user_name} ({s['level']}) - Expression {t_oral}.
                Thème : {s['topic']}.
                CRITÈRES (CE1D 2024) : Compréhensibilité et Pertinence.
                BIENVEILLANCE : Si communication réussie : Note > 12/20.
                BARÈME : 1xC=8/20, 2xC/1xD=6/20.
                Affiche le tableau ABCD et un feedback."""

                res = client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=[{"role": "user", "content": f"{eval_p}\n\nTexte: {trans}"}]
                )
                bilan_final = res.choices[0].message.content
                st.markdown(bilan_final)
                pdf = create_pdf(user_name, s['level'], s['topic'], bilan_final)
                st.download_button("📥 Télécharger mon PDF", pdf, f"Bilan_{user_name}.pdf")
