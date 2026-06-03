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
from typing import Dict, List, Optional, Any

# Must be first
st.set_page_config(page_title="Chattier Pro", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")

# ========== CONFIG ==========
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Cloud configuration
try:
    JSONBIN_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_ID = st.secrets["jsonbin"]["bin_id"]
    CLOUD = True
except:
    JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
    JSONBIN_ID = os.environ.get("JSONBIN_ID", "")
    CLOUD = bool(JSONBIN_KEY and JSONBIN_ID)

# ========== DATA LAYER (Pure Logic) ==========
class DataManager:
    """Centralized data operations - no UI code"""
    
    @staticmethod
    def load_json(filepath: pathlib.Path, default: Any = None) -> Any:
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return default if default is not None else {}
    
    @staticmethod
    def save_json(filepath: pathlib.Path, data: Any) -> None:
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except:
            pass
    
    @staticmethod
    def hash_password(pwd: str) -> str:
        return hashlib.sha256(pwd.encode()).hexdigest()
    
    @staticmethod
    def get_users() -> Dict:
        return DataManager.load_json(USERS_FILE, {})
    
    @staticmethod
    def save_users(users: Dict) -> None:
        DataManager.save_json(USERS_FILE, users)
    
    @staticmethod
    def get_profiles() -> Dict:
        return DataManager.load_json(PROFILES_FILE, {})
    
    @staticmethod
    def save_profiles(profiles: Dict) -> None:
        DataManager.save_json(PROFILES_FILE, profiles)
    
    @staticmethod
    def get_messages() -> List:
        if CLOUD:
            try:
                r = requests.get(
                    f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest",
                    headers={"X-Master-Key": JSONBIN_KEY, "X-Bin-Meta": "false"},
                    timeout=3
                )
                if r.status_code == 200:
                    data = r.json()
                    return data if isinstance(data, list) else data.get("messages", [])
            except:
                pass
        return DataManager.load_json(MESSAGES_FILE, [])
    
    @staticmethod
    def save_messages(messages: List) -> None:
        if len(messages) > 300:
            messages = messages[-300:]
        
        if CLOUD:
            try:
                requests.put(
                    f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}",
                    json={"messages": messages},
                    headers={
                        "Content-Type": "application/json",
                        "X-Master-Key": JSONBIN_KEY
                    },
                    timeout=3
                )
            except:
                pass
        
        DataManager.save_json(MESSAGES_FILE, messages)
    
    @staticmethod
    def get_user_profile(username: str) -> Dict:
        profiles = DataManager.get_profiles()
        if username not in profiles:
            profiles[username] = {
                "bio": "",
                "avatar": None,
                "wallpaper": "default",
                "status": "",
                "last_seen": "",
                "stats": {
                    "posts": 0,
                    "followers": 0,
                    "following": 0
                }
            }
        return profiles[username]
    
    @staticmethod
    def get_active_users() -> List[Dict]:
        """Get users active in last 5 minutes"""
        profiles = DataManager.get_profiles()
        active = []
        now = datetime.now()
        
        for username, profile in profiles.items():
            if profile.get("last_seen"):
                try:
                    last_seen = datetime.fromisoformat(profile["last_seen"])
                    if (now - last_seen).seconds < 300:
                        active.append({
                            "username": username,
                            "avatar": profile.get("avatar"),
                            "is_active": True,
                            "has_story": bool(hash(username) % 3 == 0)
                        })
                except:
                    pass
        
        active.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return active[:10]

