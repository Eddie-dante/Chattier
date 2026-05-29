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
import time

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
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Wallpaper collection
WALLPAPERS = {
    "✨ Abstract Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920&q=80",
    "🌌 Cosmic Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920&q=80",
    "🌊 Ocean Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920&q=80",
    "🏔️ Mountain Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🌸 Cherry Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
    "🌅 Golden Sunset": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1920&q=80",
    "🌿 Forest Mist": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&q=80",
    "🏙️ City Lights": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1920&q=80",
}

DEFAULT_WALLPAPER = "✨ Abstract Purple"

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_html(text):
    if not text:
        return ""
    return html_module.escape(str(text))

def load_json(path, default=None):
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default if default is not None else {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Error saving data: {e}")

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
    try:
        profiles = load_profiles()
        if username not in profiles:
            profiles[username] = {}
        
        profiles[username]["bio"] = sanitize_html(bio) if bio else ""
        
        if wallpaper and wallpaper in WALLPAPERS:
            profiles[username]["wallpaper"] = wallpaper
        
        if avatar_file is not None:
            try:
                UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
                image = Image.open(avatar_file)
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                else:
                    image = image.convert("RGB")
                image = image.resize((200, 200), Image.Resampling.LANCZOS)
                avatar_path = UPLOADS_DIR / f"{username}_avatar.jpg"
                image.save(avatar_path, "JPEG", quality=85)
                profiles[username]["avatar"] = str(avatar_path)
            except Exception as e:
                st.error(f"Could not process image: {e}")
                return False
        
        save_profiles(profiles)
        return True
    except Exception as e:
        st.error(f"Error updating profile: {e}")
        return False

def get_avatar_html(username, size=40):
    try:
        profiles = load_profiles()
        profile = profiles.get(username, {})
        avatar_path = profile.get("avatar")
        
        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                avatar_bytes = f.read()
            avatar_b64 = base64.b64encode(avatar_bytes).decode()
            return f'<img src="data:image/jpeg;base64,{avatar_b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;" />'
    except Exception:
        pass
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B787']
    color_idx = hash(username) % len(colors)
    bg_color = colors[color_idx]
    letter = username[0].upper() if username else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{bg_color};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;">{letter}</div>'

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
        return t.strftime("%b %d, %Y")
    except Exception:
        return "Unknown time"

def send_message(text):
    if not text or not text.strip():
        return False
    text = sanitize_html(text.strip())
    if len(text) > 500:
        return False
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "reactions": {}
    }
    st.session_state.messages.append(msg)
    save_messages()
    return True

def add_reaction(msg_id, emoji):
    try:
        for msg in st.session_state.messages:
            if msg.get("id") == msg_id:
                if "reactions" not in msg:
                    msg["reactions"] = {}
                if emoji not in msg["reactions"]:
                    msg["reactions"][emoji] = []
                
                username = st.session_state.username
                if username in msg["reactions"][emoji]:
                    msg["reactions"][emoji].remove(username)
                    if not msg["reactions"][emoji]:
                        del msg["reactions"][emoji]
                else:
                    msg["reactions"][emoji].append(username)
                break
        save_messages()
    except Exception as e:
        st.error(f"Error adding reaction: {e}")

def delete_message(msg_id):
    try:
        st.session_state.messages = [m for m in st.session_state.messages if m.get("id") != msg_id]
        save_messages()
        return True
    except Exception as e:
        st.error(f"Error deleting message: {e}")
        return False

def edit_message(msg_id, new_text):
    try:
        new_text = sanitize_html(new_text.strip())
        if not new_text:
            return False
        for msg in st.session_state.messages:
            if msg.get("id") == msg_id:
                msg["text"] = new_text
                msg["edited"] = True
                break
        save_messages()
        return True
    except Exception as e:
        st.error(f"Error editing message: {e}")
        return False

# Authentication functions
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
    if not username.isalnum():
        return False, "Username can only contain letters and numbers"
    
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
        if u.lower() == username.lower():
            if pwd == hash_password(password):
                return True, u
            else:
                return False, "Invalid password"
    return False, "Username not found"

