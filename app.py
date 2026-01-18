import streamlit as st

# 1. Configuration de la page
st.set_page_config(page_title="English Tutor FWB Pro", layout="centered")

# 2. Récupération sécurisée de la clé
api_key = st.secrets.get("OPENAI_API_KEY", "")

# 3. Le template HTML (Utilisation d'une Raw String r\"\"\" pour éviter les erreurs de syntaxe)
html_template = r"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        :root { --p: #2C3E50; --s: #3498DB; --bg: #F4F7F6; --err: #E74C3C; --ok: #27AE60; --gold: #F1C40F; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin: 0; display: flex; justify-content: center; height: 100vh; overflow: hidden; }
        .app { width: 100%; max-width: 500px; background: white; display: flex; flex-direction: column; box-shadow: 0 0 20px rgba(0,0,0,0.1); height: 100vh; }
        header { background: var(--p); color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .settings-bar { padding: 10px; background: #eee; border-bottom: 1px solid #ddd; display: flex; flex-direction: column; gap: 5px; }
        select { width: 100%; padding: 8px; border-radius: 5px; border: 1px solid #ccc; font-size: 14px; }
        .challenge-box { background: #FEF9E7; padding: 8px; border: 1px dashed var(--gold); border-radius: 5px; font-size: 0.85rem; color: #7D6608; text-align: center; font-weight: bold; }
        .topics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; padding: 10px; border-bottom: 2px solid #ddd; background: #fff; }
        .t-btn { font-size: 0.7rem; padding: 8px; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; background: white; transition: 0.2s; text-align: center; }
        .t-btn.active { background: var(--s); color: white; border-color: var(--s); }
        #chat { flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #fafafa; }
        .msg { max-width: 85%; padding: 12px; border-radius: 18px; line-height: 1.4; font-size: 1rem; position: relative; word-wrap: break-word; }
        .user { align-self: flex-end; background: var(--s); color: white; border-bottom-right-radius: 2px; }
        .ai { align-self: flex-start; background: white; border: 1px solid #ddd; color: #333; border-bottom-left-radius: 2px; }
        .controls { padding: 20px; text-align: center; border-top: 1px solid #eee; background: white; }
        #mic { width: 70px; height: 70px; border-radius: 50%; border: none; background: var(--err); color: white; font-size: 1.8rem; cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.2); outline: none; }
        #mic.listening { background: var(--ok); animation:
