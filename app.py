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
import base64

# Page config
st.set_page_config(
    page_title="ChatVerse • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize paths
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
SESSION_FILE = DATA_DIR / "session.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Beautiful wallpaper collection
WALLPAPERS = {
    "🌌 Cosmic Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920&q=80",
    "🌊 Ocean Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920&q=80",
    "🏔️ Mountain Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🌸 Cherry Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
    "🌅 Sunset Clouds": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1920&q=80",
    "✨ Abstract Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920&q=80",
}

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
            {"id": "1", "username": "Astra", "text": "Welcome to ChatVerse! 🌟 Feel free to chat and connect with everyone!", "timestamp": datetime.now().isoformat()},
            {"id": "2", "username": "Nebula", "text": "Hey everyone! Love the vibe here. What's everyone up to? ✨", "timestamp": datetime.now().isoformat()}
        ]
        save_json(MESSAGES_FILE, msgs)
    return msgs

def save_messages():
    save_json(MESSAGES_FILE, st.session_state.messages)

def load_session():
    return load_json(SESSION_FILE, {})

def save_session(username=None):
    if username:
        save_json(SESSION_FILE, {"username": username, "wallpaper": st.session_state.get("wallpaper", "🌌 Cosmic Nebula")})
    else:
        save_json(SESSION_FILE, {})

def load_settings():
    return load_json(SETTINGS_FILE, {"wallpaper": "🌌 Cosmic Nebula"})

def save_settings(settings):
    save_json(SETTINGS_FILE, settings)

# Get wallpaper URL
def get_wallpaper():
    wallpaper_name = st.session_state.get("wallpaper", "🌌 Cosmic Nebula")
    return WALLPAPERS.get(wallpaper_name, list(WALLPAPERS.values())[0])

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = load_messages()
if 'authenticated' not in st.session_state:
    saved_session = load_session()
    if saved_session.get("username"):
        st.session_state.authenticated = True
        st.session_state.username = saved_session["username"]
        st.session_state.wallpaper = saved_session.get("wallpaper", "🌌 Cosmic Nebula")
    else:
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.session_state.wallpaper = load_settings().get("wallpaper", "🌌 Cosmic Nebula")
if 'refresh_count' not in st.session_state:
    st.session_state.refresh_count = 0

wallpaper_url = get_wallpaper()

