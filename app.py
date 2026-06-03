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
st.set_page_config(page_title="Chattier Pro", page_icon="💬", layout="wide", initial_sidebar_state="expanded")

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
                            "has_story": bool(hash(username) % 3 == 0)  # Simulate stories
                        })
                except:
                    pass
        
        # Sort by most recently active
        active.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return active[:10]  # Limit to 10 stories

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
                # Remove previous vote
                for opt, voters in poll_data["options"].items():
                    if user in voters:
                        voters.remove(user)
                        poll_data["total_votes"] -= 1
                
                # Add new vote
                if option in poll_data["options"]:
                    poll_data["options"][option].append(user)
                    poll_data["total_votes"] += 1
                break
        
        DataManager.save_messages(messages)
        st.session_state.messages = messages


# ========== SESSION INIT ==========
if 'init' not in st.session_state:
    st.session_state.messages = DataManager.get_messages()
    st.session_state.auth = False
    st.session_state.user = ""
    st.session_state.view = "feed"
    st.session_state.edit_id = None
    st.session_state.reply_to = None
    st.session_state.selected_tab = "feed"
    st.session_state.init = True

if st.session_state.get('auth'):
    st.session_state.messages = DataManager.get_messages()
    # Update last seen
    profiles = DataManager.get_profiles()
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        DataManager.save_profiles(profiles)

