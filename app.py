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
import requests
from io import BytesIO

# Page config MUST be first
st.set_page_config(
    page_title="Chattier Pro • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DATABASE CONFIGURATION ====================
try:
    JSONBIN_API_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_BIN_ID = st.secrets["jsonbin"]["bin_id"]
    USE_CLOUD = True
except:
    JSONBIN_API_KEY = os.environ.get("JSONBIN_API_KEY", "")
    JSONBIN_BIN_ID = os.environ.get("JSONBIN_BIN_ID", "")
    USE_CLOUD = bool(JSONBIN_API_KEY and JSONBIN_BIN_ID)

# ==================== FILE PATHS ====================
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
ATTACHMENTS_DIR = DATA_DIR / "attachments"
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 50+ WALLPAPERS ====================
WALLPAPERS = {
    "🌈 Animated Gradient": "gradient_default",
    "✨ Abstract Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1920&q=80",
    "🌌 Cosmic Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1920&q=80",
    "🌊 Ocean Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1920&q=80",
    "🏔️ Mountain Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🌸 Cherry Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
    "🌅 Golden Sunset": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1920&q=80",
    "🌿 Forest Mist": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1920&q=80",
    "🏙️ City Lights": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1920&q=80",
    "🔥 Fiery Lava": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1920&q=80",
    "🎨 Cyberpunk Neon": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=1920&q=80",
    "🏝️ Tropical Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80",
    "❄️ Aurora Winter": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=1920&q=80",
    "🍁 Autumn Forest": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=1920&q=80",
    "💜 Lavender Fields": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=1920&q=80",
    "🌊 Deep Ocean Blue": "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1920&q=80",
    "🏔️ Alpine Peaks": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1920&q=80",
    "🌄 Desert Dunes": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1920&q=80",
    "🌌 Milky Way": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920&q=80",
    "🌸 Pink Blossoms": "https://images.unsplash.com/photo-1490750967868-88aa4e7c9d7a?w=1920&q=80",
    "🏞️ Mountain Lake": "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1920&q=80",
    "🌻 Sunflower Field": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=1920&q=80",
    "🏰 Northern Lights": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1920&q=80",
    "🌴 Palm Sunset": "https://images.unsplash.com/photo-1509233725247-49e657c54213?w=1920&q=80",
    "🎆 Fireworks Night": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=1920&q=80",
    "🌊 Stormy Sea": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1920&q=80",
    "🏔️ Snowy Mountains": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80",
    "🌅 Purple Dawn": "https://images.unsplash.com/photo-1506898667547-42e22a46e125?w=1920&q=80",
    "🍂 Autumn Road": "https://images.unsplash.com/photo-1507041957456-9c397ce39c97?w=1920&q=80",
    "🌺 Tropical Flowers": "https://images.unsplash.com/photo-1465146344425-f00d5f5c8f07?w=1920&q=80",
    "🌙 Moonlit Mountains": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1920&q=80",
    "🏖️ Crystal Clear": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=1920&q=80",
    "🌄 Golden Hour": "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1920&q=80",
    "🏜️ Red Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=1920&q=80",
    "🌊 Turquoise Waves": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=1920&q=80",
    "🌸 Spring Meadow": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=1920&q=80",
    "🌅 Sunset Silhouette": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1920&q=80",
    "🎭 Abstract Art": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=1920&q=80",
    "🌿 Zen Garden": "https://images.unsplash.com/photo-1506784365847-bbad939e9335?w=1920&q=80",
    "🏯 Japanese Temple": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1920&q=80",
    "🌌 Starry Night": "https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?w=1920&q=80",
    "🏛️ Greek Coast": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=1920&q=80",
    "🌋 Volcanic": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=1920&q=80",
    "🎪 Carnival": "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=1920&q=80",
    "🏜️ Sahara": "https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=1920&q=80",
    "🌊 Maldives": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=1920&q=80",
    "🏔️ Himalayas": "https://images.unsplash.com/photo-1486911278844-a81c5267e227?w=1920&q=80",
    "🌺 Bali Rice Fields": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=1920&q=80",
    "🏰 Neuschwanstein": "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1920&q=80",
}

DEFAULT_WALLPAPER = "🌈 Animated Gradient"

# Emoji collections
EMOJI_LIST = ["😀", "😂", "🤣", "😍", "🥰", "😘", "😜", "🤪", "😎", "🤩", 
              "🥳", "😇", "🤗", "🤔", "😴", "🥺", "😤", "😡", "💀", "👻",
              "👍", "👎", "👏", "🙌", "💪", "🤝", "❤️", "🧡", "💛", "💚",
              "💙", "💜", "🖤", "🤍", "💔", "🔥", "⭐", "🌟", "✨", "🎉",
              "🎊", "🎈", "🎂", "🍕", "🍔", "🌮", "☕", "🍺", "🏆", "💯"]

# ==================== CLOUD FUNCTIONS (OPTIMIZED) ====================
@st.cache_data(ttl=2)
def load_cloud_messages():
    if not USE_CLOUD:
        return None
    try:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
        headers = {"X-Master-Key": JSONBIN_API_KEY, "X-Bin-Meta": "false"}
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else data.get("messages", [])
    except:
        pass
    return None

def save_cloud_messages(messages):
    if not USE_CLOUD:
        return
    try:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
        headers = {"Content-Type": "application/json", "X-Master-Key": JSONBIN_API_KEY}
        requests.put(url, json={"messages": messages}, headers=headers, timeout=3)
    except:
        pass

# ==================== HELPER FUNCTIONS ====================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def sanitize_html(text):
    return html_module.escape(str(text)) if text else ""

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
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except:
        pass

def load_users():
    return load_json(USERS_FILE, {})

def load_profiles():
    profiles = load_json(PROFILES_FILE, {})
    # Ensure all profiles have status field
    for username in profiles:
        if "status" not in profiles[username]:
            profiles[username]["status"] = ""
        if "last_seen" not in profiles[username]:
            profiles[username]["last_seen"] = ""
    return profiles

def save_profiles(profiles):
    save_json(PROFILES_FILE, profiles)

def get_user_profile(username):
    profiles = load_profiles()
    return profiles.get(username, {
        "bio": "", "avatar": None, "wallpaper": DEFAULT_WALLPAPER,
        "status": "", "last_seen": ""
    })

def update_profile(username, bio, avatar_file, wallpaper, status=""):
    try:
        profiles = load_profiles()
        if username not in profiles:
            profiles[username] = {}
        
        profiles[username]["bio"] = sanitize_html(bio) if bio else ""
        profiles[username]["status"] = sanitize_html(status) if status else ""
        profiles[username]["wallpaper"] = wallpaper if wallpaper in WALLPAPERS else DEFAULT_WALLPAPER
        profiles[username]["last_seen"] = datetime.now().isoformat()
        
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
                image.thumbnail((200, 200), Image.Resampling.LANCZOS)
                avatar_path = UPLOADS_DIR / f"{username}_avatar.jpg"
                image.save(avatar_path, "JPEG", quality=80)
                profiles[username]["avatar"] = str(avatar_path)
            except:
                pass
        
        save_profiles(profiles)
        return True
    except:
        return False

def get_avatar_html(username, size=35):
    try:
        profiles = load_profiles()
        profile = profiles.get(username, {})
        avatar_path = profile.get("avatar")
        
        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                avatar_bytes = f.read()
            avatar_b64 = base64.b64encode(avatar_bytes).decode()
            return f'<img src="data:image/jpeg;base64,{avatar_b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;flex-shrink:0;" />'
    except:
        pass
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B787',
              '#FF8A80', '#B388FF', '#82B1FF', '#B9F6CA', '#FFE57F', '#FF80AB', '#EA80FC', '#8C9EFF']
    bg_color = colors[hash(username) % len(colors)]
    letter = username[0].upper() if username else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{bg_color};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;flex-shrink:0;">{letter}</div>'

