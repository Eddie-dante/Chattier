import streamlit as st
import json
import os
import html
import hashlib
import pathlib
from datetime import datetime
import uuid
import threading
import time

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="ChatVerse • community forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize paths and directories
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "chat_messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Thread lock for file operations
file_lock = threading.Lock()

# Custom CSS - Modern Forum Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    }
    
    .forum-container {
        width: 100%;
        max-width: 850px;
        height: 85vh;
        max-height: 750px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 2.5rem;
        box-shadow: 0 30px 50px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(255, 255, 255, 0.05);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        color: #e2e8f0;
        margin: 2rem auto;
    }
    
    .forum-header {
        padding: 1.2rem 1.8rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(10px);
        flex-shrink: 0;
    }
    
    .logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .logo-icon {
        font-size: 2rem;
        filter: drop-shadow(0 0 8px #7c3aed);
    }
    
    .logo h1 {
        font-weight: 600;
        font-size: 1.6rem;
        letter-spacing: -0.3px;
        background: linear-gradient(to right, #c084fc, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    
    .online-badge {
        background: rgba(255, 255, 255, 0.08);
        padding: 0.4rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    
    .online-dot {
        width: 10px;
        height: 10px;
        background: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem 1.2rem;
        display: flex;
        flex-direction: column-reverse;
        gap: 0.8rem;
        background: rgba(0, 0, 0, 0.2);
        min-height: 0;
    }
    
    .message-row {
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        animation: fadeInUp 0.3s ease-out;
    }
    
    .message-row.own-message {
        flex-direction: row-reverse;
    }
    
    @keyframes fadeInUp {
        0% {
            opacity: 0;
            transform: translateY(10px);
        }
        100% {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #a78bfa);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 0.9rem;
        color: white;
        box-shadow: 0 8px 15px rgba(124, 58, 237, 0.4);
        flex-shrink: 0;
        text-transform: uppercase;
    }
    
    .own-message .avatar {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        box-shadow: 0 8px 15px rgba(59, 130, 246, 0.5);
    }
    
    .message-bubble {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(5px);
        padding: 0.8rem 1rem;
        border-radius: 1.2rem 1.2rem 1.2rem 0.3rem;
        max-width: 70%;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
        word-wrap: break-word;
    }
    
    .own-message .message-bubble {
        background: rgba(59, 130, 246, 0.2);
        border-radius: 1.2rem 1.2rem 0.3rem 1.2rem;
        border-color: rgba(59, 130, 246, 0.3);
    }
    
    .message-author {
        font-weight: 600;
        font-size: 0.75rem;
        margin-bottom: 0.2rem;
        color: #cbd5e1;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    
    .own-message .message-author {
        color: #93c5fd;
        justify-content: flex-end;
    }
    
    .time-stamp {
        font-weight: 400;
        font-size: 0.65rem;
        color: #94a3b8;
    }
    
    .message-text {
        color: #f1f5f9;
        line-height: 1.4;
        font-size: 0.9rem;
    }
    
    .empty-chat {
        text-align: center;
        color: #64748b;
        margin: auto;
        font-style: italic;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.8rem;
        opacity: 0.8;
    }
    
    .forum-input-area {
        padding: 0.8rem 1.5rem 1rem;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(15px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        flex-shrink: 0;
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 2.5rem !important;
        padding: 0.7rem 1.2rem !important;
        color: #f8fafc !important;
        font-size: 0.9rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #c084fc !important;
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.3) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 44px !important;
        height: 44px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        color: white !important;
        font-size: 1.2rem !important;
        box-shadow: 0 8px 18px rgba(124, 58, 237, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0 !important;
        min-width: 44px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #8b5cf6, #c084fc) !important;
        transform: scale(1.05) !important;
    }
    
    .chat-messages::-webkit-scrollbar {
        width: 5px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 3px;
    }
    
    @media (max-width: 600px) {
        .forum-container {
            height: 90vh;
            border-radius: 1.5rem;
            margin: 0.5rem auto;
        }
        .message-bubble {
            max-width: 80%;
        }
    }
    
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for auto-refresh with practical timing
st.markdown("""
<script>
    // Auto-refresh every 1 second - practical and smooth
    let refreshCount = 0;
    
    function autoRefresh() {
        refreshCount++;
        // Update refresh counter if visible
        const counter = document.getElementById('refresh-count');
        if (counter) {
            counter.textContent = refreshCount;
        }
        
        // Trigger Streamlit rerun by clicking a hidden button
        const refreshBtn = window.parent.document.querySelector('[data-testid="stNotification"]');
        if (!document.hidden) {
            // Use Streamlit's internal rerun mechanism
            window.location.reload = null; // Prevent full page reload
        }
    }
    
    // Set refresh interval to 1 second for smooth operation
    setInterval(function() {
        // Find and click Streamlit's rerun button if it exists
        const rerunButton = window.parent.document.querySelector('button[kind="secondary"]');
        if (rerunButton && !document.querySelector('input:focus')) {
            // Don't auto-rerun, use Streamlit's auto-refresh instead
        }
    }, 1000);
</script>
""", unsafe_allow_html=True)

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_text(text):
    return html.escape(text)

def format_time(timestamp_str):
    try:
        msg_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        diff = now - msg_time
        
        if diff.days == 0:
            if diff.seconds < 60:
                return "Just now"
            elif diff.seconds < 3600:
                return f"{diff.seconds // 60}m ago"
            else:
                return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1:
            return "Yesterday"
        else:
            return msg_time.strftime("%b %d")
    except:
        return "Unknown"

def load_json_file(file_path, default=None):
    try:
        if file_path.exists():
            with file_lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
    except:
        pass
    return default if default is not None else []

def save_json_file(file_path, data):
    try:
        with file_lock:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def load_users():
    return load_json_file(USERS_FILE, {})

def save_users(users):
    return save_json_file(USERS_FILE, users)

def load_profiles():
    return load_json_file(PROFILES_FILE, {})

def save_profiles(profiles):
    return save_json_file(PROFILES_FILE, profiles)

def load_messages():
    messages = load_json_file(MESSAGES_FILE, [])
    if not messages:
        messages = [
            {
                "id": "1",
                "username": "Astra",
                "text": "Welcome to ChatVerse! 🌟 This is a live forum. Feel free to chat.",
                "timestamp": datetime.now().isoformat(),
                "reactions": {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []}
            },
            {
                "id": "2",
                "username": "Nebula",
                "text": "Hey everyone! Love the vibe here. What's everyone up to? ✨",
                "timestamp": datetime.now().isoformat(),
                "reactions": {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []}
            }
        ]
        save_json_file(MESSAGES_FILE, messages)
    return messages

def save_messages():
    return save_json_file(MESSAGES_FILE, st.session_state.messages)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = load_messages()
if 'username' not in st.session_state:
    st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'show_auth' not in st.session_state:
    st.session_state.show_auth = False
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = "signin"
if 'message_count' not in st.session_state:
    st.session_state.message_count = len(st.session_state.messages)

# Check for new messages (load from file)
current_messages = load_messages()
if len(current_messages) > len(st.session_state.messages):
    st.session_state.messages = current_messages
    st.session_state.message_count = len(current_messages)

def sign_up(email, username, password):
    users = load_users()
    profiles = load_profiles()
    
    if username in users:
        return False, "Username already exists"
    
    if any(u.get('email') == email for u in users.values()):
        return False, "Email already registered"
    
    users[username] = {
        "email": email,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    
    profiles[username] = {
        "bio": "",
        "avatar_url": None,
        "joined_date": datetime.now().isoformat()
    }
    
    if save_users(users) and save_profiles(profiles):
        return True, "Account created successfully!"
    return False, "Failed to create account"

def sign_in(username, password):
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    if users[username]["password"] != hash_password(password):
        return False, "Incorrect password"
    
    return True, "Signed in successfully!"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]
    st.session_state.user_email = ""
    st.session_state.show_auth = False

def add_message(message_text):
    if not message_text or not message_text.strip():
        return False
    
    message_text = message_text.strip()
    
    if len(message_text) > 350:
        st.warning("Message too long (max 350 characters)")
        return False
    
    new_msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": sanitize_text(message_text),
        "timestamp": datetime.now().isoformat(),
        "reactions": {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []}
    }
    st.session_state.messages.append(new_msg)
    st.session_state.message_count = len(st.session_state.messages)
    save_messages()
    return True

# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ ChatVerse")
    
    # Auto-refresh with practical timing
    st.markdown("### 🔄 Live Updates")
    auto_refresh = st.checkbox("Auto-refresh", value=True, help="Refresh every 2 seconds")
    
    if auto_refresh:
        st.success("🟢 Live • 2s")
        st.caption(f"Messages: {st.session_state.message_count}")
    
    st.markdown("---")
    
    if not st.session_state.authenticated:
        st.markdown("### 👋 Welcome!")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Sign In", use_container_width=True):
                st.session_state.show_auth = True
                st.session_state.auth_mode = "signin"
                st.rerun()
        with col2:
            if st.button("✨ Sign Up", use_container_width=True):
                st.session_state.show_auth = True
                st.session_state.auth_mode = "signup"
                st.rerun()
    else:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
            st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("**ChatVerse** • Modern community forum with live updates ✨")

# Main layout
col1, col2, col3 = st.columns([1, 3, 1])

with col2:
    # Forum Container
    st.markdown('<div class="forum-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="forum-header">
        <div class="logo">
            <span class="logo-icon">💬</span>
            <h1>ChatVerse</h1>
        </div>
        <div class="online-badge">
            <span class="online-dot"></span>
            <span>Live</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auth modal
    if st.session_state.show_auth:
        st.markdown("---")
        if st.session_state.auth_mode == "signin":
            st.markdown("### 🔑 Sign In")
            with st.form("signin_form"):
                username = st.text_input("Username", key="signin_username")
                password = st.text_input("Password", type="password", key="signin_password")
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Sign In", use_container_width=True)
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_auth = False
                        st.rerun()
                
                if submitted:
                    if username and password:
                        success, message = sign_in(username, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.username = username
                            users = load_users()
                            st.session_state.user_email = users[username].get('email', '')
                            st.session_state.show_auth = False
                            st.success(message)
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please fill in all fields")
        
        elif st.session_state.auth_mode == "signup":
            st.markdown("### ✨ Create Account")
            with st.form("signup_form"):
                email = st.text_input("Email", key="signup_email")
                username = st.text_input("Username", key="signup_username")
                password = st.text_input("Password", type="password", key="signup_password")
                confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
                col1, col2 = st.columns(2)
                with col1:
                    submitted = st.form_submit_button("Sign Up", use_container_width=True)
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_auth = False
                        st.rerun()
                
                if submitted:
                    if email and username and password:
                        if password != confirm:
                            st.error("Passwords don't match")
                        elif len(password) < 6:
                            st.error("Password must be at least 6 characters")
                        elif len(username) < 3:
                            st.error("Username must be at least 3 characters")
                        else:
                            success, message = sign_up(email, username, password)
                            if success:
                                st.success(message)
                                time.sleep(0.5)
                                st.session_state.show_auth = False
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("Please fill in all fields")
        st.markdown("---")
    
    # Chat Messages Area
    st.markdown('<div class="chat-messages" id="chat-messages">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-chat">
            <span style="font-size:2.5rem;">🌌</span>
            <span>No messages yet. Start the conversation!</span>
            <span style="font-size:0.8rem;">Be friendly ✨</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display newest first
        for msg in reversed(st.session_state.messages):
            is_own = msg['username'] == st.session_state.username
            avatar_letter = msg['username'][0].upper() if msg['username'] else "?"
            time_str = format_time(msg['timestamp'])
            
            message_html = f"""
            <div class="message-row {'own-message' if is_own else ''}">
                <div class="avatar">{avatar_letter}</div>
                <div class="message-bubble">
                    <div class="message-author">
                        {sanitize_text(msg['username'])}
                        <span class="time-stamp">{time_str}</span>
                    </div>
                    <div class="message-text">{msg['text']}</div>
                </div>
            </div>
            """
            st.markdown(message_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input Area
    st.markdown('<div class="forum-input-area">', unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        new_username = st.text_input(
            "Your name",
            value=st.session_state.username.replace("Guest_", ""),
            max_chars=18,
            placeholder="e.g. Nova",
            key="username_input",
            label_visibility="collapsed"
        )
        if new_username and new_username != st.session_state.username.replace("Guest_", ""):
            st.session_state.username = new_username if new_username else st.session_state.username
            st.rerun()
    
    with st.form(key="message_form", clear_on_submit=True):
        msg_col1, msg_col2 = st.columns([5, 1])
        with msg_col1:
            message = st.text_input(
                "Message",
                placeholder="Write your message...",
                max_chars=350,
                key="message_input",
                label_visibility="collapsed"
            )
        with msg_col2:
            submitted = st.form_submit_button("▶", use_container_width=True)
        
        if submitted and message and message.strip():
            if add_message(message):
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Practical auto-refresh using Streamlit's native mechanism
if auto_refresh:
    time.sleep(2)  # Refresh every 2 seconds - practical and smooth
    st.rerun()