class MessageHandler:
    """Pure message operations"""
    
    @staticmethod
    def send_message(text: str, attachment_data: Optional[str] = None, 
                    attachment_name: Optional[str] = None) -> None:
        if not text and not attachment_data:
            return
        
        text = html.escape(str(text).strip())[:1000] if text else ""
        messages = DataManager.get_messages()
        
        msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "reactions": {},
            "type": "text"
        }
        
        if attachment_data:
            msg["attachment"] = attachment_data
            msg["attachment_name"] = attachment_name
            msg["type"] = "image" if attachment_name.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif')
            ) else "file"
        
        messages.append(msg)
        
        # Update user post count
        profile = DataManager.get_user_profile(st.session_state.user)
        profile.setdefault("stats", {})["posts"] = profile.get("stats", {}).get("posts", 0) + 1
        profiles = DataManager.get_profiles()
        profiles[st.session_state.user] = profile
        DataManager.save_profiles(profiles)
        
        DataManager.save_messages(messages)
        st.session_state.messages = messages
    
    @staticmethod
    def add_reaction(msg_id: str, emoji: str) -> None:
        messages = DataManager.get_messages()
        for msg in messages:
            if msg.get("id") == msg_id:
                if "reactions" not in msg:
                    msg["reactions"] = {}
                if emoji not in msg["reactions"]:
                    msg["reactions"][emoji] = []
                
                user = st.session_state.user
                if user in msg["reactions"][emoji]:
                    msg["reactions"][emoji].remove(user)
                else:
                    msg["reactions"][emoji].append(user)
                
                if not msg["reactions"][emoji]:
                    del msg["reactions"][emoji]
                if not msg["reactions"]:
                    del msg["reactions"]
                break
        
        DataManager.save_messages(messages)
        st.session_state.messages = messages
    
    @staticmethod
    def create_poll(question: str, options: List[str]) -> None:
        messages = DataManager.get_messages()
        poll_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.user,
            "text": question,
            "timestamp": datetime.now().isoformat(),
            "type": "poll",
            "poll_data": {
                "options": {opt: [] for opt in options},
                "total_votes": 0
            }
        }
        messages.append(poll_msg)
        DataManager.save_messages(messages)
        st.session_state.messages = messages
    
    @staticmethod
    def vote_poll(msg_id: str, option: str) -> None:
        messages = DataManager.get_messages()
        user = st.session_state.user
        
        for msg in messages:
            if msg.get("id") == msg_id and msg.get("type") == "poll":
                poll_data = msg["poll_data"]
                for opt, voters in poll_data["options"].items():
                    if user in voters:
                        voters.remove(user)
                        poll_data["total_votes"] -= 1
                
                if option in poll_data["options"]:
                    poll_data["options"][option].append(user)
                    poll_data["total_votes"] += 1
                break
        
        DataManager.save_messages(messages)
        st.session_state.messages = messages
    
    @staticmethod
    def get_all_users() -> List[str]:
        messages = DataManager.get_messages()
        return list(set(m["username"] for m in messages))


# ========== SESSION STATE INITIALIZATION ==========
def init_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        'messages': DataManager.get_messages(),
        'auth': False,
        'user': "",
        'current_view': "feed",
        'edit_id': None,
        'reply_to': None,
        'show_create_modal': False,
        'init': True
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize session state
init_session_state()

# Update messages and last seen for authenticated users
if st.session_state.get('auth') and st.session_state.get('user'):
    st.session_state.messages = DataManager.get_messages()
    profiles = DataManager.get_profiles()
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        DataManager.save_profiles(profiles)