def sign_out():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.wallpaper = DEFAULT_WALLPAPER
    st.session_state.current_view = "chat"
    st.session_state.editing_msg_id = None
    st.session_state.replying_to = None
    st.rerun()

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.messages = load_messages()
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.wallpaper = DEFAULT_WALLPAPER
    st.session_state.current_view = "chat"
    st.session_state.editing_msg_id = None
    st.session_state.replying_to = None
    st.session_state.initialized = True

# Load wallpaper from profile if authenticated
if st.session_state.get('authenticated', False):
    profile_data = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile_data.get("wallpaper", DEFAULT_WALLPAPER)

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, WALLPAPERS[DEFAULT_WALLPAPER])

# Custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* Hide Streamlit default elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Main app background */
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
        backdrop-filter: blur(10px);
        z-index: -1;
    }}
    
    /* Chat container */
    .chat-container {{
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1rem;
        margin-bottom: 1rem;
    }}
    
    /* Message styling */
    .message-bubble {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 0.5rem;
    }}
    
    .message-own {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        border-color: rgba(102, 126, 234, 0.5);
    }}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background: rgba(15, 23, 42, 0.95) !important;
        backdrop-filter: blur(20px);
    }}
    
    section[data-testid="stSidebar"] > div {{
        padding-top: 2rem;
    }}
    
    /* Button styling */
    .stButton > button {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 0.8rem;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }}
    
    /* Secondary button */
    .stButton > button[kind="secondary"] {{
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    /* Input styling */
    .stTextInput > div > div > input {{
        background: rgba(255, 255, 255, 0.95);
        color: #1e293b;
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 1rem;
        padding: 0.7rem 1rem;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }}
    
    /* Text area */
    .stTextArea > div > div > textarea {{
        background: rgba(255, 255, 255, 0.95);
        color: #1e293b;
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 1rem;
        padding: 0.7rem 1rem;
    }}
    
    /* Profile card */
    .profile-card {{
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }}
    
    /* Theme cards */
    .theme-card {{
        border-radius: 1rem;
        overflow: hidden;
        border: 2px solid rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition: all 0.3s;
        margin-bottom: 0.5rem;
    }}
    
    .theme-card:hover {{
        border-color: #667eea;
        transform: scale(1.05);
    }}
    
    .theme-card.selected {{
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.4);
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 6px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: rgba(255, 255, 255, 0.05);
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 3px;
    }}
    
    /* Divider */
    hr {{
        border-color: rgba(255, 255, 255, 0.1);
    }}
    
    /* Metric cards */
    [data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        border-radius: 0.5rem;
    }}
    
    [data-testid="stMetric"] label {{
        color: #94a3b8 !important;
    }}
    
    [data-testid="stMetric"] div {{
        color: white !important;
    }}