# ========== THEME ENGINE (Pure CSS) ==========
class ThemeEngine:
    """Centralized CSS generation - no Python logic mixed"""
    
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
        
        /* === DARK LUXURIOUS BACKDROP === */
        .stApp {
            background: #0b0813;
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
            transform: translateY(-1px);
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
            width: 6px;
            height: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 3px;
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
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes glowBorder {
            0%, 100% { border-color: #667eea; }
            50% { border-color: #f093fb; }
        }
        
        .animate-fade-in {
            animation: fadeInUp 0.4s ease;
        }
        
        .animate-pulse {
            animation: pulse 2s ease-in-out infinite;
        }
        
        .animate-glow {
            animation: glowBorder 2s ease-in-out infinite;
        }
        
        /* === STORIES COMPONENT === */
        .stories-container {
            display: flex;
            overflow-x: auto;
            padding: 1rem 0.5rem;
            gap: 1rem;
            scroll-behavior: smooth;
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
            width: 64px;
            height: 64px;
            border-radius: 50%;
            padding: 3px;
            background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        }
        
        .story-avatar.active {
            animation: glowBorder 2s ease-in-out infinite;
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
            margin-bottom: 1rem;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            padding: 0.8rem 1rem;
            gap: 0.8rem;
        }
        
        .card-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            object-fit: cover;
        }
        
        .card-user-info {
            flex: 1;
        }
        
        .card-username {
            color: #f1f5f9;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .card-timestamp {
            color: #64748b;
            font-size: 0.7rem;
        }
        
        .card-image {
            width: 100%;
            max-height: 400px;
            object-fit: cover;
            border-radius: 12px;
            margin: 0.5rem 0;
        }
        
        .card-text {
            color: #e2e8f0;
            font-size: 0.9rem;
            line-height: 1.5;
            padding: 0 1rem 0.5rem 1rem;
        }
        
        .card-actions {
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            gap: 0.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .action-button {
            color: #94a3b8;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
            padding: 0.3rem 0.5rem;
            border-radius: 8px;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }
        
        .action-button:hover {
            color: #667eea;
            background: rgba(102, 126, 234, 0.1);
        }
        
        .action-button.active {
            color: #667eea;
        }
        
        /* === POLL COMPONENT === */
        .poll-container {
            padding: 0.8rem 1rem;
        }
        
        .poll-option {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 0.6rem;
            margin: 0.4rem 0;
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
            height: 4px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 2px;
            margin-top: 0.3rem;
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
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .media-artwork {
            width: 60px;
            height: 60px;
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
            font-size: 0.9rem;
        }
        
        .media-subtitle {
            color: #64748b;
            font-size: 0.8rem;
        }
        
        /* === PROFILE STATS === */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.5rem;
            text-align: center;
        }
        
        .stat-item {
            padding: 0.5rem;
        }
        
        .stat-number {
            color: #f1f5f9;
            font-size: 1.2rem;
            font-weight: 700;
        }
        
        .stat-label {
            color: #64748b;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* === BOTTOM NAVIGATION === */
        .bottom-nav {
            position: sticky;
            bottom: 1rem;
            background: rgba(15, 10, 25, 0.9);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 0.8rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin: 1rem 0;
            z-index: 1000;
        }
        
        .nav-item {
            color: #64748b;
            font-size: 1.5rem;
            cursor: pointer;
            transition: all 0.2s;
            padding: 0.3rem;
        }
        
        .nav-item:hover {
            color: #f1f5f9;
        }
        
        .nav-item.active {
            color: #667eea;
        }
        
        .nav-create-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            width: 48px;
            height: 48px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            color: white;
            cursor: pointer;
            transition: transform 0.2s;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .nav-create-btn:hover {
            transform: scale(1.1);
        }
        </style>
        """, unsafe_allow_html=True)


# ========== UI COMPONENTS (Style-Isolated) ==========
class UIComponents:
    """Pure UI rendering - no data mutations"""
    
    @staticmethod
    def render_avatar(username: str, size: int = 40, has_story: bool = False) -> str:
        """Generate avatar HTML"""
        profile = DataManager.get_user_profile(username)
        avatar_path = profile.get("avatar")
        
        if avatar_path and os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            img_html = f'<img src="data:image/jpeg;base64,{b64}" class="card-avatar" style="width:{size}px;height:{size}px;">'
        else:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', 
                     '#DDA0DD', '#98D8C8', '#F7B787', '#FF8A80', '#B388FF']
            color = colors[hash(username) % len(colors)]
            initial = username[0].upper() if username else "?"
            img_html = f'<div class="card-avatar gradient-accent" style="width:{size}px;height:{size}px;display:flex;align-items:center;justify-content:center;font-weight:700;color:white;font-size:{size*0.4}px;">{initial}</div>'
        
        story_class = "active" if has_story else ""
        return f'<div class="story-avatar {story_class}">{img_html}</div>'
    
    @staticmethod
    def render_stories_row():
        """Render stories component"""
        active_users = DataManager.get_active_users()
        
        if not active_users:
            return
        
        with st.container():
            st.markdown('<div class="stories-container">', unsafe_allow_html=True)
            
            for user_data in active_users:
                username = user_data["username"]
                avatar_html = UIComponents.render_avatar(
                    username, 
                    size=64, 
                    has_story=user_data.get("has_story", False)
                )
                st.markdown(f"""
                <div class="story-item">
                    {avatar_html}
                    <div class="story-username">@{username[:12]}</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_feed_card(msg: Dict):
        """Render a standard feed card"""
        with st.container():
            username = msg["username"]
            profile = DataManager.get_user_profile(username)
            
            # Card HTML structure
            st.markdown(f"""
            <div class="feed-card animate-fade-in">
                <div class="card-header">
                    {UIComponents.render_avatar(username, 40)}
                    <div class="card-user-info">
                        <div class="card-username">@{username}</div>
                        <div class="card-timestamp">{UIComponents.format_timestamp(msg.get('timestamp', ''))}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Message text
            if msg.get("text"):
                st.markdown(f'<div class="card-text">{msg["text"]}</div>', unsafe_allow_html=True)
            
            # Image attachment
            if msg.get("attachment") and msg.get("type") == "image":
                st.markdown(f"""
                <img src="{msg['attachment']}" class="card-image">
                """, unsafe_allow_html=True)
            
            # File attachment
            if msg.get("attachment") and msg.get("type") == "file":
                st.markdown(f"""
                <div class="media-card">
                    <div style="font-size:2rem;">📎</div>
                    <div class="media-info">
                        <div class="media-title">{msg.get('attachment_name', 'File')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Action bar with native buttons
            st.markdown('<div class="card-actions">', unsafe_allow_html=True)
            cols = st.columns([1, 1, 1, 1, 8])
            
            with cols[0]:
                if st.button("❤️", key=f"like_{msg['id']}"):
                    MessageHandler.add_reaction(msg["id"], "❤️")
                    st.rerun()
            
            with cols[1]:
                if st.button("💬", key=f"comment_{msg['id']}"):
                    st.session_state.reply_to = msg["id"]
                    st.rerun()
            
            with cols[2]:
                if st.button("🔖", key=f"bookmark_{msg['id']}"):
                    MessageHandler.add_reaction(msg["id"], "🔖")
                    st.rerun()
            
            # Reactions display
            if msg.get("reactions"):
                reaction_html = ""
                for emoji, users in msg["reactions"].items():
                    count = len(users)
                    reaction_html += f'<span class="action-button">{emoji} {count}</span>'
                
                with cols[3]:
                    st.markdown(reaction_html, unsafe_allow_html=True)
            
            st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_poll_card(msg: Dict):
        """Render poll card"""
        with st.container():
            username = msg["username"]
            poll_data = msg.get("poll_data", {})
            total_votes = poll_data.get("total_votes", 0)
            options = poll_data.get("options", {})
            
            st.markdown(f"""
            <div class="feed-card animate-fade-in">
                <div class="card-header">
                    {UIComponents.render_avatar(username, 40)}
                    <div class="card-user-info">
                        <div class="card-username">@{username}</div>
                        <div class="card-timestamp">Poll • {UIComponents.format_timestamp(msg.get('timestamp', ''))}</div>
                    </div>
                </div>
                <div class="card-text" style="font-weight:600;">{msg.get('text', '')}</div>
                <div class="poll-container">
            """, unsafe_allow_html=True)
            
            # Poll options with native buttons
            for option_name, voters in options.items():
                percentage = (len(voters) / total_votes * 100) if total_votes > 0 else 0
                
                st.markdown(f"""
                <div class="poll-option">
                    <div style="display:flex;justify-content:space-between;color:#e2e8f0;">
                        <span>{option_name}</span>
                        <span>{percentage:.0f}%</span>
                    </div>
                    <div class="poll-progress">
                        <div class="poll-progress-fill" style="width:{percentage}%"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Vote {option_name}", key=f"vote_{msg['id']}_{option_name}"):
                    MessageHandler.vote_poll(msg["id"], option_name)
                    st.rerun()
            
            st.markdown(f"""
                <div style="color:#64748b;font-size:0.7rem;margin-top:0.5rem;">
                    {total_votes} total votes
                </div>
            </div></div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_media_card(msg: Dict):
        """Render media/link card"""
        with st.container():
            username = msg["username"]
            
            st.markdown(f"""
            <div class="feed-card animate-fade-in">
                <div class="card-header">
                    {UIComponents.render_avatar(username, 40)}
                    <div class="card-user-info">
                        <div class="card-username">@{username}</div>
                        <div class="card-timestamp">{UIComponents.format_timestamp(msg.get('timestamp', ''))}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Media preview
            if msg.get("attachment") and msg.get("type") == "image":
                st.markdown(f"""
                <div class="media-card">
                    <img src="{msg['attachment']}" class="media-artwork">
                    <div class="media-info">
                        <div class="media-title">{msg.get('attachment_name', 'Media')}</div>
                        <div class="media-subtitle">Shared image</div>
                    </div>
                    <span style="color:#667eea;font-size:1.5rem;">▶️</span>
                </div>
                """, unsafe_allow_html=True)
            
            if msg.get("text"):
                st.markdown(f'<div class="card-text">{msg["text"]}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_profile_stats(username: str):
        """Render profile statistics grid"""
        profile = DataManager.get_user_profile(username)
        stats = profile.get("stats", {})
        
        with st.container():
            st.markdown(f"""
            <div class="glass-card" style="padding:1.5rem;">
                <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;">
                    {UIComponents.render_avatar(username, 60)}
                    <div>
                        <div style="color:#f1f5f9;font-weight:700;font-size:1.2rem;">@{username}</div>
                        <div style="color:#94a3b8;font-size:0.8rem;">{profile.get('status', 'No status')}</div>
                    </div>
                </div>
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
    
    @staticmethod
    def render_bottom_navigation():
        """Render sticky bottom navigation"""
        with st.container():
            st.markdown("""
            <div class="bottom-nav">
                <span class="nav-item active">🏠</span>
                <span class="nav-item">🔍</span>
                <div class="nav-create-btn">+</div>
                <span class="nav-item">💬</span>
                <span class="nav-item">👤</span>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def format_timestamp(ts: str) -> str:
        """Format timestamp for display"""
        try:
            t = datetime.fromisoformat(ts)
            diff = (datetime.now() - t).seconds
            if diff < 60:
                return "just now"
            elif diff < 3600:
                return f"{diff // 60}m ago"
            elif diff < 86400:
                return f"{diff // 3600}h ago"
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
        
        # Initialize profile
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
    # Inject global styles
    ThemeEngine.inject_global_styles()
    
    # Authentication flow
    if not st.session_state.auth:
        render_auth_screen()
    else:
        render_dashboard()

def render_auth_screen():
    """Render authentication UI"""
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

def render_dashboard():
    """Main dashboard layout"""
    
    # Sidebar - Profile section
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1rem;">
            <div style="font-size:3rem;">💬</div>
            <h3 class="gradient-text">Chattier Pro</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Profile stats
        UIComponents.render_profile_stats(st.session_state.user)
        
        st.divider()
        
        # Navigation buttons
        with st.container():
            if st.button("🏠 Feed", use_container_width=True):
                st.session_state.view = "feed"
                st.rerun()
            
            if st.button("👤 Profile", use_container_width=True):
                st.session_state.view = "profile"
                st.rerun()
            
            if st.button("🎨 Themes", use_container_width=True):
                st.session_state.view = "themes"
                st.rerun()
        
        st.divider()
        
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.auth = False
            st.session_state.user = ""
            st.rerun()
    
    # Main content area
    if st.session_state.view == "feed":
        render_feed_view()
    elif st.session_state.view == "profile":
        render_profile_view()
    elif st.session_state.view == "themes":
        render_themes_view()
    
    # Bottom navigation
    UIComponents.render_bottom_navigation()

def render_feed_view():
    """Render the main feed with stories and cards"""
    
    # Stories row
    UIComponents.render_stories_row()
    
    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)
    
    # Feed cards
    messages = st.session_state.messages[-30:]  # Last 30 messages
    
    for msg in reversed(messages):
        msg_type = msg.get("type", "text")
        
        if msg_type in ["text", "image", "file"]:
            UIComponents.render_feed_card(msg)
        elif msg_type == "poll":
            UIComponents.render_poll_card(msg)
        elif msg_type == "media":
            UIComponents.render_media_card(msg)
    
    # Quick post input
    st.divider()
    with st.container():
        with st.form("quick_post", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            
            with col1:
                text = st.text_input(
                    "What's happening?",
                    placeholder=f"Share something @{st.session_state.user}...",
                    label_visibility="collapsed"
                )
            
            with col2:
                submitted = st.form_submit_button("Post", use_container_width=True)
            
            if submitted and text.strip():
                MessageHandler.send_message(text)
                st.rerun()

def render_profile_view():
    """Render profile editing view"""
    st.markdown('<h3 style="color:#f1f5f9;">Edit Profile</h3>', unsafe_allow_html=True)
    
    with st.container():
        UIComponents.render_profile_stats(st.session_state.user)
    
    with st.form("profile_form"):
        profile = DataManager.get_user_profile(st.session_state.user)
        
        bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200)
        status = st.text_input("Status", value=profile.get("status", ""), max_chars=60)
        avatar = st.file_uploader("Avatar", type=['png', 'jpg', 'jpeg'])
        
        if st.form_submit_button("Save Profile", use_container_width=True):
            # Update profile
            profiles = DataManager.get_profiles()
            if st.session_state.user in profiles:
                profiles[st.session_state.user]["bio"] = html.escape(bio) if bio else ""
                profiles[st.session_state.user]["status"] = html.escape(status) if status else ""
                
                if avatar:
                    try:
                        img = Image.open(avatar)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = bg
                        else:
                            img = img.convert("RGB")
                        
                        img.thumbnail((200, 200))
                        avatar_path = UPLOADS_DIR / f"{st.session_state.user}_avatar.jpg"
                        img.save(avatar_path, "JPEG", quality=75)
                        profiles[st.session_state.user]["avatar"] = str(avatar_path)
                    except:
                        st.error("Failed to process avatar")
                
                DataManager.save_profiles(profiles)
                st.success("Profile updated!")
                time.sleep(0.5)
                st.rerun()

def render_themes_view():
    """Render theme selection"""
    st.markdown('<h3 style="color:#f1f5f9;">Themes</h3>', unsafe_allow_html=True)
    st.info("Theme selection coming soon!")

# ========== APP ENTRY POINT ==========
if __name__ == "__main__":
    main()
    
