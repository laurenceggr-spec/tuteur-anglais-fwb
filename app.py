<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI English Buddy - Teacher Tools</title>
    <style>
        /* --- STYLE ADAPTÉ (ACCESSIBILITÉ) --- */
        :root {
            --bg-color: #FDF6E3;
            --chat-bg: #EEE8D5;
            --user-msg: #D33682;
            --ai-msg: #268BD2;
            --error-msg: #e74c3c;
            --text-color: #333333;
            --font-main: 'Verdana', 'Arial', sans-serif;
            --score-color: #f1c40f;
            --mission-color: #16a085;
        }

        body {
            font-family: var(--font-main);
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            display: flex;
            justify-content: center;
            height: 100vh;
            letter-spacing: 0.05em; 
            line-height: 1.6;
            overflow: hidden;
        }

        .app-container {
            width: 100%;
            max-width: 400px;
            background-color: #fff;
            display: flex;
            flex-direction: column;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            height: 100%;
            position: relative;
            z-index: 10;
        }

        header {
            background-color: #2C3E50;
            color: white;
            padding: 10px 15px;
            display: flex;
            flex-direction: column;
            gap: 5px;
            z-index: 20;
        }

        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 100%;
        }
        
        .app-title {
            font-size: 1.1rem;
            font-weight: bold;
        }

        /* Indicateur de mode (Cerveau vs Robot) */
        .mode-badge {
            font-size: 0.75rem;
            padding: 2px 8px;
            border-radius: 10px;
            background-color: #95a5a6;
            color: white;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            margin-top: 2px;
        }
        .mode-badge.ai-active {
            background-color: #27AE60;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 15px; /* Espacement un peu plus grand */
        }

        .settings-btn {
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1.3rem;
            filter: grayscale(100%);
            transition: all 0.3s;
            opacity: 0.7;
            color: white;
            padding: 0;
        }
        .settings-btn:hover { opacity: 1; transform: scale(1.1); }
        .settings-btn.active {
            filter: grayscale(0%);
            text-shadow: 0 0 5px #2ecc71;
            opacity: 1;
        }
        /* Style spécifique pour le bouton Défis */
        .settings-btn.challenge-active {
            filter: none;
            opacity: 1;
            text-shadow: 0 0 5px #1abc9c;
        }

        .score-display {
            background-color: rgba(255,255,255,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: transform 0.2s;
        }

        .score-display.pop {
            transform: scale(1.3);
            background-color: var(--score-color);
            color: #333;
        }

        .topics-container {
            padding: 10px;
            background-color: #ecf0f1;
            display: flex;
            gap: 10px;
            overflow-x: auto;
            border-bottom: 1px solid #ddd;
            z-index: 20;
        }

        .topic-btn {
            background-color: white;
            border: 2px solid #bdc3c7;
            border-radius: 15px;
            padding: 8px 15px;
            font-size: 0.9rem;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s;
            color: #7f8c8d;
        }

        .topic-btn.active {
            background-color: #2980b9;
            color: white;
            border-color: #2980b9;
            font-weight: bold;
            transform: scale(1.05);
        }

        /* --- BARRE DE MISSION (NOUVEAU) --- */
        #mission-bar {
            background-color: #e8f8f5;
            color: var(--mission-color);
            font-size: 0.85rem;
            padding: 8px;
            text-align: center;
            border-bottom: 1px solid #a3e4d7;
            display: none; /* Caché par défaut */
            animation: slideDown 0.3s ease;
        }
        #mission-bar.visible { display: block; }

        @keyframes slideDown {
            from { transform: translateY(-100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        /* --- SCÈNE VISUELLE --- */
        #visual-stage {
            background-color: #f0f8ff;
            height: 120px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 4rem;
            border-bottom: 1px dashed #cbd5e0;
            transition: background-color 0.5s;
        }
        
        #visual-emoji {
            animation: bounceIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: inline-block;
        }

        /* Chat */
        #chat-box {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 15px;
            position: relative;
            z-index: 5;
        }

        .message {
            max-width: 80%;
            padding: 15px;
            border-radius: 20px;
            font-size: 1.1rem;
            position: relative;
            animation: fadeIn 0.3s ease;
            word-wrap: break-word;
        }

        .user {
            align-self: flex-end;
            background-color: var(--user-msg);
            color: white;
            border-bottom-right-radius: 5px;
        }

        .ai {
            align-self: flex-start;
            background-color: var(--ai-msg);
            color: white;
            border-bottom-left-radius: 5px;
        }

        .error-message {
            align-self: center;
            background-color: #fce4ec;
            color: #c0392b;
            font-size: 0.9rem;
            border: 1px solid #c0392b;
            text-align: center;
        }

        /* Loader pour l'IA */
        .typing-indicator {
            font-style: italic;
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-left: 10px;
            display: none;
        }
        .typing-indicator.show { display: block; }

        .points-float {
            position: absolute;
            color: var(--score-color);
            font-weight: bold;
            font-size: 1.5rem;
            pointer-events: none;
            animation: floatUp 1s ease-out forwards;
            z-index: 100;
        }

        .controls {
            padding: 20px;
            background-color: #f8f9fa;
            border-top: 2px solid #ddd;
            display: flex;
            flex-direction: column;
            gap: 10px;
            align-items: center;
            z-index: 20;
        }

        #mic-btn {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background-color: #E74C3C;
            border: none;
            color: white;
            font-size: 30px;
            cursor: pointer;
            transition: transform 0.2s, background-color 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }

        #mic-btn:active { transform: scale(0.95); }

        #mic-btn.listening {
            background-color: #27AE60;
            animation: pulse 1.5s infinite;
        }

        #status-text {
            font-size: 1.1rem;
            font-weight: bold;
            color: #7f8c8d;
            height: 25px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 90%;
            transition: color 0.2s;
            min-height: 25px;
        }

        /* --- MODALS --- */
        .modal {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0);
            background-color: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 50;
            transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            pointer-events: none;
            opacity: 0;
            width: 85%;
            max-width: 350px;
        }

        .modal.show {
            transform: translate(-50%, -50%) scale(1);
            opacity: 1;
            pointer-events: auto;
        }

        /* Input styles */
        .settings-input, .challenge-select {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 1rem;
        }
        
        label {
            display: block;
            text-align: left;
            margin-left: 5%;
            font-weight: bold;
            font-size: 0.9rem;
            color: #34495e;
            margin-top: 10px;
        }

        .save-btn {
            background-color: #27AE60;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            cursor: pointer;
            margin-top: 15px;
            font-weight: bold;
            width: 100%;
        }
        
        .delete-btn {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
            font-size: 0.8rem;
        }

        /* Animations */
        @keyframes bounceIn {
            0% { transform: scale(0); opacity: 0; }
            60% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); }
        }

        .confetti {
            position: absolute;
            top: -10px;
            z-index: 100;
            font-size: 1.5rem;
            animation: fall linear forwards;
        }

        @keyframes fall {
            to { transform: translateY(100vh) rotate(720deg); }
        }
        
        .modal-close {
            position: absolute;
            top: 10px;
            right: 15px;
            font-size: 1.5rem;
            cursor: pointer;
            color: #999;
        }
    </style>