</style>
""", unsafe_allow_html=True)

# ============ AUTH PAGE ============
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">💬</div>
            <h1 style="color: white; margin-bottom: 0.5rem;">Chattier</h1>
            <p style="color: #94a3b8; margin-bottom: 2rem;">Community Forum</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
                
                if submitted:
                    success, result = sign_in(username, password)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = result
                        st.success(f"Welcome back, {result}!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(result)
        
        with tab2:
            with st.form("signup_form"):
                username = st.text_input("Username", placeholder="Choose a username (2-20 chars)")
                password = st.text_input("Password", type="password", placeholder="Minimum 4 characters")
                confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
                
                if submitted:
                    success, msg = sign_up(username, password, confirm)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

# ============ MAIN APP ============
else:
    # Sidebar content
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem;">💬</div>
            <h2 style="color: white; margin: 0.5rem 0;">Chattier</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # User avatar and info
        profile_data = get_user_profile(st.session_state.username)
        avatar_html = get_avatar_html(st.session_state.username, 80)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            {avatar_html}
            <h3 style="color: white; margin: 0.5rem 0;">@{st.session_state.username}</h3>
            <p style="color: #94a3b8; font-size: 0.8rem;">{sanitize_html(profile_data.get('bio', 'No bio yet'))[:80]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation buttons
        st.markdown("### 📱 Navigation")
        
        # Use regular buttons without type parameter to avoid errors
        if st.button("💬 Chat Room", use_container_width=True, key="nav_chat"):
            st.session_state.current_view = "chat"
            st.session_state.editing_msg_id = None
            st.rerun()
        
        if st.button("👤 Profile Settings", use_container_width=True, key="nav_profile"):
            st.session_state.current_view = "profile"
            st.rerun()
        
        if st.button("🎨 Themes", use_container_width=True, key="nav_themes"):
            st.session_state.current_view = "themes"
            st.rerun()
        
        st.divider()
        
        # Stats
        st.markdown("### 📊 Community Stats")
        total_messages = len(st.session_state.messages)
        unique_users = len(set(m["username"] for m in st.session_state.messages)) if st.session_state.messages else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", total_messages)
        with col2:
            st.metric("Members", unique_users)
        
        st.divider()
        
        # Sign out
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
    
    # Main content area
    if st.session_state.current_view == "chat":
        # ============ CHAT VIEW ============
        
        # Chat header
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0;">💬 Community Chat</h2>
            <div style="background: rgba(16, 185, 129, 0.2); padding: 0.5rem 1rem; border-radius: 1rem; color: #10b981;">
                🟢 Online
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Messages container
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #94a3b8;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">✨</div>
                <h3>No messages yet</h3>
                <p>Be the first to start the conversation!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display last 50 messages
            for msg in st.session_state.messages[-50:]:
                is_own = msg["username"] == st.session_state.username
                msg_id = msg.get("id", "")
                
                # Check if editing
                if st.session_state.get("editing_msg_id") == msg_id:
                    with st.form(key=f"edit_{msg_id}"):
                        st.text_input("Edit message", value=msg['text'], key=f"input_{msg_id}", label_visibility="collapsed")
                        new_text = st.session_state[f"input_{msg_id}"]
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("💾 Save", use_container_width=True):
                                if edit_message(msg_id, new_text):
                                    st.session_state.editing_msg_id = None
                                    st.rerun()
                        with c2:
                            if st.form_submit_button("❌ Cancel", use_container_width=True):
                                st.session_state.editing_msg_id = None
                                st.rerun()
                else:
                    # Message display
                    col1, col2 = st.columns([1, 20])
                    
                    with col1:
                        st.markdown(get_avatar_html(msg["username"], 35), unsafe_allow_html=True)
                    
                    with col2:
                        edited_mark = " *(edited)*" if msg.get("edited") else ""
                        st.markdown(f"""
                        <div class="message-bubble {'message-own' if is_own else ''}">
                            <strong style="color: {'#c4b5fd' if is_own else '#a5b4fc'};">{sanitize_html(msg['username'])}</strong>
                            <span style="color: #94a3b8; font-size: 0.7rem;"> • {format_time(msg.get('timestamp', ''))}{edited_mark}</span>
                            <p style="color: #f8fafc; margin: 0.5rem 0 0 0;">{msg['text']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        cols = st.columns([1, 1, 1, 1, 1, 10])
                        
                        with cols[0]:
                            if st.button("👍", key=f"like_{msg_id}", help="Like"):
                                add_reaction(msg_id, "👍")
                                st.rerun()
                        
                        with cols[1]:
                            if st.button("❤️", key=f"love_{msg_id}", help="Love"):
                                add_reaction(msg_id, "❤️")
                                st.rerun()
                        
                        with cols[2]:
                            if st.button("😂", key=f"laugh_{msg_id}", help="Haha"):
                                add_reaction(msg_id, "😂")
                                st.rerun()
                        
                        with cols[3]:
                            if st.button("↩️", key=f"reply_{msg_id}", help="Reply"):
                                st.session_state.replying_to = msg_id
                                st.rerun()
                        
                        if is_own:
                            with cols[4]:
                                if st.button("✏️", key=f"editbtn_{msg_id}", help="Edit"):
                                    st.session_state.editing_msg_id = msg_id
                                    st.rerun()
                        
                        # Show reactions
                        if msg.get("reactions"):
                            reaction_html = '<div style="margin-top: 0.3rem; display: flex; gap: 0.3rem; flex-wrap: wrap;">'
                            for emoji, users in msg["reactions"].items():
                                count = len(users)
                                is_user_reacted = st.session_state.username in users
                                reaction_html += f'<span style="background: rgba(255, 255, 255, {0.3 if is_user_reacted else 0.1}); padding: 0.1rem 0.5rem; border-radius: 1rem; font-size: 0.8rem; border: 1px solid rgba(255, 255, 255, {0.5 if is_user_reacted else 0.2});">{emoji} {count}</span>'
                            reaction_html += '</div>'
                            st.markdown(reaction_html, unsafe_allow_html=True)
                        
                        # Delete button for own messages
                        if is_own:
                            if st.button("🗑️ Delete", key=f"delete_{msg_id}"):
                                if delete_message(msg_id):
                                    st.rerun()
        
        # Reply indicator
        if st.session_state.get("replying_to"):
            reply_msg = next((m for m in st.session_state.messages if m.get("id") == st.session_state.replying_to), None)
            if reply_msg:
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(102, 126, 234, 0.2); padding: 0.5rem 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; color: #94a3b8;">
                        ↩️ Replying to <strong style="color: white;">{sanitize_html(reply_msg['username'])}</strong>: {sanitize_html(reply_msg['text'][:50])}...
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("✕", key="cancel_reply"):
                        st.session_state.replying_to = None
                        st.rerun()
        
        # Message input
        st.divider()
        with st.form("message_form", clear_on_submit=True):
            col1, col2 = st.columns([6, 1])
            with col1:
                msg_text = st.text_input(
                    "Message",
                    placeholder=f"Type a message as @{st.session_state.username}...",
                    label_visibility="collapsed",
                    key="msg_input"
                )
            with col2:
                submitted = st.form_submit_button("Send 📤", use_container_width=True)
            
            if submitted and msg_text and msg_text.strip():
                if send_message(msg_text):
                    st.rerun()
    
    elif st.session_state.current_view == "profile":
        # ============ PROFILE VIEW ============
        st.markdown('<h2 style="color: white;">👤 Profile Settings</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            avatar_html = get_avatar_html(st.session_state.username, 150)
            st.markdown(avatar_html, unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: white;'>@{st.session_state.username}</h3>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Upload avatar
            avatar_file = st.file_uploader("Upload Avatar", type=['png', 'jpg', 'jpeg'])
        
        with col2:
            with st.form("profile_form"):
                profile_data = get_user_profile(st.session_state.username)
                bio = st.text_area("Bio", value=profile_data.get("bio", ""), max_chars=200, 
                                  placeholder="Tell us about yourself...", height=100)
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("💾 Save Profile", use_container_width=True):
                        current_wp = st.session_state.wallpaper
                        if update_profile(st.session_state.username, bio, avatar_file, current_wp):
                            st.success("Profile updated!")
                            time.sleep(1)
                            st.rerun()
                
                with col_b:
                    if st.form_submit_button("↩️ Back to Chat", use_container_width=True):
                        st.session_state.current_view = "chat"
                        st.rerun()
    
    elif st.session_state.current_view == "themes":
        # ============ THEMES VIEW ============
        st.markdown('<h2 style="color: white;">🎨 Choose Theme</h2>', unsafe_allow_html=True)
        st.markdown('<p style="color: #94a3b8; margin-bottom: 1rem;">Select a wallpaper for your chat experience</p>', unsafe_allow_html=True)
        
        # Display themes in grid
        for i, (theme_name, theme_url) in enumerate(WALLPAPERS.items()):
            if i % 4 == 0:
                cols = st.columns(4)
            
            with cols[i % 4]:
                is_selected = theme_name == st.session_state.wallpaper
                st.markdown(f"""
                <div class="theme-card {'selected' if is_selected else ''}">
                    <img src="{theme_url}" style="width: 100%; height: 120px; object-fit: cover;" />
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"{'✅ ' if is_selected else ''}{theme_name}", key=f"theme_{i}", use_container_width=True):
                    st.session_state.wallpaper = theme_name
                    profiles = load_profiles()
                    if st.session_state.username in profiles:
                        profiles[st.session_state.username]["wallpaper"] = theme_name
                    else:
                        profiles[st.session_state.username] = {"bio": "", "avatar": None, "wallpaper": theme_name}
                    save_profiles(profiles)
                    st.rerun()
        
        st.divider()
        if st.button("↩️ Back to Chat", use_container_width=True, key="back_from_themes"):
            st.session_state.current_view = "chat"
            st.rerun()
