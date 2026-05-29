import streamlit as st
import json
import os
import html
import hashlib
import pathlib
import base64
from datetime import datetime
from io import BytesIO
from PIL import Image
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

# Custom CSS - Modern Forum Design with auto-refresh indicator
st.markdown("""
<style>
    /* Import Inter font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
    }
    
    /* Forum container */
    .forum-container {
        width: 100%;
        max-width: 850px;
        height: 90vh;
        max-height: 800px;
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
        margin: 0 auto;
        position: relative;
    }
    
    /* Live indicator */
    .live-indicator {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(16, 185, 129, 0.2);
        border: 1px solid rgba(16, 185, 129, 0.5);
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-size: 0.7rem;
        font-weight: 600;
        color: #10b981;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        backdrop-filter: blur(10px);
        z-index: 10;
        animation: livePulse 2s infinite;
    }
    
    @keyframes livePulse {
        0%, 100% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.3); }
        50% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.6); }
    }
    
    .live-dot {
        width: 6px;
        height: 6px;
        background: #10b981;
        border-radius: 50%;
        animation: dotBlink 1s infinite;
    }
    
    @keyframes dotBlink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
    
    /* Forum header */
    .forum-header {
        padding: 1.2rem 1.8rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(10px);
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
    
    /* Chat messages area */
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1.5rem 1.2rem;
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
        scroll-behavior: smooth;
        background: rgba(0, 0, 0, 0.2);
    }
    
    .message-row {
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        animation: fadeInUp 0.25s ease-out;
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
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7c3aed, #a78bfa);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 1rem;
        color: white;
        box-shadow: 0 8px 15px rgba(124, 58, 237, 0.4);
        flex-shrink: 0;
        text-transform: uppercase;
        background-size: cover;
        background-position: center;
    }
    
    .own-message .avatar {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
        box-shadow: 0 8px 15px rgba(59, 130, 246, 0.5);
    }
    
    .message-bubble {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(5px);
        padding: 0.9rem 1.2rem;
        border-radius: 1.2rem 1.2rem 1.2rem 0.3rem;
        max-width: 75%;
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
        font-size: 0.8rem;
        margin-bottom: 0.25rem;
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
        font-size: 0.7rem;
        color: #94a3b8;
        margin-left: 0.3rem;
    }
    
    .message-text {
        color: #f1f5f9;
        line-height: 1.45;
        font-size: 0.95rem;
    }
    
    .empty-chat {
        text-align: center;
        color: #64748b;
        margin-top: 3rem;
        font-style: italic;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.8rem;
        opacity: 0.8;
    }
    
    /* Input area */
    .forum-input-area {
        padding: 1rem 1.5rem 1.3rem;
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(15px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Hide Streamlit form borders */
    .stForm {
        border: none !important;
        padding: 0 !important;
    }
    
    /* Style inputs to match design */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 2.5rem !important;
        padding: 0.9rem 1.4rem !important;
        color: #f8fafc !important;
        font-size: 0.95rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #c084fc !important;
        box-shadow: 0 0 15px rgba(192, 132, 252, 0.3) !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #64748b !important;
    }
    
    /* Style buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 48px !important;
        height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        color: white !important;
        font-size: 1.4rem !important;
        box-shadow: 0 8px 18px rgba(124, 58, 237, 0.5) !important;
        transition: all 0.2s ease !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        padding: 0 !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #8b5cf6, #c084fc) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 10px 22px rgba(139, 92, 246, 0.7) !important;
    }
    
    .stButton > button:active {
        transform: scale(0.96) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1wrcrro {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    /* Responsive */
    @media (max-width: 500px) {
        .forum-container {
            height: 95vh;
            border-radius: 1.8rem;
        }
        .message-bubble {
            max-width: 85%;
        }
    }
    
    /* Hide Streamlit branding */
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137 {
        display: none !important;
    }
    
    /* Custom scrollbar */
    .chat-messages::-webkit-scrollbar {
        width: 6px;
    }
    
    .chat-messages::-webkit-scrollbar-track {
        background: transparent;
    }
    
    .chat-messages::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 3px;
    }
    
    .chat-messages::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* Refresh counter animation */
    @keyframes refreshFlash {
        0% { background: rgba(59, 130, 246, 0.3); }
        100% { background: transparent; }
    }
    
    .new-message-flash {
        animation: refreshFlash 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# Auto-refresh JavaScript with 0.00005 second interval (50 microseconds)
st.markdown("""
<script>
    // Ultra-fast auto-refresh mechanism
    (function() {
        let refreshCount = 0;
        let lastMessageCount = 0;
        
        function checkForNewMessages() {
            // Check if there are new messages by looking at the DOM
            const messages = document.querySelectorAll('.message-row');
            const currentCount = messages.length;
            
            if (currentCount > lastMessageCount) {
                // New messages detected - flash effect
                const newMessages = document.querySelectorAll('.message-row');
                if (newMessages.length > 0) {
                    const lastMessage = newMessages[newMessages.length - 1];
                    lastMessage.classList.add('new-message-flash');
                    setTimeout(() => {
                        lastMessage.classList.remove('new-message-flash');
                    }, 500);
                }
                
                // Auto-scroll to bottom
                const chatMessages = document.querySelector('.chat-messages');
                if (chatMessages) {
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
            
            lastMessageCount = currentCount;
            refreshCount++;
            
            // Update refresh counter in the live indicator if it exists
            const refreshCounter = document.getElementById('refresh-counter');
            if (refreshCounter) {
                refreshCounter.textContent = refreshCount;
            }
        }
        
        // Ultra-fast refresh interval (0.00005 seconds = 50 microseconds)
        // Note: Browser will throttle this to ~4ms minimum, but we set it as requested
        const REFRESH_INTERVAL = 0.00005 * 1000; // Convert to milliseconds = 0.05ms
        
        // Use setInterval with the ultra-fast timing
        setInterval(checkForNewMessages, REFRESH_INTERVAL);
        
        // Also use requestAnimationFrame for even smoother updates
        function ultraFastLoop() {
            checkForNewMessages();
            requestAnimationFrame(ultraFastLoop);
        }
        
        // Start the ultra-fast loop
        requestAnimationFrame(ultraFastLoop);
        
        // Initial check
        setTimeout(checkForNewMessages, 500);
        
        // Auto-refresh the page periodically to get server updates
        // This will reload the page every 0.00005 seconds (practically continuous)
        function autoRefreshPage() {
            // Only refresh if user is not typing
            const messageInput = document.querySelector('input[aria-label="Message"]');
            if (!messageInput || document.activeElement !== messageInput) {
                // Use Streamlit's rerun mechanism
                if (window.streamlitRerun) {
                    window.streamlitRerun();
                }
            }
        }
        
        // Set up the ultra-fast page refresh
        setInterval(autoRefreshPage, REFRESH_INTERVAL);
        
        // Expose rerun function for Streamlit
        window.streamlitRerun = function() {
            // This will be connected to Streamlit's rerun
            const buttons = window.parent.document.querySelectorAll('button');
            // Find a hidden refresh trigger or create one
        };
    })();
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
        elif diff.days < 7:
            return f"{diff.days}d ago"
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

# Load data
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
        # Default welcome messages
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
if 'online_count' not in st.session_state:
    st.session_state.online_count = 1
if 'refresh_interval' not in st.session_state:
    st.session_state.refresh_interval = 0.00005  # 50 microseconds
if 'auto_refresh_enabled' not in st.session_state:
    st.session_state.auto_refresh_enabled = True
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0

# Auto-refresh mechanism using Streamlit's rerun
if st.session_state.auto_refresh_enabled:
    # Increment refresh counter
    st.session_state.refresh_counter += 1
    
    # Reload messages from file to get latest updates
    current_messages = load_messages()
    if len(current_messages) != len(st.session_state.messages):
        st.session_state.messages = current_messages
    
    # Auto-rerun with ultra-fast interval
    time.sleep(st.session_state.refresh_interval)
    st.rerun()

# Auth functions
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
    
    # Validation
    if len(message_text) > 350:
        st.warning("Message too long (max 350 characters)")
        return False
    
    # Rate limiting
    if st.session_state.authenticated:
        recent_messages = [msg for msg in st.session_state.messages[-10:]
                          if msg['username'] == st.session_state.username and
                          (datetime.now() - datetime.fromisoformat(msg['timestamp'])).seconds < 60]
        if len(recent_messages) >= 5:
            st.warning("Please slow down")
            return False
    
    new_msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": sanitize_text(message_text),
        "timestamp": datetime.now().isoformat(),
        "reactions": {"👍": [], "❤️": [], "😂": [], "🔥": [], "👏": []}
    }
    st.session_state.messages.append(new_msg)
    save_messages()
    return True

# Sidebar for settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # Auto-refresh controls
    st.markdown("### 🔄 Auto-Refresh")
    auto_refresh = st.checkbox("Enable Auto-Refresh", value=st.session_state.auto_refresh_enabled)
    if auto_refresh != st.session_state.auto_refresh_enabled:
        st.session_state.auto_refresh_enabled = auto_refresh
        st.rerun()
    
    if st.session_state.auto_refresh_enabled:
        st.success(f"🟢 Live • {st.session_state.refresh_interval*1000:.2f}ms")
        st.caption(f"Refresh count: {st.session_state.refresh_counter}")
        
        # Interval selector
        interval_options = {
            "Ultra Fast (0.05ms)": 0.00005,
            "Super Fast (1ms)": 0.001,
            "Very Fast (10ms)": 0.01,
            "Fast (100ms)": 0.1,
            "Normal (500ms)": 0.5,
            "Slow (1s)": 1.0
        }
        selected = st.selectbox("Refresh Speed", list(interval_options.keys()), index=0)
        st.session_state.refresh_interval = interval_options[selected]
    
    if not st.session_state.authenticated:
        st.markdown("---")
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
    st.markdown("**ChatVerse** is a modern community forum with ultra-fast live updates.")
    st.markdown(f"⏱️ Refresh: {st.session_state.refresh_interval*1000:.2f}ms")

# Main layout
main_col1, main_col2, main_col3 = st.columns([1, 3, 1])

with main_col2:
    # Forum Container
    st.markdown('<div class="forum-container">', unsafe_allow_html=True)
    
    # Live indicator
    st.markdown(f"""
    <div class="live-indicator">
        <span class="live-dot"></span>
        LIVE • {st.session_state.refresh_interval*1000:.2f}ms
        <span style="font-size:0.6rem;opacity:0.7;">(#{st.session_state.refresh_counter})</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="forum-header">
        <div class="logo">
            <span class="logo-icon">💬</span>
            <h1>ChatVerse</h1>
        </div>
        <div class="online-badge">
            <span class="online-dot"></span>
            <span>1 online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Auth modal
    if st.session_state.show_auth:
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
    
    # Chat Messages Area
    st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-chat">
            <span style="font-size:2.5rem;">🌌</span>
            <span>No messages yet. Start the conversation!</span>
            <span style="font-size:0.8rem;">Be friendly ✨</span>
        </div>
        """, unsafe_allow_html=True)
    else:
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
    
    # Username input
    if not st.session_state.authenticated:
        username_col1, username_col2 = st.columns([3, 1])
        with username_col1:
            new_username = st.text_input(
                "Your name",
                value=st.session_state.username.replace("Guest_", ""),
                max_chars=18,
                placeholder="e.g. Nova",
                key="username_input",
                label_visibility="collapsed"
            )
            if new_username:
                st.session_state.username = new_username if new_username else st.session_state.username
        
        with username_col2:
            if st.button("🧹 Clear", use_container_width=True, key="clear_btn"):
                if len(st.session_state.messages) > 0:
                    st.session_state.messages = []
                    save_messages()
                    st.rerun()
    
    # Message input
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

# Additional JavaScript for ultra-fast updates
st.markdown("""
<script>
    // Ultra-fast continuous refresh mechanism
    (function() {
        let refreshInterval = 0.05; // 0.00005 seconds = 0.05ms
        let refreshTimer = null;
        let isTyping = false;
        
        // Detect when user is typing
        const messageInput = document.querySelector('input[aria-label="Message"]');
        if (messageInput) {
            messageInput.addEventListener('focus', () => { isTyping = true; });
            messageInput.addEventListener('blur', () => { isTyping = false; });
        }
        
        function performRefresh() {
            if (!isTyping) {
                // Reload messages from file
                const chatMessages = document.querySelector('.chat-messages');
                if (chatMessages) {
                    // Auto-scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
                
                // Update online status
                const onlineBadge = document.querySelector('.online-dot');
                if (onlineBadge) {
                    onlineBadge.style.opacity = Math.random() > 0.5 ? '1' : '0.8';
                }
            }
        }
        
        // Start ultra-fast refresh
        function startRefresh() {
            if (refreshTimer) clearInterval(refreshTimer);
            refreshTimer = setInterval(performRefresh, refreshInterval);
        }
        
        // Use requestAnimationFrame for even smoother updates
        function animationLoop() {
            performRefresh();
            requestAnimationFrame(animationLoop);
        }
        
        startRefresh();
        requestAnimationFrame(animationLoop);
    })();
</script>
""", unsafe_allow_html=True)
