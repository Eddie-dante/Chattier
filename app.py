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

# Page config MUST be first
st.set_page_config(
    page_title="Chattier • Community Forum",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== DATABASE CONFIGURATION ====================
try:
    JSONBIN_API_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_BIN_ID = st.secrets["jsonbin"]["bin_id"]
    USE_CLOUD = True
    CLOUD_TYPE = "☁️ Cloud Connected"
except:
    JSONBIN_API_KEY = os.environ.get("JSONBIN_API_KEY", "")
    JSONBIN_BIN_ID = os.environ.get("JSONBIN_BIN_ID", "")
    USE_CLOUD = bool(JSONBIN_API_KEY and JSONBIN_BIN_ID)
    CLOUD_TYPE = "☁️ Cloud Connected" if USE_CLOUD else "💻 Local Mode"

# ==================== FILE PATHS ====================
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# ==================== 40+ WALLPAPERS ====================
WALLPAPERS = {
    # Default wallpaper (colorful gradient - generated via CSS)
    "🌈 Colorful Gradient": "gradient_default",
    
    # Unsplash wallpapers
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
    "🌧️ Rainy Window": "https://images.unsplash.com/photo-1499951360447-b19be8fe80f5?w=1920&q=80",
    "🌻 Sunflower Field": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=1920&q=80",
    "🏰 Northern Lights": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1920&q=80",
    "🌴 Palm Sunset": "https://images.unsplash.com/photo-1509233725247-49e657c54213?w=1920&q=80",
    "🎆 Fireworks Night": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=1920&q=80",
    "🏛️ Ancient Ruins": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=1920&q=80",
    "🌵 Desert Night": "https://images.unsplash.com/photo-1507400492013-162706c8c05e?w=1920&q=80",
    "🌊 Stormy Sea": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1920&q=80",
    "🏔️ Snowy Mountains": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80",
    "🌅 Purple Dawn": "https://images.unsplash.com/photo-1506898667547-42e22a46e125?w=1920&q=80",
    "🍂 Autumn Road": "https://images.unsplash.com/photo-1507041957456-9c397ce39c97?w=1920&q=80",
    "🌺 Tropical Flowers": "https://images.unsplash.com/photo-1465146344425-f00d5f5c8f07?w=1920&q=80",
    "🌙 Moonlit Mountains": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=1920&q=80",
    "🏖️ Crystal Clear": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=1920&q=80",
    "🌄 Golden Hour": "https://images.unsplash.com/photo-1495616811223-4d98c6e9c869?w=1920&q=80",
    "🌿 Bamboo Forest": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&q=80",
    "🏜️ Red Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=1920&q=80",
    "🌊 Turquoise Waves": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=1920&q=80",
    "🌸 Spring Meadow": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=1920&q=80",
    "🌅 Sunset Silhouette": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1920&q=80",
}

DEFAULT_WALLPAPER = "🌈 Colorful Gradient"

# ==================== CLOUD DATABASE FUNCTIONS ====================

def load_from_jsonbin():
    if not USE_CLOUD:
        return None
    try:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest"
        headers = {"X-Master-Key": JSONBIN_API_KEY, "X-Bin-Meta": "false"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return data.get("messages", [])
        elif response.status_code == 404:
            create_bin()
        return None
    except:
        return None

def save_to_jsonbin(messages):
    if not USE_CLOUD:
        return False
    try:
        url = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
        headers = {
            "Content-Type": "application/json",
            "X-Master-Key": JSONBIN_API_KEY,
            "X-Bin-Versioning": "false"
        }
        data = {"messages": messages}
        response = requests.put(url, json=data, headers=headers, timeout=5)
        return response.status_code in [200, 201]
    except:
        return False

def create_bin():
    try:
        url = "https://api.jsonbin.io/v3/b"
        headers = {
            "Content-Type": "application/json",
            "X-Master-Key": JSONBIN_API_KEY,
            "X-Bin-Name": "chattier-messages",
            "X-Bin-Private": "false"
        }
        response = requests.post(url, json={"messages": []}, headers=headers, timeout=5)
        if response.status_code in [200, 201]:
            result = response.json()
            new_bin_id = result.get("metadata", {}).get("id", "")
            if new_bin_id:
                save_json(pathlib.Path("data/bin_id.json"), {"bin_id": new_bin_id})
                return True
    except:
        pass
    return False

# ==================== HELPER FUNCTIONS ====================

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
    except:
        pass
    return default if default is not None else {}

def save_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

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
    except:
        pass
    
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7B787',
              '#FF8A80', '#B388FF', '#82B1FF', '#B9F6CA', '#FFE57F', '#FF80AB', '#EA80FC', '#8C9EFF']
    color_idx = hash(username) % len(colors)
    bg_color = colors[color_idx]
    letter = username[0].upper() if username else "?"
    return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{bg_color};display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;">{letter}</div>'

def load_messages():
    if USE_CLOUD:
        cloud_messages = load_from_jsonbin()
        if cloud_messages is not None:
            return cloud_messages
    return load_json(MESSAGES_FILE, [])

def save_all_messages(messages):
    if len(messages) > 500:
        messages = messages[-500:]
    if USE_CLOUD:
        save_to_jsonbin(messages)
    save_json(MESSAGES_FILE, messages)
    return True

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
        return t.strftime("%b %d, %I:%M %p")
    except:
        return ""

def send_message(text):
    if not text or not text.strip():
        return False
    text = sanitize_html(text.strip())
    if len(text) > 500:
        return False
    
    current_messages = load_messages()
    
    msg = {
        "id": str(uuid.uuid4()),
        "username": st.session_state.username,
        "text": text,
        "timestamp": datetime.now().isoformat(),
        "reactions": {}
    }
    current_messages.append(msg)
    
    if save_all_messages(current_messages):
        st.session_state.messages = current_messages
        return True
    return False

def add_reaction(msg_id, emoji):
    try:
        current_messages = load_messages()
        for msg in current_messages:
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
        
        save_all_messages(current_messages)
        st.session_state.messages = current_messages
        return True
    except:
        return False

def delete_message(msg_id):
    try:
        current_messages = load_messages()
        current_messages = [m for m in current_messages if m.get("id") != msg_id]
        save_all_messages(current_messages)
        st.session_state.messages = current_messages
        return True
    except:
        return False

def edit_message(msg_id, new_text):
    try:
        new_text = sanitize_html(new_text.strip())
        if not new_text:
            return False
        
        current_messages = load_messages()
        for msg in current_messages:
            if msg.get("id") == msg_id:
                msg["text"] = new_text
                msg["edited"] = True
                break
        
        save_all_messages(current_messages)
        st.session_state.messages = current_messages
        return True
    except:
        return False

# ==================== AUTHENTICATION ====================

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
    
    return True, "Account created! Please sign in."

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

# ==================== SESSION STATE ====================

if 'initialized' not in st.session_state:
    st.session_state.messages = load_messages()
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.wallpaper = DEFAULT_WALLPAPER
    st.session_state.current_view = "chat"
    st.session_state.editing_msg_id = None
    st.session_state.replying_to = None
    st.session_state.sidebar_state = "expanded"
    st.session_state.initialized = True
    st.session_state.message_count = len(st.session_state.messages)

if st.session_state.get('authenticated', False):
    current_messages = load_messages()
    if len(current_messages) != st.session_state.get('message_count', 0):
        st.session_state.messages = current_messages
        st.session_state.message_count = len(current_messages)

if st.session_state.get('authenticated', False):
    profile_data = get_user_profile(st.session_state.username)
    st.session_state.wallpaper = profile_data.get("wallpaper", DEFAULT_WALLPAPER)

wallpaper_url = WALLPAPERS.get(st.session_state.wallpaper, WALLPAPERS[DEFAULT_WALLPAPER])

# ==================== CUSTOM CSS ====================

# Handle default gradient wallpaper
if wallpaper_url == "gradient_default":
    wallpaper_css = """
        background: linear-gradient(135deg, 
            #667eea 0%, #764ba2 25%, #f093fb 50%, #f5576c 75%, #4facfe 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    """
    wallpaper_overlay = "background: rgba(0, 0, 0, 0.3);"
else:
    wallpaper_css = f'background-image: url("{wallpaper_url}"); background-size: cover; background-position: center; background-attachment: fixed;'
    wallpaper_overlay = "background: rgba(0, 0, 0, 0.55); backdrop-filter: blur(8px);"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    
    /* Animated gradient keyframes */
    @keyframes gradientShift {{
        0% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}
    
    @keyframes sidebarGlow {{
        0%, 100% {{ box-shadow: 0 0 20px rgba(102, 126, 234, 0.3); }}
        50% {{ box-shadow: 0 0 40px rgba(240, 147, 251, 0.5), 0 0 60px rgba(102, 126, 234, 0.3); }}
    }}
    
    .stApp {{
        {wallpaper_css}
    }}
    
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        {wallpaper_overlay}
        z-index: -1;
    }}
    
    /* Colorful Gradient Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, 
            rgba(102, 126, 234, 0.95) 0%,
            rgba(118, 75, 162, 0.95) 20%,
            rgba(240, 147, 251, 0.9) 40%,
            rgba(245, 87, 108, 0.9) 60%,
            rgba(79, 172, 254, 0.95) 80%,
            rgba(102, 126, 234, 0.95) 100%) !important;
        backdrop-filter: blur(20px);
        animation: sidebarGlow 3s ease-in-out infinite;
        border-right: 2px solid rgba(255, 255, 255, 0.2) !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: white !important;
    }}
    
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255, 255, 255, 0.2) !important;
        border: 2px solid rgba(255, 255, 255, 0.4) !important;
        color: white !important;
        backdrop-filter: blur(10px);
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }}
    
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: rgba(255, 255, 255, 0.4) !important;
        border-color: rgba(255, 255, 255, 0.8) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }}
    
    section[data-testid="stSidebar"] hr {{
        border-color: rgba(255, 255, 255, 0.3) !important;
    }}
    
    .message-bubble {{
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 0.5rem;
        animation: fadeIn 0.2s ease;
        transition: all 0.3s ease;
    }}
    
    .message-bubble:hover {{
        background: rgba(255, 255, 255, 0.15);
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .message-own {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
        border-color: rgba(102, 126, 234, 0.5);
    }}
    
    .message-own:hover {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.4), rgba(118, 75, 162, 0.4));
    }}
    
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
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255, 255, 255, 0.95);
        color: #1e293b;
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 1rem;
        padding: 0.7rem 1rem;
    }}
    
    .profile-card {{
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(240, 147, 251, 0.3));
        backdrop-filter: blur(20px);
        border-radius: 1.5rem;
        padding: 2rem;
        border: 2px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }}
    
    .theme-card {{
        border-radius: 1rem;
        overflow: hidden;
        border: 2px solid rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition: all 0.3s;
        margin-bottom: 0.5rem;
    }}
    
    .theme-card:hover {{ transform: scale(1.05); }}
    .theme-card.selected {{ border-color: #667eea; box-shadow: 0 0 20px rgba(102, 126, 234, 0.4); }}
    
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: rgba(255, 255, 255, 0.05); }}
    ::-webkit-scrollbar-thumb {{ background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 3px; }}
    
    .status-badge {{
        position: fixed;
        top: 10px;
        right: 10px;
        padding: 0.4rem 1rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        z-index: 1000;
        font-weight: 600;
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.7; }}
    }}
    
    .status-connected {{ 
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.3), rgba(79, 172, 254, 0.3)); 
        color: #10b981; 
        border: 1px solid rgba(16, 185, 129, 0.5); 
    }}
    .status-local {{ 
        background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 87, 108, 0.3)); 
        color: #fbbf24; 
        border: 1px solid rgba(251, 191, 36, 0.5); 
    }}
    
    .live-indicator {{
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: livePulse 1s infinite;
    }}
    
    @keyframes livePulse {{
        0%, 100% {{ box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
        50% {{ box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }}
    }}
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR COLLAPSE SCRIPT ====================
st.markdown("""
<script>
    // Function to collapse sidebar
    function collapseSidebar() {
        const sidebar = parent.document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            const button = sidebar.querySelector('button[kind="header"]');
            if (button) {
                button.click();
            }
        }
    }
    
    // Add click listeners to navigation buttons
    setTimeout(() => {
        const buttons = parent.document.querySelectorAll('[data-testid="stSidebar"] button');
        buttons.forEach(button => {
            if (button.textContent.includes('Chat Room') || 
                button.textContent.includes('Profile Settings') || 
                button.textContent.includes('Themes')) {
                button.addEventListener('click', () => {
                    setTimeout(collapseSidebar, 300);
                });
            }
        });
    }, 1000);
</script>
""", unsafe_allow_html=True)

# ==================== AUTH PAGE ====================

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem; animation: float 3s ease-in-out infinite;">💬</div>
            <h1 style="color: white; margin-bottom: 0.5rem; background: linear-gradient(135deg, #667eea, #764ba2, #f093fb); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Chattier</h1>
            <p style="color: #94a3b8; margin-bottom: 2rem;">Community Forum</p>
        </div>
        <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
        </style>
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
                        st.session_state.messages = load_messages()
                        st.session_state.message_count = len(st.session_state.messages)
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

# ==================== MAIN APP ====================

else:
    # Status badge
    status_class = "status-connected" if USE_CLOUD else "status-local"
    st.markdown(f"""
    <div class="status-badge {status_class}">
        <span class="live-indicator"></span>{CLOUD_TYPE}
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh button
    col_refresh, col_space = st.columns([1, 10])
    with col_refresh:
        if st.button("🔄", key="refresh_btn", help="Instant refresh"):
            st.session_state.messages = load_messages()
            st.session_state.message_count = len(st.session_state.messages)
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; filter: drop-shadow(0 0 10px rgba(255,255,255,0.5));">💬</div>
            <h2 style="color: white; margin: 0.5rem 0; text-shadow: 0 0 20px rgba(255,255,255,0.3);">Chattier</h2>
        </div>
        """, unsafe_allow_html=True)
        
        profile_data = get_user_profile(st.session_state.username)
        avatar_html = get_avatar_html(st.session_state.username, 80)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            {avatar_html}
            <h3 style="color: white; margin: 0.5rem 0; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">@{st.session_state.username}</h3>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.8rem;">{sanitize_html(profile_data.get('bio', 'No bio yet'))[:80]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown("### 📱 Navigation")
        
        if st.button("💬 Chat Room", use_container_width=True, key="nav_chat"):
            st.session_state.current_view = "chat"
            st.session_state.editing_msg_id = None
            st.session_state.messages = load_messages()
            st.rerun()
        
        if st.button("👤 Profile Settings", use_container_width=True, key="nav_profile"):
            st.session_state.current_view = "profile"
            st.rerun()
        
        if st.button("🎨 Themes", use_container_width=True, key="nav_themes"):
            st.session_state.current_view = "themes"
            st.rerun()
        
        st.divider()
        st.markdown("### 📊 Community Stats")
        
        total_messages = len(st.session_state.messages)
        unique_users = len(set(m["username"] for m in st.session_state.messages)) if st.session_state.messages else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", total_messages)
        with col2:
            st.metric("Members", unique_users)
        
        if st.session_state.messages:
            st.markdown("### 🟢 Recent Users")
            recent = list(dict.fromkeys([m["username"] for m in reversed(st.session_state.messages)]))[:5]
            for user in recent:
                st.markdown(f"• {user}")
        
        st.divider()
        
        if not USE_CLOUD:
            st.warning("⚠️ Add JSONBin keys in Secrets for cross-device chat!")
        
        if st.button("🚪 Sign Out", use_container_width=True):
            sign_out()
    
    # Main content area
    if st.session_state.current_view == "chat":
        st.markdown('<h2 style="color: white; margin-bottom: 1rem;">💬 Community Chat <span class="live-indicator" style="display: inline-block;"></span> LIVE</h2>', unsafe_allow_html=True)
        
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #94a3b8;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">✨</div>
                <h3>No messages yet</h3>
                <p>Be the first to start the conversation!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages[-50:]:
                is_own = msg["username"] == st.session_state.username
                msg_id = msg.get("id", "")
                
                if st.session_state.get("editing_msg_id") == msg_id:
                    with st.form(key=f"edit_{msg_id}"):
                        new_text = st.text_input("Edit", value=msg['text'], key=f"input_{msg_id}", label_visibility="collapsed")
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
                        
                        cols = st.columns([1, 1, 1, 1, 1, 10])
                        
                        with cols[0]:
                            if st.button("👍", key=f"like_{msg_id}"):
                                add_reaction(msg_id, "👍")
                                st.rerun()
                        with cols[1]:
                            if st.button("❤️", key=f"love_{msg_id}"):
                                add_reaction(msg_id, "❤️")
                                st.rerun()
                        with cols[2]:
                            if st.button("😂", key=f"laugh_{msg_id}"):
                                add_reaction(msg_id, "😂")
                                st.rerun()
                        with cols[3]:
                            if st.button("↩️", key=f"reply_{msg_id}"):
                                st.session_state.replying_to = msg_id
                                st.rerun()
                        if is_own:
                            with cols[4]:
                                if st.button("✏️", key=f"editbtn_{msg_id}"):
                                    st.session_state.editing_msg_id = msg_id
                                    st.rerun()
                        
                        if msg.get("reactions"):
                            reaction_html = '<div style="margin-top: 0.3rem; display: flex; gap: 0.3rem; flex-wrap: wrap;">'
                            for emoji, users in msg["reactions"].items():
                                count = len(users)
                                is_user = st.session_state.username in users
                                opacity = "0.3" if is_user else "0.1"
                                border = "0.5" if is_user else "0.2"
                                reaction_html += f'<span style="background: rgba(255,255,255,{opacity}); padding: 0.1rem 0.5rem; border-radius: 1rem; font-size: 0.8rem; border: 1px solid rgba(255,255,255,{border});">{emoji} {count}</span>'
                            reaction_html += '</div>'
                            st.markdown(reaction_html, unsafe_allow_html=True)
                        
                        if is_own:
                            if st.button("🗑️ Delete", key=f"delete_{msg_id}"):
                                if delete_message(msg_id):
                                    st.rerun()
        
        if st.session_state.get("replying_to"):
            reply_msg = next((m for m in st.session_state.messages if m.get("id") == st.session_state.replying_to), None)
            if reply_msg:
                col1, col2 = st.columns([10, 1])
                with col1:
                    st.markdown(f"""
                    <div style="background: rgba(102,126,234,0.2); padding: 0.5rem 1rem; border-radius: 0.5rem; margin-bottom: 0.5rem; color: #94a3b8;">
                        ↩️ Replying to <strong style="color: white;">{sanitize_html(reply_msg['username'])}</strong>: {sanitize_html(reply_msg['text'][:50])}...
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("✕", key="cancel_reply"):
                        st.session_state.replying_to = None
                        st.rerun()
        
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
                    st.session_state.message_count = len(st.session_state.messages)
                    st.rerun()
    
    elif st.session_state.current_view == "profile":
        st.markdown('<h2 style="color: white;">👤 Profile Settings</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="profile-card">', unsafe_allow_html=True)
            avatar_html = get_avatar_html(st.session_state.username, 150)
            st.markdown(avatar_html, unsafe_allow_html=True)
            st.markdown(f"<h3 style='color: white;'>@{st.session_state.username}</h3>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
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
        st.markdown('<h2 style="color: white;">🎨 Choose Theme</h2>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #94a3b8; margin-bottom: 1rem;">{len(WALLPAPERS)} beautiful wallpapers available</p>', unsafe_allow_html=True)
        
        search = st.text_input("🔍 Search themes", placeholder="Type to filter...")
        
        filtered_wallpapers = WALLPAPERS
        if search:
            filtered_wallpapers = {k: v for k, v in WALLPAPERS.items() if search.lower() in k.lower()}
        
        if not filtered_wallpapers:
            st.info("No themes found matching your search")
        else:
            wallpaper_items = list(filtered_wallpapers.items())
            for i, (theme_name, theme_url) in enumerate(wallpaper_items):
                if i % 4 == 0:
                    cols = st.columns(4)
                
                with cols[i % 4]:
                    is_selected = theme_name == st.session_state.wallpaper
                    
                    # Show gradient preview for default wallpaper
                    if theme_url == "gradient_default":
                        st.markdown(f"""
                        <div class="theme-card {'selected' if is_selected else ''}" style="background: linear-gradient(135deg, #667eea, #764ba2, #f093fb, #f5576c, #4facfe); height: 120px; display: flex; align-items: center; justify-content: center;">
                            <span style="color: white; font-size: 2rem; text-shadow: 0 0 20px rgba(255,255,255,0.5);">🌈</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
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

# Ultra-fast auto-refresh
if st.session_state.get('authenticated', False):
    st.markdown("""
    <script>
        setInterval(function() {
            window.location.reload();
        }, 5);
    </script>
    """, unsafe_allow_html=True)
