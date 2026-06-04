import streamlit as st
import json
import os
import html
import hashlib
import pathlib
from datetime import datetime, timedelta
import uuid
import base64
from PIL import Image
import time
import requests
from typing import Dict, List, Optional, Any, Tuple
import secrets
import logging
import io
import shutil

# Must be first Streamlit command
st.set_page_config(page_title="SocialHub Pro", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")

# ========== CONSTANTS ==========
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
FEED_POSTS_FILE = DATA_DIR / "feed_posts.json"
STORIES_FILE = DATA_DIR / "stories.json"
DIRECT_MESSAGES_FILE = DATA_DIR / "direct_messages.json"
GROUP_CHATS_FILE = DATA_DIR / "group_chats.json"
CHANNELS_FILE = DATA_DIR / "channels.json"
COMMENTS_FILE = DATA_DIR / "comments.json"
NOTIFICATIONS_FILE = DATA_DIR / "notifications.json"

MAX_POST_LENGTH = 2000
MAX_BIO_LENGTH = 200
MAX_MESSAGE_LENGTH = 1000
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 6
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_AVATAR_SIZE = 5 * 1024 * 1024
STORY_EXPIRY_HOURS = 24

AVATAR_COLORS = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7B787','#FF8A80','#B388FF','#FF5722','#9C27B0','#3F51B5','#009688','#FF9800']

# ========== LUXURY REACTIONS ==========
LUXURY_REACTIONS = {
    "crown": {"emoji": "👑", "label": "Top Tier", "color": "#FFD700"},
    "diamond": {"emoji": "💎", "label": "Brilliant", "color": "#B9F2FF"},
    "cheers": {"emoji": "🥂", "label": "Cheers", "color": "#FFE4B5"},
    "tophat": {"emoji": "🎩", "label": "Class", "color": "#C0C0C0"},
    "sparkle": {"emoji": "✨", "label": "Premium", "color": "#FFF8DC"},
    "fleur": {"emoji": "⚜️", "label": "Royal", "color": "#FFD700"},
}

# ========== SVG AVATARS ==========
MALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' style='stop-color:#667eea'/><stop offset='100%' style='stop-color:#764ba2'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='url(#g)' stroke='#FFD700' stroke-width='2'/><circle cx='50' cy='38' r='14' fill='#f1f5f9'/><ellipse cx='50' cy='72' rx='20' ry='16' fill='#f1f5f9'/></svg>"""
FEMALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='g' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' style='stop-color:#f093fb'/><stop offset='100%' style='stop-color:#f5576c'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='url(#g)' stroke='#FFD700' stroke-width='2'/><circle cx='50' cy='38' r='14' fill='#fce4ec'/><ellipse cx='50' cy='72' rx='18' ry='14' fill='#fce4ec'/></svg>"""

# ========== 20+ THEMES ==========
THEMES = {
    "midnight": {"name": "Midnight Galaxy", "icon": "🌌", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"},
    "ocean": {"name": "Deep Ocean", "icon": "🌊", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"},
    "sunset": {"name": "Golden Sunset", "icon": "🌅", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)"},
    "forest": {"name": "Enchanted Forest", "icon": "🌲", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50", "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)"},
    "neon": {"name": "Neon Nights", "icon": "💜", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
    "coffee": {"name": "Coffee Aroma", "icon": "☕", "bg": "#1a0f0a", "card": "rgba(255,255,255,0.04)", "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#8d6e63", "gradient": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)"},
    "cherry": {"name": "Cherry Blossom", "icon": "🌸", "bg": "#1a0a1a", "card": "rgba(255,255,255,0.05)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#e91e63", "gradient": "linear-gradient(135deg, #1a0a1a 0%, #2e1a2e 50%, #4e2d4e 100%)"},
    "mint": {"name": "Fresh Mint", "icon": "🌿", "bg": "#0a1a1a", "card": "rgba(255,255,255,0.04)", "text": "#e0f2f1", "secondary": "#80cbc4", "accent": "#00bfa5", "gradient": "linear-gradient(135deg, #0a1a1a 0%, #1a2e2e 50%, #2d4e4e 100%)"},
    "royal": {"name": "Royal Purple", "icon": "👑", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)"},
    "crimson": {"name": "Crimson Red", "icon": "❤️", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336", "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)"},
    "arctic": {"name": "Arctic Frost", "icon": "❄️", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)"},
    "ember": {"name": "Burning Ember", "icon": "🔥", "bg": "#1a0f00", "card": "rgba(255,255,255,0.04)", "text": "#fff3e0", "secondary": "#ffcc80", "accent": "#ff9800", "gradient": "linear-gradient(135deg, #1a0f00 0%, #2e1a00 50%, #4e2d00 100%)"},
    "plum": {"name": "Plum Garden", "icon": "🫐", "bg": "#1a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#7b1fa2", "gradient": "linear-gradient(135deg, #1a0a1a 0%, #2e1a2e 50%, #4e2d4e 100%)"},
    "teal": {"name": "Teal Paradise", "icon": "🦋", "bg": "#0a1a1a", "card": "rgba(255,255,255,0.04)", "text": "#e0f2f1", "secondary": "#80cbc4", "accent": "#009688", "gradient": "linear-gradient(135deg, #0a1a1a 0%, #1a2e2e 50%, #2d4e4e 100%)"},
    "slate": {"name": "Dark Slate", "icon": "🪨", "bg": "#1a1a2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#9fa8da", "accent": "#5c6bc0", "gradient": "linear-gradient(135deg, #1a1a2e 0%, #2e2e4e 50%, #4e4e7a 100%)"},
    "rosegold": {"name": "Rose Gold", "icon": "🌹", "bg": "#1a0f1a", "card": "rgba(255,255,255,0.05)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#c2185b", "gradient": "linear-gradient(135deg, #1a0f1a 0%, #2e1a2e 50%, #4e2d4e 100%)"},
    "midnightblue": {"name": "Midnight Blue", "icon": "🌃", "bg": "#0f0f2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#7986cb", "accent": "#3f51b5", "gradient": "linear-gradient(135deg, #0f0f2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
    "chocolate": {"name": "Dark Chocolate", "icon": "🍫", "bg": "#1a1005", "card": "rgba(255,255,255,0.04)", "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#795548", "gradient": "linear-gradient(135deg, #1a1005 0%, #2e1a0a 50%, #4e2d15 100%)"},
    "lavender": {"name": "Lavender Fields", "icon": "💐", "bg": "#1a0f2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#b39ddb", "accent": "#673ab7", "gradient": "linear-gradient(135deg, #1a0f2e 0%, #2e1a4e 50%, #4e2d7a 100%)"},
    "aqua": {"name": "Aqua Marine", "icon": "🐠", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e0f7fa", "secondary": "#80deea", "accent": "#00bcd4", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)"},
    "coral": {"name": "Coral Reef", "icon": "🐚", "bg": "#1a0a0f", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#ff6f61", "gradient": "linear-gradient(135deg, #1a0a0f 0%, #2e1a1a 50%, #4e2d2d 100%)"},
    "sage": {"name": "Sage Green", "icon": "🌱", "bg": "#0f1a0f", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#a5d6a7", "accent": "#66bb6a", "gradient": "linear-gradient(135deg, #0f1a0f 0%, #1a2e1a 50%, #2d4e2d 100%)"},
    "indigo": {"name": "Indigo Night", "icon": "💙", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#9fa8da", "accent": "#3949ab", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
    "peach": {"name": "Peach Dream", "icon": "🍑", "bg": "#1a0f0a", "card": "rgba(255,255,255,0.04)", "text": "#fff3e0", "secondary": "#ffcc80", "accent": "#ff7043", "gradient": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)"},
}

# ========== 30 WALLPAPERS ==========
WALLPAPERS = {
    "wp_luxury": {"name": "Luxury Gold", "icon": "👑", "url": None, "gradient": "linear-gradient(135deg, #1a0033 0%, #4a0066 25%, #800080 50%, #4a0080 75%, #1a0033 100%)"},
    "wp_purple": {"name": "Purple Haze", "icon": "✨", "url": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&q=60"},
    "wp_nebula": {"name": "Cosmic Nebula", "icon": "🌌", "url": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60"},
    "wp_ocean": {"name": "Ocean Waves", "icon": "🌊", "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=800&q=60"},
    "wp_stars": {"name": "Starry Mountains", "icon": "🏔️", "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60"},
    "wp_cherry": {"name": "Cherry Blossoms", "icon": "🌸", "url": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=60"},
    "wp_sunset": {"name": "Sunset Beach", "icon": "🌅", "url": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&q=60"},
    "wp_forest": {"name": "Forest Path", "icon": "🌿", "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=60"},
    "wp_city": {"name": "City Lights", "icon": "🏙️", "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=60"},
    "wp_lava": {"name": "Lava Flow", "icon": "🔥", "url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=60"},
    "wp_cyber": {"name": "Cyber Punk", "icon": "🎨", "url": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=800&q=60"},
    "wp_beach": {"name": "Tropical Beach", "icon": "🏝️", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=60"},
    "wp_aurora": {"name": "Aurora Borealis", "icon": "❄️", "url": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60"},
    "wp_autumn": {"name": "Autumn Leaves", "icon": "🍁", "url": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=800&q=60"},
    "wp_lavender": {"name": "Lavender Fields", "icon": "💜", "url": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=800&q=60"},
    "wp_alpine": {"name": "Alpine Peak", "icon": "🏔️", "url": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60"},
    "wp_desert": {"name": "Desert Dunes", "icon": "🌄", "url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800&q=60"},
    "wp_sunflower": {"name": "Sunflower Field", "icon": "🌻", "url": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=800&q=60"},
    "wp_northern": {"name": "Northern Lights", "icon": "🏰", "url": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=800&q=60"},
    "wp_fireworks": {"name": "Fireworks", "icon": "🎆", "url": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=800&q=60"},
    "wp_storm": {"name": "Stormy Sea", "icon": "🌊", "url": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800&q=60"},
    "wp_crystal": {"name": "Crystal Waters", "icon": "🏖️", "url": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=800&q=60"},
    "wp_canyon": {"name": "Grand Canyon", "icon": "🏜️", "url": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=800&q=60"},
    "wp_turquoise": {"name": "Turquoise Bay", "icon": "🌊", "url": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=800&q=60"},
    "wp_meadow": {"name": "Mountain Meadow", "icon": "🌸", "url": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=800&q=60"},
    "wp_abstract": {"name": "Abstract Art", "icon": "🎭", "url": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=800&q=60"},
    "wp_temple": {"name": "Japanese Temple", "icon": "🏯", "url": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=60"},
    "wp_greece": {"name": "Santorini", "icon": "🏛️", "url": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=60"},
    "wp_volcano": {"name": "Volcano", "icon": "🌋", "url": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=800&q=60"},
    "wp_sahara": {"name": "Sahara Desert", "icon": "🏜️", "url": "https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=800&q=60"},
}

# ========== UTILITY FUNCTIONS ==========
def validate_image(data: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except: return False

def sanitize_text(text: str, max_length: int = 2000) -> str:
    if not text: return ""
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    return html.escape(str(text).strip())[:max_length]

def format_timestamp(ts: str) -> str:
    if not ts: return ""
    try:
        t = datetime.fromisoformat(ts)
        diff = (datetime.now() - t).total_seconds()
        if diff < 5: return "now"
        elif diff < 60: return f"{int(diff)}s"
        elif diff < 3600: return f"{int(diff//60)}m"
        elif diff < 86400: return f"{int(diff//3600)}h"
        return t.strftime("%b %d")
    except: return ""

def generate_id() -> str: return str(uuid.uuid4())
def get_avatar_color(username: str) -> str: return AVATAR_COLORS[hash(username) % len(AVATAR_COLORS)] if username else AVATAR_COLORS[0]
def get_initials(username: str) -> str:
    if not username: return "?"
    return username[0].upper()

def get_svg_avatar(username: str, size: int = 36, is_female: bool = False) -> str:
    svg = FEMALE_SVG if is_female else MALE_SVG
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #FFD700;flex-shrink:0;" alt="{username}">'

def atomic_save(filepath: pathlib.Path, data: Any) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(filepath)
        return True
    except: return False

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== DATA MANAGER ==========
class DataManager:
    @staticmethod
    def load(filepath: pathlib.Path, default=None):
        if default is None: default = {}
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
        return default
    @staticmethod
    def save(filepath: pathlib.Path, data) -> bool: return atomic_save(filepath, data)
    @staticmethod
    def hash_password(pwd: str, salt: str = None) -> Tuple[str, str]:
        if salt is None: salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000)
        return h.hex(), salt
    @staticmethod
    def verify_password(pwd: str, stored_hash: str, salt: str) -> bool:
        h, _ = DataManager.hash_password(pwd, salt); return h == stored_hash
    @staticmethod
    def get_users() -> Dict: return DataManager.load(USERS_FILE, {})
    @staticmethod
    def save_users(data: Dict): DataManager.save(USERS_FILE, data)
    @staticmethod
    def user_exists(username: str) -> bool: return username.lower() in [u.lower() for u in DataManager.get_users()]
    @staticmethod
    def create_user(username: str, password: str) -> Tuple[bool, str]:
        if DataManager.user_exists(username): return False, "Username exists"
        users = DataManager.get_users(); h, s = DataManager.hash_password(password)
        users[username] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
        DataManager.save_users(users)
        profiles = DataManager.get_profiles(); profiles[username] = DataManager._default_profile(username)
        DataManager.save_profiles(profiles)
        return True, "Account created!"
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, str]:
        users = DataManager.get_users()
        for un, data in users.items():
            if un.lower() == username.lower():
                if isinstance(data, dict) and "salt" in data:
                    if DataManager.verify_password(password, data["password"], data["salt"]): return True, un
                elif isinstance(data, str) and data == hashlib.sha256(password.encode()).hexdigest():
                    h, s = DataManager.hash_password(password); users[un] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
                    DataManager.save_users(users); return True, un
                return False, "Wrong password"
        return False, "User not found"
    @staticmethod
    def _default_profile(username: str) -> Dict:
        return {"display_name": username, "bio": "", "avatar": None, "website": "", "location": "", "is_verified": False, "last_seen": "", "followers": [], "following": [], "blocked": [], "post_count": 0, "theme": "midnight", "wallpaper": "wp_luxury", "gender": "male", "created_at": datetime.now().isoformat()}
    @staticmethod
    def get_profiles() -> Dict: return DataManager.load(PROFILES_FILE, {})
    @staticmethod
    def save_profiles(data: Dict): DataManager.save(PROFILES_FILE, data)
    @staticmethod
    def get_profile(username: str) -> Dict:
        profiles = DataManager.get_profiles()
        if username not in profiles: profiles[username] = DataManager._default_profile(username); DataManager.save_profiles(profiles)
        p = profiles[username]
        for k, v in DataManager._default_profile(username).items():
            if k not in p: p[k] = v
        return p
    @staticmethod
    def update_profile(username: str, updates: Dict):
        profiles = DataManager.get_profiles()
        if username in profiles: profiles[username].update(updates); DataManager.save_profiles(profiles)
    @staticmethod
    def update_last_seen(username: str):
        profiles = DataManager.get_profiles()
        if username in profiles: profiles[username]["last_seen"] = datetime.now().isoformat(); DataManager.save_profiles(profiles)
    @staticmethod
    def get_feed_posts() -> List: return DataManager.load(FEED_POSTS_FILE, [])
    @staticmethod
    def save_feed_posts(data: List):
        if len(data) > 500: data = data[-300:]
        DataManager.save(FEED_POSTS_FILE, data)
    @staticmethod
    def get_stories() -> Dict: return DataManager.load(STORIES_FILE, {})
    @staticmethod
    def save_stories(data: Dict): DataManager.save(STORIES_FILE, data)
    @staticmethod
    def get_active_stories() -> Dict:
        stories = DataManager.get_stories(); active = {}
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        for u, ss in stories.items():
            a = [s for s in ss if s.get("timestamp", "") > cutoff]
            if a: active[u] = a
        return active
    @staticmethod
    def get_direct_messages() -> Dict: return DataManager.load(DIRECT_MESSAGES_FILE, {})
    @staticmethod
    def save_direct_messages(data: Dict): DataManager.save(DIRECT_MESSAGES_FILE, data)
    @staticmethod
    def get_chat_id(u1: str, u2: str) -> str: return f"chat_{'_'.join(sorted([u1, u2]))}"
    @staticmethod
    def get_group_chats() -> Dict: return DataManager.load(GROUP_CHATS_FILE, {})
    @staticmethod
    def save_group_chats(data: Dict): DataManager.save(GROUP_CHATS_FILE, data)
    @staticmethod
    def get_channels() -> Dict: return DataManager.load(CHANNELS_FILE, {})
    @staticmethod
    def save_channels(data: Dict): DataManager.save(CHANNELS_FILE, data)
    @staticmethod
    def get_comments() -> Dict: return DataManager.load(COMMENTS_FILE, {})
    @staticmethod
    def save_comments(data: Dict): DataManager.save(COMMENTS_FILE, data)
    @staticmethod
    def get_notifications() -> Dict: return DataManager.load(NOTIFICATIONS_FILE, {})
    @staticmethod
    def save_notifications(data: Dict): DataManager.save(NOTIFICATIONS_FILE, data)
    @staticmethod
    def add_notification(username: str, ntype: str, message: str, from_user: str = ""):
        notifs = DataManager.get_notifications()
        if username not in notifs: notifs[username] = []
        notifs[username].insert(0, {"id": generate_id(), "type": ntype, "message": message, "from_user": from_user, "timestamp": datetime.now().isoformat(), "read": False})
        notifs[username] = notifs[username][:50]; DataManager.save_notifications(notifs)
    @staticmethod
    def get_unread_count(username: str) -> int: return sum(1 for n in DataManager.get_notifications().get(username, []) if not n.get("read"))
    @staticmethod
    def get_online_users() -> List[str]:
        profiles = DataManager.get_profiles(); now = datetime.now(); online = []
        for u, p in profiles.items():
            if p.get("last_seen"):
                try:
                    if (now - datetime.fromisoformat(p["last_seen"])).total_seconds() < 300: online.append(u)
                except: pass
        return online

# ========== HANDLERS ==========
class PostHandler:
    @staticmethod
    def create(text: str, media_data: str = None, media_name: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_POST_LENGTH) if text else ""
        if not text and not media_data: return False, "Empty post"
        posts = DataManager.get_feed_posts()
        post = {"id": generate_id(), "username": st.session_state.user, "text": text, "timestamp": datetime.now().isoformat(), "type": "post", "reactions": {}}
        if media_data: post["media"] = media_data; post["media_type"] = "image"
        posts.append(post); DataManager.save_feed_posts(posts); st.session_state.feed_posts = posts
        return True, "Posted!"
    @staticmethod
    def add_reaction(post_id: str, reaction_key: str):
        posts = DataManager.get_feed_posts(); u = st.session_state.user
        for post in posts:
            if post["id"] == post_id:
                if "reactions" not in post: post["reactions"] = {}
                if reaction_key not in post["reactions"]: post["reactions"][reaction_key] = []
                if u in post["reactions"][reaction_key]: post["reactions"][reaction_key].remove(u)
                else: post["reactions"][reaction_key].append(u)
                if not post["reactions"][reaction_key]: del post["reactions"][reaction_key]
                DataManager.save_feed_posts(posts); st.session_state.feed_posts = posts; return
    @staticmethod
    def delete(post_id: str) -> bool:
        posts = DataManager.get_feed_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i); DataManager.save_feed_posts(posts); st.session_state.feed_posts = posts; return True
        return False
    @staticmethod
    def create_poll(question: str, options: List[str]) -> Tuple[bool, str]:
        question = sanitize_text(question, 500); options = [sanitize_text(o, 100) for o in options if o.strip()]
        if len(options) < 2: return False, "Need 2+ options"
        posts = DataManager.get_feed_posts()
        posts.append({"id": generate_id(), "username": st.session_state.user, "text": question, "timestamp": datetime.now().isoformat(), "type": "poll", "poll_data": {"options": {o: [] for o in options}, "total_votes": 0}})
        DataManager.save_feed_posts(posts); st.session_state.feed_posts = posts; return True, "Poll created!"
    @staticmethod
    def vote_poll(post_id: str, option: str):
        posts = DataManager.get_feed_posts(); u = st.session_state.user
        for post in posts:
            if post["id"] == post_id and post.get("type") == "poll":
                pd = post["poll_data"]
                for o, v in pd["options"].items():
                    if u in v: v.remove(u); pd["total_votes"] -= 1
                if option in pd["options"]: pd["options"][option].append(u); pd["total_votes"] += 1
                DataManager.save_feed_posts(posts); st.session_state.feed_posts = posts; return

class StoryHandler:
    @staticmethod
    def create(media_data: str, media_name: str) -> Tuple[bool, str]:
        stories = DataManager.get_stories(); u = st.session_state.user
        if u not in stories: stories[u] = []
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        stories[u] = [s for s in stories[u] if s["timestamp"] > cutoff]
        stories[u].append({"id": generate_id(), "username": u, "media": media_data, "media_name": sanitize_text(media_name, 100), "timestamp": datetime.now().isoformat(), "views": []})
        DataManager.save_stories(stories); st.session_state.stories = stories; return True, "Story posted!"

class ChatHandler:
    @staticmethod
    def send(to_user: str, text: str) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text: return False, "Empty message"
        from_user = st.session_state.user; chat_id = DataManager.get_chat_id(from_user, to_user)
        dms = DataManager.get_direct_messages()
        if chat_id not in dms: dms[chat_id] = {"participants": [from_user, to_user], "messages": [], "created_at": datetime.now().isoformat()}
        dms[chat_id]["messages"].append({"id": generate_id(), "from": from_user, "to": to_user, "text": text, "timestamp": datetime.now().isoformat(), "read": False})
        DataManager.save_direct_messages(dms); return True, "Sent!"
    @staticmethod
    def get_messages(with_user: str) -> List:
        chat_id = DataManager.get_chat_id(st.session_state.user, with_user)
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            for m in dms[chat_id]["messages"]:
                if m.get("to") == st.session_state.user: m["read"] = True
            DataManager.save_direct_messages(dms); return dms[chat_id]["messages"]
        return []
    @staticmethod
    def get_chat_list() -> List[Dict]:
        u = st.session_state.user; dms = DataManager.get_direct_messages(); online = DataManager.get_online_users(); chats = []
        for cid, cd in dms.items():
            if u in cd["participants"]:
                other = [p for p in cd["participants"] if p != u][0]; msgs = cd["messages"]; last = msgs[-1] if msgs else None
                chats.append({"with_user": other, "last_message": last["text"][:40] if last and last.get("text") else "Media", "last_time": last["timestamp"] if last else cd["created_at"], "unread": sum(1 for m in msgs if m.get("to") == u and not m.get("read")), "is_online": other in online})
        chats.sort(key=lambda x: x["last_time"], reverse=True); return chats

class GroupHandler:
    @staticmethod
    def create_group(name: str, members: List[str], is_channel: bool = False) -> Tuple[bool, str]:
        name = sanitize_text(name, 50)
        if not name: return False, "Name required"
        all_members = list(set(members + [st.session_state.user])); gid = f"{'channel' if is_channel else 'group'}_{generate_id()[:8]}"
        data = {"name": name, "admins": [st.session_state.user], "messages": [], "created_at": datetime.now().isoformat()}
        if is_channel:
            data["owner"] = st.session_state.user; data["subscribers"] = all_members
            channels = DataManager.get_channels(); channels[gid] = data; DataManager.save_channels(channels)
        else:
            data["members"] = all_members; groups = DataManager.get_group_chats(); groups[gid] = data; DataManager.save_group_chats(groups)
        return True, f"{'Channel' if is_channel else 'Group'} created!"
    @staticmethod
    def send_message(group_id: str, text: str, is_channel: bool = False) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text: return False, "Empty message"
        data = DataManager.get_channels() if is_channel else DataManager.get_group_chats()
        if group_id not in data: return False, "Not found"
        data[group_id]["messages"].append({"id": generate_id(), "from": st.session_state.user, "text": text, "timestamp": datetime.now().isoformat()})
        if is_channel: DataManager.save_channels(data)
        else: DataManager.save_group_chats(data)
        return True, "Sent!"
    @staticmethod
    def get_user_groups() -> List[Dict]:
        u = st.session_state.user; groups = DataManager.get_group_chats(); result = []
        for gid, gd in groups.items():
            if u in gd.get("members", []):
                msgs = gd["messages"]; last = msgs[-1] if msgs else None
                result.append({"id": gid, "name": gd["name"], "members": len(gd.get("members", [])), "last_message": last["text"][:30] if last and last.get("text") else "No messages", "last_time": last["timestamp"] if last else gd["created_at"]})
        return sorted(result, key=lambda x: x["last_time"], reverse=True)
    @staticmethod
    def get_user_channels() -> List[Dict]:
        u = st.session_state.user; channels = DataManager.get_channels(); result = []
        for cid, cd in channels.items():
            if u in cd.get("subscribers", []):
                msgs = cd["messages"]; last = msgs[-1] if msgs else None
                result.append({"id": cid, "name": cd["name"], "subscribers": len(cd.get("subscribers", [])), "last_message": last["text"][:30] if last and last.get("text") else "No posts", "last_time": last["timestamp"] if last else cd["created_at"]})
        return sorted(result, key=lambda x: x["last_time"], reverse=True)
    @staticmethod
    def get_group_messages(group_id: str) -> List: return DataManager.get_group_chats().get(group_id, {}).get("messages", [])
    @staticmethod
    def get_channel_messages(channel_id: str) -> List: return DataManager.get_channels().get(channel_id, {}).get("messages", [])

class CommentHandler:
    @staticmethod
    def add(post_id: str, text: str) -> Tuple[bool, str]:
        text = sanitize_text(text, 500)
        if not text: return False, "Empty comment"
        comments = DataManager.get_comments()
        if post_id not in comments: comments[post_id] = []
        comments[post_id].append({"id": generate_id(), "username": st.session_state.user, "text": text, "timestamp": datetime.now().isoformat()})
        DataManager.save_comments(comments); return True, "Comment added!"
    @staticmethod
    def get(post_id: str) -> List: return DataManager.get_comments().get(post_id, [])

class FollowHandler:
    @staticmethod
    def follow(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user: return False, "Cannot follow yourself"
        profiles = DataManager.get_profiles(); up = DataManager.get_profile(st.session_state.user); tp = DataManager.get_profile(target)
        for p in [up, tp]:
            for k in ["following", "followers", "blocked"]:
                if k not in p: p[k] = []
        if target in up["following"]: up["following"].remove(target); tp["followers"].remove(st.session_state.user); action = "Unfollowed"
        else: up["following"].append(target); tp["followers"].append(st.session_state.user); action = "Following"
        profiles[st.session_state.user] = up; profiles[target] = tp; DataManager.save_profiles(profiles); return True, f"{action}!"
    @staticmethod
    def is_following(target: str) -> bool: return target in DataManager.get_profile(st.session_state.user).get("following", [])

# ========== SESSION STATE ==========
def init_session():
    defaults = {'feed_posts': [], 'stories': {}, 'auth': False, 'user': "", 'current_tab': "feed", 'active_chat': None, 'active_group': None, 'active_channel': None, 'show_create_modal': False, 'show_new_chat': False, 'show_new_group': False, 'show_new_channel': False, 'show_comments_for': None}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
    if not st.session_state.feed_posts: st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories: st.session_state.stories = DataManager.get_stories()

init_session()
if st.session_state.get('auth'):
    st.session_state.feed_posts = DataManager.get_feed_posts()
    st.session_state.stories = DataManager.get_stories()
    DataManager.update_last_seen(st.session_state.user)

def get_theme() -> Dict:
    if st.session_state.get('auth'):
        t = DataManager.get_profile(st.session_state.user).get('theme', 'midnight')
        return THEMES.get(t, THEMES['midnight'])
    return THEMES['midnight']

def get_wallpaper() -> Dict:
    if st.session_state.get('auth'):
        w = DataManager.get_profile(st.session_state.user).get('wallpaper', 'wp_luxury')
        return WALLPAPERS.get(w, WALLPAPERS['wp_luxury'])
    return WALLPAPERS['wp_luxury']

# ========== CSS ==========
def inject_styles():
    theme = get_theme()
    wp = get_wallpaper()
    bg = f"url('{wp['url']}') center/cover no-repeat fixed" if wp.get("url") else wp.get("gradient", theme["gradient"])

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    * {{ font-family: 'Inter', sans-serif; }}
    
    /* Hide ALL Streamlit UI elements */
    #MainMenu {{ visibility: hidden !important; display: none !important; }}
    footer {{ visibility: hidden !important; display: none !important; }}
    header {{ visibility: hidden !important; display: none !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stDeployButton {{ display: none !important; }}
    [data-testid="stDecoration"] {{ display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stHeader"] {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    .stApp > header {{ display: none !important; }}
    div[data-testid="stVerticalBlock"] > div:first-child {{ display: none !important; }}
    
    /* Force full viewport */
    html, body {{
        height: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}
    
    .stApp {{
        background: {bg} !important;
        height: 100vh !important;
        width: 100vw !important;
        overflow: hidden !important;
        position: relative !important;
    }}
    
    .main {{
        height: 100vh !important;
        overflow: hidden !important;
    }}
    
    .block-container {{
        height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Fixed Top Header */
    .app-header {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 48px !important;
        background: {theme['bg']}f0 !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-bottom: 1px solid rgba(255,215,0,0.15) !important;
        padding: 0 16px !important;
        z-index: 9999 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
    }}
    
    .app-logo {{
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #FFD700, #FFA500, #FFD700) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }}
    
    /* Scrollable Main Content */
    .main-content {{
        position: fixed !important;
        top: 48px !important;
        bottom: 56px !important;
        left: 0 !important;
        right: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 8px 12px !important;
        -webkit-overflow-scrolling: touch !important;
    }}
    
    .content-wrapper {{
        max-width: 650px !important;
        margin: 0 auto !important;
        padding-bottom: 8px !important;
    }}
    
    /* Fixed Bottom Navigation - TASKBAR STYLE */
    .bottom-nav {{
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 56px !important;
        background: {theme['bg']}fa !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-top: 2px solid rgba(255,215,0,0.25) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-around !important;
        z-index: 9999 !important;
        box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
    }}
    
    .nav-item {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 2px !important;
        cursor: pointer !important;
        color: {theme['secondary']} !important;
        font-size: 0.5rem !important;
        padding: 4px 8px !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }}
    
    .nav-item.active {{
        color: #FFD700 !important;
    }}
    
    .nav-icon {{
        font-size: 1.2rem !important;
    }}
    
    /* Cards */
    .card {{
        background: {theme['card']} !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 14px !important;
        margin-bottom: 10px !important;
        overflow: hidden !important;
    }}
    
    .card-header {{
        display: flex !important;
        align-items: center !important;
        padding: 8px 10px !important;
        gap: 8px !important;
    }}
    
    .username-text {{
        color: {theme['text']} !important;
        font-weight: 600 !important;
        font-size: 0.82rem !important;
    }}
    
    .timestamp {{
        color: {theme['secondary']} !important;
        font-size: 0.62rem !important;
    }}
    
    .post-text {{
        color: #e2e8f0 !important;
        font-size: 0.85rem !important;
        line-height: 1.5 !important;
        padding: 0 10px 8px 10px !important;
        word-wrap: break-word !important;
    }}
    
    .post-media {{
        width: 100% !important;
        max-height: 350px !important;
        object-fit: cover !important;
    }}
    
    /* Luxury Reaction Bar */
    .luxury-bar {{
        display: flex !important;
        gap: 4px !important;
        padding: 6px 10px !important;
        border-top: 1px solid rgba(255,215,0,0.1) !important;
        flex-wrap: wrap !important;
    }}
    
    .luxury-btn {{
        padding: 4px 8px !important;
        border-radius: 16px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        font-size: 0.9rem !important;
        color: {theme['secondary']} !important;
    }}
    
    .luxury-btn:hover {{
        transform: scale(1.2) !important;
        background: rgba(255,215,0,0.15) !important;
        border-color: rgba(255,215,0,0.4) !important;
        box-shadow: 0 0 20px rgba(255,215,0,0.5), 0 0 40px rgba(255,215,0,0.2) !important;
        z-index: 10 !important;
    }}
    
    .luxury-btn.active {{
        background: rgba(255,215,0,0.2) !important;
        border-color: rgba(255,215,0,0.5) !important;
        box-shadow: 0 0 15px rgba(255,215,0,0.3) !important;
    }}
    
    /* Chat */
    .chat-bubble {{
        max-width: 80% !important;
        padding: 8px 12px !important;
        border-radius: 14px !important;
        font-size: 0.82rem !important;
        line-height: 1.4 !important;
        margin: 2px 0 !important;
    }}
    
    .chat-bubble.sent {{
        background: linear-gradient(135deg, #667eea, #764ba2) !important;
        color: white !important;
        align-self: flex-end !important;
        border-bottom-right-radius: 4px !important;
    }}
    
    .chat-bubble.received {{
        background: rgba(255,255,255,0.07) !important;
        color: #e2e8f0 !important;
        align-self: flex-start !important;
        border-bottom-left-radius: 4px !important;
    }}
    
    /* Stories */
    .stories-row {{
        display: flex !important;
        gap: 12px !important;
        padding: 8px 0 !important;
        overflow-x: auto !important;
        margin-bottom: 8px !important;
    }}
    
    .stories-row::-webkit-scrollbar {{ height: 0 !important; }}
    
    .story-item {{
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        gap: 3px !important;
        min-width: 60px !important;
        cursor: pointer !important;
    }}
    
    .story-ring {{
        width: 56px !important;
        height: 56px !important;
        border-radius: 50% !important;
        padding: 2.5px !important;
        background: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) !important;
        box-shadow: 0 0 12px rgba(255,215,0,0.3) !important;
    }}
    
    .story-ring.viewed {{
        background: rgba(255,255,255,0.2) !important;
        box-shadow: none !important;
    }}
    
    .story-ring-inner {{
        width: 100% !important;
        height: 100% !important;
        border-radius: 50% !important;
        object-fit: cover !important;
        border: 2px solid {theme['bg']} !important;
    }}
    
    .story-ring-inner-placeholder {{
        width: 100% !important;
        height: 100% !important;
        border-radius: 50% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-weight: 700 !important;
        color: white !important;
        font-size: 1rem !important;
        border: 2px solid {theme['bg']} !important;
    }}
    
    .story-name {{
        color: {theme['secondary']} !important;
        font-size: 0.58rem !important;
        max-width: 58px !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
    }}
    
    /* User row */
    .user-row {{
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 6px 8px !important;
        border-radius: 10px !important;
    }}
    
    .user-row:hover {{ background: rgba(255,215,0,0.04) !important; }}
    
    .online-dot {{
        width: 7px !important;
        height: 7px !important;
        border-radius: 50% !important;
        background: #10b981 !important;
        box-shadow: 0 0 6px rgba(16,185,129,0.5) !important;
    }}
    
    .unread-count {{
        background: #FFD700 !important;
        color: #1a0033 !important;
        border-radius: 10px !important;
        padding: 2px 7px !important;
        font-size: 0.6rem !important;
        font-weight: 600 !important;
    }}
    
    /* Modal */
    .modal-overlay {{
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: rgba(0,0,0,0.8) !important;
        backdrop-filter: blur(6px) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        z-index: 10000 !important;
    }}
    
    .modal-box {{
        background: {theme['bg']}fa !important;
        border: 1px solid rgba(255,215,0,0.2) !important;
        border-radius: 18px !important;
        width: 92% !important;
        max-width: 480px !important;
        max-height: 80vh !important;
        overflow-y: auto !important;
        padding: 16px !important;
    }}
    
    /* Theme & Wallpaper grids */
    .theme-grid {{ display: grid !important; grid-template-columns: repeat(3, 1fr) !important; gap: 6px !important; padding: 6px 0 !important; }}
    .wallpaper-grid {{ display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 5px !important; padding: 6px 0 !important; }}
    
    .theme-card {{
        border-radius: 10px !important;
        padding: 14px 4px !important;
        text-align: center !important;
        cursor: pointer !important;
        border: 2px solid transparent !important;
        transition: all 0.3s !important;
    }}
    
    .theme-card:hover {{ transform: scale(1.05) !important; box-shadow: 0 0 20px rgba(255,215,0,0.3) !important; }}
    .theme-card.selected {{ border-color: #FFD700 !important; box-shadow: 0 0 20px rgba(255,215,0,0.4) !important; }}
    
    .wallpaper-card {{
        border-radius: 8px !important;
        height: 50px !important;
        cursor: pointer !important;
        border: 2px solid transparent !important;
        background-size: cover !important;
        background-position: center !important;
        transition: all 0.3s !important;
    }}
    
    .wallpaper-card:hover {{ transform: scale(1.08) !important; box-shadow: 0 0 15px rgba(255,215,0,0.3) !important; }}
    .wallpaper-card.selected {{ border-color: #FFD700 !important; box-shadow: 0 0 20px rgba(255,215,0,0.5) !important; }}
    
    /* Buttons */
    .stButton > button {{
        background: rgba(255,215,0,0.08) !important;
        border: 1px solid rgba(255,215,0,0.2) !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        min-height: auto !important;
        transition: all 0.2s !important;
    }}
    
    .stButton > button:hover {{
        background: rgba(255,215,0,0.15) !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 12px rgba(255,215,0,0.25) !important;
    }}
    
    /* Inputs */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{ color: {theme['secondary']} !important; }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 3px !important; background: transparent !important; }}
    .stTabs [data-baseweb="tab"] {{ color: {theme['secondary']} !important; border-radius: 6px !important; padding: 5px 12px !important; font-size: 0.78rem !important; }}
    .stTabs [aria-selected="true"] {{ color: #FFD700 !important; background: rgba(255,215,0,0.1) !important; }}
    
    /* Expander */
    .stExpander {{ background: {theme['card']} !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; }}
    .streamlit-expanderHeader {{ color: {theme['text']} !important; font-size: 0.85rem !important; }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 4px !important; }}
    ::-webkit-scrollbar-track {{ background: transparent !important; }}
    ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
    
    /* Responsive */
    @media (max-width: 480px) {{
        .main-content {{ padding: 6px 8px !important; }}
        .card {{ border-radius: 10px !important; margin-bottom: 8px !important; }}
        .bottom-nav {{ height: 52px !important; }}
        .main-content {{ bottom: 52px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ========== RENDERERS ==========
def render_avatar(username: str, size: int = 36) -> str:
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    is_female = profile.get("gender", "male") == "female"
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #FFD700;flex-shrink:0;" alt="{username}">'
        except: pass
    return get_svg_avatar(username, size, is_female)

def render_story_ring(username: str, size: int = 56, has_new: bool = False) -> str:
    ring_class = "story-ring" if has_new else "story-ring viewed"
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    is_female = profile.get("gender", "male") == "female"
    if path and os.path.exists(path):
        with open(path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
        return f'<div class="{ring_class}"><img src="data:image/jpeg;base64,{b64}" class="story-ring-inner" alt="{username}"></div>'
    color = get_avatar_color(username)
    return f'<div class="{ring_class}"><div class="story-ring-inner-placeholder" style="font-size:{size*0.3}px;background:{color};">{get_initials(username)}</div></div>'

def render_header():
    user = st.session_state.user; unread = DataManager.get_unread_count(user)
    badge = f'<span style="background:#FFD700;color:#1a0033;border-radius:50%;padding:1px 5px;font-size:0.55rem;font-weight:700;position:absolute;top:-6px;right:-8px;">{unread}</span>' if unread > 0 else ''
    st.markdown(f'<div class="app-header"><div class="app-logo">👑 SocialHub</div><div style="display:flex;align-items:center;gap:12px;color:{get_theme()["text"]};"><span style="position:relative;">🔔{badge}</span>{render_avatar(user, 28)}</div></div>', unsafe_allow_html=True)

def render_stories_bar():
    user = st.session_state.user; active = DataManager.get_active_stories()
    html = '<div class="stories-row">'
    html += f'<div class="story-item">{render_story_ring(user, 56, user not in active)}<div class="story-name">You</div></div>'
    for u, ss in active.items():
        if u != user:
            has_new = any(st.session_state.user not in s.get("views", []) for s in ss)
            html += f'<div class="story-item">{render_story_ring(u, 56, has_new)}<div class="story-name">@{u[:8]}</div></div>'
    if len(active) <= 1: html += '<div style="color:#94a3b8;display:flex;align-items:center;font-size:0.7rem;padding-left:8px;">No stories</div>'
    html += '</div>'; st.markdown(html, unsafe_allow_html=True)

def render_luxury_bar(post_id: str, reactions: Dict):
    st.markdown('<div class="luxury-bar">', unsafe_allow_html=True)
    cols = st.columns(len(LUXURY_REACTIONS))
    for i, (rkey, rdata) in enumerate(LUXURY_REACTIONS.items()):
        count = len(reactions.get(rkey, [])); active = "active" if st.session_state.user in reactions.get(rkey, []) else ""
        with cols[i]:
            if st.button(f"{rdata['emoji']} {count}", key=f"lux_{rkey}_{post_id}", help=rdata['label']):
                PostHandler.add_reaction(post_id, rkey); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_post_card(post: Dict):
    username = post.get("username", ""); pid = post.get("id", ""); is_owner = username == st.session_state.user
    st.markdown(f'<div class="card"><div class="card-header">{render_avatar(username)}<div style="flex:1;"><div class="username-text">@{html.escape(username)}</div><div class="timestamp">{format_timestamp(post.get("timestamp", ""))}</div></div></div>', unsafe_allow_html=True)
    if post.get("text"): st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
    if post.get("media") and post.get("media_type") == "image": st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post">', unsafe_allow_html=True)
    render_luxury_bar(pid, post.get("reactions", {}))
    st.markdown('<div style="display:flex;align-items:center;padding:4px 10px 8px 10px;gap:8px;">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 3])
    with c1:
        if st.button("💬", key=f"cm_{pid}"): st.session_state.show_comments_for = None if st.session_state.show_comments_for == pid else pid; st.rerun()
    with c2:
        if st.button("📤", key=f"sh_{pid}"): st.toast("Link copied!")
    if is_owner:
        with c3:
            if st.button("🗑️", key=f"dl_{pid}"): PostHandler.delete(pid); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.show_comments_for == pid: render_comments(pid)
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(post: Dict):
    username = post.get("username", ""); pid = post.get("id", ""); pd = post.get("poll_data", {})
    total = pd.get("total_votes", 0); options = pd.get("options", {})
    st.markdown(f'<div class="card"><div class="card-header">{render_avatar(username)}<div style="flex:1;"><div class="username-text">@{html.escape(username)}</div><div class="timestamp">📊 Poll - {format_timestamp(post.get("timestamp", ""))}</div></div></div><div class="post-text" style="font-weight:600;">{html.escape(post.get("text", ""))}</div><div style="padding:0 10px 8px 10px;">', unsafe_allow_html=True)
    for opt, voters in options.items():
        pct = (len(voters) / total * 100) if total > 0 else 0; voted = st.session_state.user in voters
        st.markdown(f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:5px 8px;margin:3px 0;{"border:1px solid #FFD700;" if voted else ""}"><div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.8rem;"><span>{"✓ " if voted else ""}{html.escape(opt)}</span><span>{pct:.0f}%</span></div><div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;margin-top:3px;"><div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#FFD700,#FFA500);border-radius:2px;"></div></div></div>', unsafe_allow_html=True)
        if st.button(f"Vote", key=f"pv_{pid}_{opt[:8]}"): PostHandler.vote_poll(pid, opt); st.rerun()
    st.markdown(f'<div style="color:#94a3b8;font-size:0.6rem;margin-top:4px;">{total} votes</div></div></div>', unsafe_allow_html=True)

def render_comments(post_id: str):
    comments = CommentHandler.get(post_id)
    st.markdown('<div style="padding:4px 10px;border-top:1px solid rgba(255,215,0,0.1);">', unsafe_allow_html=True)
    for c in comments[-15:]:
        st.markdown(f'<div style="margin:3px 0;display:flex;gap:5px;align-items:flex-start;">{render_avatar(c["username"], 20)}<div><span style="color:#f1f5f9;font-weight:600;font-size:0.7rem;">@{html.escape(c["username"])}</span> <span style="color:#e2e8f0;font-size:0.73rem;">{html.escape(c["text"])}</span></div></div>', unsafe_allow_html=True)
    with st.form(f"cmf_{post_id}", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1: txt = st.text_input("Comment", placeholder="Write...", key=f"ci_{post_id}")
        with c2:
            if st.form_submit_button("Post"):
                if txt.strip(): CommentHandler.add(post_id, txt); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    a = st.session_state.get('active_chat'); g = st.session_state.get('active_group'); c = st.session_state.get('active_channel')
    if st.button("← Back", use_container_width=True, key="back"): st.session_state.active_chat = None; st.session_state.active_group = None; st.session_state.active_channel = None; st.rerun()
    if a:
        msgs = ChatHandler.get_messages(a)
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);">{render_avatar(a, 32)}<div class="username-text">@{html.escape(a)}</div></div>', unsafe_allow_html=True)
        for m in msgs:
            sent = m.get("from") == st.session_state.user; cls = "sent" if sent else "received"
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:{"flex-end" if sent else "flex-start"};padding:0 4px;"><div class="chat-bubble {cls}">{html.escape(m.get("text",""))}<div style="font-size:0.55rem;opacity:0.7;text-align:right;">{format_timestamp(m["timestamp"])}</div></div></div>', unsafe_allow_html=True)
        with st.form(f"dmf_{a}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1: txt = st.text_input("Message", placeholder="Type...", key=f"dmt_{a}")
            with c2:
                if st.form_submit_button("➤"):
                    if txt.strip(): ChatHandler.send(a, txt); st.rerun()
    elif g:
        msgs = GroupHandler.get_group_messages(g); gd = DataManager.get_group_chats().get(g, {})
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);"><div style="width:32px;height:32px;border-radius:50%;background:#667eea;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div><div class="username-text">{html.escape(gd.get("name","Group"))}</div></div>', unsafe_allow_html=True)
        for m in msgs:
            sent = m.get("from") == st.session_state.user; cls = "sent" if sent else "received"
            sender = "" if sent else f'<div style="color:#FFD700;font-size:0.6rem;">@{html.escape(m.get("from",""))}</div>'
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:{"flex-end" if sent else "flex-start"};padding:0 4px;"><div class="chat-bubble {cls}">{sender}{html.escape(m.get("text",""))}<div style="font-size:0.55rem;opacity:0.7;text-align:right;">{format_timestamp(m["timestamp"])}</div></div></div>', unsafe_allow_html=True)
        with st.form(f"grpf_{g}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1: txt = st.text_input("Message", placeholder="Type...", key=f"grpt_{g}")
            with c2:
                if st.form_submit_button("➤"):
                    if txt.strip(): GroupHandler.send_message(g, txt); st.rerun()
    elif c:
        msgs = GroupHandler.get_channel_messages(c); cd = DataManager.get_channels().get(c, {})
        is_admin = st.session_state.user in cd.get("admins", [])
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);"><div style="width:32px;height:32px;border-radius:50%;background:#f093fb;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div><div class="username-text">{html.escape(cd.get("name","Channel"))}</div></div>', unsafe_allow_html=True)
        for m in msgs:
            st.markdown(f'<div class="card" style="margin:4px 0;padding:6px 8px;"><div style="display:flex;align-items:center;gap:5px;">{render_avatar(m.get("from",""), 24)}<div class="username-text">@{html.escape(m.get("from",""))}</div><div class="timestamp">{format_timestamp(m["timestamp"])}</div></div><div style="color:#e2e8f0;font-size:0.8rem;margin-top:3px;">{html.escape(m.get("text",""))}</div></div>', unsafe_allow_html=True)
        if is_admin:
            with st.form(f"chnf_{c}", clear_on_submit=True):
                c1, c2 = st.columns([5, 1])
                with c1: txt = st.text_input("Broadcast", placeholder="Post...", key=f"chnt_{c}")
                with c2:
                    if st.form_submit_button("📢"):
                        if txt.strip(): GroupHandler.send_message(c, txt, is_channel=True); st.rerun()

def render_create_modal():
    if not st.session_state.get('show_create_modal'): return
    st.markdown(f'<div class="modal-overlay"><div class="modal-box"><h3 style="color:#FFD700;text-align:center;margin-bottom:10px;">✨ Create</h3>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["Post", "Poll", "Story"])
    with t1:
        with st.form("cpf", clear_on_submit=True):
            text = st.text_area("What's on your mind?", max_chars=MAX_POST_LENGTH, height=80, placeholder="Share...")
            media = st.file_uploader("Image", type=['png','jpg','jpeg','gif','webp'], key="mup")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post", use_container_width=True):
                    md, mn = None, None
                    if media and media.size <= MAX_FILE_SIZE:
                        fb = media.read()
                        if validate_image(fb): md = base64.b64encode(fb).decode()
                    if text.strip() or md: PostHandler.create(text, md); st.session_state.show_create_modal = False; st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    with t2:
        with st.form("cplf", clear_on_submit=True):
            q = st.text_input("Question", max_chars=500, placeholder="Ask something...")
            opts = st.text_area("Options (one per line)", height=80, placeholder="Option 1\nOption 2")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Create Poll", use_container_width=True):
                    if q and opts:
                        olist = [o.strip() for o in opts.split('\n') if o.strip()]
                        if len(olist) >= 2: PostHandler.create_poll(q, olist); st.session_state.show_create_modal = False; st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    with t3:
        with st.form("csf", clear_on_submit=True):
            sm = st.file_uploader("Story image", type=['png','jpg','jpeg','gif','webp'], key="sup")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post Story", use_container_width=True):
                    if sm and sm.size <= MAX_FILE_SIZE:
                        fb = sm.read()
                        if validate_image(fb): StoryHandler.create(base64.b64encode(fb).decode(), sm.name); st.session_state.show_create_modal = False; st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    if st.button("✕ Close", use_container_width=True, key="close_modal"): st.session_state.show_create_modal = False; st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_bottom_nav():
    current = st.session_state.get('current_tab', 'feed')
    theme = get_theme()
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    tabs = [("feed", "🏠", "Feed"), ("explore", "🔍", "Explore"), ("create", "➕", "Create"), ("chats", "💬", "Chats"), ("profile", "👤", "Profile")]
    cols = st.columns(5)
    for i, (tab, icon, label) in enumerate(tabs):
        with cols[i]:
            if current == tab:
                st.markdown(f'<div style="text-align:center;padding:2px;"><div style="font-size:1.2rem;color:#FFD700;">{icon}</div><div style="font-size:0.5rem;color:#FFD700;font-weight:600;">{label}</div></div>', unsafe_allow_html=True)
            else:
                if st.button(icon, key=f"nav_{tab}", use_container_width=True, help=label):
                    if tab == "create": st.session_state.show_create_modal = True
                    else: st.session_state.current_tab = tab; st.session_state.show_create_modal = False; st.session_state.active_chat = None; st.session_state.active_group = None; st.session_state.active_channel = None
                    st.rerun()
                st.markdown(f'<div style="text-align:center;font-size:0.48rem;color:{theme["secondary"]};margin-top:-6px;">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== PAGES ==========
def render_feed_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    render_stories_bar()
    if st.button("✨ What's on your mind?", use_container_width=True, key="qp"): st.session_state.show_create_modal = True; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    posts = st.session_state.feed_posts
    if not posts: st.markdown('<div style="text-align:center;padding:3rem 1rem;color:#94a3b8;"><div style="font-size:3rem;">👑</div><p>Welcome to SocialHub Pro!</p></div>', unsafe_allow_html=True)
    else:
        for post in reversed(posts[-40:]):
            if post.get("type") == "poll": render_poll_card(post)
            else: render_post_card(post)
    st.markdown('</div>', unsafe_allow_html=True)

def render_explore_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">🔍 Explore</h3>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Search users...", key="es")
    users = list(DataManager.get_users().keys())
    filtered = [u for u in users if u != st.session_state.user and (not search or search.lower() in u.lower())]
    for u in filtered[:30]:
        is_following = FollowHandler.is_following(u)
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1: st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:4px 0;">{render_avatar(u, 34)}<div class="username-text">@{html.escape(u)}</div></div>', unsafe_allow_html=True)
        with c2:
            if st.button("✓ Following" if is_following else "+ Follow", key=f"ef_{u}", use_container_width=True): FollowHandler.follow(u); st.rerun()
        with c3:
            if st.button("💬", key=f"em_{u}", use_container_width=True): st.session_state.active_chat = u; st.session_state.current_tab = "chats"; st.rerun()
        st.markdown("<hr style='border-color:rgba(255,215,0,0.04);margin:0;'>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_chats_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    if st.session_state.get('active_chat') or st.session_state.get('active_group') or st.session_state.get('active_channel'): render_chat_interface(); st.markdown('</div>', unsafe_allow_html=True); return
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">💬 Messages</h3>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("New Chat", use_container_width=True, key="nc"): st.session_state.show_new_chat = True
    with c2:
        if st.button("New Group", use_container_width=True, key="ng"): st.session_state.show_new_group = True
    with c3:
        if st.button("New Channel", use_container_width=True, key="nch"): st.session_state.show_new_channel = True
    t1, t2, t3 = st.tabs(["DMs", "Groups", "Channels"])
    with t1:
        chats = ChatHandler.get_chat_list()
        if chats:
            for ch in chats:
                dot = '<span class="online-dot"></span>' if ch['is_online'] else ''
                unread = f'<span class="unread-count">{ch["unread"]}</span>' if ch['unread'] > 0 else ''
                st.markdown(f'<div class="user-row" style="justify-content:space-between;"><div style="display:flex;align-items:center;gap:6px;flex:1;">{render_avatar(ch["with_user"], 36)}<div style="flex:1;min-width:0;"><div style="display:flex;align-items:center;gap:3px;"><span class="username-text">@{html.escape(ch["with_user"])}</span>{dot}</div><div style="color:#94a3b8;font-size:0.65rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{html.escape(ch["last_message"])}</div></div></div><div style="text-align:right;flex-shrink:0;"><div class="timestamp">{format_timestamp(ch["last_time"])}</div>{unread}</div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"oc_{ch['with_user']}"): st.session_state.active_chat = ch['with_user']; st.rerun()
                st.markdown("<hr style='border-color:rgba(255,215,0,0.03);margin:0;'>", unsafe_allow_html=True)
        else: st.info("No conversations")
        if st.session_state.get('show_new_chat'):
            with st.expander("New Chat", expanded=True):
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                if avail:
                    sel = st.selectbox("User", avail, key="ncs")
                    if st.button("Start", use_container_width=True): st.session_state.active_chat = sel; st.session_state.show_new_chat = False; st.rerun()
    with t2:
        groups = GroupHandler.get_user_groups()
        if groups:
            for gr in groups:
                st.markdown(f'<div class="user-row"><div style="width:36px;height:36px;border-radius:50%;background:#667eea;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div><div><div class="username-text">{html.escape(gr["name"])}</div><div style="color:#94a3b8;font-size:0.65rem;">{gr["members"]} members</div></div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"og_{gr['id']}"): st.session_state.active_group = gr['id']; st.rerun()
        else: st.info("No groups")
        if st.session_state.get('show_new_group'):
            with st.expander("New Group", expanded=True):
                gn = st.text_input("Name", max_chars=50, key="ngn", placeholder="Group name")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                mems = st.multiselect("Members", avail, key="ngm")
                if st.button("Create", use_container_width=True) and gn: GroupHandler.create_group(gn, mems); st.session_state.show_new_group = False; st.rerun()
    with t3:
        channels = GroupHandler.get_user_channels()
        if channels:
            for ch in channels:
                st.markdown(f'<div class="user-row"><div style="width:36px;height:36px;border-radius:50%;background:#f093fb;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div><div><div class="username-text">{html.escape(ch["name"])}</div><div style="color:#94a3b8;font-size:0.65rem;">{ch["subscribers"]} subscribers</div></div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"och_{ch['id']}"): st.session_state.active_channel = ch['id']; st.rerun()
        else: st.info("No channels")
        if st.session_state.get('show_new_channel'):
            with st.expander("New Channel", expanded=True):
                cn = st.text_input("Name", max_chars=50, key="nchn", placeholder="Channel name")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                subs = st.multiselect("Subscribers", avail, key="nchs")
                if st.button("Create", use_container_width=True) and cn: GroupHandler.create_group(cn, subs or [], is_channel=True); st.session_state.show_new_channel = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_profile_page():
    user = st.session_state.user; profile = DataManager.get_profile(user); theme = get_theme()
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;padding:12px 0;">{render_avatar(user, 64)}<h2 style="color:#FFD700;margin-top:6px;">@{html.escape(user)}</h2><p style="color:{theme["secondary"]};font-size:0.8rem;">{html.escape(profile.get("bio","No bio"))}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;justify-content:space-around;text-align:center;padding:10px;border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:10px;"><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{profile.get("post_count",0)}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Posts</div></div><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("followers",[]))}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Followers</div></div><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("following",[]))}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Following</div></div></div>', unsafe_allow_html=True)
    
    with st.expander("✏️ Edit Profile"):
        with st.form("epf"):
            bio = st.text_area("Bio", value=profile.get("bio",""), max_chars=MAX_BIO_LENGTH, placeholder="About you...")
            gender = st.selectbox("Gender", ["male","female"], index=0 if profile.get("gender","male")=="male" else 1)
            avatar_file = st.file_uploader("Avatar", type=['png','jpg','jpeg'], key="pau")
            if st.form_submit_button("Save", use_container_width=True):
                updates = {"bio": sanitize_text(bio, MAX_BIO_LENGTH), "gender": gender}
                if avatar_file and avatar_file.size <= MAX_AVATAR_SIZE:
                    try:
                        img = Image.open(avatar_file)
                        if img.mode in ('RGBA','LA','P'): bg = Image.new('RGB', img.size, (255,255,255)); bg.paste(img.convert('RGBA'), mask=img.split()[-1] if img.mode=='RGBA' else None); img = bg
                        else: img = img.convert("RGB")
                        img.thumbnail((200,200)); path = UPLOADS_DIR / f"{user}_avatar.jpg"; img.save(path, "JPEG", quality=80); updates["avatar"] = str(path)
                    except: st.error("Image error")
                DataManager.update_profile(user, updates); st.success("Updated!"); st.rerun()
    
    with st.expander("🎨 Themes (20+)"):
        st.markdown('<div class="theme-grid">', unsafe_allow_html=True)
        ct = profile.get('theme','midnight')
        for tk, td in THEMES.items():
            sel = "selected" if ct == tk else ""
            st.markdown(f'<div class="theme-card {sel}" style="background:{td["gradient"]};"><div style="font-size:1.3rem;">{td["icon"]}</div><div style="color:white;font-size:0.6rem;margin-top:3px;">{td["name"]}</div></div>', unsafe_allow_html=True)
            if st.button("Apply", key=f"th_{tk}"): DataManager.update_profile(user, {"theme": tk}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("🖼️ Wallpapers (30)"):
        st.markdown('<div class="wallpaper-grid">', unsafe_allow_html=True)
        cw = profile.get('wallpaper','wp_luxury')
        for wk, wd in WALLPAPERS.items():
            sel = "selected" if cw == wk else ""
            bg = f"background-image:url('{wd['url']}');" if wd.get("url") else f"background:{wd.get('gradient','')};"
            st.markdown(f'<div class="wallpaper-card {sel}" style="{bg}" title="{wd["name"]}"></div>', unsafe_allow_html=True)
            if st.button("Apply", key=f"wp_{wk}"): DataManager.update_profile(user, {"wallpaper": wk}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    posts = [p for p in st.session_state.feed_posts if p.get("username")==user]
    if posts:
        st.markdown('<h4 style="color:#FFD700;margin-top:10px;">Your Posts</h4>', unsafe_allow_html=True)
        for post in reversed(posts[-20:]):
            if post.get("type")=="poll": render_poll_card(post)
            else: render_post_card(post)
    
    if st.button("🚪 Sign Out", use_container_width=True, key="so"):
        for k in list(st.session_state.keys()): del st.session_state[k]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTH ==========
def render_auth():
    st.markdown("<style>html,body{overflow:auto!important;height:auto!important;position:relative!important;}.stApp{position:relative!important;overflow:auto!important;}</style>", unsafe_allow_html=True)
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown('<div style="text-align:center;padding:2rem 0;"><div style="font-size:4rem;">👑</div><h1 style="background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.2rem;font-weight:800;">SocialHub Pro</h1><p style="color:#94a3b8;">Premium Social Experience</p></div>', unsafe_allow_html=True)
        t1, t2 = st.tabs(["Sign In", "Sign Up"])
        with t1:
            with st.form("li"):
                u = st.text_input("Username", key="li_u"); p = st.text_input("Password", type="password", key="li_p")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if u and p:
                        ok, res = DataManager.authenticate(u, p)
                        if ok: st.session_state.auth = True; st.session_state.user = res; st.session_state.feed_posts = DataManager.get_feed_posts(); st.rerun()
                        else: st.error(res)
        with t2:
            with st.form("su"):
                u = st.text_input("Username", key="su_u"); p = st.text_input("Password", type="password", key="su_p"); cp = st.text_input("Confirm", type="password", key="su_cp")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not u or not p: st.error("Fill all fields")
                    elif p != cp: st.error("Passwords don't match")
                    elif len(p) < MIN_PASSWORD_LENGTH: st.error("Password too short")
                    elif not u.isalnum(): st.error("Letters/numbers only")
                    else:
                        ok, msg = DataManager.create_user(u, p)
                        if ok: st.success(msg)
                        else: st.error(msg)

# ========== MAIN ==========
def main():
    init_session()
    inject_styles()
    if not st.session_state.get('auth'): render_auth(); return
    render_header()
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    tab = st.session_state.get('current_tab', 'feed')
    if tab == "feed": render_feed_page()
    elif tab == "explore": render_explore_page()
    elif tab == "chats": render_chats_page()
    elif tab == "profile": render_profile_page()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.get('show_create_modal'): render_create_modal()
    render_bottom_nav()

if __name__ == "__main__":
    main()
