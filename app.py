import streamlit as st

# Configuration
st.set_page_config(page_title="English Tutor FWB Pro", layout="centered")

# Clé API OpenAI récupérée de manière sécurisée
api_key = st.secrets.get("OPENAI_API_KEY", "")

# On utilise une chaîne brute (R) pour éviter les conflits d'accolades, 
# mais on injecte quand même la clé API proprement.
html_code = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root {{ --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }}
        .app {{ width: 100%; max-width: 500px; background: white; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); height: 100vh; }}
        header {{ background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .settings-bar {{ padding: 10px; background: #eee; border-bottom: 1px solid #ddd; display: flex; flex-direction: column; gap: 5px; }}
        select {{ width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ccc; }}
        .challenge-box {{ background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; }}
        .topics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }}
        .t-btn {{ font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; transition: 0.2s; text-align: center; }}
        .t-btn.active {{ background: var(--s); color: white; border-color: var(--s); }}
        #chat {{ flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }}
        .msg {{ max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; position: relative; word-wrap: break-word; }}
        .user {{ align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }}
        .ai {{ align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }}
        .controls {{ padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }}
        #mic {{ width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); outline: none; }}
        #mic.listening {{ background: var(--ok); animation: pulse 1.5s infinite; }}
        @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(39,174,96, 0.7); }} 70% {{ box-shadow: 0 0 0 15px rgba(39,174,96, 0); }} }}
    </style>
</head>
<body>
<div class="app">
    <header>
        <div style="font-weight:bold;">English Tutor FWB 🇧🇪</div>
        <div>⭐ <span id="score-val">0</span></div>
    </header>
    <div class="settings-bar">
        <select id="lvl">
            <option value="A1 (P3-P6)">Niveau P3-P6 (A1)</option>
            <option value="A2.1 (S1-S2)">Niveau S1-S2 (A2.1)</option>
            <option value="A2.2 (S3)">Niveau S3 (A
