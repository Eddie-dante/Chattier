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
if "wallpaper" not in st.session_state:
    st.session_state.wallpaper = "beach"
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Wallpaper options
wallpapers = {
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600",
    "mountains": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1600",
    "forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1600",
    "sunset": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1600",
    "ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1600",
    "garden": "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1600",
    "city": "https://images.unsplash.com/photo-1444723121867-7a241cacace9?w=1600",
    "stars": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1600"
}

# Custom CSS with dynamic wallpaper
st.markdown(f"""
<style>
    .stApp {{
        background-image: url('{wallpapers[st.session_state.wallpaper]}');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        transition: background-image 0.5s ease;
    }}
    
    .stApp > header {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }}
    
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }}
    
    [data-testid="stChatMessage"] {{
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 10px;
        margin: 10px 0;
        animation: fadeIn 0.3s ease-in;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    [data-testid="stSidebar"] {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }}
    
    h1, h2, h3 {{
        color: #1a1a2e !important;
    }}
    
    .stMarkdown {{
        color: #1a1a2e;
    }}
    
    /* Auto-refresh indicator */
    .refresh-indicator {{
        position: fixed;
        bottom: 10px;
        right: 10px;
        background: rgba(0,0,0,0.7);
        color: #10b981;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: bold;
        z-index: 999;
        animation: pulse 1s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
    }}
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
    # Main chat
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("💬 ChatVerse")
    with col2:
        st.markdown(f"**Welcome, {st.session_state.username}** 👋")
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
        st.markdown("### 🖼️ Change Wallpaper")
        selected_wallpaper = st.selectbox(
            "Choose theme",
            options=list(wallpapers.keys()),
            format_func=lambda x: x.title(),
            index=list(wallpapers.keys()).index(st.session_state.wallpaper)
        )
        if selected_wallpaper != st.session_state.wallpaper:
            st.session_state.wallpaper = selected_wallpaper
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("## 👤 My Profile")
        
        # Edit profile section
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
                if users[st.session_state.username] == hash_password(old_pass):
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
        st.markdown("## 📊 Chat Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        
        try:
            if st.session_state.messages:
                unique_users = len(set(msg["username"] for msg in st.session_state.messages))
                st.metric("Community Members", unique_users)
        except:
            pass
        
        st.markdown("---")
        
        # Clear chat button
        if st.button("🗑️ Clear All Messages", use_container_width=True):
            confirm = st.checkbox("⚠️ Confirm delete all messages?")
            if confirm:
                st.session_state.messages = []
                save_messages(st.session_state.messages)
                st.success("Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎨 About")
        st.info("✨ Welcome to ChatVerse! A bright, friendly community forum where everyone can connect.")
    
    # Display messages
    st.markdown("### 💬 Live Chat")
    
    # Reload messages from file to show new ones
    st.session_state.messages = load_messages()
    
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            if msg["username"] == st.session_state.username:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
            else:
                with st.chat_message("assistant", avatar="💬"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
    
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
    
    # SUPER FAST AUTO-REFRESH (0.0005 seconds = 2000 times per second)
    # Refresh indicator
    st.markdown('<div class="refresh-indicator">⚡ LIVE • Auto-refreshing</div>', unsafe_allow_html=True)
    
    # Ultra-fast auto-refresh
    time.sleep(0.0005)  # 0.5 milliseconds refresh
    st.rerun()
