import streamlit as st
import datetime
import uuid
import hashlib
import json
import os
import time
import random

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
if "wallpaper" not in st.session_state:
    st.session_state.wallpaper = "dark"

# Wallpaper options
wallpapers = {
    "dark": "linear-gradient(145deg, #0f172a 0%, #1e293b 100%)",
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600",
    "mountains": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1600",
    "forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1600",
    "sunset": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1600",
    "ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1600"
}

# Custom CSS
def get_css():
    if st.session_state.wallpaper == "dark":
        bg = wallpapers["dark"]
    else:
        bg = f"url('{wallpapers[st.session_state.wallpaper]}')"
    
    return f"""
    <style>
        .stApp {{
            background: {bg};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Glass card effect for all text containers */
        .stChatMessage, .stAlert, .stInfo, .stSuccess, .stWarning, .stError {{
            background: rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(18px) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 1rem !important;
        }}
        
        /* Message bubbles */
        [data-testid="stChatMessage"] {{
            background: rgba(255, 255, 255, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 1.2rem !important;
            padding: 0.9rem 1.2rem !important;
            margin-bottom: 1rem !important;
            animation: fadeInUp 0.3s ease-out !important;
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Typing indicator */
        .typing-bubble {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1.2rem;
            padding: 0.7rem 1.2rem;
            margin-bottom: 1rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            animation: fadeInUp 0.3s ease-out;
        }}
        
        .dot {{
            width: 8px;
            height: 8px;
            background: #c084fc;
            border-radius: 50%;
            display: inline-block;
            animation: bounce 1.4s infinite ease-in-out;
        }}
        
        .dot:nth-child(1) {{ animation-delay: -0.32s; }}
        .dot:nth-child(2) {{ animation-delay: -0.16s; }}
        
        @keyframes bounce {{
            0%, 60%, 100% {{ transform: translateY(0); opacity: 0.4; }}
            30% {{ transform: translateY(-10px); opacity: 1; }}
        }}
        
        /* Sidebar glass */
        [data-testid="stSidebar"] {{
            background: rgba(15, 23, 42, 0.8) !important;
            backdrop-filter: blur(18px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        
        /* Input fields */
        .stTextInput > div > div > input, .stChatInput > div > div > textarea {{
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 2rem !important;
            color: white !important;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: #c084fc !important;
            box-shadow: 0 0 15px rgba(192, 132, 252, 0.3) !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
            border: none !important;
            border-radius: 2rem !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }}
        
        .stButton > button:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 5px 15px rgba(124, 58, 237, 0.4) !important;
        }}
        
        /* Headers */
        h1, h2, h3, .stMarkdown {{
            color: #e2e8f0 !important;
        }}
        
        h1 {{
            background: linear-gradient(135deg, #c084fc, #a78bfa) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }}
        
        /* Online badge */
        .online-badge {{
            background: rgba(255,255,255,0.08);
            padding: 0.3rem 0.8rem;
            border-radius: 2rem;
            font-size: 0.8rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border: 1px solid rgba(255,255,255,0.15);
        }}
        
        .online-dot {{
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); border-radius: 10px; }}
        ::-webkit-scrollbar-thumb {{ background: #7c3aed; border-radius: 10px; }}
        
        /* Refresh indicator */
        .refresh-indicator {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(124, 58, 237, 0.8);
            backdrop-filter: blur(10px);
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            z-index: 999;
        }}
    </style>
    """

# Authentication
if not st.session_state.logged_in:
    st.markdown(get_css(), unsafe_allow_html=True)
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
    st.markdown(get_css(), unsafe_allow_html=True)
    
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
        st.markdown("## 🎨 Customize")
        
        # Wallpaper selector
        st.markdown("### 🖼️ Theme")
        selected_wallpaper = st.selectbox(
            "Choose background",
            options=list(wallpapers.keys()),
            format_func=lambda x: x.title(),
            index=list(wallpapers.keys()).index(st.session_state.wallpaper)
        )
        if selected_wallpaper != st.session_state.wallpaper:
            st.session_state.wallpaper = selected_wallpaper
            st.rerun()
        
        st.markdown("---")
        
        # Profile section
        st.markdown("## 👤 My Profile")
        st.markdown(f"**@{st.session_state.username}**")
        
        # Edit profile
        with st.expander("✏️ Edit Profile", expanded=False):
            # Change username
            new_username = st.text_input("Change Username", value=st.session_state.username)
            if new_username != st.session_state.username:
                if st.button("Update Username"):
                    users = load_users()
                    if new_username not in users:
                        users[new_username] = users.pop(st.session_state.username)
                        save_users(users)
                        st.session_state.username = new_username
                        st.success("Username updated! Please sign in again.")
                        st.session_state.logged_in = False
                        st.rerun()
                    else:
                        st.error("Username already taken")
            
            # Change password
            st.markdown("---")
            st.markdown("#### Change Password")
            old_pass = st.text_input("Current Password", type="password", key="old")
            new_pass = st.text_input("New Password", type="password", key="new")
            confirm_pass = st.text_input("Confirm New Password", type="password", key="confirm")
            
            if st.button("Update Password"):
                users = load_users()
                if st.session_state.username in users and users[st.session_state.username] == hash_password(old_pass):
                    if new_pass == confirm_pass:
                        users[st.session_state.username] = hash_password(new_pass)
                        save_users(users)
                        st.success("Password updated! Please sign in again.")
                        st.session_state.logged_in = False
                        st.rerun()
                    else:
                        st.error("New passwords don't match")
                else:
                    st.error("Current password is incorrect")
        
        st.markdown("---")
        
        # Chat stats
        st.markdown("## 📊 Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        
        if st.session_state.messages:
            unique_users = len(set(msg.get("username", "") for msg in st.session_state.messages))
            st.metric("Community Members", unique_users)
        
        st.markdown("---")
        
        # Clear chat
        if st.button("🗑️ Clear All Messages", use_container_width=True):
            confirm = st.checkbox("⚠️ Confirm delete all messages?")
            if confirm:
                st.session_state.messages = []
                save_messages(st.session_state.messages)
                st.success("Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        st.info("✨ Glass morphism design • Live chat • Community forum")
    
    # Main chat area
    st.markdown("### 💬 Live Chat")
    
    # Random typing indicator (for fun)
    if random.random() < 0.15 and len(st.session_state.messages) > 3:
        other_users = list(set(msg.get("username", "") for msg in st.session_state.messages if msg.get("username") != st.session_state.username))
        if other_users:
            typing_user = random.choice(other_users)
            st.markdown(f"""
            <div class="typing-bubble">
                <span>✍️ {typing_user}</span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
                <span style="font-size: 0.75rem; margin-left: 0.3rem;">typing...</span>
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
                    st.markdown(f"**{msg.get('username', 'Unknown')}**  `{msg.get('time', '')}`")
                    st.write(msg.get('text', ''))
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{msg.get('username', 'Unknown')}**  `{msg.get('time', '')}`")
                    st.write(msg.get('text', ''))
    
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
    st.markdown('<div class="refresh-indicator">⚡ LIVE</div>', unsafe_allow_html=True)
    
    # Auto-refresh every 1 second
    time.sleep(1)
    st.rerun()