</head>
<body>

<div class="app-container">
    <header>
        <div class="header-top">
            <div class="header-actions">
                <button class="settings-btn" id="settings-btn" onclick="openSettings()" title="Configure AI Key">⚙️</button>
                <!-- NOUVEAU BOUTON DÉFIS -->
                <button class="settings-btn" id="challenges-btn" onclick="openChallenges()" title="Teacher Constraints">🎯</button>
                
                <div style="display:flex; flex-direction:column;">
                    <span class="app-title">🇬🇧 English Buddy</span>
                    <span id="mode-badge" class="mode-badge">🤖 Demo Mode</span>
                </div>
            </div>
            <div class="score-display" id="score-board">
                ⭐ <span id="score-val">0</span>
            </div>
        </div>
    </header>

    <div class="topics-container">
        <button class="topic-btn active" onclick="setTopic('intro')">👋 Intro</button>
        <button class="topic-btn" onclick="setTopic('restaurant')">🍔 Restaurant</button>
        <button class="topic-btn" onclick="setTopic('hobbies')">⚽ Hobbies</button>
    </div>

    <!-- NOUVEAU : BARRE DE MISSION -->
    <div id="mission-bar">
        🎯 <strong>Mission:</strong> <span id="mission-text">Aucune contrainte</span>
    </div>

    <div id="visual-stage">
        <div id="visual-emoji">👋</div>
    </div>

    <div id="chat-box">
        <div class="message ai">
            Hello! Let's start. Speak to earn points! 🏆
        </div>
        <div id="typing" class="typing-indicator">Thinking...</div>
    </div>

    <!-- Modal Level Up -->
    <div id="level-up-modal" class="modal">
        <div style="font-size: 3rem;">🎉</div>
        <h2 style="color: #e67e22; margin: 10px 0;">LEVEL UP!</h2>
        <p>You are a superstar!</p>
    </div>

    <!-- Modal Settings (API Key) -->
    <div id="settings-modal" class="modal">
        <span class="modal-close" onclick="closeSettings()">&times;</span>
        <h3>🤖 Brain Settings</h3>
        <p style="font-size: 0.9rem;">Paste your OpenAI API Key here (starts with sk-...).</p>
        <input type="password" id="api-key-input" class="settings-input" placeholder="Paste OpenAI Key here...">
        <div id="key-status" style="font-size:0.8rem; margin-bottom:10px; color:#e74c3c;"></div>
        <button class="save-btn" onclick="saveSettings()">Save & Connect</button>
        <button class="delete-btn" onclick="clearKey()">🗑️ Clear Key</button>
    </div>

    <!-- NOUVEAU : MODAL DÉFIS / CONTRAINTES -->
    <div id="challenges-modal" class="modal">
        <span class="modal-close" onclick="closeChallenges()">&times;</span>
        <h3 style="color:#16a085;">🎯 Teacher Constraints</h3>
        <p style="font-size:0.8rem; color:#666;">Configurez les exigences pour l'élève (Mode Smart recommandé).</p>
        
        <label for="vocab-input">Mots à placer (optionnel)</label>
        <input type="text" id="vocab-input" class="settings-input" placeholder="ex: happy, because, yesterday">
        
        <label for="grammar-select">Focus Grammaire</label>
        <select id="grammar-select" class="challenge-select">
            <option value="None">Aucun (Libre)</option>
            <option value="Past Tense">Passé (Past Simple)</option>
            <option value="Future Tense">Futur (Will / Going to)</option>
            <option value="Present Continuous">Présent Continu (-ing)</option>
            <option value="Adjectives">Richesse des Adjectifs</option>
            <option value="Questions">Poser des questions</option>
        </select>
        
        <button class="save-btn" style="background-color:#16a085;" onclick="saveChallenges()">Activer les Défis</button>
    </div>

    <div class="controls">
        <div id="status-text">Click mic & Speak</div>
        <button id="mic-btn" aria-label="Microphone">🎤</button>
    </div>
