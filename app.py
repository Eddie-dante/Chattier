import streamlit as st
import json
import os
import html as html_module
import hashlib
import pathlib
from datetime import datetime
import uuid
import random
import time

# Page config
st.set_page_config(
    page_title="ChatVerse • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize paths
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
SESSION_FILE = DATA_DIR / "session.json"

# Custom CSS - matching the HTML design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
        min-height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* Containers */
    .auth-container, .chat-container {
        width: 100%;
        max-width: 900px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(18px);
        border-radius: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
        margin: 0 auto;
    }
    
    .chat-container {
        height: 85vh;
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
        flex-shrink: 0;
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
        color: #e2e8f0;
    }
    
    .online-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        display: inline-block;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Messages */
    .messages-area {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        min-height: 0;
    }
    
    .message {
        display: flex;
        gap: 0.7rem;
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
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
        font-size: 0.9rem;
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
    
    .empty {
        text-align: center;
        color: #64748b;
        padding: 2rem;
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
        margin: 0 1.5rem;
        color: #cbd5e1;
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
    
    /* Input area */
    .input-area {
        padding: 1rem 1.5rem;
        background: rgba(0,0,0,0.2);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        flex-shrink: 0;
    }
    
    .user-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    
    .user-label {
        color: #a5b4fc;
        font-size: 0.85rem;
    }
    
    /* Form styling */
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        padding: 0.7rem 1rem !important;
        border-radius: 2rem !important;
        color: white !important;
        font-size: 0.9rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #c084fc !important;
        box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 2rem !important;
        color: white !important;
        cursor: pointer !important;
        font-weight: bold !important;
        transition: transform 0.2s !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.05) !important;
    }
    
    .clear-btn > button {
        background: rgba(255,255,255,0.1) !important;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.7rem !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 1rem;
        color: #94a3b8;
        padding: 0.7rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        color: white !important;
    }
    
    /* Scrollbar */
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
    
    /* Hide Streamlit form borders */
    .stForm {
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_html(text):
    return html_module.escape(text)

def load_json(path, default=None):
    try:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    except:
        pass
    return default if default is not None else {}

def save_json(path, data):
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

def load_messages():
    msgs = load_json(MESSAGES_FILE, [])
    if not msgs:
        msgs = [
            {"id": "1", "username": "Astra", "text": "Welcome to ChatVerse! 🌟", "timestamp": (datetime.now().isoformat())},
            {"id": "2", "username": "Nebula", "text": "Hey everyone! 👋", "timestamp": (datetime.now().isoformat())}
        ]
        save_json(MESSAGES_FILE, msgs)
    return msgs

def save_messages():
    save_json(MESSAGES_FILE, st.session_state.messages)

def load_session():
    return load_json(SESSION_FILE, {}).get("username")

def save_session(username=None):
    if username:
        save_json(SESSION_FILE, {"username": username})
    else:
        save_json(SESSION_FILE, {})

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = load_messages()
if 'authenticated' not in st.session_state:
    saved_user = load_session()
    if saved_user:
        st.session_state.authenticated = True
        st.session_state.username = saved_user
    else:
        st.session_state.authenticated = False
        st.session_state.username = ""
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

# Auth functions
def sign_up(username, password, confirm):
    if not username or not password:
        return False, "Please fill all fields"
    if password != confirm:
        return False, "Passwords do not match"
    
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = hash_password(password)
    save_users(users)
    return True, "Account created! Please sign in."

def sign_in(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        st.session_state.authenticated = True
        st.session_state.username = username
        save_session(username)
        return True, "Signed in!"
    return False, "Invalid username or password"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = ""
    save_session(None)

def send_message(text):
    if not text or not text.strip():
        return
    text = text.strip()
    if len(text) > 300:
        st.warning("Message too long (max 300 chars)")
        return
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": sanitize_html(text),
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.messages.append(msg)
    save_messages()

def clear_chat():
    st.session_state.messages = []
    save_messages()

# Format time
def format_time(ts):
    try:
        t = datetime.fromisoformat(ts)
        now = datetime.now()
        diff = now - t
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        return t.strftime("%b %d")
    except:
        return ""

# Typing indicator logic
def get_typing_users():
    if len(st.session_state.messages) < 2:
        return None
    others = list(set(m["username"] for m in st.session_state.messages 
                     if m["username"] != st.session_state.username))
    if others and random.random() < 0.15:
        return random.choice(others)
    return None

# Main app
st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# Check for new messages from file
latest = load_messages()
if len(latest) > len(st.session_state.messages):
    st.session_state.messages = latest

if not st.session_state.authenticated:
    # Auth UI
    st.markdown("""
    <div class="auth-container">
        <h1 style="text-align:center;margin-bottom:0.5rem;color:white;">💬 ChatVerse</h1>
        <p style="text-align:center;color:#94a3b8;margin-bottom:2rem;">Community Forum</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter password", key="login_pass")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                success, msg = sign_in(username, password)
                if success:
                    st.success(msg)
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error(msg)
    
    with tab2:
        with st.form("signup_form"):
            username = st.text_input("Username", placeholder="Choose username", key="signup_user")
            password = st.text_input("Password", type="password", placeholder="Choose password", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="signup_confirm")
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            if submitted:
                success, msg = sign_up(username, password, confirm)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

else:
    # Chat UI
    online_count = len(set(m["username"] for m in st.session_state.messages)) + 1
    
    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="logo">💬 ChatVerse</div>
            <div class="online-badge">
                <span class="online-dot"></span>
                <span>{online_count} online</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Typing indicator
    typing_user = get_typing_users()
    if typing_user:
        st.markdown(f"""
        <div class="typing-indicator">
            <span>✍️ {sanitize_html(typing_user)}</span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
        """, unsafe_allow_html=True)
    
    # Messages
    st.markdown('<div class="messages-area">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown('<div class="empty">💫 No messages yet. Start the conversation!</div>', unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_own = msg["username"] == st.session_state.username
            avatar = msg["username"][0].upper()
            time_str = format_time(msg.get("timestamp", ""))
            
            st.markdown(f"""
            <div class="message {'own' if is_own else ''}">
                <div class="avatar">{sanitize_html(avatar)}</div>
                <div class="bubble">
                    <div class="name">
                        {sanitize_html(msg['username'])}
                        <span class="time">{time_str}</span>
                    </div>
                    <div class="text">{msg['text']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="user-bar">
        <span class="user-label">👤 {sanitize_html(st.session_state.username)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("message_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            msg = st.text_input(
                "Message",
                placeholder="Type your message...",
                max_chars=300,
                key="msg_input",
                label_visibility="collapsed"
            )
        with col2:
            send_btn = st.form_submit_button("Send", use_container_width=True)
        
        if send_btn and msg and msg.strip():
            send_message(msg)
            st.rerun()
    
    # Clear and sign out buttons
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_btn"):
            clear_chat()
            st.rerun()
    with c2:
        if st.button("🚪 Sign Out", use_container_width=True, key="signout_btn"):
            sign_out()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Auto-refresh every 0.5 seconds
st.session_state.refresh_count += 1
time.sleep(0.5)
st.rerun()
