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
import re

# Must be first Streamlit command
st.set_page_config(page_title="Socialite", page_icon="👑", layout="wide", initial_sidebar_state="collapsed")

# ========== BRAND EMOJI GENERATOR ==========
def generate_socialite_emoji() -> str:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <radialGradient id="gG" cx="50%" cy="40%" r="50%"><stop offset="0%" style="stop-color:#4A90D9"/><stop offset="100%" style="stop-color:#1A3A5C"/></radialGradient>
    <linearGradient id="gold" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:#FFD700"/><stop offset="100%" style="stop-color:#FFA500"/></linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="3"/><feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <circle cx="100" cy="100" r="85" fill="url(#gG)" stroke="url(#gold)" stroke-width="3" filter="url(#glow)"/>
  <ellipse cx="100" cy="100" rx="85" ry="30" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  <ellipse cx="100" cy="100" rx="30" ry="85" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  <ellipse cx="85" cy="70" rx="20" ry="12" fill="rgba(255,255,255,0.2)"/>
  <ellipse cx="120" cy="80" rx="15" ry="10" fill="rgba(255,255,255,0.2)"/>
  <g transform="translate(55, 55)">
    <rect x="-12" y="15" width="24" height="30" rx="5" fill="#2C3E50" stroke="url(#gold)" stroke-width="1.5"/>
    <polygon points="0,15 -3,30 3,30" fill="#FFD700"/>
    <circle cx="0" cy="5" r="12" fill="#F5DEB3" stroke="url(#gold)" stroke-width="1.5"/>
    <path d="M-10,0 Q-12,-10 -5,-14 Q0,-16 5,-14 Q12,-10 10,0" fill="#1A1A1A"/>
    <circle cx="-5" cy="4" r="1.5" fill="#1A1A1A"/><circle cx="5" cy="4" r="1.5" fill="#1A1A1A"/>
    <polygon points="-8,-16 -10,-22 -5,-20 0,-25 5,-20 10,-22 8,-16" fill="url(#gold)"/>
  </g>
  <g transform="translate(145, 55)">
    <path d="M-10,15 L-14,45 L14,45 L10,15 Z" fill="#C2185B" stroke="url(#gold)" stroke-width="1.5"/>
    <circle cx="0" cy="5" r="12" fill="#FFE0BD" stroke="url(#gold)" stroke-width="1.5"/>
    <path d="M-10,0 Q-12,-8 -8,-13 Q-3,-16 3,-15 Q8,-14 10,-10 Q12,-5 10,0" fill="#8B4513"/>
    <circle cx="-5" cy="4" r="1.5" fill="#1A1A1A"/><circle cx="5" cy="4" r="1.5" fill="#1A1A1A"/>
    <polygon points="-6,-16 -8,-20 -4,-18 0,-23 4,-18 8,-20 6,-16" fill="url(#gold)"/>
  </g>
  <polygon points="100,-10 85,-20 90,-15 95,-25 100,-15 105,-25 110,-15 115,-20" fill="url(#gold)" filter="url(#glow)"/>
</svg>"""
    return svg

def get_socialite_emoji_html(size: int = 80) -> str:
    b64 = base64.b64encode(generate_socialite_emoji().encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" alt="Socialite" style="filter:drop-shadow(0 0 20px rgba(255,215,0,0.5));animation:float 3s ease-in-out infinite;">'

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
SAVED_POSTS_FILE = DATA_DIR / "saved_posts.json"

MAX_POST_LENGTH = 5000
MAX_BIO_LENGTH = 500
MAX_MESSAGE_LENGTH = 5000
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_AVATAR_SIZE = 10 * 1024 * 1024
STORY_EXPIRY_HOURS = 24
ONLINE_THRESHOLD = 300

AVATAR_COLORS = ['#FF6B6B','#4ECDC4','#45B7D1','#96CEB4','#FFEAA7','#DDA0DD','#98D8C8','#F7B787','#FF8A80','#B388FF','#FF5722','#9C27B0','#3F51B5','#009688','#FF9800','#795548','#607D8B','#E91E63','#00BCD4','#8BC34A']

# ========== LUXURY REACTIONS ==========
LUXURY_REACTIONS = {
    "crown": {"emoji": "👑", "label": "Royal"},
    "diamond": {"emoji": "💎", "label": "Brilliant"},
    "cheers": {"emoji": "🥂", "label": "Cheers"},
    "tophat": {"emoji": "🎩", "label": "Classy"},
    "sparkle": {"emoji": "✨", "label": "Premium"},
    "fleur": {"emoji": "⚜️", "label": "Noble"},
}

# ========== SVG AVATARS ==========
MALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='mg'><stop offset='0%' style='stop-color:#667eea'/><stop offset='100%' style='stop-color:#764ba2'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='url(#mg)' stroke='#FFD700' stroke-width='2.5'/><circle cx='50' cy='36' r='15' fill='#F5DEB3'/><ellipse cx='50' cy='75' rx='22' ry='16' fill='#F5DEB3'/><circle cx='44' cy='34' r='2' fill='#1A1A1A'/><circle cx='56' cy='34' r='2' fill='#1A1A1A'/><path d='M46 40 Q50 44 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/><path d='M35 30 Q50 15 65 30' fill='#2C1810'/><polygon points='38,22 40,16 44,19 50,14 56,19 60,16 62,22' fill='#FFD700'/></svg>"""
FEMALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><defs><linearGradient id='fg'><stop offset='0%' style='stop-color:#f093fb'/><stop offset='100%' style='stop-color:#f5576c'/></linearGradient></defs><circle cx='50' cy='50' r='48' fill='url(#fg)' stroke='#FFD700' stroke-width='2.5'/><circle cx='50' cy='36' r='14' fill='#FFE0BD'/><ellipse cx='50' cy='72' rx='18' ry='15' fill='#FFE0BD'/><circle cx='45' cy='34' r='2' fill='#1A1A1A'/><circle cx='55' cy='34' r='2' fill='#1A1A1A'/><path d='M46 40 Q50 43 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/><path d='M47 41 Q50 44 53 41' fill='#E91E63'/><path d='M32 25 Q25 15 28 8 Q35 18 40 22' fill='#8B4513'/><path d='M68 25 Q75 15 72 8 Q65 18 60 22' fill='#8B4513'/><polygon points='40,22 42,16 46,20 50,15 54,20 58,16 60,22' fill='#FFD700'/></svg>"""

