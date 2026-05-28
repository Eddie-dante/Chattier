import streamlit as st
import datetime
import uuid
import hashlib
import json
import os
import time

st.set_page_config(page_title="ChatVerse", page_icon="💬", layout="wide")

# File storage
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = load_messages()

# Custom CSS for glass morphism
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Glass card effect for all text */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(18px) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 1rem !important;
        margin-bottom: 1rem !important;
        animation: fadeIn 0.3s ease-out !important;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Sidebar glass */
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(18px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Input glass */
    .stTextInput > div > div > input, .stChatInput > div > div > textarea {
        background: rgba(255, 255, 255, 0.07) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 2rem !important;
        color: white !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        border-radius: 2rem !important;
        color: white !important;
        font-weight: 600 !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.02) !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(135deg, #c084fc, #a78bfa) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    /* Typing bubble */
    .typing-bubble {
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
    
    .dot {
        width: 6px;
        height: 6px;
        background: #c084fc;
        border-radius: 50%;
        display: inline-block;
        animation: bounce 1.4s infinite;
    }
    
    .dot:nth-child(1) { animation-delay: -0.32s; }
    .dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-8px); }
    }
    
    /* Online badge */
    .online-badge {
        background: rgba(255,255,255,0.08);
        padding: 0.3rem 0.8rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        display: inline-flex;
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
    
    /* Live indicator */
    .live-indicator {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(124, 58, 237, 0.8);
        backdrop-filter: blur(10px);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        color: white;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.logged_in:
    st.title("💬 ChatVerse")
    st.markdown("### Welcome to the Community Forum")
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                users = load_users()
                if username in users and users[username] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("signup"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
            if submitted:
                if not new_user or not new_pass:
                    st.error("Fill all fields")
                elif new_pass != confirm:
                    st.error("Passwords don't match")
                else:
                    users = load_users()
                    if new_user in users:
                        st.error("Username already exists")
                    else:
                        users[new_user] = hash_password(new_pass)
                        save_users(users)
                        st.success("Account created! Please sign in.")

else:
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("💬 ChatVerse")
    with col2:
        online_count = len(set(msg.get("username", "") for msg in st.session_state.messages)) + 1
        st.markdown(f"""
        <div class="online-badge">
            <span class="online-dot"></span>
            <span>{online_count} online</span>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown(f"## 👤 {st.session_state.username}")
        st.markdown("---")
        st.markdown("## 📊 Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        
        if st.session_state.messages:
            unique_users = len(set(msg.get("username", "") for msg in st.session_state.messages))
            st.metric("Community Members", unique_users)
        
        st.markdown("---")
        
        if st.button("🗑️ Clear All Messages", use_container_width=True):
            if st.checkbox("Confirm delete all messages?"):
                st.session_state.messages = []
                save_messages(st.session_state.messages)
                st.success("Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        st.info("✨ Glass morphism design • Live chat")
    
    # Main chat
    st.markdown("### 💬 Live Chat")
    
    # Typing indicator (random for fun)
    import random
    if random.random() < 0.1 and len(st.session_state.messages) > 2:
        other_users = list(set(msg.get("username", "") for msg in st.session_state.messages if msg.get("username") != st.session_state.username))
        if other_users:
            typing_user = random.choice(other_users)
            st.markdown(f"""
            <div class="typing-bubble">
                <span>✍️ {typing_user}</span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
            """, unsafe_allow_html=True)
    
    # Reload messages
    st.session_state.messages = load_messages()
    
    # Display messages
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            if msg.get("username") == st.session_state.username:
                with st.chat_message("user"):
                    st.markdown(f"**{msg.get('username')}**  `{msg.get('time')}`")
                    st.write(msg.get('text'))
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{msg.get('username')}**  `{msg.get('time')}`")
                    st.write(msg.get('text'))
    
    # Message input
    prompt = st.chat_input("Type your message here...")
    
    if prompt:
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": prompt,
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
        st.session_state.messages.append(new_msg)
        save_messages(st.session_state.messages)
        st.rerun()
    
    # Live indicator
    st.markdown('<div class="live-indicator">⚡ LIVE</div>', unsafe_allow_html=True)
    
    # Auto-refresh
    time.sleep(0.5)
    st.rerun()