</div>

<script>
    const micBtn = document.getElementById('mic-btn');
    const chatBox = document.getElementById('chat-box');
    const statusText = document.getElementById('status-text');
    const scoreVal = document.getElementById('score-val');
    const scoreBoard = document.getElementById('score-board');
    const levelModal = document.getElementById('level-up-modal');
    const settingsModal = document.getElementById('settings-modal');
    const challengesModal = document.getElementById('challenges-modal');
    const visualEmoji = document.getElementById('visual-emoji');
    const typingIndicator = document.getElementById('typing');
    const settingsBtn = document.getElementById('settings-btn');
    const challengesBtn = document.getElementById('challenges-btn');
    const keyStatus = document.getElementById('key-status');
    const apiKeyInput = document.getElementById('api-key-input');
    const modeBadge = document.getElementById('mode-badge');
    const missionBar = document.getElementById('mission-bar');
    const missionText = document.getElementById('mission-text');
    
    let isRecognizing = false;
    let score = 0;
    let hasRecognizedSomething = false;
    let apiKey = localStorage.getItem("openai_api_key") || "";

    // --- VARIABLES DÉFIS ---
    let targetVocab = "";
    let grammarFocus = "None";

    // --- INITIALISATION ---
    window.onload = function() {
        updateModeUI();
        if (apiKey && apiKey.startsWith("sk-")) {
            addMessage("System: OpenAI Key loaded. Ready! 🧠", "ai");
            apiKeyInput.value = apiKey;
        }
    };

    function updateModeUI() {
        if (apiKey && apiKey.startsWith("sk-")) {
            settingsBtn.classList.add('active');
            modeBadge.classList.add('ai-active');
            modeBadge.innerText = "🧠 Smart Mode";
        } else {
            settingsBtn.classList.remove('active');
            modeBadge.classList.remove('ai-active');
            modeBadge.innerText = "🤖 Demo Mode";
        }
    }

    // --- GESTION DES MODALS ---
    function openSettings() { settingsModal.classList.add('show'); if(apiKey) apiKeyInput.value = apiKey; }
    function closeSettings() { settingsModal.classList.remove('show'); }
    
    function openChallenges() { challengesModal.classList.add('show'); }
    function closeChallenges() { challengesModal.classList.remove('show'); }

    // --- SAUVEGARDE CLÉ API ---
    function saveSettings() {
        const input = document.getElementById('api-key-input');
        const rawKey = input.value.trim();
        if (rawKey.length > 0 && !rawKey.startsWith("sk-")) {
            keyStatus.innerText = "⚠️ Key should start with 'sk-'.";
            return;
        }
        apiKey = rawKey;
        localStorage.setItem("openai_api_key", apiKey);
        keyStatus.innerText = "";
        settingsModal.classList.remove('show');
        updateModeUI();
        addMessage(apiKey ? "System: Real AI Activated! 🧠" : "System: Demo Mode", "ai");
    }

    function clearKey() {
        apiKey = "";
        localStorage.removeItem("openai_api_key");
        apiKeyInput.value = "";
        closeSettings();
        updateModeUI();
        addMessage("System: Key removed.", "ai");
    }

    // --- SAUVEGARDE DÉFIS ---
    function saveChallenges() {
        const vocabInput = document.getElementById('vocab-input');
        const grammarSelect = document.getElementById('grammar-select');
        
        targetVocab = vocabInput.value.trim();
        grammarFocus = grammarSelect.value;
        
        // Mise à jour visuelle
        if (targetVocab || grammarFocus !== "None") {
            challengesBtn.classList.add('challenge-active');
            missionBar.classList.add('visible');
            
            let missionDisplay = "";
            if(grammarFocus !== "None") missionDisplay += `Utiliser: <strong>${grammarFocus}</strong>. `;
            if(targetVocab) missionDisplay += `Mots: <strong>${targetVocab}</strong>.`;
            
            missionText.innerHTML = missionDisplay;
            addMessage("👨‍🏫 Teacher: New mission updated!", "ai");
        } else {
            challengesBtn.classList.remove('challenge-active');
            missionBar.classList.remove('visible');
            addMessage("👨‍🏫 Teacher: Free talk mode.", "ai");
        }
        
        closeChallenges();
    }

    // --- GAMIFICATION & CONFETTI (IDENTIQUE) ---
    function addPoints(amount) {
        const oldScore = score;
        score += amount;
        scoreVal.innerText = score;
        scoreBoard.classList.add('pop');
        setTimeout(() => scoreBoard.classList.remove('pop'), 200);
        showFloatingPoints(amount);
        if (Math.floor(score / 50) > Math.floor(oldScore / 50)) triggerLevelUp();
    }

    function showFloatingPoints(amount) {
        const floatEl = document.createElement('div');
        floatEl.classList.add('points-float');
        floatEl.innerText = `+${amount}`;
        floatEl.style.left = (50 + Math.random() * 40 - 20) + '%';
        floatEl.style.bottom = '120px';
        document.querySelector('.app-container').appendChild(floatEl);
        setTimeout(() => floatEl.remove(), 1000);
    }

    function triggerLevelUp() {
        speak("Congratulations! Level up!");
        levelModal.classList.add('show');
        for(let i=0; i<30; i++) createConfetti();
        setTimeout(() => levelModal.classList.remove('show'), 3000);
    }

    function createConfetti() {
        const emojis = ['🎉', '⭐', '🇬🇧', '🏆', '✨'];
        const confetti = document.createElement('div');
        confetti.innerText = emojis[Math.floor(Math.random() * emojis.length)];
        confetti.classList.add('confetti');
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.animationDuration = (Math.random() * 2 + 1) + 's';
        document.querySelector('.app-container').appendChild(confetti);
        setTimeout(() => confetti.remove(), 3000);
    }

    // --- SUJETS ---
    let currentTopic = 'intro';
    const topicsData = {
        'intro': { start: "Hello! Tell me your name!", mainEmoji: "👋", keywords: [{trigger:"your name",reply:"My name is Buddy! 🤖 What is yours?",emoji:"🤖"}, {trigger:"my name",reply:"Nice to meet you! How are you?",emoji:"🤝"}, {trigger:"yes",reply:"Wonderful!",emoji:"👍"}], default: "Tell me more about yourself!" },
        'restaurant': { start: "Welcome! What do you want to eat?", mainEmoji: "🍽️", keywords: [{trigger:"burger",reply:"Yummy! Fries?",emoji:"🍔"}, {trigger:"pizza",reply:"Good choice!",emoji:"🍕"}], default: "We have burgers, pizza, and salad." },
        'hobbies': { start: "What is your favorite hobby?", mainEmoji: "⚽", keywords: [{trigger:"football",reply:"Goal! Favorite player?",emoji:"🥅"}, {trigger:"music",reply:"I love music!",emoji:"🎸"}], default: "That sounds fun!" }
    };

    function setTopic(topic) {
        currentTopic = topic;
        document.querySelectorAll('.topic-btn').forEach(btn => {
            btn.classList.remove('active');
            if(btn.innerText.toLowerCase().includes(topic) || (topic === 'intro' && btn.innerText.includes('Intro'))) btn.classList.add('active');
        });
        const data = topicsData[topic];
        updateVisual(data.mainEmoji);
        addMessage(data.start, 'ai');
        speak(data.start);
    }

    function updateVisual(emoji) {
        visualEmoji.style.animation = 'none';
        visualEmoji.offsetHeight;
        visualEmoji.style.animation = null; 
        visualEmoji.innerText = emoji;
    }

    // --- RECONNAISSANCE VOCALE ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Use Chrome."); micBtn.disabled = true; } 
    else {
        const recognition = new SpeechRecognition();
        recognition.lang = 'en-US';
        recognition.interimResults = true; 
        recognition.maxAlternatives = 1;

        micBtn.addEventListener('click', () => {
            if (isRecognizing) { recognition.stop(); return; }
            try { recognition.start(); hasRecognizedSomething = false; } catch (e) { console.error(e); }
        });

        recognition.onstart = () => { isRecognizing = true; micBtn.classList.add('listening'); statusText.innerText = "Listening..."; statusText.style.color = "#27AE60"; };
        recognition.onend = () => { isRecognizing = false; micBtn.classList.remove('listening'); statusText.innerText = hasRecognizedSomething ? "Click mic & Speak" : "😕 Nothing heard"; statusText.style.color = hasRecognizedSomething ? "#7f8c8d" : "#E74C3C"; };
        
        recognition.onresult = (event) => {
            let interim = '', final = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) final += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }
            if (interim || final) hasRecognizedSomething = true;
            if (interim) { statusText.innerText = interim + "..."; statusText.style.color = "#E67E22"; }
            if (final) { statusText.innerText = "Got it! ✅"; statusText.style.color = "#27AE60"; addMessage(final, 'user'); addPoints(10); botReply(final); }
        };
        recognition.onerror = (e) => { if(e.error !== 'no-speech') statusText.innerText = "Error: " + e.error; };
    }

    function addMessage(text, sender) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        if(text.includes("Error") || text.includes("⚠️")) div.classList.add('error-message');
        div.innerText = text;
        chatBox.insertBefore(div, typingIndicator); 
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function speak(text) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
    }

    async function botReply(userText) {
        if (apiKey && apiKey.startsWith("sk-")) await callOpenAIAPI(userText);
        else simpleBotReply(userText);
    }

    // --- CERVEAU AVEC CONTRAINTES (VERSION OPENAI) ---
    async function callOpenAIAPI(userText) {
        typingIndicator.classList.add('show');
        
        // Construction du Prompt avec les contraintes
        let constraintText = "";
        if (targetVocab) constraintText += `The student MUST try to use these words: [${targetVocab}]. Check if they used them. `;
        if (grammarFocus !== "None") constraintText += `The student SHOULD practice this grammar: [${grammarFocus}]. `;

        const systemPrompt = `
        Act as a supportive English tutor for a child.
        Topic: ${currentTopic}.
        
        TEACHER MISSION (Constraints):
        ${constraintText}
        
        Instructions:
        1. Reply in simple English (A1/A2).
        2. Keep it short (max 25 words).
        3. ALWAYS ask a follow-up question.
        4. If constraints are set:
           - If student used the required words/grammar, PRAISE them explicitly (e.g. "Great use of 'yesterday'!").
           - If student missed them, gently nudge them (e.g. "Can you try saying that with 'yesterday'?").
        5. Return ONLY the reply text.
        `;

        const payload = {
            model: "gpt-4o-mini", // Modèle rapide et économique d'OpenAI
            messages: [
                { role: "system", content: systemPrompt },
                { role: "user", content: userText }
            ],
            temperature: 0.7
        };

        try {
            const response = await fetch("https://api.openai.com/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${apiKey}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error.message);
            }

            const aiReply = data.choices[0].message.content;

            typingIndicator.classList.remove('show');
            addMessage(aiReply, 'ai');
            speak(aiReply);
            
            if (aiReply.includes('Good') || aiReply.includes('Great')) updateVisual("⭐");
            else if (aiReply.includes('?')) updateVisual("🤔");
            else updateVisual("👍");

        } catch (error) {
            console.error(error);
            typingIndicator.classList.remove('show');
            addMessage(`⚠️ ${error.message}`, "ai");
            setTimeout(() => { updateModeUI(); simpleBotReply(userText); }, 2000);
        }
    }

    function simpleBotReply(userText) {
        // En mode démo, on ignore les contraintes complexes, mais on prévient
        if (targetVocab || grammarFocus !== "None") {
            setTimeout(() => addMessage("ℹ️ (Switch to Smart Mode for Constraints Check)", "ai"), 500);
        }

        const lowerText = userText.toLowerCase();
        const topicData = topicsData[currentTopic];
        let reply = topicData.default;
        let reactionEmoji = topicData.mainEmoji;

        for (const item of topicData.keywords) {
            if (lowerText.includes(item.trigger)) { reply = item.reply; reactionEmoji = item.emoji; break; }
        }
        if (lowerText.includes("thank")) reply = "You're welcome!";
        if (lowerText.includes("bye")) reply = "See you soon!";

        updateVisual(reactionEmoji);
        addMessage(reply, 'ai');
        speak(reply);
    }
</script>

</body>
</html>