# ========== THEME ENGINE ==========
class ThemeEngine:
    """Centralized CSS generation"""
    
    @staticmethod
    def inject_global_styles():
        st.markdown("""
        <style>
        /* === GLOBAL RESET & FONTS === */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {
            font-family: 'Inter', sans-serif;
        }
        
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Hide sidebar completely */
        section[data-testid="stSidebar"] {
            display: none;
        }
        
        /* === PREVENT BODY SCROLL === */
        html, body {
            overflow: hidden !important;
            height: 100vh !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .stApp {
            background: #0b0813;
            height: 100vh !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* === MAIN CONTENT CONTAINER === */
        .main > div {
            height: 100vh !important;
            overflow: hidden !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        section.main {
            height: 100vh !important;
            overflow: hidden !important;
        }
        
        .block-container {
            height: 100vh !important;
            overflow: hidden !important;
            padding: 0 !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        /* === GLASSMORPHISM BASE === */
        .glass-card {
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.2);
        }
        
        /* === GRADIENT ACCENTS === */
        .gradient-accent {
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        /* === SCROLLBARS === */
        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        
        ::-webkit-scrollbar-track {
            background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
        }
        
        /* === ANIMATIONS === */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes glowBorder {
            0%, 100% { border-color: #667eea; }
            50% { border-color: #f093fb; }
        }
        
        @keyframes slideUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .animate-fade-in {
            animation: fadeInUp 0.4s ease;
        }
        
        .animate-glow {
            animation: glowBorder 2s ease-in-out infinite;
        }
        
        /* === FIXED TOP HEADER === */
        .top-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 56px;
            background: rgba(15, 10, 25, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding: 0 1rem;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header-title {
            color: #f1f5f9;
            font-size: 1.2rem;
            font-weight: 700;
        }
        
        /* === FIXED BOTTOM NAVIGATION === */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 70px;
            background: rgba(15, 10, 25, 0.95);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-around;
            z-index: 100;
            padding: 0 0.5rem;
        }
        
        /* === SCROLLABLE CONTENT AREA === */
        .scrollable-content {
            position: fixed;
            top: 56px;
            bottom: 70px;
            left: 0;
            right: 0;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 0.5rem 1rem;
        }
        
        .content-inner {
            max-width: 800px;
            margin: 0 auto;
            padding-bottom: 1rem;
        }
        
        /* === STORIES COMPONENT === */
        .stories-container {
            display: flex;
            overflow-x: auto;
            padding: 0.5rem 0;
            gap: 1rem;
            scroll-behavior: smooth;
            margin-bottom: 0.5rem;
        }
        
        .stories-container::-webkit-scrollbar {
            height: 0;
        }
        
        .story-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.3rem;
            min-width: 70px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .story-item:hover {
            transform: scale(1.05);
        }
        
        .story-avatar {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            padding: 3px;
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        }
        
        .story-avatar.active {
            animation: glowBorder 2s ease-in-out infinite;
        }
        
        .story-avatar-inner {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #0b0813;
        }
        
        .story-username {
            color: #94a3b8;
            font-size: 0.7rem;
            text-align: center;
            max-width: 70px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        /* === FEED CARDS === */
        .feed-card {
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            margin-bottom: 0.8rem;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            padding: 0.7rem 1rem;
            gap: 0.8rem;
        }
        
        .card-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }
        
        .card-avatar-placeholder {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: white;
            font-size: 0.9rem;
            border: 2px solid rgba(102, 126, 234, 0.3);
        }
        
        .card-user-info {
            flex: 1;
        }
        
        .card-username {
            color: #f1f5f9;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        .card-timestamp {
            color: #64748b;
            font-size: 0.65rem;
        }
        
        .card-image {
            width: 100%;
            max-height: 300px;
            object-fit: cover;
            border-radius: 12px;
            margin: 0.3rem 0;
        }
        
        .card-text {
            color: #e2e8f0;
            font-size: 0.85rem;
            line-height: 1.4;
            padding: 0 1rem 0.5rem 1rem;
        }
        
        .card-actions {
            display: flex;
            align-items: center;
            padding: 0.3rem 1rem;
            gap: 0.3rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .action-button {
            color: #94a3b8;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s;
            padding: 0.2rem 0.4rem;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
        }
        
        .action-button:hover {
            color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
        
        /* === POLL COMPONENT === */
        .poll-container {
            padding: 0.5rem 1rem;
        }
        
        .poll-option {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 0.5rem;
            margin: 0.3rem 0;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            overflow: hidden;
        }
        
        .poll-option:hover {
            background: rgba(102, 126, 234, 0.2);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .poll-progress {
            height: 3px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 2px;
            margin-top: 0.2rem;
            overflow: hidden;
        }
        
        .poll-progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 2px;
            transition: width 0.3s ease;
        }
        
        /* === MEDIA CARD === */
        .media-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 0.8rem;
            margin: 0.3rem 1rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
        }
        
        .media-artwork {
            width: 50px;
            height: 50px;
            border-radius: 8px;
            object-fit: cover;
            flex-shrink: 0;
        }
        
        .media-info {
            flex: 1;
        }
        
        .media-title {
            color: #f1f5f9;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        .media-subtitle {
            color: #64748b;
            font-size: 0.75rem;
        }
        
        /* === PROFILE STATS === */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            text-align: center;
        }
        
        .stat-item {
            padding: 0.6rem 0.5rem;
        }
        
        .stat-number {
            color: #f1f5f9;
            font-size: 1.2rem;
            font-weight: 700;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.1rem;
        }
        
        /* === CREATE MODAL === */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(5px);
            display: flex;
            align-items: flex-end;
            justify-content: center;
            z-index: 1001;
        }
        
        .modal-content {
            background: rgba(20, 15, 35, 0.98);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px 24px 0 0;
            width: 100%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            padding: 1.5rem;
            animation: slideUp 0.3s ease;
        }
        
        .modal-handle {
            width: 40px;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 2px;
            margin: 0 auto 1rem auto;
        }
        
        /* === MEMBER LIST === */
        .member-card {
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 0.7rem;
            margin-bottom: 0.4rem;
            display: flex;
            align-items: center;
            gap: 0.7rem;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .member-card:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateX(4px);
        }
        
        .member-avatar {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        
        .member-info {
            flex: 1;
        }
        
        .member-username {
            color: #f1f5f9;
            font-weight: 600;
            font-size: 0.85rem;
        }
        
        .member-status {
            color: #64748b;
            font-size: 0.7rem;
        }
        
        .online-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
            flex-shrink: 0;
        }
        
        .offline-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6b7280;
            flex-shrink: 0;
        }
        
        /* === EMPTY STATE === */
        .empty-state {
            text-align: center;
            padding: 3rem 2rem;
            color: #64748b;
        }
        
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 0.8rem;
        }
        
        /* === THEME GRID === */
        .theme-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.6rem;
            padding: 0.8rem 0;
        }
        
        .theme-card {
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        
        .theme-card:hover {
            transform: scale(1.05);
        }
        
        .theme-card.selected {
            border-color: #667eea;
            box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        
        /* === Streamlit Button Overrides === */
        .stButton > button {
            background: transparent !important;
            border: none !important;
            color: inherit !important;
            padding: 0.3rem 0.5rem !important;
            font-size: 1rem !important;
            min-height: unset !important;
            line-height: 1 !important;
        }
        
        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.1) !important;
            border: none !important;
            color: inherit !important;
        }
        
        .stButton > button:focus {
            box-shadow: none !important;
        }
        
        /* Hide Streamlit elements that break layout */
        .stDeployButton, [data-testid="stDecoration"] {
            display: none !important;
        }
        
        /* Compact form elements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #f1f5f9 !important;
            border-radius: 8px !important;
            padding: 0.5rem 0.8rem !important;
            font-size: 0.85rem !important;
        }
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {
            color: #64748b !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.06) !important;
            border-radius: 12px !important;
            color: #f1f5f9 !important;
        }
        </style>
        """, unsafe_allow_html=True)


