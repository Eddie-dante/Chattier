import streamlit as st
import json
import os
import html as html_module
import hashlib
import pathlib
from datetime import datetime
import uuid
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

# Premium wallpaper collection - Expanded
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
    "🎨 Cyberpunk": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=1920&q=80",
    "🏝️ Tropical Paradise": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80",
    "❄️ Winter Aurora": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=1920&q=80",
    "🍁 Autumn Forest": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=1920&q=80",
    "🌺 Sakura Dream": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
    "💜 Lavender Fields": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=1920&q=80",
    "🌊 Deep Ocean": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1920&q=80",
    "🏔️ Mountain Peak": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1920&q=80",
    "🌙 Moonlight": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🎆 Neon Nights": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=1920&q=80",
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
    
    # Generate color based on username
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B787']
    color_idx = hash(username) % len(colors)
    bg_color = colors[color_idx]
    
    letter = username[0].upper() if username else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{bg_color};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;flex-shrink:0;box-shadow:0 2px 8px rgba(0,0,0,0.1);">{letter}</div>'

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
        elif diff.days < 7:
            return f"{diff.days}d ago"
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
    st.session_state.last_refresh = time.time()

# Load wallpaper from profile if authenticated
if st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile.get("wallpaper", DEFAULT_WALLPAPER)

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, WALLPAPERS[DEFAULT_WALLPAPER])