# ========== THEMES ==========
THEMES = {
    "midnight": {"name": "Midnight", "icon": "🌌", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"},
    "ocean": {"name": "Ocean", "icon": "🌊", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"},
    "sunset": {"name": "Sunset", "icon": "🌅", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)"},
    "forest": {"name": "Forest", "icon": "🌲", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50", "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)"},
    "neon": {"name": "Neon", "icon": "💜", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
    "coffee": {"name": "Coffee", "icon": "☕", "bg": "#1a0f0a", "card": "rgba(255,255,255,0.04)", "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#8d6e63", "gradient": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)"},
    "cherry": {"name": "Cherry", "icon": "🌸", "bg": "#1a0a1a", "card": "rgba(255,255,255,0.05)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#e91e63", "gradient": "linear-gradient(135deg, #1a0a1a 0%, #2e1a2e 50%, #4e2d4e 100%)"},
    "royal": {"name": "Royal", "icon": "👑", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)"},
    "crimson": {"name": "Crimson", "icon": "❤️", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336", "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)"},
    "arctic": {"name": "Arctic", "icon": "❄️", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)"},
    "ember": {"name": "Ember", "icon": "🔥", "bg": "#1a0f00", "card": "rgba(255,255,255,0.04)", "text": "#fff3e0", "secondary": "#ffcc80", "accent": "#ff9800", "gradient": "linear-gradient(135deg, #1a0f00 0%, #2e1a00 50%, #4e2d00 100%)"},
    "mint": {"name": "Mint", "icon": "🌿", "bg": "#0a1a1a", "card": "rgba(255,255,255,0.04)", "text": "#e0f2f1", "secondary": "#80cbc4", "accent": "#00bfa5", "gradient": "linear-gradient(135deg, #0a1a1a 0%, #1a2e2e 50%, #2d4e4e 100%)"},
}

# ========== WALLPAPERS ==========
WALLPAPERS = {
    "wp_socialite": {"name": "Socialite Luxury", "icon": "👑", "url": None, "gradient": "linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%)"},
    "wp_purple": {"name": "Purple Haze", "icon": "✨", "url": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1200&q=80"},
    "wp_nebula": {"name": "Nebula", "icon": "🌌", "url": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1200&q=80"},
    "wp_ocean": {"name": "Ocean", "icon": "🌊", "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&q=80"},
    "wp_sunset": {"name": "Sunset", "icon": "🌅", "url": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1200&q=80"},
    "wp_forest": {"name": "Forest", "icon": "🌿", "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80"},
    "wp_city": {"name": "City Lights", "icon": "🏙️", "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1200&q=80"},
    "wp_aurora": {"name": "Aurora", "icon": "❄️", "url": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=1200&q=80"},
    "wp_beach": {"name": "Beach", "icon": "🏝️", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80"},
    "wp_mountains": {"name": "Mountains", "icon": "🏔️", "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&q=80"},
}

# ========== UTILITY FUNCTIONS ==========
def validate_image(data: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except:
        return False

def sanitize_text(text: str, max_length: int = 5000) -> str:
    if not text: return ""
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    return html.escape(str(text).strip())[:max_length]

def format_timestamp(ts: str) -> str:
    if not ts: return ""
    try:
        t = datetime.fromisoformat(ts)
        diff = (datetime.now() - t).total_seconds()
        if diff < 10: return "just now"
        elif diff < 60: return f"{int(diff)}s ago"
        elif diff < 3600: return f"{int(diff//60)}m ago"
        elif diff < 86400: return f"{int(diff//3600)}h ago"
        elif diff < 604800: return f"{int(diff//86400)}d ago"
        return t.strftime("%b %d, %Y")
    except:
        return ""

def format_full_date(ts: str) -> str:
    if not ts: return ""
    try:
        t = datetime.fromisoformat(ts)
        return t.strftime("%B %d, %Y at %I:%M %p")
    except:
        return ""

def generate_id() -> str:
    return str(uuid.uuid4())

def get_avatar_color(username: str) -> str:
    if not username: return AVATAR_COLORS[0]
    return AVATAR_COLORS[hash(username) % len(AVATAR_COLORS)]

def get_initials(username: str) -> str:
    if not username: return "?"
    parts = username.replace('_', ' ').split()
    if len(parts) >= 2: return (parts[0][0] + parts[1][0]).upper()
    return username[0].upper()

def get_svg_avatar(username: str, size: int = 36, is_female: bool = False) -> str:
    svg = FEMALE_SVG if is_female else MALE_SVG
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #FFD700;flex-shrink:0;box-shadow:0 0 10px rgba(255,215,0,0.3);" alt="{username}">'

def atomic_save(filepath: pathlib.Path, data: Any) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        tmp = filepath.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(filepath)
        return True
    except:
        return False

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
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default

    @staticmethod
    def save(filepath: pathlib.Path, data) -> bool:
        return atomic_save(filepath, data)

    @staticmethod
    def hash_password(pwd: str, salt: str = None) -> Tuple[str, str]:
        if salt is None: salt = secrets.token_hex(32)
        h = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 200000)
        return h.hex(), salt

    @staticmethod
    def verify_password(pwd: str, stored_hash: str, salt: str) -> bool:
        h, _ = DataManager.hash_password(pwd, salt)
        return h == stored_hash

    @staticmethod
    def get_users() -> Dict:
        return DataManager.load(USERS_FILE, {})

    @staticmethod
    def save_users(data: Dict):
        DataManager.save(USERS_FILE, data)

    @staticmethod
    def user_exists(username: str) -> bool:
        return username.lower() in [u.lower() for u in DataManager.get_users()]

    @staticmethod
    def create_user(username: str, password: str) -> Tuple[bool, str]:
        if DataManager.user_exists(username):
            return False, "Username already exists"
        if len(username) < 3 or len(username) > MAX_USERNAME_LENGTH:
            return False, f"Username must be 3-{MAX_USERNAME_LENGTH} characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Only letters, numbers, and underscores allowed"
        users = DataManager.get_users()
        h, s = DataManager.hash_password(password)
        users[username] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
        DataManager.save_users(users)
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager._default_profile(username)
        DataManager.save_profiles(profiles)
        logger.info(f"New user created: {username}")
        return True, "Account created successfully!"

    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, str]:
        users = DataManager.get_users()
        for un, data in users.items():
            if un.lower() == username.lower():
                if isinstance(data, dict) and "salt" in data:
                    if DataManager.verify_password(password, data["password"], data["salt"]):
                        return True, un
                elif isinstance(data, str) and data == hashlib.sha256(password.encode()).hexdigest():
                    h, s = DataManager.hash_password(password)
                    users[un] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
                    DataManager.save_users(users)
                    return True, un
                return False, "Incorrect password"
        return False, "User not found"

    @staticmethod
    def _default_profile(username: str) -> Dict:
        return {
            "display_name": username, "bio": "", "avatar": None,
            "cover_photo": None, "website": "", "location": "",
            "is_verified": False, "is_premium": False, "last_seen": "",
            "followers": [], "following": [], "blocked": [],
            "post_count": 0, "theme": "midnight", "wallpaper": "wp_socialite",
            "gender": "male", "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def get_profiles() -> Dict:
        return DataManager.load(PROFILES_FILE, {})

    @staticmethod
    def save_profiles(data: Dict):
        DataManager.save(PROFILES_FILE, data)

    @staticmethod
    def get_profile(username: str) -> Dict:
        profiles = DataManager.get_profiles()
        if username not in profiles:
            profiles[username] = DataManager._default_profile(username)
            DataManager.save_profiles(profiles)
        p = profiles[username]
        defaults = DataManager._default_profile(username)
        for k, v in defaults.items():
            if k not in p:
                p[k] = v
        return p

    @staticmethod
    def update_profile(username: str, updates: Dict):
        profiles = DataManager.get_profiles()
        if username in profiles:
            profiles[username].update(updates)
            DataManager.save_profiles(profiles)

    @staticmethod
    def update_last_seen(username: str):
        profiles = DataManager.get_profiles()
        if username in profiles:
            profiles[username]["last_seen"] = datetime.now().isoformat()
            DataManager.save_profiles(profiles)

    @staticmethod
    def get_feed_posts() -> List:
        return DataManager.load(FEED_POSTS_FILE, [])

    @staticmethod
    def save_feed_posts(data: List):
        if len(data) > 5000:
            data = data[-3000:]
        DataManager.save(FEED_POSTS_FILE, data)

    @staticmethod
    def get_stories() -> Dict:
        return DataManager.load(STORIES_FILE, {})

    @staticmethod
    def save_stories(data: Dict):
        DataManager.save(STORIES_FILE, data)

    @staticmethod
    def get_active_stories() -> Dict:
        stories = DataManager.get_stories()
        active = {}
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        for u, ss in stories.items():
            a = [s for s in ss if s.get("timestamp", "") > cutoff]
            if a:
                active[u] = a
        return active

    @staticmethod
    def get_direct_messages() -> Dict:
        return DataManager.load(DIRECT_MESSAGES_FILE, {})

    @staticmethod
    def save_direct_messages(data: Dict):
        DataManager.save(DIRECT_MESSAGES_FILE, data)

    @staticmethod
    def get_chat_id(u1: str, u2: str) -> str:
        return f"dm_{'_'.join(sorted([u1.lower(), u2.lower()]))}"

    @staticmethod
    def get_group_chats() -> Dict:
        return DataManager.load(GROUP_CHATS_FILE, {})

    @staticmethod
    def save_group_chats(data: Dict):
        DataManager.save(GROUP_CHATS_FILE, data)

    @staticmethod
    def get_channels() -> Dict:
        return DataManager.load(CHANNELS_FILE, {})

    @staticmethod
    def save_channels(data: Dict):
        DataManager.save(CHANNELS_FILE, data)

    @staticmethod
    def get_comments() -> Dict:
        return DataManager.load(COMMENTS_FILE, {})

    @staticmethod
    def save_comments(data: Dict):
        DataManager.save(COMMENTS_FILE, data)

    @staticmethod
    def get_notifications() -> Dict:
        return DataManager.load(NOTIFICATIONS_FILE, {})

    @staticmethod
    def save_notifications(data: Dict):
        DataManager.save(NOTIFICATIONS_FILE, data)

    @staticmethod
    def add_notification(username: str, ntype: str, message: str, from_user: str = ""):
        notifs = DataManager.get_notifications()
        if username not in notifs:
            notifs[username] = []
        notifs[username].insert(0, {
            "id": generate_id(), "type": ntype, "message": message,
            "from_user": from_user, "timestamp": datetime.now().isoformat(), "read": False
        })
        if len(notifs[username]) > 200:
            notifs[username] = notifs[username][:200]
        DataManager.save_notifications(notifs)

    @staticmethod
    def get_unread_count(username: str) -> int:
        return sum(1 for n in DataManager.get_notifications().get(username, []) if not n.get("read"))

    @staticmethod
    def mark_all_read(username: str):
        notifs = DataManager.get_notifications()
        if username in notifs:
            for n in notifs[username]:
                n["read"] = True
            DataManager.save_notifications(notifs)

    @staticmethod
    def get_online_users() -> List[str]:
        profiles = DataManager.get_profiles()
        now = datetime.now()
        online = []
        for u, p in profiles.items():
            if p.get("last_seen"):
                try:
                    if (now - datetime.fromisoformat(p["last_seen"])).total_seconds() < ONLINE_THRESHOLD:
                        online.append(u)
                except:
                    pass
        return online

    @staticmethod
    def get_saved_posts() -> Dict:
        return DataManager.load(SAVED_POSTS_FILE, {})

    @staticmethod
    def save_saved_posts(data: Dict):
        DataManager.save(SAVED_POSTS_FILE, data)

    @staticmethod
    def is_post_saved(username: str, post_id: str) -> bool:
        return post_id in DataManager.get_saved_posts().get(username, [])

    @staticmethod
    def search_users(query: str, limit: int = 50) -> List[Dict]:
        users = DataManager.get_users()
        profiles = DataManager.get_profiles()
        results = []
        q = query.lower()
        for u in users:
            if q in u.lower() or q in profiles.get(u, {}).get("display_name", "").lower():
                p = profiles.get(u, {})
                results.append({
                    "username": u,
                    "display_name": p.get("display_name", u),
                    "bio": p.get("bio", ""),
                    "avatar": p.get("avatar"),
                    "followers": len(p.get("followers", [])),
                    "is_verified": p.get("is_verified", False),
                    "is_premium": p.get("is_premium", False)
                })
            if len(results) >= limit:
                break
        return results

# ========== HANDLERS ==========
class PostHandler:
    @staticmethod
    def create(text: str, media_data: str = None, media_name: str = None,
               location: str = "") -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_POST_LENGTH) if text else ""
        if not text and not media_data:
            return False, "Post cannot be empty"
        posts = DataManager.get_feed_posts()
        post = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "type": "post",
            "reactions": {},
            "comments_count": 0,
            "shares_count": 0,
            "views_count": 0,
            "is_edited": False,
            "edited_at": None,
            "location": sanitize_text(location, 100) if location else "",
            "is_pinned": False
        }
        if media_data:
            post["media"] = media_data
            post["media_name"] = sanitize_text(media_name, 200) if media_name else "media"
            post["media_type"] = "image"
        posts.append(post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        p = DataManager.get_profile(st.session_state.user)
        p["post_count"] = p.get("post_count", 0) + 1
        DataManager.save_profiles(DataManager.get_profiles())
        return True, "Posted successfully!"

    @staticmethod
    def edit(post_id: str, new_text: str) -> Tuple[bool, str]:
        new_text = sanitize_text(new_text, MAX_POST_LENGTH)
        if not new_text:
            return False, "Post cannot be empty"
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id and post["username"] == st.session_state.user:
                post["text"] = new_text
                post["is_edited"] = True
                post["edited_at"] = datetime.now().isoformat()
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Post updated!"
        return False, "Post not found"

    @staticmethod
    def delete(post_id: str) -> Tuple[bool, str]:
        posts = DataManager.get_feed_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Post deleted!"
        return False, "Post not found"

    @staticmethod
    def add_reaction(post_id: str, reaction_key: str):
        posts = DataManager.get_feed_posts()
        u = st.session_state.user
        for post in posts:
            if post["id"] == post_id:
                if "reactions" not in post:
                    post["reactions"] = {}
                for rk in list(post["reactions"].keys()):
                    if u in post["reactions"][rk]:
                        post["reactions"][rk].remove(u)
                        if not post["reactions"][rk]:
                            del post["reactions"][rk]
                if reaction_key not in post["reactions"]:
                    post["reactions"][reaction_key] = []
                post["reactions"][reaction_key].append(u)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return

    @staticmethod
    def save_post(post_id: str) -> Tuple[bool, str]:
        u = st.session_state.user
        saved = DataManager.get_saved_posts()
        if u not in saved:
            saved[u] = []
        if post_id in saved[u]:
            saved[u].remove(post_id)
            DataManager.save_saved_posts(saved)
            return True, "Post unsaved"
        saved[u].append(post_id)
        if len(saved[u]) > 5000:
            saved[u] = saved[u][-5000:]
        DataManager.save_saved_posts(saved)
        return True, "Post saved!"

    @staticmethod
    def create_poll(question: str, options: List[str], duration_hours: int = 168) -> Tuple[bool, str]:
        question = sanitize_text(question, 500)
        options = [sanitize_text(o, 200) for o in options if o.strip()]
        if len(options) < 2:
            return False, "Need at least 2 options"
        if len(options) > 20:
            return False, "Maximum 20 options"
        posts = DataManager.get_feed_posts()
        poll_post = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": question,
            "timestamp": datetime.now().isoformat(),
            "type": "poll",
            "poll_data": {
                "options": {o: [] for o in options},
                "total_votes": 0,
                "ends_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()
            }
        }
        posts.append(poll_post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        return True, "Poll created!"

    @staticmethod
    def vote_poll(post_id: str, option: str):
        posts = DataManager.get_feed_posts()
        u = st.session_state.user
        for post in posts:
            if post["id"] == post_id and post.get("type") == "poll":
                pd = post["poll_data"]
                for o, v in pd["options"].items():
                    if u in v:
                        v.remove(u)
                        pd["total_votes"] -= 1
                if option in pd["options"]:
                    pd["options"][option].append(u)
                    pd["total_votes"] += 1
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return

class StoryHandler:
    @staticmethod
    def create(media_data: str, media_name: str, caption: str = "") -> Tuple[bool, str]:
        stories = DataManager.get_stories()
        u = st.session_state.user
        if u not in stories:
            stories[u] = []
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        stories[u] = [s for s in stories[u] if s["timestamp"] > cutoff]
        if len(stories[u]) >= 20:
            return False, "Maximum 20 active stories"
        stories[u].append({
            "id": generate_id(),
            "username": u,
            "media": media_data,
            "media_name": sanitize_text(media_name, 200),
            "caption": sanitize_text(caption, 200) if caption else "",
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=STORY_EXPIRY_HOURS)).isoformat(),
            "views": []
        })
        DataManager.save_stories(stories)
        st.session_state.stories = stories
        return True, "Story posted!"

    @staticmethod
    def view(username: str, story_id: str):
        stories = DataManager.get_stories()
        if username in stories:
            for s in stories[username]:
                if s["id"] == story_id and st.session_state.user not in s["views"]:
                    s["views"].append(st.session_state.user)
            DataManager.save_stories(stories)
            st.session_state.stories = stories

    @staticmethod
    def delete(story_id: str) -> Tuple[bool, str]:
        stories = DataManager.get_stories()
        u = st.session_state.user
        if u in stories:
            for i, s in enumerate(stories[u]):
                if s["id"] == story_id:
                    stories[u].pop(i)
                    if not stories[u]:
                        del stories[u]
                    DataManager.save_stories(stories)
                    st.session_state.stories = stories
                    return True, "Story deleted!"
        return False, "Story not found"

class ChatHandler:
    @staticmethod
    def send(to_user: str, text: str, media_data: str = None,
             media_name: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH) if text else ""
        if not text and not media_data:
            return False, "Message cannot be empty"
        from_user = st.session_state.user
        # Check if blocked
        tp = DataManager.get_profile(to_user)
        if from_user in tp.get("blocked", []):
            return False, "You are blocked by this user"
        chat_id = DataManager.get_chat_id(from_user, to_user)
        dms = DataManager.get_direct_messages()
        if chat_id not in dms:
            dms[chat_id] = {
                "participants": [from_user, to_user],
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "is_encrypted": True
            }
        msg = {
            "id": generate_id(),
            "from": from_user,
            "to": to_user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "delivered": True
        }
        if media_data:
            msg["media"] = media_data
            msg["media_name"] = sanitize_text(media_name, 200) if media_name else "file"
            msg["media_type"] = "image"
        dms[chat_id]["messages"].append(msg)
        if len(dms[chat_id]["messages"]) > 10000:
            dms[chat_id]["messages"] = dms[chat_id]["messages"][-10000:]
        DataManager.save_direct_messages(dms)
        DataManager.add_notification(to_user, "message", f"New message from @{from_user}", from_user)
        return True, "Message sent!"

    @staticmethod
    def get_messages(with_user: str) -> List[Dict]:
        chat_id = DataManager.get_chat_id(st.session_state.user, with_user)
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            for m in dms[chat_id]["messages"]:
                if m.get("to") == st.session_state.user:
                    m["read"] = True
            DataManager.save_direct_messages(dms)
            return dms[chat_id]["messages"]
        return []

    @staticmethod
    def get_chat_list() -> List[Dict]:
        u = st.session_state.user
        dms = DataManager.get_direct_messages()
        online = DataManager.get_online_users()
        profiles = DataManager.get_profiles()
        chats = []
        for cid, cd in dms.items():
            if u in cd["participants"]:
                other = [p for p in cd["participants"] if p != u][0]
                msgs = cd["messages"]
                last = msgs[-1] if msgs else None
                unread = sum(1 for m in msgs if m.get("to") == u and not m.get("read", False))
                other_profile = profiles.get(other, {})
                chats.append({
                    "with_user": other,
                    "display_name": other_profile.get("display_name", other),
                    "last_message": last["text"][:100] if last and last.get("text") else "📷 Media" if last and last.get("media") else "No messages",
                    "last_time": last["timestamp"] if last else cd["created_at"],
                    "unread": unread,
                    "is_online": other in online,
                    "is_verified": other_profile.get("is_verified", False),
                    "is_premium": other_profile.get("is_premium", False)
                })
        chats.sort(key=lambda x: x["last_time"], reverse=True)
        return chats

    @staticmethod
    def delete_message(chat_id: str, msg_id: str) -> Tuple[bool, str]:
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            for i, m in enumerate(dms[chat_id]["messages"]):
                if m["id"] == msg_id and m["from"] == st.session_state.user:
                    dms[chat_id]["messages"].pop(i)
                    DataManager.save_direct_messages(dms)
                    return True, "Message deleted"
        return False, "Message not found"

class GroupHandler:
    @staticmethod
    def create(name: str, members: List[str], is_channel: bool = False,
               description: str = "") -> Tuple[bool, str]:
        name = sanitize_text(name, 100)
        if not name:
            return False, "Name is required"
        all_members = list(set(members + [st.session_state.user]))
        if len(all_members) < 2 and not is_channel:
            return False, "Need at least 2 members"
        gid = f"{'channel' if is_channel else 'group'}_{generate_id()[:8]}"
        data = {
            "name": name,
            "owner": st.session_state.user,
            "admins": [st.session_state.user],
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "description": sanitize_text(description, 500) if description else "",
            "icon": None,
            "is_public": False
        }
        if is_channel:
            data["subscribers"] = all_members
            channels = DataManager.get_channels()
            channels[gid] = data
            DataManager.save_channels(channels)
        else:
            data["members"] = all_members
            groups = DataManager.get_group_chats()
            groups[gid] = data
            DataManager.save_group_chats(groups)
            for m in members:
                if m != st.session_state.user:
                    DataManager.add_notification(m, "group_invite", f"You were added to '{name}'", st.session_state.user)
        return True, f"{'Channel' if is_channel else 'Group'} '{name}' created!"

    @staticmethod
    def send_message(group_id: str, text: str, media_data: str = None,
                    is_channel: bool = False) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text and not media_data:
            return False, "Message cannot be empty"
        data = DataManager.get_channels() if is_channel else DataManager.get_group_chats()
        if group_id not in data:
            return False, "Not found"
        if is_channel and st.session_state.user not in data[group_id].get("admins", []):
            return False, "Only admins can post in channels"
        if not is_channel and st.session_state.user not in data[group_id].get("members", []):
            return False, "You are not a member of this group"
        msg = {
            "id": generate_id(),
            "from": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        if media_data:
            msg["media"] = media_data
        data[group_id]["messages"].append(msg)
        if is_channel:
            DataManager.save_channels(data)
        else:
            DataManager.save_group_chats(data)
        return True, "Message sent!"

    @staticmethod
    def get_user_groups() -> List[Dict]:
        u = st.session_state.user
        groups = DataManager.get_group_chats()
        result = []
        for gid, gd in groups.items():
            if u in gd.get("members", []):
                msgs = gd["messages"]
                last = msgs[-1] if msgs else None
                result.append({
                    "id": gid,
                    "name": gd["name"],
                    "members": len(gd.get("members", [])),
                    "description": gd.get("description", ""),
                    "last_message": last["text"][:50] if last and last.get("text") else "No messages",
                    "last_time": last["timestamp"] if last else gd["created_at"],
                    "is_admin": u in gd.get("admins", []),
                    "is_owner": u == gd.get("owner", "")
                })
        return sorted(result, key=lambda x: x["last_time"], reverse=True)

    @staticmethod
    def get_user_channels() -> List[Dict]:
        u = st.session_state.user
        channels = DataManager.get_channels()
        result = []
        for cid, cd in channels.items():
            if u in cd.get("subscribers", []):
                msgs = cd["messages"]
                last = msgs[-1] if msgs else None
                result.append({
                    "id": cid,
                    "name": cd["name"],
                    "subscribers": len(cd.get("subscribers", [])),
                    "description": cd.get("description", ""),
                    "last_message": last["text"][:50] if last and last.get("text") else "No posts",
                    "last_time": last["timestamp"] if last else cd["created_at"],
                    "is_admin": u in cd.get("admins", []),
                    "is_owner": u == cd.get("owner", "")
                })
        return sorted(result, key=lambda x: x["last_time"], reverse=True)

    @staticmethod
    def get_group_messages(group_id: str) -> List:
        return DataManager.get_group_chats().get(group_id, {}).get("messages", [])

    @staticmethod
    def get_channel_messages(channel_id: str) -> List:
        return DataManager.get_channels().get(channel_id, {}).get("messages", [])

class CommentHandler:
    @staticmethod
    def add(post_id: str, text: str, parent_id: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, 1000)
        if not text:
            return False, "Comment cannot be empty"
        comments = DataManager.get_comments()
        if post_id not in comments:
            comments[post_id] = []
        comment = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "likes": [],
            "parent_id": parent_id,
            "replies": []
        }
        if parent_id:
            for c in comments[post_id]:
                if c["id"] == parent_id:
                    c["replies"].append(comment)
                    break
        else:
            comments[post_id].append(comment)
        DataManager.save_comments(comments)
        # Update comment count on post
        posts = DataManager.get_feed_posts()
        for p in posts:
            if p["id"] == post_id:
                p["comments_count"] = len(comments[post_id])
                break
        DataManager.save_feed_posts(posts)
        return True, "Comment added!"

    @staticmethod
    def get(post_id: str) -> List:
        return DataManager.get_comments().get(post_id, [])

    @staticmethod
    def delete(post_id: str, comment_id: str) -> Tuple[bool, str]:
        comments = DataManager.get_comments()
        if post_id in comments:
            for i, c in enumerate(comments[post_id]):
                if c["id"] == comment_id and c["username"] == st.session_state.user:
                    comments[post_id].pop(i)
                    DataManager.save_comments(comments)
                    return True, "Comment deleted!"
        return False, "Comment not found"

class FollowHandler:
    @staticmethod
    def follow(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user:
            return False, "You cannot follow yourself"
        profiles = DataManager.get_profiles()
        up = DataManager.get_profile(st.session_state.user)
        tp = DataManager.get_profile(target)
        for p in [up, tp]:
            for k in ["following", "followers", "blocked", "follow_requests"]:
                if k not in p:
                    p[k] = []
        if st.session_state.user in tp.get("blocked", []):
            return False, "You are blocked by this user"
        if target in up.get("blocked", []):
            return False, "Unblock this user first"
        if target in up["following"]:
            up["following"].remove(target)
            if st.session_state.user in tp["followers"]:
                tp["followers"].remove(st.session_state.user)
            action = "Unfollowed"
        else:
            up["following"].append(target)
            tp["followers"].append(st.session_state.user)
            action = "Following"
            DataManager.add_notification(target, "follow", f"@{st.session_state.user} started following you", st.session_state.user)
        profiles[st.session_state.user] = up
        profiles[target] = tp
        DataManager.save_profiles(profiles)
        return True, f"{action}!"

    @staticmethod
    def is_following(target: str) -> bool:
        return target in DataManager.get_profile(st.session_state.user).get("following", [])

    @staticmethod
    def block(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user:
            return False, "You cannot block yourself"
        profiles = DataManager.get_profiles()
        up = DataManager.get_profile(st.session_state.user)
        for k in ["following", "followers", "blocked"]:
            if k not in up:
                up[k] = []
        if target in up["blocked"]:
            up["blocked"].remove(target)
            action = "Unblocked"
        else:
            up["blocked"].append(target)
            if target in up.get("following", []):
                up["following"].remove(target)
            tp = DataManager.get_profile(target)
            if st.session_state.user in tp.get("followers", []):
                tp["followers"].remove(st.session_state.user)
            profiles[target] = tp
            action = "Blocked"
        profiles[st.session_state.user] = up
        DataManager.save_profiles(profiles)
        return True, f"{action}!"

# ========== SESSION STATE ==========
def init_session():
    defaults = {
        'feed_posts': [],
        'stories': {},
        'auth': False,
        'user': "",
        'current_tab': "feed",
        'active_chat': None,
        'active_group': None,
        'active_channel': None,
        'chat_type': None,
        'show_create_modal': False,
        'show_notifications': False,
        'show_new_chat': False,
        'show_new_group': False,
        'show_new_channel': False,
        'show_comments_for': None,
        'editing_post': None,
        'viewing_profile': None,
        'confirm_delete': None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    if not st.session_state.feed_posts:
        st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories:
        st.session_state.stories = DataManager.get_stories()

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
        w = DataManager.get_profile(st.session_state.user).get('wallpaper', 'wp_socialite')
        return WALLPAPERS.get(w, WALLPAPERS['wp_socialite'])
    return WALLPAPERS['wp_socialite']

# ========== CSS STYLES ==========
def inject_styles():
    theme = get_theme()
    wp = get_wallpaper()
    if wp.get("url"):
        bg = f"url('{wp['url']}') center/cover no-repeat fixed"
    else:
        bg = wp.get("gradient", theme["gradient"])

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;700;900&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    
    #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
    .stApp > header {{ display: none !important; }}
    div[data-testid="stVerticalBlock"] > div:first-child {{ display: none !important; }}
    
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
    
    .main {{ height: 100vh !important; overflow: hidden !important; }}
    
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
        background-clip: text !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }}
    
    .badge {{
        background: #FFD700 !important;
        color: #1a0033 !important;
        border-radius: 50% !important;
        padding: 1px 6px !important;
        font-size: 0.6rem !important;
        font-weight: 700 !important;
        position: absolute !important;
        top: -8px !important;
        right: -10px !important;
        box-shadow: 0 0 10px rgba(255,215,0,0.5) !important;
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
        max-height: 400px !important;
        object-fit: cover !important;
    }}
    
    /* Luxury Reaction Bar */
    .luxury-bar {{
        display: flex !important;
        gap: 3px !important;
        padding: 6px 8px !important;
        border-top: 1px solid rgba(255,215,0,0.1) !important;
        flex-wrap: wrap !important;
    }}
    
    .luxury-btn {{
        padding: 4px 7px !important;
        border-radius: 16px !important;
        cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        font-size: 0.85rem !important;
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
    
    /* Chat Bubbles */
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
    
    /* User Row */
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
        background: rgba(0,0,0,0.85) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
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
    
    /* Theme and Wallpaper Grids */
    .theme-grid {{
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 6px !important;
        padding: 6px 0 !important;
    }}
    
    .wallpaper-grid {{
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        gap: 5px !important;
        padding: 6px 0 !important;
    }}
    
    .theme-card {{
        border-radius: 10px !important;
        padding: 14px 4px !important;
        text-align: center !important;
        cursor: pointer !important;
        border: 2px solid transparent !important;
        transition: all 0.3s !important;
    }}
    
    .theme-card:hover {{
        transform: scale(1.05) !important;
        box-shadow: 0 0 20px rgba(255,215,0,0.3) !important;
    }}
    
    .theme-card.selected {{
        border-color: #FFD700 !important;
        box-shadow: 0 0 20px rgba(255,215,0,0.4) !important;
    }}
    
    .wallpaper-card {{
        border-radius: 8px !important;
        height: 50px !important;
        cursor: pointer !important;
        border: 2px solid transparent !important;
        background-size: cover !important;
        background-position: center !important;
        transition: all 0.3s !important;
    }}
    
    .wallpaper-card:hover {{
        transform: scale(1.08) !important;
        box-shadow: 0 0 15px rgba(255,215,0,0.3) !important;
    }}
    
    .wallpaper-card.selected {{
        border-color: #FFD700 !important;
        box-shadow: 0 0 20px rgba(255,215,0,0.5) !important;
    }}
    
    /* Streamlit Button Overrides */
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
        cursor: pointer !important;
    }}
    
    .stButton > button:hover {{
        background: rgba(255,215,0,0.15) !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 12px rgba(255,215,0,0.25) !important;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
    }}
    
    .stTextInput > div > div > input::placeholder,
    .stTextArea > div > div > textarea::placeholder {{
        color: {theme['secondary']} !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 3px !important;
        background: transparent !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {theme['secondary']} !important;
        border-radius: 6px !important;
        padding: 5px 12px !important;
        font-size: 0.78rem !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: #FFD700 !important;
        background: rgba(255,215,0,0.1) !important;
    }}
    
    .stExpander {{
        background: {theme['card']} !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }}
    
    .streamlit-expanderHeader {{
        color: {theme['text']} !important;
        font-size: 0.85rem !important;
    }}
    
    ::-webkit-scrollbar {{ width: 4px !important; }}
    ::-webkit-scrollbar-track {{ background: transparent !important; }}
    ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
    
    /* Socialite Brand Animation */
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    @media (max-width: 480px) {{
        .main-content {{ padding: 6px 8px !important; }}
        .card {{ border-radius: 10px !important; margin-bottom: 8px !important; }}
        .bottom-nav {{ height: 52px !important; }}
        .main-content {{ bottom: 52px !important; }}
        .app-header {{ height: 44px !important; }}
        .main-content {{ top: 44px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ========== AVATAR RENDERERS ==========
def render_avatar(username: str, size: int = 36) -> str:
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    is_female = profile.get("gender", "male") == "female"
    is_premium = profile.get("is_premium", False)
    
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            border = "3px solid #FFD700" if is_premium else "2px solid #FFD700"
            glow = "box-shadow:0 0 15px rgba(255,215,0,0.5);" if is_premium else "box-shadow:0 0 8px rgba(255,215,0,0.2);"
            return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border};flex-shrink:0;{glow}" alt="{username}">'
        except:
            pass
    
    return get_svg_avatar(username, size, is_female)

def render_story_ring(username: str, size: int = 56, has_new: bool = False) -> str:
    ring_class = "story-ring" if has_new else "story-ring viewed"
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<div class="{ring_class}"><img src="data:image/jpeg;base64,{b64}" class="story-ring-inner" alt="{username}"></div>'
    
    color = get_avatar_color(username)
    return f'<div class="{ring_class}"><div class="story-ring-inner-placeholder" style="font-size:{size*0.3}px;background:{color};">{get_initials(username)}</div></div>'

# ========== UI COMPONENTS ==========
def render_header():
    user = st.session_state.user
    unread = DataManager.get_unread_count(user)
    theme = get_theme()
    
    badge_html = f'<span class="badge">{unread}</span>' if unread > 0 else ''
    emoji_html = get_socialite_emoji_html(24)
    
    header_html = f"""
    <div class="app-header">
        <div class="app-logo">{emoji_html} Socialite</div>
        <div style="display:flex;align-items:center;gap:12px;color:{theme['text']};">
            <span style="position:relative;cursor:pointer;" onclick="document.getElementById('notif_btn').click();">🔔{badge_html}</span>
            {render_avatar(user, 28)}
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Hidden notification button
    if st.button("🔔", key="notif_btn", label_visibility="collapsed"):
        DataManager.mark_all_read(user)
        st.rerun()

def render_stories_bar():
    user = st.session_state.user
    active = DataManager.get_active_stories()
    
    html_parts = ['<div class="stories-row">']
    
    has_own = user in active
    html_parts.append(
        f'<div class="story-item">{render_story_ring(user, 56, not has_own)}'
        f'<div class="story-name">You</div></div>'
    )
    
    for u, ss in active.items():
        if u != user:
            has_new = any(st.session_state.user not in s.get("views", []) for s in ss)
            html_parts.append(
                f'<div class="story-item">{render_story_ring(u, 56, has_new)}'
                f'<div class="story-name">@{u[:8]}</div></div>'
            )
    
    if len(active) <= 1:
        html_parts.append(
            '<div style="color:#94a3b8;display:flex;align-items:center;font-size:0.7rem;padding-left:8px;">'
            'No stories yet</div>'
        )
    
    html_parts.append('</div>')
    st.markdown(''.join(html_parts), unsafe_allow_html=True)

def render_luxury_bar(post_id: str, reactions: Dict):
    st.markdown('<div class="luxury-bar">', unsafe_allow_html=True)
    cols = st.columns(len(LUXURY_REACTIONS))
    
    for i, (rkey, rdata) in enumerate(LUXURY_REACTIONS.items()):
        count = len(reactions.get(rkey, []))
        is_active = st.session_state.user in reactions.get(rkey, [])
        active_class = "active" if is_active else ""
        
        with cols[i]:
            if st.button(
                f"{rdata['emoji']} {count}",
                key=f"lux_{rkey}_{post_id}",
                help=rdata['label']
            ):
                PostHandler.add_reaction(post_id, rkey)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_post_card(post: Dict):
    username = post.get("username", "")
    pid = post.get("id", "")
    is_owner = username == st.session_state.user
    profile = DataManager.get_profile(username)
    is_verified = profile.get("is_verified", False)
    is_premium = profile.get("is_premium", False)
    is_edited = post.get("is_edited", False)
    
    # Build badges
    badges = []
    if is_verified:
        badges.append('<span style="color:#FFD700;font-size:0.65rem;">✓✓</span>')
    if is_premium:
        badges.append('<span style="color:#FFD700;font-size:0.6rem;">👑</span>')
    badge_html = ''.join(badges)
    
    edited_text = ' · Edited' if is_edited else ''
    
    # Build header
    header_html = (
        f'<div class="card">'
        f'<div class="card-header">'
        f'{render_avatar(username)}'
        f'<div style="flex:1;">'
        f'<div class="username-text">@{html.escape(username)}{badge_html}</div>'
        f'<div class="timestamp">{format_timestamp(post.get("timestamp", ""))}{edited_text}</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Post text
    if post.get("text"):
        st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
    
    # Post media
    if post.get("media") and post.get("media_type") == "image":
        st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post media">', unsafe_allow_html=True)
    
    # Luxury reaction bar
    render_luxury_bar(pid, post.get("reactions", {}))
    
    # Action buttons
    st.markdown('<div style="display:flex;align-items:center;padding:4px 10px 8px 10px;gap:8px;">', unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    
    with c1:
        if st.button("💬", key=f"cm_{pid}"):
            if st.session_state.show_comments_for == pid:
                st.session_state.show_comments_for = None
            else:
                st.session_state.show_comments_for = pid
            st.rerun()
    
    with c2:
        if st.button("🔄", key=f"rp_{pid}"):
            st.toast("Reposted successfully!", icon="🔄")
    
    with c3:
        is_saved = DataManager.is_post_saved(st.session_state.user, pid)
        save_icon = "📌" if is_saved else "🔖"
        if st.button(save_icon, key=f"sv_{pid}"):
            result, msg = PostHandler.save_post(pid)
            st.toast(msg, icon="✅" if "saved" in msg.lower() else "ℹ️")
            st.rerun()
    
    if is_owner:
        with c4:
            if st.button("🗑️ Delete", key=f"dl_{pid}"):
                if st.session_state.confirm_delete == pid:
                    PostHandler.delete(pid)
                    st.session_state.confirm_delete = None
                    st.rerun()
                else:
                    st.session_state.confirm_delete = pid
                    st.toast("Click again to confirm delete", icon="⚠️")
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Comments section
    if st.session_state.show_comments_for == pid:
        render_comments(pid)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(post: Dict):
    username = post.get("username", "")
    pid = post.get("id", "")
    pd = post.get("poll_data", {})
    total = pd.get("total_votes", 0)
    options = pd.get("options", {})
    profile = DataManager.get_profile(username)
    is_verified = profile.get("is_verified", False)
    ends_at = pd.get("ends_at", "")
    
    verified_badge = '<span style="color:#FFD700;">✓✓</span>' if is_verified else ''
    ends_text = f' · Ends {format_timestamp(ends_at)}' if ends_at else ''
    
    # Header
    header_html = (
        f'<div class="card">'
        f'<div class="card-header">'
        f'{render_avatar(username)}'
        f'<div style="flex:1;">'
        f'<div class="username-text">@{html.escape(username)}{verified_badge}</div>'
        f'<div class="timestamp">📊 Poll · {format_timestamp(post.get("timestamp", ""))}{ends_text}</div>'
        f'</div>'
        f'</div>'
        f'<div class="post-text" style="font-weight:600;">{html.escape(post.get("text", ""))}</div>'
        f'<div style="padding:0 10px 8px 10px;">'
    )
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Options
    for opt, voters in options.items():
        pct = (len(voters) / total * 100) if total > 0 else 0
        voted = st.session_state.user in voters
        border = "border:1px solid #FFD700;" if voted else ""
        
        option_html = (
            f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:5px 8px;margin:3px 0;{border}">'
            f'<div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.8rem;">'
            f'<span>{"✓ " if voted else ""}{html.escape(opt)}</span>'
            f'<span>{pct:.0f}%</span>'
            f'</div>'
            f'<div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;margin-top:3px;">'
            f'<div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#FFD700,#FFA500);border-radius:2px;"></div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(option_html, unsafe_allow_html=True)
        
        if st.button("Vote", key=f"pv_{pid}_{opt[:8]}"):
            PostHandler.vote_poll(pid, opt)
            st.rerun()
    
    st.markdown(f'<div style="color:#94a3b8;font-size:0.6rem;margin-top:4px;">{total} votes</div></div></div>', unsafe_allow_html=True)

def render_comments(post_id: str):
    comments = CommentHandler.get(post_id)
    st.markdown('<div style="padding:4px 10px;border-top:1px solid rgba(255,215,0,0.1);">', unsafe_allow_html=True)
    
    for c in comments[-20:]:
        comment_html = (
            f'<div style="margin:3px 0;display:flex;gap:5px;align-items:flex-start;">'
            f'{render_avatar(c["username"], 20)}'
            f'<div>'
            f'<span style="color:#f1f5f9;font-weight:600;font-size:0.7rem;">@{html.escape(c["username"])}</span> '
            f'<span style="color:#e2e8f0;font-size:0.73rem;">{html.escape(c["text"])}</span>'
            f'<div style="color:#64748b;font-size:0.6rem;">{format_timestamp(c["timestamp"])}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(comment_html, unsafe_allow_html=True)
    
    # Add comment form
    with st.form(f"cmf_{post_id}", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            txt = st.text_input(
                "Add a comment",
                placeholder="Write a comment...",
                key=f"ci_{post_id}"
            )
        with c2:
            if st.form_submit_button("Post", use_container_width=True):
                if txt.strip():
                    result, msg = CommentHandler.add(post_id, txt)
                    if result:
                        st.rerun()
                    else:
                        st.error(msg)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    ac = st.session_state.get('active_chat')
    ag = st.session_state.get('active_group')
    ach = st.session_state.get('active_channel')
    
    if st.button("← Back to Messages", use_container_width=True, key="back_btn"):
        st.session_state.active_chat = None
        st.session_state.active_group = None
        st.session_state.active_channel = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Direct Message
    if ac:
        msgs = ChatHandler.get_messages(ac)
        
        chat_header = (
            f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;'
            f'border-bottom:1px solid rgba(255,215,0,0.1);">'
            f'{render_avatar(ac, 32)}'
            f'<div class="username-text">@{html.escape(ac)}</div>'
            f'</div>'
        )
        st.markdown(chat_header, unsafe_allow_html=True)
        
        for m in msgs:
            sent = m.get("from") == st.session_state.user
            cls = "sent" if sent else "received"
            align = "flex-end" if sent else "flex-start"
            
            read_status = ""
            if sent:
                read_status = " ✓✓" if m.get("read") else " ✓"
            
            msg_html = (
                f'<div style="display:flex;flex-direction:column;align-items:{align};padding:0 4px;">'
                f'<div class="chat-bubble {cls}">'
                f'{html.escape(m.get("text", ""))}'
                f'<div style="font-size:0.55rem;opacity:0.7;text-align:right;">'
                f'{format_timestamp(m["timestamp"])}{read_status}'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(msg_html, unsafe_allow_html=True)
        
        with st.form(f"dmf_{ac}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input(
                    "Message",
                    placeholder="Type a message...",
                    key=f"dmt_{ac}"
                )
            with c2:
                if st.form_submit_button("➤ Send", use_container_width=True):
                    if txt.strip():
                        result, msg = ChatHandler.send(ac, txt)
                        if result:
                            st.rerun()
                        else:
                            st.error(msg)
    
    # Group Chat
    elif ag:
        msgs = GroupHandler.get_group_messages(ag)
        gd = DataManager.get_group_chats().get(ag, {})
        
        group_header = (
            f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;'
            f'border-bottom:1px solid rgba(255,215,0,0.1);">'
            f'<div style="width:32px;height:32px;border-radius:50%;background:#667eea;'
            f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div>'
            f'<div>'
            f'<div class="username-text">{html.escape(gd.get("name", "Group"))}</div>'
            f'<div style="color:#94a3b8;font-size:0.6rem;">{len(gd.get("members", []))} members</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(group_header, unsafe_allow_html=True)
        
        for m in msgs:
            sent = m.get("from") == st.session_state.user
            cls = "sent" if sent else "received"
            align = "flex-end" if sent else "flex-start"
            
            sender_html = ""
            if not sent:
                sender_html = f'<div style="color:#FFD700;font-size:0.6rem;">@{html.escape(m.get("from", ""))}</div>'
            
            msg_html = (
                f'<div style="display:flex;flex-direction:column;align-items:{align};padding:0 4px;">'
                f'<div class="chat-bubble {cls}">'
                f'{sender_html}'
                f'{html.escape(m.get("text", ""))}'
                f'<div style="font-size:0.55rem;opacity:0.7;text-align:right;">'
                f'{format_timestamp(m["timestamp"])}'
                f'</div>'
                f'</div>'
                f'</div>'
            )
            st.markdown(msg_html, unsafe_allow_html=True)
        
        with st.form(f"grpf_{ag}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input(
                    "Message",
                    placeholder="Type a message...",
                    key=f"grpt_{ag}"
                )
            with c2:
                if st.form_submit_button("➤ Send", use_container_width=True):
                    if txt.strip():
                        result, msg = GroupHandler.send_message(ag, txt)
                        if result:
                            st.rerun()
                        else:
                            st.error(msg)
    
    # Channel
    elif ach:
        msgs = GroupHandler.get_channel_messages(ach)
        cd = DataManager.get_channels().get(ach, {})
        is_admin = st.session_state.user in cd.get("admins", [])
        
        channel_header = (
            f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;'
            f'border-bottom:1px solid rgba(255,215,0,0.1);">'
            f'<div style="width:32px;height:32px;border-radius:50%;background:#f093fb;'
            f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div>'
            f'<div>'
            f'<div class="username-text">{html.escape(cd.get("name", "Channel"))}</div>'
            f'<div style="color:#94a3b8;font-size:0.6rem;">{len(cd.get("subscribers", []))} subscribers</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(channel_header, unsafe_allow_html=True)
        
        for m in msgs:
            msg_html = (
                f'<div class="card" style="margin:4px 0;padding:6px 8px;">'
                f'<div style="display:flex;align-items:center;gap:5px;">'
                f'{render_avatar(m.get("from", ""), 24)}'
                f'<div>'
                f'<div class="username-text">@{html.escape(m.get("from", ""))}</div>'
                f'<div class="timestamp">{format_timestamp(m["timestamp"])}</div>'
                f'</div>'
                f'</div>'
                f'<div style="color:#e2e8f0;font-size:0.8rem;margin-top:3px;">{html.escape(m.get("text", ""))}</div>'
                f'</div>'
            )
            st.markdown(msg_html, unsafe_allow_html=True)
        
        if is_admin:
            with st.form(f"chnf_{ach}", clear_on_submit=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    txt = st.text_input(
                        "Broadcast message",
                        placeholder="Post to channel...",
                        key=f"chnt_{ach}"
                    )
                with c2:
                    if st.form_submit_button("📢 Post", use_container_width=True):
                        if txt.strip():
                            result, msg = GroupHandler.send_message(ach, txt, is_channel=True)
                            if result:
                                st.rerun()
                            else:
                                st.error(msg)

def render_create_modal():
    if not st.session_state.get('show_create_modal'):
        return
    
    st.markdown(
        '<div class="modal-overlay"><div class="modal-box">'
        '<h3 style="color:#FFD700;text-align:center;margin-bottom:10px;">✨ Create Post</h3>',
        unsafe_allow_html=True
    )
    
    t1, t2, t3 = st.tabs(["📝 Post", "📊 Poll", "📷 Story"])
    
    with t1:
        with st.form("cpf", clear_on_submit=True):
            text = st.text_area(
                "What's on your mind?",
                max_chars=MAX_POST_LENGTH,
                height=100,
                placeholder="Share your thoughts with the world..."
            )
            media = st.file_uploader("Add image", type=['png','jpg','jpeg','gif','webp'], key="mup")
            location = st.text_input("Location (optional)", placeholder="Add location", key="cpl")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📤 Post", use_container_width=True):
                    media_data = None
                    media_name = None
                    if media and media.size <= MAX_FILE_SIZE:
                        file_bytes = media.read()
                        if validate_image(file_bytes):
                            media_data = base64.b64encode(file_bytes).decode()
                            media_name = media.name
                    
                    if text.strip() or media_data:
                        result, msg = PostHandler.create(text, media_data, media_name, location)
                        if result:
                            st.session_state.show_create_modal = False
                            st.rerun()
                        else:
                            st.error(msg)
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    with t2:
        with st.form("cplf", clear_on_submit=True):
            question = st.text_input("Poll question", max_chars=500, placeholder="What do you want to ask?")
            options_text = st.text_area("Options (one per line)", height=100, placeholder="Option 1\nOption 2\nOption 3")
            duration = st.slider("Duration (hours)", 1, 168, 24)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📊 Create Poll", use_container_width=True):
                    if question and options_text:
                        options = [o.strip() for o in options_text.split('\n') if o.strip()]
                        if len(options) >= 2:
                            result, msg = PostHandler.create_poll(question, options, duration)
                            if result:
                                st.session_state.show_create_modal = False
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Need at least 2 options")
                    else:
                        st.error("Please fill all fields")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    with t3:
        with st.form("csf", clear_on_submit=True):
            story_media = st.file_uploader("Story image", type=['png','jpg','jpeg','gif','webp'], key="sup")
            caption = st.text_input("Caption (optional)", placeholder="Add a caption", key="scap")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📷 Post Story", use_container_width=True):
                    if story_media and story_media.size <= MAX_FILE_SIZE:
                        file_bytes = story_media.read()
                        if validate_image(file_bytes):
                            media_data = base64.b64encode(file_bytes).decode()
                            result, msg = StoryHandler.create(media_data, story_media.name, caption)
                            if result:
                                st.session_state.show_create_modal = False
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.error("Please select a valid image")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    if st.button("✕ Close", use_container_width=True, key="close_modal_btn"):
        st.session_state.show_create_modal = False
        st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_bottom_nav():
    current = st.session_state.get('current_tab', 'feed')
    theme = get_theme()
    
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    
    tabs = [
        ("feed", "🏠", "Feed"),
        ("explore", "🔍", "Explore"),
        ("create", "➕", "Create"),
        ("chats", "💬", "Chats"),
        ("profile", "👤", "Profile"),
    ]
    
    cols = st.columns(5)
    for i, (tab, icon, label) in enumerate(tabs):
        with cols[i]:
            if current == tab:
                st.markdown(
                    f'<div style="text-align:center;padding:2px;">'
                    f'<div style="font-size:1.2rem;color:#FFD700;">{icon}</div>'
                    f'<div style="font-size:0.5rem;color:#FFD700;font-weight:600;">{label}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                if st.button(icon, key=f"nav_{tab}", use_container_width=True, help=label):
                    if tab == "create":
                        st.session_state.show_create_modal = True
                    else:
                        st.session_state.current_tab = tab
                        st.session_state.show_create_modal = False
                        st.session_state.active_chat = None
                        st.session_state.active_group = None
                        st.session_state.active_channel = None
                        st.session_state.show_comments_for = None
                    st.rerun()
                
                st.markdown(
                    f'<div style="text-align:center;font-size:0.48rem;color:{theme["secondary"]};margin-top:-6px;">'
                    f'{label}</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== PAGES ==========
def render_feed_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Stories bar
    render_stories_bar()
    
    # Quick post button
    if st.button("✨ What's on your mind? Tap to post...", use_container_width=True, key="qp_btn"):
        st.session_state.show_create_modal = True
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feed posts
    posts = st.session_state.feed_posts
    
    if not posts:
        emoji_html = get_socialite_emoji_html(100)
        welcome_html = (
            f'<div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">'
            f'<div style="animation:float 3s ease-in-out infinite;">{emoji_html}</div>'
            f'<h3 style="color:#FFD700;margin-top:1rem;">Welcome to Socialite</h3>'
            f'<p style="font-size:0.9rem;">Where Luxury Meets Connection</p>'
            f'<p style="font-size:0.8rem;">Follow users or create your first post to get started!</p>'
            f'</div>'
        )
        st.markdown(welcome_html, unsafe_allow_html=True)
    else:
        for post in reversed(posts[-50:]):
            if post.get("type") == "poll":
                render_poll_card(post)
            else:
                render_post_card(post)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_explore_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">🔍 Explore Users</h3>', unsafe_allow_html=True)
    
    search_query = st.text_input("Search users", placeholder="Search by username...", key="explore_search")
    
    all_users = list(DataManager.get_users().keys())
    
    if search_query:
        filtered = [u for u in all_users if u != st.session_state.user and search_query.lower() in u.lower()]
    else:
        filtered = [u for u in all_users if u != st.session_state.user]
    
    if not filtered:
        st.info("No users found matching your search.")
    else:
        for u in filtered[:50]:
            profile = DataManager.get_profile(u)
            is_following = FollowHandler.is_following(u)
            
            c1, c2, c3 = st.columns([4, 1, 1])
            
            with c1:
                bio_preview = (profile.get("bio", "") or "No bio")[:60]
                user_info = (
                    f'<div style="display:flex;align-items:center;gap:6px;padding:4px 0;">'
                    f'{render_avatar(u, 34)}'
                    f'<div>'
                    f'<div class="username-text">@{html.escape(u)}</div>'
                    f'<div style="color:#94a3b8;font-size:0.65rem;">'
                    f'{len(profile.get("followers", []))} followers · {html.escape(bio_preview)}'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(user_info, unsafe_allow_html=True)
            
            with c2:
                btn_label = "✓ Following" if is_following else "+ Follow"
                if st.button(btn_label, key=f"explore_follow_{u}", use_container_width=True):
                    result, msg = FollowHandler.follow(u)
                    if result:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.toast(msg, icon="❌")
            
            with c3:
                if st.button("💬 Chat", key=f"explore_msg_{u}", use_container_width=True):
                    st.session_state.active_chat = u
                    st.session_state.current_tab = "chats"
                    st.rerun()
            
            st.markdown("<hr style='border-color:rgba(255,215,0,0.04);margin:0;'>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chats_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # If in an active conversation, show chat interface
    if st.session_state.get('active_chat') or st.session_state.get('active_group') or st.session_state.get('active_channel'):
        render_chat_interface()
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">💬 Messages</h3>', unsafe_allow_html=True)
    
    # Quick action buttons
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💬 New Chat", use_container_width=True, key="chat_new_chat"):
            st.session_state.show_new_chat = True
    with c2:
        if st.button("👥 New Group", use_container_width=True, key="chat_new_group"):
            st.session_state.show_new_group = True
    with c3:
        if st.button("📢 New Channel", use_container_width=True, key="chat_new_channel"):
            st.session_state.show_new_channel = True
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different chat types
    t1, t2, t3 = st.tabs(["📱 Direct Messages", "👥 Groups", "📢 Channels"])
    
    # Direct Messages tab
    with t1:
        chats = ChatHandler.get_chat_list()
        
        if chats:
            for chat in chats:
                online_dot = '<span class="online-dot"></span>' if chat['is_online'] else ''
                unread_badge = f'<span class="unread-count">{chat["unread"]}</span>' if chat['unread'] > 0 else ''
                
                chat_row = (
                    f'<div class="user-row" style="justify-content:space-between;">'
                    f'<div style="display:flex;align-items:center;gap:6px;flex:1;">'
                    f'{render_avatar(chat["with_user"], 36)}'
                    f'<div style="flex:1;min-width:0;">'
                    f'<div style="display:flex;align-items:center;gap:3px;">'
                    f'<span class="username-text">@{html.escape(chat["with_user"])}</span>'
                    f'{online_dot}'
                    f'</div>'
                    f'<div style="color:#94a3b8;font-size:0.65rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                    f'{html.escape(chat["last_message"])}'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                    f'<div style="text-align:right;flex-shrink:0;">'
                    f'<div class="timestamp">{format_timestamp(chat["last_time"])}</div>'
                    f'{unread_badge}'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(chat_row, unsafe_allow_html=True)
                
                if st.button("Open", key=f"open_chat_{chat['with_user']}"):
                    st.session_state.active_chat = chat['with_user']
                    st.session_state.show_new_chat = False
                    st.rerun()
                
                st.markdown("<hr style='border-color:rgba(255,215,0,0.03);margin:0;'>", unsafe_allow_html=True)
        else:
            st.info("No conversations yet. Start a new chat!")
        
        # New chat expander
        if st.session_state.get('show_new_chat'):
            with st.expander("Start New Chat", expanded=True):
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                if available:
                    selected_user = st.selectbox("Select user", available, key="new_chat_select")
                    if st.button("Start Chat", use_container_width=True, key="start_new_chat"):
                        st.session_state.active_chat = selected_user
                        st.session_state.show_new_chat = False
                        st.rerun()
                else:
                    st.info("No other users available yet")
    
    # Groups tab
    with t2:
        groups = GroupHandler.get_user_groups()
        
        if groups:
            for group in groups:
                group_row = (
                    f'<div class="user-row">'
                    f'<div style="width:36px;height:36px;border-radius:50%;background:#667eea;'
                    f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div>'
                    f'<div>'
                    f'<div class="username-text">{html.escape(group["name"])}</div>'
                    f'<div style="color:#94a3b8;font-size:0.65rem;">{group["members"]} members</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(group_row, unsafe_allow_html=True)
                
                if st.button("Open", key=f"open_group_{group['id']}"):
                    st.session_state.active_group = group['id']
                    st.session_state.show_new_group = False
                    st.rerun()
        else:
            st.info("No groups yet. Create one!")
        
        # New group expander
        if st.session_state.get('show_new_group'):
            with st.expander("Create New Group", expanded=True):
                group_name = st.text_input("Group name", max_chars=100, key="new_group_name", placeholder="Enter group name")
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                selected_members = st.multiselect("Add members", available, key="new_group_members")
                
                if st.button("Create Group", use_container_width=True, key="create_group_btn") and group_name:
                    result, msg = GroupHandler.create(group_name, selected_members)
                    if result:
                        st.toast(msg, icon="✅")
                        st.session_state.show_new_group = False
                        st.rerun()
                    else:
                        st.error(msg)
    
    # Channels tab
    with t3:
        channels = GroupHandler.get_user_channels()
        
        if channels:
            for channel in channels:
                channel_row = (
                    f'<div class="user-row">'
                    f'<div style="width:36px;height:36px;border-radius:50%;background:#f093fb;'
                    f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div>'
                    f'<div>'
                    f'<div class="username-text">{html.escape(channel["name"])}</div>'
                    f'<div style="color:#94a3b8;font-size:0.65rem;">{channel["subscribers"]} subscribers</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(channel_row, unsafe_allow_html=True)
                
                if st.button("Open", key=f"open_channel_{channel['id']}"):
                    st.session_state.active_channel = channel['id']
                    st.session_state.show_new_channel = False
                    st.rerun()
        else:
            st.info("No channels yet. Create one!")
        
        # New channel expander
        if st.session_state.get('show_new_channel'):
            with st.expander("Create New Channel", expanded=True):
                channel_name = st.text_input("Channel name", max_chars=100, key="new_channel_name", placeholder="Enter channel name")
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                selected_subs = st.multiselect("Add subscribers", available, key="new_channel_subs")
                
                if st.button("Create Channel", use_container_width=True, key="create_channel_btn") and channel_name:
                    result, msg = GroupHandler.create(channel_name, selected_subs or [], is_channel=True)
                    if result:
                        st.toast(msg, icon="✅")
                        st.session_state.show_new_channel = False
                        st.rerun()
                    else:
                        st.error(msg)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_profile_page():
    user = st.session_state.user
    profile = DataManager.get_profile(user)
    theme = get_theme()
    
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Build badges
    badges = []
    if profile.get("is_verified"):
        badges.append('<span style="color:#FFD700;font-size:1rem;">✓✓</span>')
    if profile.get("is_premium"):
        badges.append('<span style="color:#FFD700;font-size:0.9rem;">👑</span>')
    badge_html = ''.join(badges)
    
    # Build optional fields
    optional_fields = []
    if profile.get("website"):
        optional_fields.append(f'<p style="color:{theme["secondary"]};font-size:0.7rem;">🌐 {html.escape(profile["website"])}</p>')
    if profile.get("location"):
        optional_fields.append(f'<p style="color:{theme["secondary"]};font-size:0.7rem;">📍 {html.escape(profile["location"])}</p>')
    optional_html = ''.join(optional_fields)
    
    # Profile header
    profile_header = (
        f'<div style="text-align:center;padding:12px 0;">'
        f'{render_avatar(user, 72)}'
        f'<h2 style="color:#FFD700;margin-top:6px;">@{html.escape(user)}{badge_html}</h2>'
        f'<p style="color:{theme["secondary"]};font-size:0.8rem;">{html.escape(profile.get("bio", "No bio yet"))}</p>'
        f'{optional_html}'
        f'</div>'
    )
    st.markdown(profile_header, unsafe_allow_html=True)
    
    # Stats
    stats_html = (
        f'<div style="display:flex;justify-content:space-around;text-align:center;padding:10px;'
        f'border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:10px;">'
        f'<div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{profile.get("post_count", 0)}</div>'
        f'<div style="color:{theme["secondary"]};font-size:0.55rem;">Posts</div></div>'
        f'<div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("followers", []))}</div>'
        f'<div style="color:{theme["secondary"]};font-size:0.55rem;">Followers</div></div>'
        f'<div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("following", []))}</div>'
        f'<div style="color:{theme["secondary"]};font-size:0.55rem;">Following</div></div>'
        f'</div>'
    )
    st.markdown(stats_html, unsafe_allow_html=True)
    
    # Edit Profile
    with st.expander("✏️ Edit Profile", expanded=False):
        with st.form("edit_profile_form"):
            display_name = st.text_input("Display Name", value=profile.get("display_name", user))
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=MAX_BIO_LENGTH, placeholder="Tell people about yourself...")
            website = st.text_input("Website", value=profile.get("website", ""), placeholder="https://...")
            location = st.text_input("Location", value=profile.get("location", ""), placeholder="City, Country")
            
            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("Gender", ["male", "female"], index=0 if profile.get("gender", "male") == "male" else 1)
            with col2:
                is_private = st.checkbox("Private Account", value=profile.get("is_private", False))
            
            avatar_file = st.file_uploader("Profile Picture", type=['png','jpg','jpeg','webp'], key="profile_avatar")
            
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                updates = {
                    "display_name": sanitize_text(display_name, 50),
                    "bio": sanitize_text(bio, MAX_BIO_LENGTH),
                    "website": sanitize_text(website, 200),
                    "location": sanitize_text(location, 100),
                    "gender": gender,
                    "is_private": is_private
                }
                
                if avatar_file and avatar_file.size <= MAX_AVATAR_SIZE:
                    try:
                        img = Image.open(avatar_file)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new('RGB', img.size, (255, 255, 255))
                            bg.paste(img.convert('RGBA'), mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = bg
                        else:
                            img = img.convert("RGB")
                        img.thumbnail((400, 400))
                        avatar_path = UPLOADS_DIR / f"{user}_avatar.jpg"
                        img.save(avatar_path, "JPEG", quality=85)
                        updates["avatar"] = str(avatar_path)
                    except Exception as e:
                        st.error(f"Failed to process avatar: {e}")
                
                DataManager.update_profile(user, updates)
                st.success("Profile updated successfully!")
                st.rerun()
    
    # Theme selection
    with st.expander("🎨 Themes (12)", expanded=False):
        st.markdown('<div class="theme-grid">', unsafe_allow_html=True)
        current_theme = profile.get('theme', 'midnight')
        
        for theme_key, theme_data in THEMES.items():
            selected_class = "selected" if current_theme == theme_key else ""
            
            theme_card = (
                f'<div class="theme-card {selected_class}" style="background:{theme_data["gradient"]};">'
                f'<div style="font-size:1.3rem;">{theme_data["icon"]}</div>'
                f'<div style="color:white;font-size:0.6rem;margin-top:3px;">{theme_data["name"]}</div>'
                f'</div>'
            )
            st.markdown(theme_card, unsafe_allow_html=True)
            
            if st.button("Apply", key=f"theme_{theme_key}"):
                DataManager.update_profile(user, {"theme": theme_key})
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Wallpaper selection
    with st.expander("🖼️ Wallpapers (10)", expanded=False):
        st.markdown('<div class="wallpaper-grid">', unsafe_allow_html=True)
        current_wp = profile.get('wallpaper', 'wp_socialite')
        
        for wp_key, wp_data in WALLPAPERS.items():
            selected_class = "selected" if current_wp == wp_key else ""
            
            if wp_data.get("url"):
                bg_style = f"background-image:url('{wp_data['url']}');"
            else:
                bg_style = f"background:{wp_data.get('gradient', '')};"
            
            wp_card = (
                f'<div class="wallpaper-card {selected_class}" style="{bg_style}" title="{wp_data["name"]}"></div>'
            )
            st.markdown(wp_card, unsafe_allow_html=True)
            
            if st.button("Apply", key=f"wallpaper_{wp_key}"):
                DataManager.update_profile(user, {"wallpaper": wp_key})
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # User's posts
    user_posts = [p for p in st.session_state.feed_posts if p.get("username") == user]
    if user_posts:
        st.markdown(f'<h4 style="color:#FFD700;margin-top:10px;">Your Posts ({len(user_posts)})</h4>', unsafe_allow_html=True)
        for post in reversed(user_posts[-30:]):
            if post.get("type") == "poll":
                render_poll_card(post)
            else:
                render_post_card(post)
    
    # Sign out
    if st.button("🚪 Sign Out", use_container_width=True, key="sign_out_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTHENTICATION SCREEN ==========
def render_auth_screen():
    """Render the login/registration screen"""
    st.markdown("""
    <style>
    html, body {
        overflow: auto !important;
        height: auto !important;
        position: relative !important;
    }
    .stApp {
        position: relative !important;
        overflow: auto !important;
    }
    .block-container {
        overflow: auto !important;
        height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        emoji_html = get_socialite_emoji_html(120)
        
        # Brand header
        brand_html = (
            f'<div style="text-align:center;padding:2rem 0;">'
            f'<div style="animation:float 3s ease-in-out infinite;">{emoji_html}</div>'
            f'<h1 style="font-family:Playfair Display,serif;font-size:2.5rem;font-weight:900;'
            f'background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);'
            f'-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'
            f'margin-top:1rem;">Socialite</h1>'
            f'<p style="color:#94a3b8;font-size:1rem;font-family:Playfair Display,serif;">'
            f'Where Luxury Meets Connection</p>'
            f'<p style="color:#64748b;font-size:0.75rem;">'
            f'Feed · Stories · Chat · Groups · Channels</p>'
            f'</div>'
        )
        st.markdown(brand_html, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
        
        # Sign In Tab
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username", key="login_username")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
                
                if st.form_submit_button("🔓 Sign In", use_container_width=True):
                    if not username or not password:
                        st.error("Please fill in all fields")
                    else:
                        success, result = DataManager.authenticate(username, password)
                        if success:
                            st.session_state.auth = True
                            st.session_state.user = result
                            st.session_state.feed_posts = DataManager.get_feed_posts()
                            st.session_state.stories = DataManager.get_stories()
                            st.rerun()
                        else:
                            st.error(result)
        
        # Sign Up Tab
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input(
                    "Choose Username",
                    placeholder=f"3-{MAX_USERNAME_LENGTH} characters, letters/numbers/underscores",
                    key="signup_username"
                )
                new_password = st.text_input(
                    "Choose Password",
                    type="password",
                    placeholder=f"Minimum {MIN_PASSWORD_LENGTH} characters",
                    key="signup_password"
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="signup_confirm"
                )
                
                if st.form_submit_button("✨ Create Account", use_container_width=True):
                    # Validation
                    if not new_username or not new_password:
                        st.error("Please fill in all required fields")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < MIN_PASSWORD_LENGTH:
                        st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                    elif len(new_username) < 3 or len(new_username) > MAX_USERNAME_LENGTH:
                        st.error(f"Username must be 3-{MAX_USERNAME_LENGTH} characters")
                    elif not re.match(r'^[a-zA-Z0-9_]+$', new_username):
                        st.error("Username can only contain letters, numbers, and underscores")
                    else:
                        success, msg = DataManager.create_user(new_username, new_password)
                        if success:
                            st.success(msg)
                            st.info("You can now sign in with your new account!")
                            st.balloons()
                        else:
                            st.error(msg)

# ========== MAIN APPLICATION ==========
def main():
    """Main application entry point"""
    # Initialize session state
    init_session()
    
    # Inject CSS styles
    inject_styles()
    
    # Route based on authentication state
    if not st.session_state.get('auth'):
        render_auth_screen()
        return
    
    # Render header
    render_header()
    
    # Main scrollable content area
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    tab = st.session_state.get('current_tab', 'feed')
    
    if tab == "feed":
        render_feed_page()
    elif tab == "explore":
        render_explore_page()
    elif tab == "chats":
        render_chats_page()
    elif tab == "profile":
        render_profile_page()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Modals
    if st.session_state.get('show_create_modal'):
        render_create_modal()
    
    # Bottom navigation
    render_bottom_nav()

if __name__ == "__main__":
    main()