def load_messages():
    cloud_msgs = load_cloud_messages()
    if cloud_msgs is not None:
        return cloud_msgs
    return load_json(MESSAGES_FILE, [])

def save_all_messages(messages):
    if len(messages) > 500:
        messages = messages[-500:]
    save_cloud_messages(messages)
    save_json(MESSAGES_FILE, messages)

def format_time(ts):
    try:
        t = datetime.fromisoformat(ts)
        now = datetime.now()
        diff = now - t
        if diff.days == 0:
            if diff.seconds < 60: return "Just now"
            elif diff.seconds < 3600: return f"{diff.seconds // 60}m ago"
            return f"{diff.seconds // 3600}h ago"
        elif diff.days == 1: return "Yesterday"
        elif diff.days < 7: return f"{diff.days}d ago"
        return t.strftime("%b %d, %I:%M %p")
    except:
        return ""

def send_message(text, attachment_data=None, attachment_name=None):
    if not text and not attachment_data:
        return False
    text = sanitize_html(text.strip()) if text else ""
    if len(text) > 1000:
        return False
    
    current_messages = load_messages()
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "reactions": {},
    }
    
    if attachment_data and attachment_name:
        msg["attachment"] = attachment_data
        msg["attachment_name"] = attachment_name
        msg["attachment_type"] = "image" if attachment_name.lower().endswith(('.png','.jpg','.jpeg','.gif')) else "file"
    
    current_messages.append(msg)
    save_all_messages(current_messages)
    st.session_state.messages = current_messages
    return True

