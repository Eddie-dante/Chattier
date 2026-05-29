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
from PIL import Image
import io

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
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

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
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default if default is not None else {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Save error: {e}")

# User management
def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

# Profile management
def load_profiles():
    return load_json(PROFILES_FILE, {})

def save_profiles(profiles):
    save_json(PROFILES_FILE, profiles)

def get_user_profile(username):
    profiles = load_profiles()
    return profiles.get(username, {"bio": "", "avatar": None, "wallpaper": "🌌 Cosmic Nebula"})

def update_profile(username, bio, avatar_file, wallpaper):
    profiles = load_profiles()
    if username not in profiles:
        profiles[username] = {}
    
    profiles[username]["bio"] = sanitize_html(bio) if bio else ""
    profiles[username]["wallpaper"] = wallpaper
    
    if avatar_file:
        try:
            image = Image.open(avatar_file)
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            avatar_path = UPLOADS_DIR / f"{username}_avatar.png"
            image.save(avatar_path, "PNG")
            profiles[username]["avatar"] = str(avatar_path)
        except Exception as e:
            st.error(f"Avatar error: {e}")
    
    save_profiles(profiles)

def get_avatar_html(username, size=40):
    profiles = load_profiles()
    profile = profiles.get(username, {})
    avatar_path = profile.get("avatar")
    
    if avatar_path and os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            avatar_bytes = f.read()
        avatar_b64 = base64.b64encode(avatar_bytes).decode()
        return f'<img src="data:image/png;base64,{avatar_b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
    else:
        letter = username[0].upper() if username else "?"
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#a78bfa);display:flex;align-items:center;justify-content:center;font-weight:bold;color:white;font-size:{size*0.4}px;">{letter}</div>'

# Messages management
def load_messages():
    return load_json(MESSAGES_FILE, [])

def save_messages():
    save_json(MESSAGES_FILE, st.session_state.messages)

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

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = load_messages()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""
if 'show_profile' not in st.session_state:
    st.session_state.show_profile = False
if 'wallpaper' not in st.session_state:
    st.session_state.wallpaper = "🌌 Cosmic Nebula"
if 'last_message_count' not in st.session_state:
    st.session_state.last_message_count = len(st.session_state.messages)

# Load user's wallpaper preference
if st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile.get("wallpaper", "🌌 Cosmic Nebula")

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, list(WALLPAPERS.values())[0])

# Custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .stApp {{
        background-image: url("{wallpaper_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(15, 23, 42, 0.78);
        backdrop-filter: blur(8px);
        z-index: -1;
    }}
    
    .chat-wrapper {{
        max-width: 850px;
        margin: 1rem auto;
        height: 90vh;
        display: flex;
        flex-direction: column;
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        box-shadow: 0 25px 60px rgba(0,0,0,0.5);
        overflow: hidden;
    }}
    
    .chat-header {{
        padding: 1rem 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(0,0,0,0.25);
        flex-shrink: 0;
    }}
    
    .logo {{
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #c084fc, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    .online-badge {{
        background: rgba(255,255,255,0.08);
        padding: 0.35rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #e2e8f0;
        border: 1px solid rgba(255,255,255,0.1);
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
        0%, 100% {{ opacity: 1; box-shadow: 0 0 6px #10b981; }}
        50% {{ opacity: 0.4; box-shadow: 0 0 2px #10b981; }}
    }}
    
    .messages-container {{
        flex: 1;
        overflow-y: auto;
        padding: 1.2rem;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        min-height: 0;
    }}
    
    .message-row {{
        display: flex;
        gap: 0.7rem;
        animation: slideIn 0.3s ease;
        align-items: flex-start;
        width: 100%;
    }}
    
    .message-row.own {{
        flex-direction: row-reverse;
    }}
    
    @keyframes slideIn {{
        from {{ opacity: 0; transform: translateY(8px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .msg-avatar {{
        flex-shrink: 0;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        overflow: hidden;
    }}
    
    .msg-bubble {{
        max-width: 62%;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 0.65rem 1rem;
        border-radius: 1rem 1rem 1rem 0.2rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
    }}
    
    .message-row.own .msg-bubble {{
        background: rgba(59, 130, 246, 0.28);
        border-color: rgba(59, 130, 246, 0.35);
        border-radius: 1rem 1rem 0.2rem 1rem;
    }}
    
    .msg-name {{
        font-size: 0.75rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    
    .message-row.own .msg-name {{
        justify-content: flex-end;
        color: #93c5fd;
    }}
    
    .msg-time {{
        font-size: 0.65rem;
        color: #94a3b8;
        font-weight: 400;
    }}
    
    .msg-text {{
        color: #f1f5f9;
        word-wrap: break-word;
        font-size: 0.9rem;
        line-height: 1.45;
    }}
    
    .empty-chat {{
        text-align: center;
        color: #94a3b8;
        padding: 3rem 2rem;
        margin: auto;
    }}
    
    .input-area {{
        padding: 0.9rem 1.5rem;
        background: rgba(0,0,0,0.35);
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        flex-shrink: 0;
    }}
    
    .user-info {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        color: #a5b4fc;
        font-size: 0.85rem;
        font-weight: 500;
    }}
    
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.13) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        padding: 0.7rem 1.1rem !important;
        border-radius: 2rem !important;
        color: #ffffff !important;
        font-size: 0.9rem !important;
        caret-color: #c084fc !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: rgba(255, 255, 255, 0.45) !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #c084fc !important;
        box-shadow: 0 0 18px rgba(192, 132, 252, 0.3) !important;
        background: rgba(255, 255, 255, 0.18) !important;
    }}
    
    .stButton > button {{
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        border: none !important;
        padding: 0.5rem 1.2rem !important;
        border-radius: 2rem !important;
        color: white !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    
    .stButton > button:hover {{
        transform: scale(1.04) !important;
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.45) !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.8rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.06);
        border-radius: 1rem;
        color: #cbd5e1 !important;
        padding: 0.6rem 1rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #7c3aed, #a855f7) !important;
        color: white !important;
    }}
    
    ::-webkit-scrollbar {{ width: 5px; }}
    ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.2); }}
    ::-webkit-scrollbar-thumb {{ background: rgba(124, 58, 237, 0.5); border-radius: 10px; }}
    
    .stForm {{ border: none !important; }}
    label {{ color: #cbd5e1 !important; }}
    
    .profile-container {{
        max-width: 600px;
        margin: 2rem auto;
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 2rem;
        padding: 2rem;
        border: 1px solid rgba(255,255,255,0.12);
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
    if len(username) < 2:
        return False, "Username too short"
    
    users = load_users()
    if username in users:
        return False, "Username already exists"
    
    users[username] = hash_password(password)
    save_users(users)
    
    # Create default profile
    profiles = load_profiles()
    profiles[username] = {"bio": "", "avatar": None, "wallpaper": "🌌 Cosmic Nebula"}
    save_profiles(profiles)
    
    return True, "Account created! Please sign in."

def sign_in(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        st.session_state.authenticated = True
        st.session_state.username = username
        profile = get_user_profile(username)
        st.session_state.wallpaper = profile.get("wallpaper", "🌌 Cosmic Nebula")
        return True, f"Welcome back, {username}!"
    return False, "Invalid username or password"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.show_profile = False

def send_message(text):
    if not text or not text.strip():
        return False
    text = text.strip()
    if len(text) > 500:
        st.warning("Message too long (max 500 chars)")
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

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 ChatVerse")
    
    if not st.session_state.authenticated:
        st.markdown("### 👋 Welcome!")
        st.markdown("Sign in to chat and customize your experience")
        st.markdown("---")
    
    # Wallpaper selector
    st.markdown("### 🖼️ Wallpaper")
    current_wp = st.session_state.get("wallpaper", "🌌 Cosmic Nebula")
    wp_list = list(WALLPAPERS.keys())
    
    selected_wp = st.selectbox(
        "Background",
        wp_list,
        index=wp_list.index(current_wp) if current_wp in wp_list else 0,
        label_visibility="collapsed"
    )
    
    if selected_wp != current_wp:
        st.session_state.wallpaper = selected_wp
        if st.session_state.authenticated:
            profile = get_user_profile(st.session_state.username)
            profile["wallpaper"] = selected_wp
            profiles = load_profiles()
            profiles[st.session_state.username] = profile
            save_profiles(profiles)
        st.rerun()
    
    if st.session_state.authenticated:
        st.markdown("---")
        st.markdown(f"### 👤 {st.session_state.username}")
        
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.session_state.show_profile = True
            st.rerun()
        
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    st.metric("Messages", len(st.session_state.messages))
    if st.session_state.messages:
        users = len(set(m["username"] for m in st.session_state.messages))
        st.metric("Participants", users)

# Profile page
if st.session_state.show_profile and st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    
    st.markdown('<div class="profile-container">', unsafe_allow_html=True)
    st.markdown(f"## ✏️ Edit Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Profile Picture")
        avatar_html = get_avatar_html(st.session_state.username, 150)
        st.markdown(avatar_html, unsafe_allow_html=True)
        
        avatar_file = st.file_uploader("Upload picture", type=['png', 'jpg', 'jpeg'], key="avatar_upload")
    
    with col2:
        with st.form("profile_form"):
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200, 
                             placeholder="Tell us about yourself...", height=100)
            
            wallpaper_choice = st.selectbox("Default Wallpaper", list(WALLPAPERS.keys()),
                                          index=list(WALLPAPERS.keys()).index(
                                              profile.get("wallpaper", "🌌 Cosmic Nebula")))
            
            col_a, col_b = st.columns(2)
            with col_a:
                save_btn = st.form_submit_button("💾 Save", use_container_width=True)
            with col_b:
                cancel_btn = st.form_submit_button("↩️ Back", use_container_width=True)
            
            if save_btn:
                update_profile(st.session_state.username, bio, avatar_file, wallpaper_choice)
                st.session_state.wallpaper = wallpaper_choice
                st.success("Profile updated!")
                time.sleep(0.5)
                st.session_state.show_profile = False
                st.rerun()
            
            if cancel_btn:
                st.session_state.show_profile = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Auth page
elif not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width:500px;margin:3rem auto;background:rgba(30,41,59,0.7);backdrop-filter:blur(20px);border-radius:2rem;padding:2rem;border:1px solid rgba(255,255,255,0.12);">
        <h1 style="text-align:center;color:white;margin-bottom:0.5rem;">💬 ChatVerse</h1>
        <p style="text-align:center;color:#94a3b8;margin-bottom:2rem;">Community Forum</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_pass")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
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
            username = st.text_input("Username", placeholder="Choose a username", key="signup_user")
            password = st.text_input("Password", type="password", placeholder="Create password (min 4 chars)", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                success, msg = sign_up(username, password, confirm)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# Main chat
else:
    # Check for real new messages
    latest_msgs = load_messages()
    if len(latest_msgs) > len(st.session_state.messages):
        st.session_state.messages = latest_msgs
    
    online_count = max(1, len(set(m["username"] for m in st.session_state.messages[-50:])))
    
    # Chat wrapper
    st.markdown(f"""
    <div class="chat-wrapper">
        <div class="chat-header">
            <div class="logo">💬 ChatVerse</div>
            <div class="online-badge">
                <span class="online-dot"></span>
                <span>{online_count} active</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Messages area
    st.markdown('<div class="messages-container" id="msg-container">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-chat">
            <div style="font-size:3rem;">💫</div>
            <div style="margin-top:0.5rem;font-size:1.1rem;">No messages yet</div>
            <div style="font-size:0.85rem;opacity:0.8;">Be the first to start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_own = msg["username"] == st.session_state.username
            time_str = format_time(msg.get("timestamp", ""))
            avatar_html = get_avatar_html(msg["username"], 40)
            
            st.markdown(f"""
            <div class="message-row {'own' if is_own else ''}">
                <div class="msg-avatar">{avatar_html}</div>
                <div class="msg-bubble">
                    <div class="msg-name">
                        {sanitize_html(msg['username'])}
                        <span class="msg-time">{time_str}</span>
                    </div>
                    <div class="msg-text">{msg['text']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="user-info">
        <span>👤 {sanitize_html(st.session_state.username)}</span>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("msg_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            msg_text = st.text_input(
                "Message",
                placeholder="Type your message here...",
                max_chars=500,
                key="msg_input",
                label_visibility="collapsed"
            )
        with c2:
            sent = st.form_submit_button("📤", use_container_width=True)
        
        if sent and msg_text and msg_text.strip():
            if send_message(msg_text):
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Real-time auto-refresh
time.sleep(1.5)
st.rerun()
