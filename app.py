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

# Page config MUST be first
st.set_page_config(
    page_title="Chattier • Community Forum",
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

# Premium wallpaper collection
WALLPAPERS = {
    "✨ Abstract Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920&q=80",
    "🌌 Cosmic Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920&q=80",
    "🌊 Ocean Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920&q=80",
    "🏔️ Mountain Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🌸 Cherry Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
    "🌅 Golden Sunset": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1920&q=80",
    "🌿 Forest Mist": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&q=80",
    "🏙️ City Lights": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1920&q=80",
    "🌌 Starry Night": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920&q=80",
    "🔥 Lava Abstract": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1920&q=80",
}

DEFAULT_WALLPAPER = "✨ Abstract Purple"

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
    except:
        pass

def load_users():
    return load_json(USERS_FILE, {})

def save_users(users):
    save_json(USERS_FILE, users)

def load_profiles():
    return load_json(PROFILES_FILE, {})

def save_profiles(profiles):
    save_json(PROFILES_FILE, profiles)

def get_user_profile(username):
    profiles = load_profiles()
    return profiles.get(username, {"bio": "", "avatar": None, "wallpaper": DEFAULT_WALLPAPER})

def update_profile(username, bio, avatar_file, wallpaper):
    profiles = load_profiles()
    if username not in profiles:
        profiles[username] = {}
    
    profiles[username]["bio"] = sanitize_html(bio) if bio else ""
    
    if wallpaper and wallpaper in WALLPAPERS:
        profiles[username]["wallpaper"] = wallpaper
    
    if avatar_file is not None:
        try:
            image = Image.open(avatar_file)
            image = image.convert("RGB")
            image = image.resize((200, 200), Image.Resampling.LANCZOS)
            avatar_path = UPLOADS_DIR / f"{username}_avatar.jpg"
            image.save(avatar_path, "JPEG", quality=85)
            profiles[username]["avatar"] = str(avatar_path)
        except Exception as e:
            st.error(f"Could not process image: {e}")
    
    save_profiles(profiles)
    return True

def get_avatar_html(username, size=40):
    profiles = load_profiles()
    profile = profiles.get(username, {})
    avatar_path = profile.get("avatar")
    
    if avatar_path and os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as f:
                avatar_bytes = f.read()
            avatar_b64 = base64.b64encode(avatar_bytes).decode()
            return f'<div style="width:{size}px;height:{size}px;border-radius:50%;overflow:hidden;flex-shrink:0;"><img src="data:image/jpeg;base64,{avatar_b64}" style="width:100%;height:100%;object-fit:cover;" /></div>'
        except:
            pass
    
    letter = username[0].upper() if username else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#a78bfa);display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;flex-shrink:0;">{letter}</div>'

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
        return t.strftime("%b %d")
    except:
        return ""

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.messages = load_messages()
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.show_profile = False
    st.session_state.wallpaper = DEFAULT_WALLPAPER
    st.session_state.initialized = True

# Load wallpaper from profile if authenticated
if st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile.get("wallpaper", DEFAULT_WALLPAPER)

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, WALLPAPERS[DEFAULT_WALLPAPER])

