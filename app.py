import streamlit as st
import datetime
import uuid
import hashlib
import json
import os
import time
from PIL import Image
import io
import base64
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
if "typing_users" not in st.session_state:
    st.session_state.typing_users = set()
if "last_typing_time" not in st.session_state:
    st.session_state.last_typing_time = {}

# Wallpaper options
wallpapers = {
    "dark": "linear-gradient(145deg, #0f172a 0%, #1e293b 100%)",
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600",
    "mountains": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1600",
    "forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1600",
    "sunset": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1600",
    "ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1600"
}

# Custom CSS with glass morphism and typing bubble
def get_css():
    if st.session_state.wallpaper == "dark":
        bg = wallpapers["dark"]
    else:
        bg = f"url('{wallpapers[st.session_state.wallpaper]}')"
    
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        .stApp {{
            background: {bg};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            transition: all 0.5s ease;
        }}
        
        /* Glass card effect */
        .glass-card {{
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-radius: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 25px 50px rgba(0,0,0,0.3);
            padding: 1rem;
            margin-bottom: 1rem;
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
        
        /* Typing indicator bubble */
        .typing-indicator {{
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
        
        .typing-dot {{
            width: 8px;
            height: 8px;
            background: #c084fc;
            border-radius: 50%;
            display: inline-block;
            animation: typingAnimation 1.4s infinite ease-in-out;
        }}
        
        .typing-dot:nth-child(1) {{
            animation-delay: -0.32s;
        }}
        
        .typing-dot:nth-child(2) {{
            animation-delay: -0.16s;
        }}
        
        @keyframes typingAnimation {{
            0%, 60%, 100% {{
                transform: translateY(0);
                opacity: 0.4;
            }}
            30% {{
                transform: translateY(-10px);
                opacity: 1;
            }}
        }}
        
        /* Sidebar glass effect */
        [data-testid="stSidebar"] {{
            background: rgba(15, 23, 42, 0.8) !important;
            backdrop-filter: blur(18px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        
        /* Input fields glass effect */
        .stTextInput > div > div > input {{
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 2rem !important;
            color: white !important;
            padding: 0.7rem 1.4rem !important;
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
            box-shadow: 0 8px 18px rgba(124, 58, 237, 0.3) !important;
        }}
        
        .stButton > button:hover {{
            transform: scale(1.02) !important;
            box-shadow: 0 10px 22px rgba(139, 92, 246, 0.5) !important;
        }}
        
        /* Headers */
        h1, h2, h3 {{
            background: linear-gradient(135deg, #c084fc, #a78bfa) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 600 !important;
        }}
        
        /* Text colors */
        .stMarkdown, .stCaption {{
            color: #e2e8f0 !important;
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
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.5; transform: scale(0.8); }}
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 6px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #7c3aed;
            border-radius: 10px;
        }}
        
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
            animation: pulse 1s infinite;
        }}
        
        /* Chat input area */
        .stChatInput > div > div > textarea {{
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 2rem !important;
            color: white !important;
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
                if username in users and users[username].get("password") == hash_password(password):
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
                        users[new_user] = {
                            "password": hash_password(new_pass),
                            "profile_pic": None,
                            "bio": "",
                            "joined": datetime.datetime.now().isoformat()
                        }
                        save_users(users)
                        st.success("Account created! Please sign in.")

else:
    st.markdown(get_css(), unsafe_allow_html=True)
    
    # Header with online badge
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
        
        users_data = load_users()
        current_user_data = users_data.get(st.session_state.username, {})
        
        # Display current profile pic safely
        col1, col2 = st.columns([1, 2])
        with col1:
            profile_pic = current_user_data.get("profile_pic") if current_user_data else None
            if profile_pic and profile_pic != "None":
                try:
                    st.image(profile_pic, width=60, caption="")
                except:
                    st.markdown(f"### 🧑")
            else:
                st.markdown(f"### 🧑")
        
        with col2:
            st.markdown(f"**@{st.session_state.username}**")
            bio = current_user_data.get("bio") if current_user_data else ""
            if bio:
                st.caption(bio[:50])
        
        # Edit profile
        with st.expander("✏️ Edit Profile", expanded=False):
            # Profile picture upload
            uploaded_file = st.file_uploader("Profile Picture", type=['jpg', 'png', 'jpeg'])
            if uploaded_file:
                img = Image.open(uploaded_file)
                img = img.resize((150, 150))
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                profile_pic_data = f"data:image/png;base64,{img_str}"
                
                users_data = load_users()
                if st.session_state.username in users_data:
                    users_data[st.session_state.username]["profile_pic"] = profile_pic_data
                    save_users(users_data)
                    st.success("Profile picture updated!")
                    st.rerun()
            
            # Bio
            current_bio = current_user_data.get("bio") if current_user_data else ""
            new_bio = st.text_area("Bio", value=current_bio, 
                                   placeholder="Tell us about yourself...", max_chars=100)
            if st.button("Save Bio"):
                users_data = load_users()
                if st.session_state.username in users_data:
                    users_data[st.session_state.username]["bio"] = new_bio
                    save_users(users_data)
                    st.success("Bio updated!")
                    st.rerun()
            
            # Change username
            st.markdown("---")
            new_username = st.text_input("Change Username", value=st.session_state.username)
            if new_username != st.session_state.username:
                if st.button("Update Username"):
                    users = load_users()
                    if new_username not in users:
                        users[new_username] = users.pop(st.session_state.username)
                        save_users(users)
                        st.session_state.username = new_username
                        st.success("Username updated!")
                        st.rerun()
                    else:
                        st.error("Username already taken")
        
        st.markdown("---")
        
        # Chat stats
        st.markdown("## 📊 Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        
        try:
            if st.session_state.messages:
                unique_users = len(set(msg.get("username", "") for msg in st.session_state.messages if msg.get("username")))
                st.metric("Community Members", unique_users)
        except:
            pass
        
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
        st.info("✨ Welcome to ChatVerse! A friendly community forum with glass morphism design and live typing indicators!")
    
    # Main chat area
    st.markdown("### 💬 Live Chat")
    
    # Simulate typing indicator
    if random.random() < 0.1 and len(st.session_state.messages) > 0:
        other_users = list(set(msg.get("username", "") for msg in st.session_state.messages if msg.get("username") != st.session_state.username))
        if other_users:
            typing_user = random.choice(other_users)
            st.markdown(f"""
            <div class="typing-indicator">
                <span>💬 {typing_user}</span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span style="font-size: 0.8rem; margin-left: 0.3rem;">typing...</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Reload messages
    st.session_state.messages = load_messages()
    
    # Display messages with glass cards
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            # Get profile pic if exists safely
            users_data = load_users()
            user_info = users_data.get(msg.get("username", ""), {})
            
            if msg.get("username") == st.session_state.username:
                with st.chat_message("user"):
                    st.markdown(f"**{msg.get('username', 'Unknown')}**  `{msg.get('time', '')}`")
                    st.write(msg.get('text', ''))
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{msg.get('username', 'Unknown')}**  `{msg.get('time', '')}`")
                    bio = user_info.get("bio") if user_info else ""
                    if bio:
                        st.caption(f"📝 {bio[:50]}")
                    st.write(msg.get('text', ''))
    
    # Message input with typing detection
    prompt = st.chat_input("Type your message here...")
    
    if prompt:
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": prompt,
            "time": datetime.datetime.now().strftime("%I:%M %p"),
            "timestamp": datetime.datetime.now().isoformat()
        }
        st.session_state.messages.append(new_msg)
        save_messages(st.session_state.messages)
        st.rerun()
    
    # Auto-refresh indicator
    st.markdown('<div class="refresh-indicator">⚡ LIVE • Auto-refreshing</div>', unsafe_allow_html=True)
    
    # Auto-refresh every 0.5 seconds
    time.sleep(0.5)
    st.rerun()