# Custom CSS with wallpaper and VISIBLE text
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .stApp {{
        background-image: url("{wallpaper_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        min-height: 100vh;
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(5px);
        z-index: -1;
    }}
    
    /* Containers */
    .auth-container, .chat-container {{
        width: 100%;
        max-width: 900px;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 2rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.5);
        margin: 1rem auto;
    }}
    
    .chat-container {{
        height: 85vh;
        display: flex;
        flex-direction: column;
        padding: 0;
        overflow: hidden;
    }}
    
    /* Header */
    .chat-header {{
        padding: 1rem 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(0,0,0,0.3);
        flex-shrink: 0;
    }}
    
    .logo {{
        font-size: 1.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #c084fc, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    .online-badge {{
        background: rgba(255,255,255,0.1);
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #e2e8f0;
    }}
    
    .online-dot {{
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        display: inline-block;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    /* Messages - FIXED LAYOUT */
    .messages-area {{
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        min-height: 0;
    }}
    
    .message {{
        display: flex;
        gap: 0.7rem;
        animation: slideIn 0.3s ease;
        align-items: flex-start;
    }}
    
    .message.own {{
        flex-direction: row-reverse;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .avatar {{
        width: 40px;
        height: 40px;
        min-width: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #a78bfa);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        flex-shrink: 0;
        font-size: 0.9rem;
    }}
    
    .message.own .avatar {{
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
    }}
    
    .bubble {{
        max-width: 65%;
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(10px);
        padding: 0.7rem 1rem;
        border-radius: 1rem 1rem 1rem 0.2rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }}
    
    .message.own .bubble {{
        background: rgba(59, 130, 246, 0.3);
        border-color: rgba(59, 130, 246, 0.4);
        border-radius: 1rem 1rem 0.2rem 1rem;
    }}
    
    .name {{
        font-size: 0.75rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.3rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    
    .message.own .name {{
        justify-content: flex-end;
        color: #93c5fd;
    }}
    
    .text {{
        color: #f1f5f9;
        word-wrap: break-word;
        font-size: 0.9rem;
        line-height: 1.4;
    }}
    
    .time {{
        font-size: 0.65rem;
        color: #94a3b8;
        font-weight: 400;
    }}
    
    .empty {{
        text-align: center;
        color: #94a3b8;
        padding: 3rem 2rem;
        font-style: italic;
    }}
    
    /* Typing indicator */
    .typing-indicator {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 1rem;
        padding: 0.5rem 1rem;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        margin: 0 1.5rem;
        color: #cbd5e1;
        font-size: 0.85rem;
    }}
    
    .typing-dot {{
        width: 6px;
        height: 6px;
        background: #c084fc;
        border-radius: 50%;
        display: inline-block;
        animation: bounce 1.4s infinite;
    }}
    
    .typing-dot:nth-child(1) {{ animation-delay: -0.32s; }}
    .typing-dot:nth-child(2) {{ animation-delay: -0.16s; }}
    
    @keyframes bounce {{
        0%, 60%, 100% {{ transform: translateY(0); }}
        30% {{ transform: translateY(-8px); }}
    }}
    
    /* Input area */
    .input-area {{
        padding: 1rem 1.5rem;
        background: rgba(0,0,0,0.4);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        flex-shrink: 0;
    }}
    
    .user-bar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
    }}
    
    .user-label {{
        color: #a5b4fc;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    /* FIXED: Visible text in inputs */
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        padding: 0.7rem 1rem !important;
        border-radius: 2rem !important;
        color: #ffffff !important;
        font-size: 0.9rem !important;
        caret-color: #c084fc !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: rgba(255, 255, 255, 0.5) !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #c084fc !important;
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.3) !important;
        background: rgba(255, 255, 255, 0.18) !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        border-radius: 2rem !important;
        color: white !important;
        cursor: pointer !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.5) !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.08);
        border-radius: 1rem;
        color: #cbd5e1 !important;
        padding: 0.7rem;
        font-weight: 500;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        color: white !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(0,0,0,0.3);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(124, 58, 237, 0.6);
        border-radius: 10px;
    }}
    
    /* Form styling */
    .stForm {{
        border: none !important;
    }}
    
    /* Labels */
    label {{
        color: #cbd5e1 !important;
    }}
    
    /* Sidebar */
    .css-1d391kg, .css-1wrcrro {{
        background: rgba(15, 23, 42, 0.9) !important;
        backdrop-filter: blur(15px) !important;
    }}
    
    /* Markdown text */
    .stMarkdown {{
        color: #e2e8f0 !important;
    }}
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning {{
        background: rgba(0,0,0,0.3) !important;
        backdrop-filter: blur(10px) !important;
    }}