def add_reaction(msg_id, emoji):
    current_messages = load_messages()
    for msg in current_messages:
        if msg.get("id") == msg_id:
            if "reactions" not in msg: msg["reactions"] = {}
            if emoji not in msg["reactions"]: msg["reactions"][emoji] = []
            
            username = st.session_state.username
            if username in msg["reactions"][emoji]:
                msg["reactions"][emoji].remove(username)
                if not msg["reactions"][emoji]: del msg["reactions"][emoji]
            else:
                msg["reactions"][emoji].append(username)
            break
    save_all_messages(current_messages)
    st.session_state.messages = current_messages

def delete_message(msg_id):
    current_messages = load_messages()
    current_messages = [m for m in current_messages if m.get("id") != msg_id]
    save_all_messages(current_messages)
    st.session_state.messages = current_messages

def edit_message(msg_id, new_text):
    new_text = sanitize_html(new_text.strip())
    if not new_text: return
    current_messages = load_messages()
    for msg in current_messages:
        if msg.get("id") == msg_id:
            msg["text"] = new_text
            msg["edited"] = True
            break
    save_all_messages(current_messages)
    st.session_state.messages = current_messages

# ==================== AUTHENTICATION ====================
def sign_up(username, password, confirm):
    if not username or not password: return False, "Fill all fields"
    if password != confirm: return False, "Passwords don't match"
    if len(password) < 4: return False, "Password too short (min 4)"
    if len(username) < 2: return False, "Username too short"
    if len(username) > 20: return False, "Username too long"
    if not username.isalnum(): return False, "Only letters/numbers"
    
    users = load_users()
    if username.lower() in [u.lower() for u in users]: return False, "Username exists"
    
    users[username] = hash_password(password)
    save_users(users)
    
    profiles = load_profiles()
    profiles[username] = {"bio": "", "avatar": None, "wallpaper": DEFAULT_WALLPAPER, "status": "", "last_seen": datetime.now().isoformat()}
    save_profiles(profiles)
    
    return True, "Account created!"

def sign_in(username, password):
    users = load_users()
    for u, pwd in users.items():
        if u.lower() == username.lower():
            return (True, u) if pwd == hash_password(password) else (False, "Wrong password")
    return False, "User not found"

def sign_out():
    for key in ['authenticated', 'username', 'wallpaper', 'current_view', 'editing_msg_id', 'replying_to', 'viewing_profile']:
        if key in st.session_state:
            st.session_state[key] = "" if key in ['username', 'wallpaper', 'current_view'] else (False if key == 'authenticated' else None)
    st.session_state.authenticated = False
    st.rerun()

# ==================== SESSION STATE ====================
if 'initialized' not in st.session_state:
    st.session_state.messages = load_messages()
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.wallpaper = DEFAULT_WALLPAPER
    st.session_state.current_view = "chat"
    st.session_state.editing_msg_id = None
    st.session_state.replying_to = None
    st.session_state.show_emoji = False
    st.session_state.viewing_profile = None
    st.session_state.initialized = True
    st.session_state.msg_count = len(st.session_state.messages)

# Update messages efficiently
if st.session_state.get('authenticated'):
    new_msgs = load_messages()
    if len(new_msgs) != st.session_state.get('msg_count', 0):
        st.session_state.messages = new_msgs
        st.session_state.msg_count = len(new_msgs)
    
    profile_data = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile_data.get("wallpaper", DEFAULT_WALLPAPER)
    # Update last seen
    profiles = load_profiles()
    if st.session_state.username in profiles:
        profiles[st.session_state.username]["last_seen"] = datetime.now().isoformat()
        save_profiles(profiles)

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, WALLPAPERS[DEFAULT_WALLPAPER])

