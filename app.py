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
if "profile_pics" not in st.session_state:
    st.session_state.profile_pics = {}

# Wallpaper options
wallpapers = {
    "dark": "linear-gradient(145deg, #0f172a 0%, #1e293b 100%)",
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600",
    "mountains": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1600",
    "forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1600",
    "sunset": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1600",
    "ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1600"
}

# Custom CSS with glass morphism
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
        
        /* Chat container */
        .chat-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(18px);
            border-radius: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
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
        
        /* User message styling */
        [data-testid="stChatMessage"][data-testid="stChatMessage"]:has(div[data-testid="stMarkdown"]:first-child) {{
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(96, 165, 250, 0.1)) !important;
            border-color: rgba(59, 130, 246, 0.3) !important;
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
        
        /* Avatar styling */
        .avatar-container {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        
        .avatar-img {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
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
                if username in users and users[username]["password"] == hash_password(password):
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
        st.markdown(f"""
        <div class="online-badge">
            <span class="online-dot"></span>
            <span>Live Chat</span>
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
        
        # Display current profile pic
        col1, col2 = st.columns([1, 2])
        with col1:
            if current_user_data.get("profile_pic"):
                st.image(current_user_data["profile_pic"], width=60, caption="")
            else:
                st.markdown(f"### 🧑\n**{st.session_state.username[0].upper()}**")
        
        with col2:
            st.markdown(f"**@{st.session_state.username}**")
            if current_user_data.get("bio"):
                st.caption(current_user_data["bio"])
        
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
                users_data[st.session_state.username]["profile_pic"] = f"data:image/png;base64,{img_str}"
                save_users(users_data)
                st.success("Profile picture updated!")
                st.rerun()
            
            # Bio
            new_bio = st.text_area("Bio", value=current_user_data.get("bio", ""), 
                                   placeholder="Tell us about yourself...", max_chars=100)
            if st.button("Save Bio"):
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
                unique_users = len(set(msg["username"] for msg in st.session_state.messages))
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
        st.info("✨ Welcome to ChatVerse! A friendly community forum with glass morphism design.")
    
    # Main chat area
    st.markdown("### 💬 Live Chat")
    
    # Reload messages
    st.session_state.messages = load_messages()
    
    # Display messages with glass cards
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            # Get profile pic if exists
            users_data = load_users()
            user_info = users_data.get(msg["username"], {})
            
            if msg["username"] == st.session_state.username:
                with st.chat_message("user"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    if user_info.get("bio"):
                        st.caption(f"📝 {user_info['bio'][:50]}")
                    st.write(msg["text"])
    
    # Message input
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
    
    # Ultra-fast auto-refresh (0.0005 seconds)
    time.sleep(0.0005)
    st.rerun()