# Premium CSS with better text visibility
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
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
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(8px);
        z-index: -1;
    }}
    
    /* Main container */
    .main-container {{
        display: flex;
        gap: 1rem;
        max-width: 1400px;
        margin: 0 auto;
        padding: 1rem;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background: rgba(15, 23, 42, 0.85) !important;
        backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }}
    
    [data-testid="stSidebar"] * {{
        color: #f1f5f9 !important;
    }}
    
    /* Logo styling */
    .chattier-logo {{
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
        position: relative;
    }}
    
    .logo-animated {{
        width: 80px;
        height: 80px;
        margin: 0 auto;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 3rem;
        animation: float 3s ease-in-out infinite;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        position: relative;
        overflow: hidden;
    }}
    
    .logo-animated::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
        transform: rotate(45deg);
        animation: shine 3s infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    @keyframes shine {{
        0% {{ transform: translateX(-100%) rotate(45deg); }}
        100% {{ transform: translateX(100%) rotate(45deg); }}
    }}
    
    .logo-text {{
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 1rem;
        letter-spacing: -0.5px;
    }}
    
    .logo-subtitle {{
        font-size: 0.8rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }}
    
    /* Chat container */
    .chat-wrapper {{
        flex: 1;
        max-width: 900px;
        margin: 0 auto;
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        overflow: hidden;
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    }}
    
    .chat-header {{
        padding: 1rem 1.5rem;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2), rgba(118, 75, 162, 0.2));
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    
    .chat-title {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .chat-icon {{
        font-size: 1.5rem;
    }}
    
    .chat-title-text {{
        font-size: 1.2rem;
        font-weight: 600;
        color: #f1f5f9;
    }}
    
    .online-badge {{
        background: rgba(16, 185, 129, 0.2);
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }}
    
    .online-dot {{
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.5; }}
    }}
    
    /* Messages area */
    .messages-container {{
        height: 65vh;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
    }}
    
    .message-row {{
        display: flex;
        gap: 0.75rem;
        animation: slideIn 0.3s ease;
    }}
    
    .message-row-own {{
        flex-direction: row-reverse;
    }}
    
    @keyframes slideIn {{
        from {{
            opacity: 0;
            transform: translateY(10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .message-content {{
        max-width: 65%;
    }}
    
    .message-bubble {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 0.6rem 1rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .message-row-own .message-bubble {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        border-color: rgba(102, 126, 234, 0.5);
    }}
    
    .message-author {{
        font-size: 0.7rem;
        font-weight: 600;
        color: #a5b4fc;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    
    .message-row-own .message-author {{
        justify-content: flex-end;
        color: #c4b5fd;
    }}
    
    .message-time {{
        font-size: 0.6rem;
        color: #94a3b8;
        font-weight: 400;
    }}
    
    .message-text {{
        color: #f8fafc;
        font-size: 0.9rem;
        line-height: 1.4;
        word-wrap: break-word;
    }}
    
    /* Input area */
    .input-area {{
        padding: 1rem 1.5rem;
        background: rgba(0, 0, 0, 0.3);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    .input-wrapper {{
        display: flex;
        gap: 0.75rem;
        align-items: center;
    }}
    
    /* Fix for text input visibility */
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 1rem !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.9rem !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: #94a3b8 !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 1rem !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }}
    
    /* Form styling */
    .stForm {{
        background: transparent !important;
    }}
    
    /* Auth card */
    .auth-wrapper {{
        max-width: 450px;
        margin: 2rem auto;
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 50px rgba(0,0,0,0.3);
    }}
    
    /* Profile card */
    .profile-wrapper {{
        max-width: 650px;
        margin: 1rem auto;
        background: rgba(30, 41, 59, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: rgba(0,0,0,0.2);
        border-radius: 0.5rem;
        padding: 0.25rem;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        border-radius: 0.5rem;
        color: #cbd5e1 !important;
        padding: 0.5rem 1rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
    }}
    
    /* Text area for bio */
    .stTextArea textarea {{
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important;
        border: 1px solid rgba(102, 126, 234, 0.3) !important;
        border-radius: 0.8rem !important;
    }}
    
    /* File uploader */
    .stFileUploader > div {{
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px dashed rgba(255, 255, 255, 0.2) !important;
        border-radius: 0.8rem !important;
    }}
    
    /* Selectbox */
    .stSelectbox > div > div {{
        background: rgba(255, 255, 255, 0.95) !important;
        color: #1e293b !important;
        border-radius: 0.8rem !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
        border-radius: 3px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 3px;
    }}
    
    /* Responsive */
    @media (max-width: 768px) {{
        .messages-container {{
            height: 55vh;
        }}
        .message-content {{
            max-width: 80%;
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
    
    return True, "Account created successfully! Please sign in."

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
    st.rerun()

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
    # Beautiful Animated Logo
    st.markdown("""
    <div class="chattier-logo">
        <div class="logo-animated">
            💬
        </div>
        <div class="logo-text">Chattier</div>
        <div class="logo-subtitle">Community Forum</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if not st.session_state.authenticated:
        st.info("👋 Welcome! Sign in to join the conversation.")
    
    # Theme selector
    st.markdown("### 🎨 Theme Gallery")
    current_wp = st.session_state.get("wallpaper", DEFAULT_WALLPAPER)
    wp_list = list(WALLPAPERS.keys())
    
    try:
        current_idx = wp_list.index(current_wp)
    except:
        current_idx = 0
    
    # Create 2 columns for wallpaper preview
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
    
    st.markdown("---")
    
    if st.session_state.authenticated:
        # User info
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            avatar_html = get_avatar_html(st.session_state.username, 60)
            st.markdown(avatar_html, unsafe_allow_html=True)
        
        st.markdown(f"**@{st.session_state.username}**", unsafe_allow_html=True)
        
        profile_data = get_user_profile(st.session_state.username)
        if profile_data.get("bio"):
            st.caption(f"📝 {profile_data['bio'][:50]}...")
        
        st.markdown("---")
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit Profile", use_container_width=True):
                st.session_state.show_profile = True
                st.rerun()
        with col2:
            if st.button("🚪 Sign Out", use_container_width=True):
                sign_out()
        
        st.markdown("---")
        
        # Stats
        st.markdown("### 📊 Community Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Messages", len(st.session_state.messages))
        with col2:
            if st.session_state.messages:
                unique_users = len(set(m["username"] for m in st.session_state.messages))
                st.metric("Community Members", unique_users)
            else:
                st.metric("Community Members", 0)
    
    st.markdown("---")
    st.caption("Made with ❤️ • v2.0")

# ============ PROFILE PAGE ============
if st.session_state.get('show_profile', False) and st.session_state.authenticated:
    profile = get_user_profile(st.session_state.username)
    
    st.markdown('<div class="profile-wrapper">', unsafe_allow_html=True)
    st.markdown("## ✨ Edit Your Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Profile Picture")
        avatar_html = get_avatar_html(st.session_state.username, 150)
        st.markdown(f'<div style="margin-bottom:1rem; text-align:center;">{avatar_html}</div>', unsafe_allow_html=True)
        avatar_file = st.file_uploader("Upload new avatar", type=['png', 'jpg', 'jpeg'], 
                                       key="avatar_upload", label_visibility="collapsed")
        st.caption("Recommended: Square image, 200×200px")
    
    with col2:
        with st.form("profile_form"):
            bio = st.text_area("About Me", value=profile.get("bio", ""), max_chars=200, 
                             placeholder="Tell the community about yourself...", height=100)
            
            try:
                wp_idx = wp_list.index(profile.get("wallpaper", DEFAULT_WALLPAPER))
            except:
                wp_idx = 0
            
            default_theme = st.selectbox("Default Theme", wp_list, index=wp_idx)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
            with col_btn2:
                cancel_btn = st.form_submit_button("↩️ Cancel", use_container_width=True)
            
            if save_btn:
                if update_profile(st.session_state.username, bio, avatar_file, default_theme):
                    st.session_state.wallpaper = default_theme
                    st.success("✅ Profile updated successfully!")
                    time.sleep(0.5)
                    st.session_state.show_profile = False
                    st.rerun()
            
            if cancel_btn:
                st.session_state.show_profile = False
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ============ AUTH PAGE ============
elif not st.session_state.authenticated:
    st.markdown("""
    <div class="auth-wrapper">
        <div style="text-align:center; margin-bottom:2rem;">
            <div style="width:60px;height:60px;margin:0 auto;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:15px;display:flex;align-items:center;justify-content:center;font-size:2rem;margin-bottom:1rem;">
                💬
            </div>
            <h2 style="color:#f1f5f9;">Welcome to Chattier</h2>
            <p style="color:#94a3b8;">Join the community conversation</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
    
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
            username = st.text_input("Username", placeholder="Choose a username (2-20 chars)", key="signup_user")
            password = st.text_input("Password", type="password", placeholder="Minimum 4 characters", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")
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
    
    # Calculate online users (users who messaged in last hour)
    online_count = 1
    if st.session_state.messages:
        recent_msgs = [m for m in st.session_state.messages if 
                      (datetime.now() - datetime.fromisoformat(m.get("timestamp", datetime.now().isoformat()))).seconds < 3600]
        online_count = max(1, len(set(m["username"] for m in recent_msgs)))
    
    # Chat UI
    st.markdown(f"""
    <div class="chat-wrapper">
        <div class="chat-header">
            <div class="chat-title">
                <div class="chat-icon">💬</div>
                <div class="chat-title-text">Community Chat</div>
            </div>
            <div class="online-badge">
                <div class="online-dot"></div>
                <span>{online_count} online now</span>
            </div>
        </div>
        <div class="messages-container">
    """, unsafe_allow_html=True)
    
    # Display messages
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding:3rem;">
            <div style="font-size:4rem; margin-bottom:1rem;">✨</div>
            <div style="color:#94a3b8;">No messages yet</div>
            <div style="color:#64748b; font-size:0.85rem;">Be the first to start the conversation!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            is_own = msg["username"] == st.session_state.username
            time_str = format_time(msg.get("timestamp", ""))
            avatar_html = get_avatar_html(msg["username"], 36)
            
            st.markdown(f"""
            <div class="message-row {'message-row-own' if is_own else ''}">
                {avatar_html}
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="message-author">
                            <span>{sanitize_html(msg['username'])}</span>
                            <span class="message-time">{time_str}</span>
                        </div>
                        <div class="message-text">{msg['text']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Message input
    st.markdown("""
        <div class="input-area">
            <div class="input-wrapper">
    """, unsafe_allow_html=True)
    
    with st.form("msg_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            msg_text = st.text_input(
                "Message",
                placeholder=f"Message as @{st.session_state.username}...",
                max_chars=500,
                key="msg_input",
                label_visibility="collapsed"
            )
        with col2:
            sent = st.form_submit_button("Send 📤", use_container_width=True)
        
        if sent and msg_text and msg_text.strip():
            if send_message(msg_text):
                st.rerun()
    
    st.markdown('</div></div></div>', unsafe_allow_html=True)