</style>
""", unsafe_allow_html=True)

# Auth functions
def sign_up(username, password, confirm):
    if not username or not password:
        return False, "Please fill all fields"
    if password != confirm:
        return False, "Passwords do not match"
    if len(password) < 4:
        return False, "Password too short (min 4 chars)"
    
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
        return True, f"Welcome back, {username}!"
    return False, "Invalid username or password"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = ""
    save_session(None)

def send_message(text):
    if not text or not text.strip():
        return False
    text = text.strip()
    if len(text) > 300:
        st.warning("Message too long (max 300 chars)")
        return False
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": sanitize_html(text),
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.messages.append(msg)
    save_messages()
    return True

def clear_chat():
    st.session_state.messages = []
    save_messages()

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
        return t.strftime("%b %d, %H:%M")
    except:
        return ""

def get_typing_users():
    if len(st.session_state.messages) < 2:
        return None
    others = list(set(m["username"] for m in st.session_state.messages 
                     if m["username"] != st.session_state.username))
    if others and random.random() < 0.12:
        return random.choice(others)
    return None

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 ChatVerse")
    
    # Wallpaper selector
    st.markdown("### 🖼️ Wallpaper")
    current_wallpaper = st.session_state.get("wallpaper", "🌌 Cosmic Nebula")
    
    wallpaper_options = list(WALLPAPERS.keys())
    selected_wallpaper = st.selectbox(
        "Choose background",
        wallpaper_options,
        index=wallpaper_options.index(current_wallpaper) if current_wallpaper in wallpaper_options else 0,
        label_visibility="collapsed"
    )
    
    if selected_wallpaper != current_wallpaper:
        st.session_state.wallpaper = selected_wallpaper
        settings = load_settings()
        settings["wallpaper"] = selected_wallpaper
        save_settings(settings)
        if st.session_state.authenticated:
            save_session(st.session_state.username)
        st.rerun()
    
    # Preview current wallpaper
    st.image(WALLPAPERS[selected_wallpaper], caption=selected_wallpaper, use_column_width=True)
    
    st.markdown("---")
    
    if st.session_state.authenticated:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
            st.rerun()
    else:
        st.markdown("### 👋 Welcome!")
        st.markdown("Sign in to chat with the community")
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("**ChatVerse** is a beautiful community forum. Choose your wallpaper, sign in, and start chatting! ✨")

# Main app
if not st.session_state.authenticated:
    # Auth UI
    st.markdown("""
    <div class="auth-container">
        <h1 style="text-align:center;margin-bottom:0.5rem;color:white;">💬 ChatVerse</h1>
        <p style="text-align:center;color:#94a3b8;margin-bottom:2rem;">Beautiful Community Forum</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            st.markdown("### Welcome Back")
            username = st.text_input("Username", placeholder="Enter your username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            submitted = st.form_submit_button("Sign In 🔓", use_container_width=True)
            if submitted:
                success, msg = sign_in(username, password)
                if success:
                    st.success(msg)
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
    
    with tab2:
        with st.form("signup_form"):
            st.markdown("### Create Account")
            username = st.text_input("Username", placeholder="Choose a username", key="signup_user")
            password = st.text_input("Password", type="password", placeholder="Create a password (min 4 chars)", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account 🚀", use_container_width=True)
            if submitted:
                success, msg = sign_up(username, password, confirm)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

else:
    # Chat UI
    online_count = max(1, len(set(m["username"] for m in st.session_state.messages)))
    
    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="logo">💬 ChatVerse</div>
            <div class="online-badge">
                <span class="online-dot"></span>
                <span>{online_count} online</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Typing indicator
    typing_user = get_typing_users()
    if typing_user:
        st.markdown(f"""
        <div class="typing-indicator">
            <span>✍️ {sanitize_html(typing_user)} is typing</span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
        """, unsafe_allow_html=True)
    
    # Messages area with proper layout
    st.markdown('<div class="messages-area">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty">
            <div style="font-size:3rem;">🌌</div>
            <div style="margin-top:0.5rem;">No messages yet.</div>
            <div style="font-size:0.85rem;">Start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
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
                placeholder="Type your message here...",
                max_chars=300,
                key="msg_input",
                label_visibility="collapsed"
            )
        with col2:
            send_btn = st.form_submit_button("📤 Send", use_container_width=True)
        
        if send_btn and msg and msg.strip():
            if send_message(msg):
                st.rerun()
    
    # Buttons row
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_btn", help="Clear all messages"):
            clear_chat()
            st.rerun()
    with c2:
        if st.button("🚪 Sign Out", use_container_width=True, key="signout_btn"):
            sign_out()
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Check for new messages from other instances
latest = load_messages()
if len(latest) > len(st.session_state.messages):
    st.session_state.messages = latest

# Auto-refresh
st.session_state.refresh_count += 1
time.sleep(1)
st.rerun()