# ========== UI COMPONENTS ==========
class UIComponents:
    """Pure UI rendering"""
    
    @staticmethod
    def render_avatar_html(username: str, size: int = 40, has_story: bool = False) -> str:
        """Generate avatar HTML string"""
        profile = DataManager.get_user_profile(username)
        avatar_path = profile.get("avatar")
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                 '#DDA0DD', '#98D8C8', '#F7B787', '#FF8A80', '#B388FF']
        color = colors[hash(username) % len(colors)]
        
        story_class = "active" if has_story else ""
        
        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'''
            <div class="story-avatar {story_class}">
                <img src="data:image/jpeg;base64,{b64}" class="story-avatar-inner" style="width:{size}px;height:{size}px;">
            </div>
            '''
        else:
            initial = username[0].upper() if username else "?"
            return f'''
            <div class="story-avatar {story_class}">
                <div class="card-avatar-placeholder gradient-accent" style="width:{size}px;height:{size}px;font-size:{size*0.45}px;">
                    {initial}
                </div>
            </div>
            '''
    
    @staticmethod
    def render_top_header():
        """Render the fixed top header bar"""
        username = st.session_state.get('user', 'User')
        st.markdown(f"""
        <div class="top-header">
            <div class="header-title">Chattier Pro</div>
            {UIComponents.render_avatar_html(username, 32)}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_stories_row():
        """Render stories component"""
        active_users = DataManager.get_active_users()
        current_user = st.session_state.get('user', '')
        
        if not active_users and not current_user:
            return
        
        stories_html = '<div class="stories-container">'
        
        # Add current user's story
        if current_user:
            stories_html += f"""
            <div class="story-item">
                {UIComponents.render_avatar_html(current_user, 60, False)}
                <div class="story-username">Your Story</div>
            </div>
            """
        
        for user_data in active_users:
            if user_data["username"] != current_user:
                stories_html += f"""
                <div class="story-item">
                    {UIComponents.render_avatar_html(user_data['username'], 60, user_data.get('has_story', False))}
                    <div class="story-username">@{user_data['username'][:12]}</div>
                </div>
                """
        
        stories_html += '</div>'
        st.markdown(stories_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_feed_card(msg: Dict):
        """Render a standard feed card"""
        username = msg.get("username", "unknown")
        msg_id = msg.get("id", str(uuid.uuid4()))
        
        card_html = f"""
        <div class="feed-card animate-fade-in">
            <div class="card-header">
                {UIComponents.render_avatar_html(username, 36)}
                <div class="card-user-info">
                    <div class="card-username">@{html.escape(username)}</div>
                    <div class="card-timestamp">{UIComponents.format_timestamp(msg.get('timestamp', ''))}</div>
                </div>
            </div>
        """
        
        if msg.get("text"):
            edited_badge = ' <span style="color:#64748b;font-size:0.65rem;">(edited)</span>' if msg.get("edited") else ""
            card_html += f'<div class="card-text">{html.escape(msg["text"])}{edited_badge}</div>'
        
        if msg.get("attachment") and msg.get("type") == "image":
            card_html += f'<img src="{msg["attachment"]}" class="card-image">'
        
        if msg.get("attachment") and msg.get("type") == "file":
            card_html += f"""
            <div class="media-card">
                <div style="font-size:1.5rem;">📎</div>
                <div class="media-info">
                    <div class="media-title">{html.escape(msg.get('attachment_name', 'File'))}</div>
                    <div class="media-subtitle">Shared file</div>
                </div>
            </div>
            """
        
        card_html += '<div class="card-actions">'
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Action buttons using Streamlit columns
        action_cols = st.columns([1, 1, 1, 2, 5])
        
        with action_cols[0]:
            if st.button("❤️", key=f"like_{msg_id}"):
                MessageHandler.add_reaction(msg_id, "❤️")
                st.rerun()
        
        with action_cols[1]:
            if st.button("💬", key=f"comment_{msg_id}"):
                st.session_state.reply_to = msg_id
                st.rerun()
        
        with action_cols[2]:
            if st.button("🔖", key=f"bookmark_{msg_id}"):
                MessageHandler.add_reaction(msg_id, "🔖")
                st.rerun()
        
        # Show reactions
        if msg.get("reactions"):
            reaction_html = ""
            for emoji, users in msg["reactions"].items():
                count = len(users)
                reaction_html += f'<span class="action-button">{emoji} {count}</span>'
            with action_cols[3]:
                st.markdown(reaction_html, unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_poll_card(msg: Dict):
        """Render poll card"""
        username = msg.get("username", "unknown")
        msg_id = msg.get("id", str(uuid.uuid4()))
        poll_data = msg.get("poll_data", {})
        total_votes = poll_data.get("total_votes", 0)
        options = poll_data.get("options", {})
        
        card_html = f"""
        <div class="feed-card animate-fade-in">
            <div class="card-header">
                {UIComponents.render_avatar_html(username, 36)}
                <div class="card-user-info">
                    <div class="card-username">@{html.escape(username)}</div>
                    <div class="card-timestamp">Poll • {UIComponents.format_timestamp(msg.get('timestamp', ''))}</div>
                </div>
            </div>
            <div class="card-text" style="font-weight:600;">{html.escape(msg.get('text', ''))}</div>
            <div class="poll-container">
        """
        
        for option_name, voters in options.items():
            percentage = (len(voters) / total_votes * 100) if total_votes > 0 else 0
            safe_option = html.escape(option_name)
            
            card_html += f"""
            <div class="poll-option">
                <div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.85rem;">
                    <span>{safe_option}</span>
                    <span>{percentage:.0f}%</span>
                </div>
                <div class="poll-progress">
                    <div class="poll-progress-fill" style="width:{percentage}%"></div>
                </div>
            </div>
            """
        
        card_html += f"""
                <div style="color:#64748b;font-size:0.65rem;margin-top:0.4rem;">
                    {total_votes} total votes
                </div>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # Vote buttons
        for option_name in options.keys():
            safe_option = html.escape(option_name)
            if st.button(f"Vote {safe_option[:15]}", key=f"vote_{msg_id}_{option_name[:20]}"):
                MessageHandler.vote_poll(msg_id, option_name)
                st.rerun()
    
    @staticmethod
    def render_profile_view():
        """Render profile page"""
        current_user = st.session_state.get('user', '')
        if not current_user:
            return
            
        profile = DataManager.get_user_profile(current_user)
        stats = profile.get("stats", {})
        
        st.markdown('<div class="content-inner">', unsafe_allow_html=True)
        
        # Profile header
        st.markdown(f"""
        <div class="glass-card" style="padding:1.5rem;text-align:center;margin-bottom:0.8rem;">
            {UIComponents.render_avatar_html(current_user, 70)}
            <h2 style="color:#f1f5f9;margin-top:0.8rem;font-size:1.2rem;">@{current_user}</h2>
            <p style="color:#94a3b8;font-size:0.85rem;">{html.escape(profile.get('status', 'No status set'))}</p>
            <p style="color:#64748b;margin-top:0.8rem;font-size:0.8rem;">{html.escape(profile.get('bio', 'No bio yet'))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats grid
        st.markdown(f"""
        <div class="glass-card" style="padding:1rem;margin-bottom:0.8rem;">
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-number">{stats.get('posts', 0)}</div>
                    <div class="stat-label">Posts</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{stats.get('followers', 0)}</div>
                    <div class="stat-label">Followers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">{stats.get('following', 0)}</div>
                    <div class="stat-label">Following</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Edit profile form
        with st.expander("✏️ Edit Profile", expanded=False):
            with st.form("profile_edit_form"):
                bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200)
                status = st.text_input("Status", value=profile.get("status", ""), max_chars=60)
                avatar_file = st.file_uploader("Avatar", type=['png', 'jpg', 'jpeg'])
                
                if st.form_submit_button("Save Profile", use_container_width=True):
                    profiles = DataManager.get_profiles()
                    if current_user in profiles:
                        profiles[current_user]["bio"] = html.escape(bio) if bio else ""
                        profiles[current_user]["status"] = html.escape(status) if status else ""
                        
                        if avatar_file:
                            try:
                                img = Image.open(avatar_file)
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    bg = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                    img = bg
                                else:
                                    img = img.convert("RGB")
                                
                                img.thumbnail((200, 200))
                                avatar_path = UPLOADS_DIR / f"{current_user}_avatar.jpg"
                                img.save(avatar_path, "JPEG", quality=75)
                                profiles[current_user]["avatar"] = str(avatar_path)
                            except Exception as e:
                                st.error(f"Failed to process avatar: {e}")
                        
                        DataManager.save_profiles(profiles)
                        st.success("Profile updated!")
                        time.sleep(0.5)
                        st.rerun()
        
        # Sign out button
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = ""
            st.session_state.current_view = "feed"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_members_view():
        """Render members/directory page"""
        all_users = MessageHandler.get_all_users()
        
        st.markdown('<div class="content-inner">', unsafe_allow_html=True)
        
        # Search bar
        search_query = st.text_input("Search members", label_visibility="collapsed", 
                                    placeholder="🔍 Search members...")
        
        filtered_users = [u for u in all_users 
                        if search_query.lower() in u.lower()] if search_query else all_users
        
        if filtered_users:
            for username in filtered_users[:20]:
                profile = DataManager.get_user_profile(username)
                is_online = False
                if profile.get("last_seen"):
                    try:
                        last_seen = datetime.fromisoformat(profile["last_seen"])
                        is_online = (datetime.now() - last_seen).seconds < 300
                    except:
                        pass
                
                dot_class = "online-dot" if is_online else "offline-dot"
                status_text = "Online" if is_online else html.escape(profile.get("status", "Offline"))
                
                st.markdown(f"""
                <div class="member-card">
                    {UIComponents.render_avatar_html(username, 44)}
                    <div class="member-info">
                        <div class="member-username">@{html.escape(username)}</div>
                        <div class="member-status">{status_text[:50]}</div>
                    </div>
                    <div class="{dot_class}"></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">👥</div>
                <p>No members found</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_themes_view():
        """Render themes selection page"""
        themes = [
            {"name": "Midnight", "colors": ["#0b0813", "#1a1030", "#2d1b4e"], "icon": "🌙"},
            {"name": "Ocean", "colors": ["#0a192f", "#112240", "#233554"], "icon": "🌊"},
            {"name": "Sunset", "colors": ["#1a0a2e", "#2d1b4e", "#4a1942"], "icon": "🌅"},
            {"name": "Forest", "colors": ["#0a1a0a", "#1a2f1a", "#2d4e2d"], "icon": "🌲"},
            {"name": "Neon", "colors": ["#0a0a2e", "#1a1a4e", "#2d2d7a"], "icon": "💜"},
            {"name": "Ruby", "colors": ["#1a0a0a", "#2e1a1a", "#4e2d2d"], "icon": "❤️"},
        ]
        
        st.markdown('<div class="content-inner">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#f1f5f9;font-size:1.1rem;">Choose Theme</h3>', unsafe_allow_html=True)
        
        st.markdown('<div class="theme-grid">', unsafe_allow_html=True)
        
        for i, theme in enumerate(themes):
            gradient = f"linear-gradient(135deg, {theme['colors'][0]}, {theme['colors'][1]}, {theme['colors'][2]})"
            
            st.markdown(f"""
            <div class="theme-card" style="background:{gradient};">
                <div style="font-size:1.8rem;">{theme['icon']}</div>
                <div style="color:white;font-size:0.75rem;margin-top:0.4rem;">{theme['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Apply", key=f"theme_{i}"):
                st.success(f"{theme['name']} theme applied!")
                st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_create_modal():
        """Render create post modal"""
        st.markdown("""
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-handle"></div>
                <h3 style="color:#f1f5f9;text-align:center;font-size:1.1rem;">Create Post</h3>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Text Post", "Poll"])
        
        with tab1:
            with st.form("create_text_post", clear_on_submit=True):
                text = st.text_area("What's on your mind?", max_chars=1000, height=80)
                attachment = st.file_uploader("Add image", type=['png', 'jpg', 'jpeg', 'gif'])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Post", use_container_width=True):
                        att_data = None
                        att_name = None
                        if attachment:
                            try:
                                att_data = base64.b64encode(attachment.read()).decode()
                                att_name = attachment.name
                            except:
                                st.error("Failed to process attachment")
                        
                        if text.strip() or att_data:
                            MessageHandler.send_message(text, att_data, att_name)
                            st.session_state.show_create_modal = False
                            st.rerun()
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        with tab2:
            with st.form("create_poll", clear_on_submit=True):
                question = st.text_input("Poll question", max_chars=200)
                options_text = st.text_area("Options (one per line)", height=80,
                                           placeholder="Option 1\nOption 2\nOption 3")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Create Poll", use_container_width=True):
                        if question and options_text:
                            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                            if len(options) >= 2:
                                MessageHandler.create_poll(question, options)
                                st.session_state.show_create_modal = False
                                st.rerun()
                            else:
                                st.error("Add at least 2 options")
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_bottom_navigation():
        """Render the fixed bottom navigation bar"""
        current = st.session_state.get('current_view', 'feed')
        
        st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
        
        nav_cols = st.columns([1, 1, 1.2, 1, 1])
        
        with nav_cols[0]:
            if st.button("🏠", key="nav_feed", use_container_width=True, help="Feed"):
                st.session_state.current_view = "feed"
                st.session_state.show_create_modal = False
                st.rerun()
            if current == "feed":
                st.markdown('<div style="text-align:center;color:#667eea;font-size:0.55rem;margin-top:-8px;">Feed</div>', 
                          unsafe_allow_html=True)
        
        with nav_cols[1]:
            if st.button("👥", key="nav_members", use_container_width=True, help="Members"):
                st.session_state.current_view = "members"
                st.session_state.show_create_modal = False
                st.rerun()
            if current == "members":
                st.markdown('<div style="text-align:center;color:#667eea;font-size:0.55rem;margin-top:-8px;">Members</div>', 
                          unsafe_allow_html=True)
        
        with nav_cols[2]:
            if st.button("➕", key="nav_create", use_container_width=True, help="Create"):
                st.session_state.show_create_modal = not st.session_state.get('show_create_modal', False)
                st.rerun()
            st.markdown('<div style="text-align:center;color:#f093fb;font-size:0.55rem;margin-top:-8px;">Create</div>', 
                      unsafe_allow_html=True)
        
        with nav_cols[3]:
            if st.button("🎨", key="nav_themes", use_container_width=True, help="Themes"):
                st.session_state.current_view = "themes"
                st.session_state.show_create_modal = False
                st.rerun()
            if current == "themes":
                st.markdown('<div style="text-align:center;color:#667eea;font-size:0.55rem;margin-top:-8px;">Themes</div>', 
                          unsafe_allow_html=True)
        
        with nav_cols[4]:
            if st.button("👤", key="nav_profile", use_container_width=True, help="Profile"):
                st.session_state.current_view = "profile"
                st.session_state.show_create_modal = False
                st.rerun()
            if current == "profile":
                st.markdown('<div style="text-align:center;color:#667eea;font-size:0.55rem;margin-top:-8px;">Profile</div>', 
                          unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def format_timestamp(ts: str) -> str:
        """Format timestamp for display"""
        if not ts:
            return ""
        try:
            t = datetime.fromisoformat(ts)
            diff = (datetime.now() - t).total_seconds()
            if diff < 60:
                return "now"
            elif diff < 3600:
                return f"{int(diff // 60)}m"
            elif diff < 86400:
                return f"{int(diff // 3600)}h"
            return t.strftime("%b %d")
        except:
            return ""


# ========== AUTHENTICATION ==========
class AuthHandler:
    """Authentication logic"""
    
    @staticmethod
    def sign_up(username: str, password: str, confirm: str) -> tuple:
        if not username or not password:
            return False, "Fill all fields"
        if password != confirm:
            return False, "Passwords don't match"
        if len(password) < 4:
            return False, "Password too short"
        if len(username) < 2 or len(username) > 20:
            return False, "Username 2-20 chars"
        if not username.isalnum():
            return False, "Only letters/numbers"
        
        users = DataManager.get_users()
        if username.lower() in [u.lower() for u in users]:
            return False, "Username exists"
        
        users[username] = DataManager.hash_password(password)
        DataManager.save_users(users)
        
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager.get_user_profile(username)
        DataManager.save_profiles(profiles)
        
        return True, "Account created!"
    
    @staticmethod
    def sign_in(username: str, password: str) -> tuple:
        users = DataManager.get_users()
        for un, pw in users.items():
            if un.lower() == username.lower():
                if pw == DataManager.hash_password(password):
                    return True, un
                return False, "Wrong password"
        return False, "User not found"


# ========== MAIN APP ==========
def main():
    # Ensure session state is initialized
    init_session_state()
    
    # Inject global styles
    ThemeEngine.inject_global_styles()
    
    # Route to appropriate view
    if not st.session_state.get('auth', False):
        render_auth_screen()
    else:
        render_app_shell()

def render_auth_screen():
    """Render authentication screen"""
    # For auth screen, allow normal scrolling
    st.markdown("""
    <style>
    html, body {
        overflow: auto !important;
        height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    
    with center:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;">
            <div style="font-size:5rem;">💬</div>
            <h1 class="gradient-text" style="font-size:2.5rem;">Chattier Pro</h1>
            <p style="color:#64748b;">Premium Social Experience</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    success, result = AuthHandler.sign_in(username, password)
                    if success:
                        st.session_state.auth = True
                        st.session_state.user = result
                        st.session_state.current_view = "feed"
                        st.rerun()
                    else:
                        st.error(result)
        
        with tab2:
            with st.form("signup_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                confirm = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    success, message = AuthHandler.sign_up(username, password, confirm)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

def render_app_shell():
    """Main app shell with fixed layout - no page scrolling"""
    
    # Fixed top header
    UIComponents.render_top_header()
    
    # Scrollable content area (only this section scrolls)
    st.markdown('<div class="scrollable-content">', unsafe_allow_html=True)
    
    current_view = st.session_state.get('current_view', 'feed')
    
    if current_view == "feed":
        # Stories
        UIComponents.render_stories_row()
        
        # Messages feed
        messages = st.session_state.get('messages', [])
        if messages:
            display_messages = messages[-30:]
        else:
            display_messages = []
        
        if not display_messages:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">✨</div>
                <p style="color:#94a3b8;">No messages yet</p>
                <p style="color:#64748b;font-size:0.8rem;">Be the first to post!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in reversed(display_messages):
                msg_type = msg.get("type", "text")
                
                if msg_type in ["text", "image", "file"]:
                    UIComponents.render_feed_card(msg)
                elif msg_type == "poll":
                    UIComponents.render_poll_card(msg)
                elif msg_type == "media":
                    UIComponents.render_feed_card(msg)
    
    elif current_view == "profile":
        UIComponents.render_profile_view()
    
    elif current_view == "members":
        UIComponents.render_members_view()
    
    elif current_view == "themes":
        UIComponents.render_themes_view()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create modal overlay
    if st.session_state.get('show_create_modal', False):
        UIComponents.render_create_modal()
    
    # Fixed bottom navigation
    UIComponents.render_bottom_navigation()


if __name__ == "__main__":
    main()