# ==================== OPTIMIZED CSS ====================
if wallpaper_url == "gradient_default":
    wallpaper_css = """background: linear-gradient(135deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%); background-size: 400% 400%; animation: gradientShift 15s ease infinite;"""
    overlay = "background: rgba(0,0,0,0.3);"
else:
    wallpaper_css = f'background-image: url("{wallpaper_url}"); background-size: cover; background-position: center; background-attachment: fixed;'
    overlay = "background: rgba(0,0,0,0.55); backdrop-filter: blur(8px);"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer {{visibility: hidden;}}
    
    @keyframes gradientShift {{ 0%{{background-position:0% 50%}} 50%{{background-position:100% 50%}} 100%{{background-position:0% 50%}} }}
    
    .stApp {{ {wallpaper_css} }}
    .stApp::before {{ content:""; position:fixed; top:0; left:0; width:100%; height:100%; {overlay} z-index:-1; }}
    
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, rgba(102,126,234,0.95), rgba(118,75,162,0.95), rgba(240,147,251,0.9), rgba(245,87,108,0.9), rgba(79,172,254,0.95)) !important;
        backdrop-filter: blur(20px); border-right: 2px solid rgba(255,255,255,0.2) !important;
    }}
    section[data-testid="stSidebar"] * {{ color: white !important; }}
    section[data-testid="stSidebar"] .stButton>button {{
        background: rgba(255,255,255,0.2) !important; border: 2px solid rgba(255,255,255,0.4) !important;
        backdrop-filter: blur(10px); font-weight: 600 !important; transition: all 0.2s !important;
    }}
    section[data-testid="stSidebar"] .stButton>button:hover {{
        background: rgba(255,255,255,0.4) !important; transform: translateY(-2px);
    }}
    
    .message-wrapper {{ display:flex; width:100%; margin-bottom:0.5rem; animation: fadeIn 0.2s ease; }}
    .message-wrapper.sent {{ justify-content:flex-end; }}
    .message-wrapper.received {{ justify-content:flex-start; }}
    @keyframes fadeIn {{ from{{opacity:0;transform:translateY(10px)}} to{{opacity:1;transform:translateY(0)}} }}
    
    .message-bubble {{
        max-width:70%; padding:0.6rem 0.9rem; border-radius:1rem; border:1px solid rgba(255,255,255,0.1);
        word-wrap:break-word; transition: all 0.2s;
    }}
    .sent .message-bubble {{ background: linear-gradient(135deg, rgba(102,126,234,0.4), rgba(118,75,162,0.4)); border-color: rgba(102,126,234,0.5); margin-right:0.5rem; }}
    .received .message-bubble {{ background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); margin-left:0.5rem; }}
    
    .message-username {{ font-size:0.7rem; font-weight:600; }}
    .sent .message-username {{ color:#c4b5fd; }}
    .received .message-username {{ color:#a5b4fc; }}
    .message-time {{ font-size:0.6rem; color:#94a3b8; }}
    .message-text {{ color:#f8fafc; font-size:0.9rem; line-height:1.4; }}
    
    .emoji-btn {{
        background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
        padding: 0.3rem 0.6rem; border-radius: 0.5rem; cursor: pointer; font-size: 1.2rem;
        transition: all 0.2s; display: inline-block; margin: 0.1rem;
    }}
    .emoji-btn:hover {{ background: rgba(255,255,255,0.3); transform: scale(1.2); }}
    
    .stButton>button {{
        background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none;
        border-radius: 0.8rem; padding: 0.5rem 1rem; font-weight: 600; transition: all 0.3s; width: 100%;
    }}
    .stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102,126,234,0.4); }}
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {{
        background: rgba(255,255,255,0.95); color: #1e293b; border: 1px solid rgba(102,126,234,0.3);
        border-radius: 1rem; padding: 0.7rem 1rem;
    }}
    
    .profile-card {{
        background: linear-gradient(135deg, rgba(102,126,234,0.3), rgba(240,147,251,0.3));
        backdrop-filter: blur(20px); border-radius: 1.5rem; padding: 2rem;
        border: 2px solid rgba(255,255,255,0.2); text-align: center;
    }}
    
    .theme-card {{
        border-radius: 0.8rem; overflow: hidden; border: 2px solid rgba(255,255,255,0.1);
        cursor: pointer; transition: all 0.2s; margin-bottom: 0.3rem;
    }}
    .theme-card:hover {{ transform: scale(1.05); border-color: #667eea; }}
    .theme-card.selected {{ border-color: #667eea; box-shadow: 0 0 20px rgba(102,126,234,0.4); }}
    
    .status-dot {{ width:10px; height:10px; border-radius:50%; display:inline-block; }}
    .status-online {{ background:#10b981; box-shadow: 0 0 10px rgba(16,185,129,0.5); }}
    .status-away {{ background:#fbbf24; }}
    .status-offline {{ background:#6b7280; }}
    
    ::-webkit-scrollbar {{ width:4px; }}
    ::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); }}
    ::-webkit-scrollbar-thumb {{ background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 2px; }}
    
    .attachment-preview {{ max-width:200px; border-radius:0.5rem; margin-top:0.3rem; cursor:pointer; }}
</style>
""", unsafe_allow_html=True)

# ==================== AUTH PAGE ====================
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center; padding:2rem 0;">
            <div style="font-size:4rem;">💬</div>
            <h1 style="color:white; background:linear-gradient(135deg,#667eea,#764ba2,#f093fb); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Chattier Pro</h1>
            <p style="color:#94a3b8;">Premium Community Forum</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Sign Up"])
        with tab1:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    success, result = sign_in(u, p)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.username = result
                        st.session_state.messages = load_messages()
                        st.session_state.msg_count = len(st.session_state.messages)
                        st.success(f"Welcome, {result}!")
                        time.sleep(0.3)
                        st.rerun()
                    else:
                        st.error(result)
        with tab2:
            with st.form("signup"):
                u = st.text_input("Username", placeholder="2-20 chars, letters/numbers")
                p = st.text_input("Password", type="password", placeholder="Min 4 chars")
                c = st.text_input("Confirm Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    success, msg = sign_up(u, p, c)
                    if success: st.success(msg)
                    else: st.error(msg)

# ==================== MAIN APP ====================
else:
    # Sidebar
    with st.sidebar:
        st.markdown('<div style="text-align:center;"><div style="font-size:3rem;">💬</div><h2>Chattier Pro</h2></div>', unsafe_allow_html=True)
        
        profile_data = get_user_profile(st.session_state.username)
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:1rem;">
            {get_avatar_html(st.session_state.username, 70)}
            <h3>@{st.session_state.username}</h3>
            <p style="font-size:0.75rem; opacity:0.9;">{sanitize_html(profile_data.get('status', 'No status'))[:60]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        views = {"💬 Chat": "chat", "👤 My Profile": "profile", "👥 Members": "members", "🎨 Themes": "themes"}
        for label, view in views.items():
            if st.button(label, use_container_width=True, key=f"nav_{view}"):
                st.session_state.current_view = view
                st.session_state.viewing_profile = None
                st.rerun()
        
        st.divider()
        st.markdown("### 📊 Stats")
        msgs = len(st.session_state.messages)
        users = len(set(m["username"] for m in st.session_state.messages)) if st.session_state.messages else 0
        st.metric("Messages", msgs)
        st.metric("Members", users)
        
        st.divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
    
    # ==================== CHAT VIEW ====================
    if st.session_state.current_view == "chat":
        st.markdown('<h2 style="color:white;">💬 Community Chat</h2>', unsafe_allow_html=True)
        
        if not st.session_state.messages:
            st.markdown('<div style="text-align:center;padding:3rem;color:#94a3b8;"><div style="font-size:4rem;">✨</div><h3>No messages</h3><p>Start the conversation!</p></div>', unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages[-30:]:
                is_own = msg["username"] == st.session_state.username
                msg_id = msg.get("id", "")
                align = "sent" if is_own else "received"
                
                if st.session_state.get("editing_msg_id") == msg_id:
                    with st.form(key=f"edit_{msg_id}"):
                        nt = st.text_input("Edit", value=msg['text'], label_visibility="collapsed")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.form_submit_button("💾", use_container_width=True):
                                edit_message(msg_id, nt)
                                st.session_state.editing_msg_id = None
                                st.rerun()
                        with c2:
                            if st.form_submit_button("✕", use_container_width=True):
                                st.session_state.editing_msg_id = None
                                st.rerun()
                else:
                    edited = ' <span style="font-size:0.6rem;color:#94a3b8;">(edited)</span>' if msg.get("edited") else ""
                    
                    st.markdown(f"""
                    <div class="message-wrapper {align}">
                        <div style="flex-shrink:0; align-self:flex-end; margin:{'0 0 0 0.5rem' if is_own else '0 0.5rem 0 0'};">{get_avatar_html(msg['username'], 28)}</div>
                        <div style="max-width:70%;">
                            <div class="message-bubble">
                                <div style="display:flex; align-items:center; gap:0.3rem; margin-bottom:0.2rem; {'justify-content:flex-end;' if is_own else ''}">
                                    <span class="message-username">{sanitize_html(msg['username'])}</span>
                                    <span class="message-time">• {format_time(msg.get('timestamp', ''))}{edited}</span>
                                </div>
                                {f'<div class="message-text">{msg["text"]}</div>' if msg.get("text") else ""}
                                {f'<a href="{msg["attachment"]}" target="_blank"><img src="{msg["attachment"]}" class="attachment-preview" /></a>' if msg.get("attachment") and msg.get("attachment_type") == "image" else ""}
                                {f'<a href="{msg["attachment"]}" target="_blank" style="color:#a5b4fc; text-decoration:underline;">📎 {msg.get("attachment_name", "File")}</a>' if msg.get("attachment") and msg.get("attachment_type") != "image" else ""}
                            </div>
                    """, unsafe_allow_html=True)
                    
                    # Quick actions
                    cols = st.columns([1,1,1,1,1,8])
                    with cols[0]:
                        if st.button("👍", key=f"l_{msg_id}"): add_reaction(msg_id, "👍"); st.rerun()
                    with cols[1]:
                        if st.button("❤️", key=f"h_{msg_id}"): add_reaction(msg_id, "❤️"); st.rerun()
                    with cols[2]:
                        if st.button("😂", key=f"f_{msg_id}"): add_reaction(msg_id, "😂"); st.rerun()
                    with cols[3]:
                        if st.button("↩️", key=f"r_{msg_id}"): st.session_state.replying_to = msg_id; st.rerun()
                    if is_own:
                        with cols[4]:
                            if st.button("✏️", key=f"e_{msg_id}"): st.session_state.editing_msg_id = msg_id; st.rerun()
                    
                    # Reactions display
                    if msg.get("reactions"):
                        rhtml = '<div style="margin-top:0.2rem; display:flex; gap:0.2rem; flex-wrap:wrap;">'
                        for em, users in msg["reactions"].items():
                            active = st.session_state.username in users
                            rhtml += f'<span style="background:rgba(255,255,255,{0.3 if active else 0.1}); padding:0.1rem 0.4rem; border-radius:1rem; font-size:0.75rem; border:1px solid rgba(255,255,255,{0.5 if active else 0.2});">{em} {len(users)}</span>'
                        rhtml += '</div>'
                        st.markdown(rhtml, unsafe_allow_html=True)
                    
                    if is_own:
                        if st.button("🗑️", key=f"d_{msg_id}"): delete_message(msg_id); st.rerun()
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Reply bar
        if st.session_state.get("replying_to"):
            rm = next((m for m in st.session_state.messages if m.get("id") == st.session_state.replying_to), None)
            if rm:
                c1, c2 = st.columns([10,1])
                with c1:
                    st.info(f"↩️ Replying to {rm['username']}: {rm.get('text','')[:50]}...")
                with c2:
                    if st.button("✕"): st.session_state.replying_to = None; st.rerun()
        
        # Emoji picker toggle
        c1, c2 = st.columns([1, 10])
        with c1:
            if st.button("😊 Emojis", use_container_width=True):
                st.session_state.show_emoji = not st.session_state.get('show_emoji', False)
        
        if st.session_state.get('show_emoji'):
            em_cols = st.columns(10)
            for i, emoji in enumerate(EMOJI_LIST[:50]):
                with em_cols[i % 10]:
                    if st.button(emoji, key=f"emoji_{i}"):
                        st.session_state.emoji_to_add = emoji
                        st.session_state.show_emoji = False
                        st.rerun()
        
        # Message input
        st.divider()
        with st.form("msg_form", clear_on_submit=True):
            default_text = st.session_state.get('emoji_to_add', '')
            if default_text:
                st.session_state.emoji_to_add = ''
            
            c1, c2, c3 = st.columns([5, 1, 1])
            with c1:
                msg_text = st.text_input("Message", placeholder=f"Type as @{st.session_state.username}...", label_visibility="collapsed", value=default_text, key="msg_in")
            with c2:
                attach_file = st.file_uploader("📎", type=['png','jpg','jpeg','gif','pdf','txt','zip'], label_visibility="collapsed", key="attach")
            with c3:
                send_btn = st.form_submit_button("📤", use_container_width=True)
            
            if send_btn:
                attachment_data = None
                attachment_name = None
                if attach_file:
                    try:
                        file_bytes = attach_file.read()
                        attachment_data = base64.b64encode(file_bytes).decode()
                        attachment_name = attach_file.name
                    except:
                        pass
                
                if msg_text.strip() or attachment_data:
                    send_message(msg_text if msg_text else "", attachment_data, attachment_name)
                    st.rerun()
    
    # ==================== PROFILE VIEW ====================
    elif st.session_state.current_view == "profile":
        st.markdown('<h2 style="color:white;">👤 My Profile</h2>', unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            st.markdown(get_avatar_html(st.session_state.username, 120), unsafe_allow_html=True)
            st.markdown(f"<h3>@{st.session_state.username}</h3>", unsafe_allow_html=True)
            
            profile = get_user_profile(st.session_state.username)
            status = profile.get('status', '')
            last_seen = profile.get('last_seen', '')
            if last_seen:
                try:
                    lt = datetime.fromisoformat(last_seen)
                    diff = (datetime.now() - lt).seconds
                    if diff < 300:
                        st.markdown('<span class="status-dot status-online"></span> Online', unsafe_allow_html=True)
                    elif diff < 3600:
                        st.markdown(f'<span class="status-dot status-away"></span> Last seen {diff//60}m ago', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="status-dot status-offline"></span> Offline', unsafe_allow_html=True)
                except:
                    pass
            st.markdown('</div>', unsafe_allow_html=True)
            
            avatar_file = st.file_uploader("Change Avatar", type=['png','jpg','jpeg'])
        
        with c2:
            with st.form("profile_form"):
                profile_data = get_user_profile(st.session_state.username)
                bio = st.text_area("Bio", value=profile_data.get("bio", ""), max_chars=200, placeholder="About yourself...", height=80)
                status = st.text_input("Status", value=profile_data.get("status", ""), max_chars=60, placeholder="What's on your mind?")
                
                c_a, c_b = st.columns(2)
                with c_a:
                    if st.form_submit_button("💾 Save", use_container_width=True):
                        update_profile(st.session_state.username, bio, avatar_file, st.session_state.wallpaper, status)
                        st.success("Updated!")
                        time.sleep(0.5)
                        st.rerun()
                with c_b:
                    if st.form_submit_button("↩️ Back", use_container_width=True):
                        st.session_state.current_view = "chat"
                        st.rerun()
    
    # ==================== MEMBERS VIEW ====================
    elif st.session_state.current_view == "members":
        # Check if viewing a specific profile
        if st.session_state.get('viewing_profile'):
            vp = st.session_state.viewing_profile
            profile = get_user_profile(vp)
            
            st.markdown(f'<h2 style="color:white;">👤 {sanitize_html(vp)}\'s Profile</h2>', unsafe_allow_html=True)
            
            if st.button("↩️ Back to Members"):
                st.session_state.viewing_profile = None
                st.rerun()
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown('<div class="profile-card">', unsafe_allow_html=True)
                st.markdown(get_avatar_html(vp, 120), unsafe_allow_html=True)
                st.markdown(f"<h3>@{sanitize_html(vp)}</h3>", unsafe_allow_html=True)
                
                status = profile.get('status', '')
                if status:
                    st.markdown(f'<p style="color:#94a3b8;">{sanitize_html(status)}</p>', unsafe_allow_html=True)
                
                last_seen = profile.get('last_seen', '')
                if last_seen:
                    try:
                        lt = datetime.fromisoformat(last_seen)
                        diff = (datetime.now() - lt).seconds
                        if diff < 300:
                            st.markdown('<span class="status-dot status-online"></span> Online now', unsafe_allow_html=True)
                        elif diff < 3600:
                            st.markdown(f'<span class="status-dot status-away"></span> {diff//60}m ago', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<span class="status-dot status-offline"></span> {format_time(last_seen)}', unsafe_allow_html=True)
                    except:
                        pass
                st.markdown('</div>', unsafe_allow_html=True)
            
            with c2:
                st.markdown("### About")
                bio = profile.get('bio', '')
                st.markdown(f'<p style="color:#f8fafc; background:rgba(255,255,255,0.1); padding:1rem; border-radius:0.5rem;">{sanitize_html(bio) if bio else "No bio yet"}</p>', unsafe_allow_html=True)
                
                # Show user's messages
                user_msgs = [m for m in st.session_state.messages if m["username"] == vp][-10:]
                if user_msgs:
                    st.markdown("### Recent Messages")
                    for m in reversed(user_msgs):
                        st.markdown(f'<div style="background:rgba(255,255,255,0.05); padding:0.5rem; border-radius:0.5rem; margin-bottom:0.3rem;"><span style="color:#94a3b8; font-size:0.7rem;">{format_time(m.get("timestamp",""))}</span><p style="color:#f8fafc; margin:0.2rem 0;">{m.get("text","")}</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<h2 style="color:white;">👥 Community Members</h2>', unsafe_allow_html=True)
            
            profiles = load_profiles()
            all_users = list(set([m["username"] for m in st.session_state.messages])) if st.session_state.messages else []
            
            if not all_users:
                st.info("No members yet. Send a message to be the first!")
            else:
                # Search
                search = st.text_input("🔍 Search members", placeholder="Type username...")
                filtered = [u for u in all_users if search.lower() in u.lower()] if search else all_users
                
                for i, user in enumerate(filtered[:20]):
                    if i % 3 == 0:
                        cols = st.columns(3)
                    
                    profile = get_user_profile(user)
                    last_seen = profile.get('last_seen', '')
                    is_online = False
                    if last_seen:
                        try:
                            is_online = (datetime.now() - datetime.fromisoformat(last_seen)).seconds < 300
                        except:
                            pass
                    
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.08); border-radius:1rem; padding:1rem; text-align:center; margin-bottom:0.5rem;">
                            {get_avatar_html(user, 60)}
                            <h4 style="color:white; margin:0.3rem 0;">@{sanitize_html(user)}</h4>
                            <span class="status-dot {'status-online' if is_online else 'status-offline'}"></span>
                            {'Online' if is_online else 'Offline'}
                            <p style="color:#94a3b8; font-size:0.7rem; margin-top:0.3rem;">{sanitize_html(profile.get('status', 'No status'))[:40]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("View Profile", key=f"vp_{user}", use_container_width=True):
                            st.session_state.viewing_profile = user
                            st.rerun()
    
    # ==================== THEMES VIEW ====================
    elif st.session_state.current_view == "themes":
        st.markdown(f'<h2 style="color:white;">🎨 Themes ({len(WALLPAPERS)})</h2>', unsafe_allow_html=True)
        
        search = st.text_input("🔍 Search", placeholder="Filter themes...")
        filtered = {k:v for k,v in WALLPAPERS.items() if search.lower() in k.lower()} if search else WALLPAPERS
        
        items = list(filtered.items())
        for i, (name, url) in enumerate(items):
            if i % 5 == 0:
                cols = st.columns(5)
            
            with cols[i % 5]:
                sel = name == st.session_state.wallpaper
                if url == "gradient_default":
                    st.markdown(f'<div class="theme-card {"selected" if sel else ""}" style="background:linear-gradient(135deg,#667eea,#764ba2,#f093fb,#f5576c,#4facfe);height:100px;display:flex;align-items:center;justify-content:center;"><span style="font-size:2rem;">🌈</span></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="theme-card {"selected" if sel else ""}"><img src="{url}" style="width:100%;height:100px;object-fit:cover;" /></div>', unsafe_allow_html=True)
                
                if st.button(f"{'✅' if sel else ''} {name}", key=f"th_{i}", use_container_width=True):
                    st.session_state.wallpaper = name
                    profiles = load_profiles()
                    if st.session_state.username in profiles:
                        profiles[st.session_state.username]["wallpaper"] = name
                    save_profiles(profiles)
                    st.rerun()
        
        if st.button("↩️ Back to Chat", use_container_width=True):
            st.session_state.current_view = "chat"
            st.rerun()

# Lightweight refresh (only checks for new messages)
if st.session_state.get('authenticated'):
    st.markdown("""
    <script>
        // Check for new messages every 2 seconds (lightweight)
        setInterval(function() {
            fetch(window.location.href).then(r => r.text()).then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newCount = doc.querySelectorAll('.message-wrapper').length;
                const currentCount = document.querySelectorAll('.message-wrapper').length;
                if (newCount > currentCount) {
                    window.location.reload();
                }
            });
        }, 2000);
    </script>
    """, unsafe_allow_html=True)

# Update last seen on activity
if st.session_state.get('authenticated'):
    profiles = load_profiles()
    if st.session_state.username in profiles:
        profiles[st.session_state.username]["last_seen"] = datetime.now().isoformat()
        save_profiles(profiles)
