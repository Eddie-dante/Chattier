<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ChatVerse • Community Forum</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem;
        }

        /* Auth container */
        .auth-container, .chat-container {
            width: 100%;
            max-width: 900px;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(18px);
            border-radius: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 2rem;
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        }

        .chat-container {
            height: 90vh;
            display: flex;
            flex-direction: column;
            padding: 0;
            overflow: hidden;
        }

        /* Header */
        .chat-header {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.2);
        }

        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #c084fc, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .online-badge {
            background: rgba(255,255,255,0.1);
            padding: 0.3rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .online-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Messages area */
        .messages-area {
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .message {
            display: flex;
            gap: 0.7rem;
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.own {
            flex-direction: row-reverse;
        }

        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #7c3aed, #a78bfa);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            flex-shrink: 0;
        }

        .message.own .avatar {
            background: linear-gradient(135deg, #3b82f6, #60a5fa);
        }

        .bubble {
            max-width: 70%;
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            padding: 0.7rem 1rem;
            border-radius: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .message.own .bubble {
            background: rgba(59, 130, 246, 0.2);
            border-color: rgba(59, 130, 246, 0.3);
        }

        .name {
            font-size: 0.75rem;
            color: #94a3b8;
            margin-bottom: 0.2rem;
        }

        .message.own .name {
            text-align: right;
        }

        .text {
            color: #f1f5f9;
            word-wrap: break-word;
        }

        .time {
            font-size: 0.65rem;
            color: #64748b;
            margin-left: 0.5rem;
        }

        /* Input area */
        .input-area {
            padding: 1rem 1.5rem;
            background: rgba(0,0,0,0.2);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .message-row {
            display: flex;
            gap: 0.5rem;
        }

        #message {
            flex: 1;
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 0.7rem 1rem;
            border-radius: 2rem;
            color: white;
            font-size: 0.9rem;
        }

        button {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            border: none;
            padding: 0.7rem 1.5rem;
            border-radius: 2rem;
            color: white;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }

        button:hover {
            transform: scale(1.05);
        }

        input:focus {
            outline: none;
            border-color: #c084fc;
        }

        /* Typing indicator */
        .typing-indicator {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 0.5rem 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }

        .typing-dot {
            width: 6px;
            height: 6px;
            background: #c084fc;
            border-radius: 50%;
            display: inline-block;
            animation: bounce 1.4s infinite;
        }

        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
        }

        /* Form styling */
        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            color: #cbd5e1;
            margin-bottom: 0.5rem;
        }

        .form-group input {
            width: 100%;
            background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.2);
            padding: 0.7rem 1rem;
            border-radius: 1rem;
            color: white;
        }

        .tabs {
            display: flex;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }

        .tab {
            flex: 1;
            text-align: center;
            padding: 0.7rem;
            background: rgba(255,255,255,0.05);
            border-radius: 1rem;
            cursor: pointer;
            color: #94a3b8;
        }

        .tab.active {
            background: linear-gradient(135deg, #7c3aed, #a855f7);
            color: white;
        }

        .empty {
            text-align: center;
            color: #64748b;
            padding: 2rem;
        }

        ::-webkit-scrollbar {
            width: 6px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
        }

        ::-webkit-scrollbar-thumb {
            background: #7c3aed;
            border-radius: 10px;
        }
    </style>
</head>
<body>
<div id="app"></div>

<script>
    // Simple working chat app with auth
    const STORAGE_USERS = 'chatverse_users';
    const STORAGE_MESSAGES = 'chatverse_messages';
    const STORAGE_SESSION = 'chatverse_session';
    
    let currentUser = null;
    let messages = [];
    let activeTab = 'login';
    
    // Load data
    function loadUsers() {
        const saved = localStorage.getItem(STORAGE_USERS);
        if (saved) {
            return JSON.parse(saved);
        }
        return {};
    }
    
    function saveUsers(users) {
        localStorage.setItem(STORAGE_USERS, JSON.stringify(users));
    }
    
    function loadMessages() {
        const saved = localStorage.getItem(STORAGE_MESSAGES);
        if (saved) {
            return JSON.parse(saved);
        }
        return [
            { id: '1', username: 'Astra', text: 'Welcome to ChatVerse! 🌟', time: new Date(Date.now() - 3600000).toLocaleTimeString() },
            { id: '2', username: 'Nebula', text: 'Hey everyone! 👋', time: new Date(Date.now() - 1800000).toLocaleTimeString() }
        ];
    }
    
    function saveMessages() {
        localStorage.setItem(STORAGE_MESSAGES, JSON.stringify(messages));
    }
    
    function saveSession() {
        if (currentUser) {
            localStorage.setItem(STORAGE_SESSION, currentUser);
        } else {
            localStorage.removeItem(STORAGE_SESSION);
        }
    }
    
    function loadSession() {
        const saved = localStorage.getItem(STORAGE_SESSION);
        if (saved) {
            currentUser = saved;
            renderChat();
        } else {
            renderAuth();
        }
    }
    
    // Hash password (simple)
    function hashPassword(password) {
        let hash = 0;
        for (let i = 0; i < password.length; i++) {
            hash = ((hash << 5) - hash) + password.charCodeAt(i);
            hash |= 0;
        }
        return hash.toString();
    }
    
    // Sign up
    function signup(username, password, confirm) {
        if (!username || !password) {
            alert('Please fill all fields');
            return false;
        }
        if (password !== confirm) {
            alert('Passwords do not match');
            return false;
        }
        
        const users = loadUsers();
        if (users[username]) {
            alert('Username already exists');
            return false;
        }
        
        users[username] = hashPassword(password);
        saveUsers(users);
        alert('Account created! Please sign in.');
        return true;
    }
    
    // Sign in
    function signin(username, password) {
        const users = loadUsers();
        if (users[username] && users[username] === hashPassword(password)) {
            currentUser = username;
            saveSession();
            renderChat();
            return true;
        } else {
            alert('Invalid username or password');
            return false;
        }
    }
    
    // Sign out
    function signout() {
        currentUser = null;
        saveSession();
        renderAuth();
    }
    
    // Send message
    function sendMessage() {
        const input = document.getElementById('message');
        const text = input.value.trim();
        if (!text) return;
        
        const newMsg = {
            id: Date.now().toString(),
            username: currentUser,
            text: text,
            time: new Date().toLocaleTimeString()
        };
        
        messages.push(newMsg);
        saveMessages();
        renderMessages();
        input.value = '';
        input.focus();
    }
    
    // Clear chat
    function clearChat() {
        if (confirm('Clear all messages? This cannot be undone.')) {
            messages = [];
            saveMessages();
            renderMessages();
        }
    }
    
    // Render messages
    function renderMessages() {
        const container = document.getElementById('messages');
        if (!container) return;
        
        if (messages.length === 0) {
            container.innerHTML = '<div class="empty">💫 No messages yet. Start the conversation!</div>';
            return;
        }
        
        let html = '';
        for (let msg of messages) {
            const isOwn = msg.username === currentUser;
            const avatar = msg.username.charAt(0).toUpperCase();
            
            html += `
                <div class="message ${isOwn ? 'own' : ''}">
                    <div class="avatar">${avatar}</div>
                    <div class="bubble">
                        <div class="name">
                            ${escapeHtml(msg.username)}
                            <span class="time">${escapeHtml(msg.time)}</span>
                        </div>
                        <div class="text">${escapeHtml(msg.text)}</div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML = html;
        container.scrollTop = container.scrollHeight;
    }
    
    // Typing indicator
    function showTypingIndicator() {
        const container = document.getElementById('typingContainer');
        if (!container) return;
        
        const others = [...new Set(messages.filter(m => m.username !== currentUser).map(m => m.username))];
        if (others.length > 0 && Math.random() < 0.15) {
            const typingUser = others[Math.floor(Math.random() * others.length)];
            container.innerHTML = `
                <div class="typing-indicator">
                    <span>✍️ ${escapeHtml(typingUser)}</span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            `;
            setTimeout(() => {
                if (document.getElementById('typingContainer')) {
                    document.getElementById('typingContainer').innerHTML = '';
                }
            }, 3000);
        } else {
            container.innerHTML = '';
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Render chat UI
    function renderChat() {
        messages = loadMessages();
        
        const onlineCount = new Set(messages.map(m => m.username)).size + 1;
        
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="chat-container">
                <div class="chat-header">
                    <div class="logo">💬 ChatVerse</div>
                    <div class="online-badge">
                        <span class="online-dot"></span>
                        <span>${onlineCount} online</span>
                    </div>
                </div>
                
                <div id="typingContainer"></div>
                
                <div class="messages-area" id="messages"></div>
                
                <div class="input-area">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                        <span style="color: #a5b4fc;">👤 ${escapeHtml(currentUser)}</span>
                        <button onclick="clearChat()" style="background: rgba(255,255,255,0.1); padding: 0.3rem 0.8rem; font-size: 0.7rem;">🗑️ Clear</button>
                    </div>
                    <div class="message-row">
                        <input type="text" id="message" placeholder="Type your message..." maxlength="300">
                        <button onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        `;
        
        renderMessages();
        
        // Auto-refresh every 0.5 seconds
        setInterval(() => {
            const newMessages = loadMessages();
            if (JSON.stringify(messages) !== JSON.stringify(newMessages)) {
                messages = newMessages;
                renderMessages();
            }
            showTypingIndicator();
        }, 500);
        
        // Enter key to send
        const input = document.getElementById('message');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendMessage();
            });
        }
    }
    
    // Render auth UI
    function renderAuth() {
        const app = document.getElementById('app');
        app.innerHTML = `
            <div class="auth-container">
                <h1 style="text-align: center; margin-bottom: 1rem;">💬 ChatVerse</h1>
                <p style="text-align: center; color: #94a3b8; margin-bottom: 2rem;">Community Forum</p>
                
                <div class="tabs">
                    <div class="tab ${activeTab === 'login' ? 'active' : ''}" onclick="setTab('login')">Sign In</div>
                    <div class="tab ${activeTab === 'signup' ? 'active' : ''}" onclick="setTab('signup')">Sign Up</div>
                </div>
                
                <div id="authForm"></div>
            </div>
        `;
        renderAuthForm();
    }
    
    function setTab(tab) {
        activeTab = tab;
        renderAuth();
    }
    
    function renderAuthForm() {
        const container = document.getElementById('authForm');
        if (!container) return;
        
        if (activeTab === 'login') {
            container.innerHTML = `
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="loginUsername" placeholder="Enter username">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="loginPassword" placeholder="Enter password">
                </div>
                <button onclick="handleLogin()" style="width: 100%;">Sign In</button>
            `;
        } else {
            container.innerHTML = `
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" id="signupUsername" placeholder="Choose username">
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" id="signupPassword" placeholder="Choose password">
                </div>
                <div class="form-group">
                    <label>Confirm Password</label>
                    <input type="password" id="signupConfirm" placeholder="Confirm password">
                </div>
                <button onclick="handleSignup()" style="width: 100%;">Sign Up</button>
            `;
        }
    }
    
    function handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        signin(username, password);
    }
    
    function handleSignup() {
        const username = document.getElementById('signupUsername').value;
        const password = document.getElementById('signupPassword').value;
        const confirm = document.getElementById('signupConfirm').value;
        signup(username, password, confirm);
    }
    
    // Make functions global
    window.sendMessage = sendMessage;
    window.clearChat = clearChat;
    window.setTab = setTab;
    window.handleLogin = handleLogin;
    window.handleSignup = handleSignup;
    
    // Start app
    loadSession();
</script>
</body>
</html>