# Premium CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
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
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(6px);
        z-index: -1;
    }}
    
    .block-container {{
        padding: 1rem !important;
        max-width: 100% !important;
    }}
    
    /* Chattier branding */
    .brand-logo {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    
    .brand-icon {{
        width: 42px;
        height: 42px;
        background: linear-gradient(135deg, #7c3aed, #c084fc);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.5);
    }}
    
    .brand-name {{
        font-size: 1.5rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #c084fc, #e9d5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* Chat container */
    .chat-container {{
        max-width: 800px;
        margin: 0 auto;
        height: 88vh;
        display: flex;
        flex-direction: column;
        background: rgba(30, 41, 59, 0.55);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.4);
        overflow: hidden;
    }}
    
    .chat-header {{
        padding: 0.9rem 1.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: rgba(0,0,0,0.2);
        flex-shrink: 0;
    }}
    
    .status-badge {{
        background: rgba(255,255,255,0.06);
        padding: 0.3rem 0.9rem;
        border-radius: 1.5rem;
        font-size: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
        color: #cbd5e1;
        border: 1px solid rgba(255,255,255,0.08);
    }}
    
    .status-dot {{
        width: 7px;
        height: 7px;
        background: #10b981;
        border-radius: 50%;
        animation: statusPulse 2s infinite;
    }}
    
    @keyframes statusPulse {{
        0%, 100% {{ opacity: 1; box-shadow: 0 0 4px #10b981; }}
        50% {{ opacity: 0.4; box-shadow: 0 0 1px #10b981; }}
    }}
    
    /* Messages */
    .messages-area {{
        flex: 1;
        overflow-y: auto;
        padding: 1rem 1.2rem;
        display: flex;
        flex-direction: column;
        gap: 0.7rem;
        min-height: 0;
    }}
    
    .msg-row {{
        display: flex;
        gap: 0.6rem;
        animation: msgIn 0.25s ease;
        align-items: flex-start;
    }}
    
    .msg-row.own {{
        flex-direction: row-reverse;
    }}
    
    @keyframes msgIn {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .msg-bubble {{
        max-width: 60%;
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(8px);
        padding: 0.55rem 0.9rem;
        border-radius: 0.9rem 0.9rem 0.9rem 0.2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        word-wrap: break-word;
    }}
    
    .msg-row.own .msg-bubble {{
        background: rgba(124, 58, 237, 0.25);
        border-color: rgba(124, 58, 237, 0.3);
        border-radius: 0.9rem 0.9rem 0.2rem 0.9rem;
    }}
    
    .msg-author {{
        font-size: 0.7rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.15rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }}
    
    .msg-row.own .msg-author {{
        justify-content: flex-end;
        color: #c4b5fd;
    }}
    
    .msg-time {{
        font-size: 0.6rem;
        color: #94a3b8;
        font-weight: 400;
    }}
    
    .msg-text {{
        color: #f1f5f9;
        font-size: 0.88rem;
        line-height: 1.4;
    }}
    
    .empty-state {{
        text-align: center;
        color: #94a3b8;
        padding: 2rem;
        margin: auto;
    }}
    
    /* Input */
    .input-section {{
        padding: 0.8rem 1.2rem;
        background: rgba(0,0,0,0.25);
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        flex-shrink: 0;
    }}
    
    .user-tag {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.4rem;
        color: #a5b4fc;
        font-size: 0.8rem;
        font-weight: 500;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        padding: 0.6rem 1rem !important;
        border-radius: 1.5rem !important;
        color: #ffffff !important;
        font-size: 0.88rem !important;
        caret-color: #c084fc !important;
        height: auto !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: rgba(255, 255, 255, 0.4) !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #a78bfa !important;
        box-shadow: 0 0 12px rgba(167, 139, 250, 0.25) !important;
        background: rgba(255, 255, 255, 0.15) !important;
    }}
    
    /* Text area */
    .stTextArea textarea {{
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.18) !important;
        border-radius: 1rem !important;
        color: #ffffff !important;
        font-size: 0.88rem !important;
    }}
    
    .stTextArea textarea:focus {{
        border-color: #a78bfa !important;
        box-shadow: 0 0 12px rgba(167, 139, 250, 0.25) !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, #7c3aed, #8b5cf6) !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        border-radius: 1.5rem !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        height: auto !important;
        min-height: 38px !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4) !important;
        background: linear-gradient(135deg, #8b5cf6, #a78bfa) !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 0.8rem;
        color: #cbd5e1 !important;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.85rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #7c3aed, #8b5cf6) !important;
        color: white !important;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(15px) !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 4px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: rgba(124, 58, 237, 0.4); border-radius: 4px; }}
    
    /* Forms */
    .stForm {{ border: none !important; padding: 0 !important; }}
    
    /* Auth card */
    .auth-card {{
        max-width: 440px;
        margin: 2rem auto;
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    }}
    
    /* Profile card */
    .profile-card {{
        max-width: 600px;
        margin: 1rem auto;
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.4);
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 0.8rem !important;
        padding: 0.5rem !important;
    }}
    
    /* Select box */
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 0.8rem !important;
        color: white !important;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .chat-container {{
            height: 92vh;
            border-radius: 1rem;
        }}
        .msg-bubble {{
            max-width: 75%;
        }}
        .block-container {{
            padding: 0.3rem !important;
        }}
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
        return False, "Password must be at least 4 characters"
    if len(username) < 2:
        return False, "Username must be at least 2 characters"
    if len(username) > 20:
        return False, "Username too long (max 20 chars)"
    
    users = load_users()
    if username.lower() in [u.lower() for u in users]:
        return False, "Username already exists"
    
    users[username] = hash_password(password)
    save_users(users)
    
    profiles = load_profiles()
    profiles[username] = {"bio": "", "avatar": None, "wallpaper": DEFAULT_WALLPAPER}
    save_profiles(profiles)
    
    return True, "Account created successfully!"

def sign_in(username, password):
    users = load_users()
    for u, pwd in users.items():
        if u.lower() == username.lower() and pwd == hash_password(password):
            st.session_state.authenticated = True
            st.session_state.username = u
            profile = get_user_profile(u)
            st.session_state.wallpaper = profile.get("wallpaper", DEFAULT_WALLPAPER)
            return True, f"Welcome back, {u}!"
    return False, "Invalid username or password"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.show_profile = False
    st.session_state.wallpaper = DEFAULT_WALLPAPER

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

# ============ SIDEBAR ============
with st.sidebar:
    # Brand
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:1.5rem;">
        <div style="width:38px;height:38px;background:linear-gradient(135deg,#7c3aed,#c084fc);border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:1.2rem;box-shadow:0 4px 12px rgba(124,58,237,0.4);">💬</div>
        <span style="font-size:1.4rem;font-weight:800;background:linear-gradient(135deg,#c084fc,#e9d5ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Chattier</span>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.authenticated:
        st.markdown("### 👋 Welcome to Chattier")
        st.caption("Sign in to join the conversation")
        st.markdown("---")
    
    # Wallpaper
    st.markdown("### 🎨 Theme")
    current_wp = st.session_state.get("wallpaper", DEFAULT_WALLPAPER)
    wp_list = list(WALLPAPERS.keys())
    
    try:
        current_idx = wp_list.index(current_wp)
    except:
        current_idx = 0
    
    selected_wp = st.selectbox(
        "Choose wallpaper",
        wp_list,
        index=current_idx,
        label_visibility="collapsed"
    )
    
    if selected_wp != current_wp:
        st.session_state.wallpaper = selected_wp
        if st.session_state.authenticated:
            profiles = load_profiles()
            if st.session_state.username in profiles:
                profiles[st.session_state.username]["wallpaper"] = selected_wp
            else:
                profiles[st.session_state.username] = {"bio": "", "avatar": None, "wallpaper": selected_wp}
            save_profiles(profiles)
        st.rerun()
    
    if st.session_state.authenticated:
        st.markdown("---")
        st.markdown(f"### 👤 {st.session_state.username}")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✏️ Profile", use_container_width=True):
                st.session_state.show_profile = True
                st.rerun()
        with c2:
            if st.button("🚪 Logout", use_container_width=True):
                sign_out()
                st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Activity")
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Messages", len(st.session_state.messages))
    with c2:
        if st.session_state.messages:
            users = len(set(m["username"] for m in st.session_state.messages))
            st.metric("Users", users)
        else:
            st.metric("Users", 0)
    
    st.markdown("---")
    st.caption("© 2024 Chattier • v1.0")
    st.caption("Made with ❤️")

# ============ PROFILE PAGE ============
if st.session_state.show_profile and st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    
    st.markdown('<div class="profile-card">', unsafe_allow_html=True)
    st.markdown("## ✏️ Edit Profile")
    
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.markdown("#### Avatar")
        avatar_html = get_avatar_html(st.session_state.username, 140)
        st.markdown(f'<div style="margin-bottom:1rem;">{avatar_html}</div>', unsafe_allow_html=True)
        avatar_file = st.file_uploader("Upload image", type=['png', 'jpg', 'jpeg'], 
                                       key="avatar_upload", label_visibility="collapsed")
        st.caption("Recommended: 200×200px")
    
    with c2:
        with st.form("profile_form"):
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200, 
                             placeholder="Write something about yourself...", height=100)
            
            try:
                wp_idx = wp_list.index(profile.get("wallpaper", DEFAULT_WALLPAPER))
            except:
                wp_idx = 0
            
            wallpaper_choice = st.selectbox("Default theme", wp_list, index=wp_idx)
            
            ca, cb = st.columns(2)
            with ca:
                save_btn = st.form_submit_button("💾 Save", use_container_width=True)
            with cb:
                cancel_btn = st.form_submit_button("↩️ Back", use_container_width=True)
            
            if save_btn:
                if update_profile(st.session_state.username, bio, avatar_file, wallpaper_choice):
                    st.session_state.wallpaper = wallpaper_choice
                    st.success("Profile updated!")
                    time.sleep(0.4)
                    st.session_state.show_profile = False
                    st.rerun()
            
            if cancel_btn:
                st.session_state.show_profile = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============ AUTH PAGE ============
elif not st.session_state.authenticated:
    st.markdown("""
    <div class="auth-card">
        <div style="text-align:center;margin-bottom:1.5rem;">
            <div style="display:flex;align-items:center;justify-content:center;gap:0.6rem;margin-bottom:0.5rem;">
                <div style="width:48px;height:48px;background:linear-gradient(135deg,#7c3aed,#c084fc);border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.6rem;box-shadow:0 6px 20px rgba(124,58,237,0.4);">💬</div>
                <span style="font-size:2rem;font-weight:800;background:linear-gradient(135deg,#c084fc,#e9d5ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Chattier</span>
            </div>
            <p style="color:#94a3b8;font-size:0.9rem;">Community Forum</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Your username", key="login_user")
            password = st.text_input("Password", type="password", placeholder="Your password", key="login_pass")
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
            password = st.text_input("Password", type="password", placeholder="Min 4 characters", key="signup_pass")
            confirm = st.text_input("Confirm password", type="password", placeholder="Re-enter password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                success, msg = sign_up(username, password, confirm)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# ============ CHAT PAGE ============
else:
    # Sync messages
    latest_msgs = load_messages()
    if len(latest_msgs) > len(st.session_state.messages):
        st.session_state.messages = latest_msgs
    
    online_count = max(1, len(set(m["username"] for m in st.session_state.messages[-50:])))
    
    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="brand-logo">
                <div class="brand-icon">💬</div>
                <span class="brand-name">Chattier</span>
            </div>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>{online_count} online</span>
            </div>
        </div>
        <div class="messages-area">
    """, unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:3rem;">💫</div>
            <div style="margin-top:0.5rem;font-weight:500;">No messages yet</div>
            <div style="font-size:0.8rem;opacity:0.7;">Be the first to start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_own = msg["username"] == st.session_state.username
            time_str = format_time(msg.get("timestamp", ""))
            avatar_html = get_avatar_html(msg["username"], 36)
            
            st.markdown(f"""
            <div class="msg-row {'own' if is_own else ''}">
                {avatar_html}
                <div class="msg-bubble">
                    <div class="msg-author">
                        {sanitize_html(msg['username'])}
                        <span class="msg-time">{time_str}</span>
                    </div>
                    <div class="msg-text">{msg['text']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="input-section">
            <div class="user-tag">
                <span>👤 {sanitize_html(st.session_state.username)}</span>
            </div>
    """, unsafe_allow_html=True)
    
    with st.form("msg_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            msg_text = st.text_input(
                "Message",
                placeholder="Type a message...",
                max_chars=500,
                key="msg_input",
                label_visibility="collapsed"
            )
        with c2:
            sent = st.form_submit_button("📤", use_container_width=True)
        
        if sent and msg_text and msg_text.strip():
            if send_message(msg_text):
                st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)

# Auto-refresh
time.sleep(2)
st.rerun()
