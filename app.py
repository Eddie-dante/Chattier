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
import imghdr
from functools import lru_cache
import logging

# Must be first
st.set_page_config(page_title="Chattier Pro", page_icon="💬", layout="wide", initial_sidebar_state="collapsed")

# ========== LOGGING SETUP ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== CONFIG ==========
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
MESSAGES_FILE = DATA_DIR / "messages.json"
USERS_FILE = DATA_DIR / "users.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Cloud configuration
try:
    JSONBIN_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_ID = st.secrets["jsonbin"]["bin_id"]
    CLOUD = True
except:
    JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
    JSONBIN_ID = os.environ.get("JSONBIN_ID", "")
    CLOUD = bool(JSONBIN_KEY and JSONBIN_ID)

# Rate limiting configuration
RATE_LIMITS = {
    "post": 3.0,        # 1 post per 3 seconds
    "reaction": 1.0,    # 1 reaction per second
    "vote": 0.5,        # 2 votes per second
}

# ========== RATE LIMITER ==========
class RateLimiter:
    """Rate limiting for user actions"""
    
    def __init__(self):
        self.last_action = {}
    
    def check_limit(self, user: str, action: str, limit_seconds: Optional[float] = None) -> bool:
        """Check if user can perform action based on rate limit"""
        if limit_seconds is None:
            limit_seconds = RATE_LIMITS.get(action, 2.0)
        
        key = f"{user}_{action}"
        now = time.time()
        
        if key in self.last_action:
            if now - self.last_action[key] < limit_seconds:
                return False
        
        self.last_action[key] = now
        return True
    
    def time_until_next(self, user: str, action: str) -> float:
        """Get seconds until next action is allowed"""
        key = f"{user}_{action}"
        if key not in self.last_action:
            return 0
        
        limit_seconds = RATE_LIMITS.get(action, 2.0)
        elapsed = time.time() - self.last_action[key]
        return max(0, limit_seconds - elapsed)

# ========== DATA LAYER (Pure Logic) ==========
class DataManager:
    """Centralized data operations with error handling and backups"""
    
    _instance = None
    _cache = {}
    _cache_timestamps = {}
    CACHE_TTL = 30  # seconds
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @staticmethod
    def load_json(filepath: pathlib.Path, default: Any = None) -> Any:
        """Load JSON with error handling and backup creation"""
        if default is None:
            default = {}
        
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Loaded {filepath.name}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt JSON in {filepath}: {e}")
            # Try to restore from backup
            backup_path = BACKUP_DIR / f"{filepath.stem}_backup.json"
            if backup_path.exists():
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"Restored from backup: {backup_path.name}")
                    return data
                except:
                    pass
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
        
        return default
    
    @staticmethod
    def save_json(filepath: pathlib.Path, data: Any) -> bool:
        """Save JSON with backup creation and error handling"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup of existing file
            if filepath.exists():
                backup_path = BACKUP_DIR / f"{filepath.stem}_backup.json"
                try:
                    with open(filepath, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            json.dump(json.load(src), dst)
                except:
                    pass
            
            # Write new data
            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.replace(filepath)
            logger.info(f"Saved {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return False
    
    @staticmethod
    def hash_password(pwd: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt using PBKDF2"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            pwd.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return hash_obj.hex(), salt
    
    @staticmethod
    def verify_password(pwd: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        computed_hash, _ = DataManager.hash_password(pwd, salt)
        return computed_hash == stored_hash
    
    @staticmethod
    def get_users() -> Dict:
        """Get users with cache"""
        cache_key = 'users'
        if cache_key in DataManager._cache:
            if time.time() - DataManager._cache_timestamps.get(cache_key, 0) < DataManager.CACHE_TTL:
                return DataManager._cache[cache_key]
        
        users = DataManager.load_json(USERS_FILE, {})
        DataManager._cache[cache_key] = users
        DataManager._cache_timestamps[cache_key] = time.time()
        return users
    
    @staticmethod
    def save_users(users: Dict) -> None:
        """Save users and update cache"""
        DataManager.save_json(USERS_FILE, users)
        DataManager._cache['users'] = users
        DataManager._cache_timestamps['users'] = time.time()
    
    @staticmethod
    def get_profiles() -> Dict:
        """Get profiles with cache"""
        cache_key = 'profiles'
        if cache_key in DataManager._cache:
            if time.time() - DataManager._cache_timestamps.get(cache_key, 0) < DataManager.CACHE_TTL:
                return DataManager._cache[cache_key]
        
        profiles = DataManager.load_json(PROFILES_FILE, {})
        DataManager._cache[cache_key] = profiles
        DataManager._cache_timestamps[cache_key] = time.time()
        return profiles
    
    @staticmethod
    def save_profiles(profiles: Dict) -> None:
        """Save profiles and update cache"""
        DataManager.save_json(PROFILES_FILE, profiles)
        DataManager._cache['profiles'] = profiles
        DataManager._cache_timestamps['profiles'] = time.time()
    
    @staticmethod
    def get_messages(page: int = 1, per_page: int = 50) -> Tuple[List, bool]:
        """Get messages with pagination"""
        cache_key = 'messages'
        if cache_key in DataManager._cache:
            if time.time() - DataManager._cache_timestamps.get(cache_key, 0) < DataManager.CACHE_TTL:
                messages = DataManager._cache[cache_key]
            else:
                messages = None
        else:
            messages = None
        
        if messages is None:
            if CLOUD:
                try:
                    r = requests.get(
                        f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest",
                        headers={"X-Master-Key": JSONBIN_KEY, "X-Bin-Meta": "false"},
                        timeout=5
                    )
                    r.raise_for_status()
                    data = r.json()
                    messages = data if isinstance(data, list) else data.get("messages", [])
                    logger.info("Loaded messages from cloud")
                except requests.RequestException as e:
                    logger.warning(f"Failed to load from cloud: {e}")
                    messages = DataManager.load_json(MESSAGES_FILE, [])
                except Exception as e:
                    logger.error(f"Unexpected error loading from cloud: {e}")
                    messages = DataManager.load_json(MESSAGES_FILE, [])
            else:
                messages = DataManager.load_json(MESSAGES_FILE, [])
            
            # Validate message structure
            messages = [msg for msg in messages if isinstance(msg, dict) and 'id' in msg]
            
            DataManager._cache[cache_key] = messages
            DataManager._cache_timestamps[cache_key] = time.time()
        
        # Paginate
        total = len(messages)
        start = max(0, total - (page * per_page))
        end = total - ((page - 1) * per_page) if page > 1 else total
        has_more = start > 0
        
        return messages[start:end], has_more
    
    @staticmethod
    def save_messages(messages: List) -> None:
        """Save messages with size limit and cloud sync"""
        # Size limit with warning
        if len(messages) > 500:
            archived_count = len(messages) - 300
            messages = messages[-300:]
            logger.warning(f"Archived {archived_count} old messages to maintain limit")
        
        # Validate messages
        messages = [msg for msg in messages if isinstance(msg, dict) and 'id' in msg]
        
        # Update cache
        DataManager._cache['messages'] = messages
        DataManager._cache_timestamps['messages'] = time.time()
        
        # Save locally
        DataManager.save_json(MESSAGES_FILE, messages)
        
        # Sync to cloud
        if CLOUD:
            try:
                response = requests.put(
                    f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}",
                    json={"messages": messages},
                    headers={
                        "Content-Type": "application/json",
                        "X-Master-Key": JSONBIN_KEY
                    },
                    timeout=5
                )
                response.raise_for_status()
                logger.info("Synced messages to cloud")
            except requests.RequestException as e:
                logger.warning(f"Cloud sync failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected cloud sync error: {e}")
    
    @staticmethod
    def get_user_profile(username: str) -> Dict:
        """Get user profile with defaults"""
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
                },
                "created_at": datetime.now().isoformat(),
                "badges": []
            }
        return profiles[username]
    
    @staticmethod
    def get_active_users() -> List[Dict]:
        """Get users active in last 5 minutes with enhanced data"""
        profiles = DataManager.get_profiles()
        active = []
        now = datetime.now()
        
        for username, profile in profiles.items():
            if profile.get("last_seen"):
                try:
                    last_seen = datetime.fromisoformat(profile["last_seen"])
                    diff_seconds = (now - last_seen).total_seconds()
                    
                    if diff_seconds < 300:  # 5 minutes
                        active.append({
                            "username": username,
                            "avatar": profile.get("avatar"),
                            "is_active": diff_seconds < 60,  # Green dot if < 1 min
                            "has_story": bool(hash(username) % 3 == 0),
                            "status": profile.get("status", ""),
                            "last_seen": profile["last_seen"]
                        })
                except (ValueError, TypeError) as e:
                    logger.debug(f"Invalid last_seen for {username}: {e}")
                    pass
        
        active.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return active[:15]

# ========== MESSAGE HANDLER ==========
class MessageHandler:
    """Pure message operations with validation and rate limiting"""
    
    @staticmethod
    def validate_message_text(text: str) -> str:
        """Validate and sanitize message text"""
        if not text:
            return ""
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
        # Escape HTML
        text = html.escape(str(text).strip())
        # Limit length
        return text[:2000]
    
    @staticmethod
    def validate_image_data(data: bytes) -> bool:
        """Validate uploaded file is actually an image"""
        try:
            img_type = imghdr.what(None, data)
            return img_type in ['jpeg', 'png', 'gif', 'webp']
        except Exception:
            return False
    
    @staticmethod
    def send_message(text: str, attachment_data: Optional[str] = None, 
                    attachment_name: Optional[str] = None) -> Tuple[bool, str]:
        """Send a message with validation and rate limiting"""
        # Rate limit check
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(
                st.session_state.user, 
                "post"
            ):
                wait_time = st.session_state.rate_limiter.time_until_next(
                    st.session_state.user, 
                    "post"
                )
                return False, f"Please wait {wait_time:.1f}s before posting again"
        
        if not text and not attachment_data:
            return False, "Message cannot be empty"
        
        # Validate text
        text = MessageHandler.validate_message_text(text) if text else ""
        
        # Validate attachment
        if attachment_data:
            try:
                # Check file size (max 10MB for base64)
                if len(attachment_data) > 10 * 1024 * 1024:
                    return False, "File too large (max 10MB)"
                
                # Validate image if it's an image type
                if attachment_name and attachment_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    try:
                        file_bytes = base64.b64decode(attachment_data)
                        if not MessageHandler.validate_image_data(file_bytes):
                            return False, "Invalid image file"
                    except Exception:
                        return False, "Failed to process image"
            except Exception as e:
                logger.error(f"Attachment validation failed: {e}")
                return False, "Failed to process attachment"
        
        messages, _ = DataManager.get_messages()
        
        msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "reactions": {},
            "type": "text",
            "edited": False,
            "edited_at": None
        }
        
        if attachment_data:
            msg["attachment"] = attachment_data
            msg["attachment_name"] = html.escape(attachment_name) if attachment_name else "file"
            msg["type"] = "image" if attachment_name and attachment_name.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            ) else "file"
        
        messages.append(msg)
        
        # Update user post count
        profile = DataManager.get_user_profile(st.session_state.user)
        profile.setdefault("stats", {})["posts"] = profile.get("stats", {}).get("posts", 0) + 1
        profiles = DataManager.get_profiles()
        profiles[st.session_state.user] = profile
        DataManager.save_profiles(profiles)
        
        # Save messages
        DataManager.save_messages(messages)
        st.session_state.messages = messages
        
        logger.info(f"Message sent by {st.session_state.user}: {msg['id']}")
        return True, "Message sent!"
    
    @staticmethod
    def edit_message(msg_id: str, new_text: str) -> Tuple[bool, str]:
        """Edit an existing message"""
        if not new_text.strip():
            return False, "Message cannot be empty"
        
        new_text = MessageHandler.validate_message_text(new_text)
        messages, _ = DataManager.get_messages()
        
        for msg in messages:
            if msg.get("id") == msg_id and msg.get("username") == st.session_state.user:
                msg["text"] = new_text
                msg["edited"] = True
                msg["edited_at"] = datetime.now().isoformat()
                DataManager.save_messages(messages)
                st.session_state.messages = messages
                return True, "Message updated!"
        
        return False, "Message not found or unauthorized"
    
    @staticmethod
    def delete_message(msg_id: str) -> Tuple[bool, str]:
        """Delete a message"""
        messages, _ = DataManager.get_messages()
        
        for i, msg in enumerate(messages):
            if msg.get("id") == msg_id and msg.get("username") == st.session_state.user:
                messages.pop(i)
                
                # Update user post count
                profile = DataManager.get_user_profile(st.session_state.user)
                profile["stats"]["posts"] = max(0, profile.get("stats", {}).get("posts", 0) - 1)
                profiles = DataManager.get_profiles()
                profiles[st.session_state.user] = profile
                DataManager.save_profiles(profiles)
                
                DataManager.save_messages(messages)
                st.session_state.messages = messages
                return True, "Message deleted!"
        
        return False, "Message not found or unauthorized"
    
    @staticmethod
    def add_reaction(msg_id: str, emoji: str) -> Tuple[bool, str]:
        """Add or remove reaction with rate limiting"""
        # Rate limit check
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(
                st.session_state.user, 
                "reaction"
            ):
                return False, "Too fast"
        
        messages, _ = DataManager.get_messages()
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
                
                # Clean up empty reactions
                if not msg["reactions"][emoji]:
                    del msg["reactions"][emoji]
                if not msg["reactions"]:
                    del msg["reactions"]
                
                DataManager.save_messages(messages)
                st.session_state.messages = messages
                return True, "Reaction updated!"
        
        return False, "Message not found"
    
    @staticmethod
    def create_poll(question: str, options: List[str]) -> Tuple[bool, str]:
        """Create a poll with validation"""
        if not question.strip():
            return False, "Question cannot be empty"
        
        options = [opt.strip() for opt in options if opt.strip()]
        if len(options) < 2:
            return False, "Need at least 2 options"
        if len(options) > 10:
            return False, "Maximum 10 options allowed"
        
        question = html.escape(question[:500])
        options = [html.escape(opt[:100]) for opt in options]
        
        messages, _ = DataManager.get_messages()
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
        
        return True, "Poll created!"
    
    @staticmethod
    def vote_poll(msg_id: str, option: str) -> Tuple[bool, str]:
        """Vote on a poll with rate limiting"""
        # Rate limit check
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(
                st.session_state.user, 
                "vote"
            ):
                return False, "Too fast"
        
        messages, _ = DataManager.get_messages()
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
                
                DataManager.save_messages(messages)
                st.session_state.messages = messages
                return True, "Vote recorded!"
        
        return False, "Poll not found"
    
    @staticmethod
    def get_all_users() -> List[str]:
        """Get all unique users from messages"""
        messages, _ = DataManager.get_messages()
        return sorted(list(set(m["username"] for m in messages if "username" in m)))
    
    @staticmethod
    def search_messages(query: str) -> List[Dict]:
        """Search through messages"""
        if not query:
            return []
        
        query = query.lower()
        messages, _ = DataManager.get_messages()
        results = []
        
        for msg in reversed(messages):
            if query in msg.get("text", "").lower():
                results.append(msg)
                if len(results) >= 20:
                    break
        
        return results

# ========== SESSION STATE INITIALIZATION ==========
def init_session_state():
    """Initialize all session state variables with defaults"""
    defaults = {
        'messages': [],
        'auth': False,
        'user': "",
        'current_view': "feed",
        'edit_id': None,
        'reply_to': None,
        'show_create_modal': False,
        'init': True,
        'rate_limiter': RateLimiter(),
        'page': 1,
        'has_more': False,
        'search_query': "",
        'toast_messages': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Load messages if not loaded
    if not st.session_state.messages:
        messages, has_more = DataManager.get_messages(page=1)
        st.session_state.messages = messages
        st.session_state.has_more = has_more

# Initialize session state
init_session_state()

# Update messages and last seen for authenticated users
if st.session_state.get('auth') and st.session_state.get('user'):
    messages, has_more = DataManager.get_messages()
    st.session_state.messages = messages
    st.session_state.has_more = has_more
    
    profiles = DataManager.get_profiles()
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        DataManager.save_profiles(profiles)

# ========== THEME ENGINE ==========
class ThemeEngine:
    """Centralized CSS generation with responsive design"""
    
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
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .animate-fade-in {
            animation: fadeInUp 0.4s ease;
        }
        
        .animate-glow {
            animation: glowBorder 2s ease-in-out infinite;
        }
        
        .animate-pulse {
            animation: pulse 2s ease-in-out infinite;
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
            word-wrap: break-word;
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
        
        /* === LOADING SPINNER === */
        .loading-spinner {
            display: flex;
            justify-content: center;
            padding: 1rem;
        }
        
        .spinner {
            width: 24px;
            height: 24px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* === TOAST NOTIFICATIONS === */
        .toast-container {
            position: fixed;
            top: 64px;
            right: 1rem;
            z-index: 1002;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .toast {
            background: rgba(20, 15, 35, 0.95);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            color: #f1f5f9;
            font-size: 0.85rem;
            animation: slideIn 0.3s ease;
            max-width: 300px;
        }
        
        .toast.success {
            border-left: 3px solid #10b981;
        }
        
        .toast.error {
            border-left: 3px solid #ef4444;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
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
        
        /* === RESPONSIVE DESIGN === */
        @media (max-width: 768px) {
            .card-text {
                font-size: 0.8rem !important;
            }
            
            .story-avatar {
                width: 50px !important;
                height: 50px !important;
            }
            
            .bottom-nav {
                height: 60px !important;
            }
            
            .scrollable-content {
                top: 56px;
                bottom: 60px;
            }
            
            .modal-content {
                max-height: 70vh;
            }
        }
        
        @media (max-width: 480px) {
            .feed-card {
                border-radius: 12px;
            }
            
            .card-header {
                padding: 0.5rem 0.7rem;
            }
            
            .card-text {
                padding: 0 0.7rem 0.3rem 0.7rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)


# ========== UI COMPONENTS ==========
class UIComponents:
    """Pure UI rendering with accessibility support"""
    
    @staticmethod
    def render_avatar_html(username: str, size: int = 40, has_story: bool = False) -> str:
        """Generate avatar HTML string with fallback"""
        profile = DataManager.get_user_profile(username)
        avatar_path = profile.get("avatar")
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                 '#DDA0DD', '#98D8C8', '#F7B787', '#FF8A80', '#B388FF']
        color = colors[hash(username) % len(colors)]
        
        story_class = "active" if has_story else ""
        
        if avatar_path and os.path.exists(avatar_path):
            try:
                with open(avatar_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                return f'''
                <div class="story-avatar {story_class}" role="img" aria-label="{html.escape(username)}'s avatar">
                    <img src="data:image/jpeg;base64,{b64}" class="story-avatar-inner" 
                         style="width:{size}px;height:{size}px;" alt="{html.escape(username)}'s avatar">
                </div>
                '''
            except Exception:
                pass
        
        initial = username[0].upper() if username else "?"
        return f'''
        <div class="story-avatar {story_class}" role="img" aria-label="{html.escape(username)}'s avatar">
            <div class="card-avatar-placeholder gradient-accent" 
                 style="width:{size}px;height:{size}px;font-size:{size*0.45}px;">
                {html.escape(initial)}
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
        
        stories_html = '<div class="stories-container" role="list" aria-label="Stories">'
        
        # Add current user's story
        if current_user:
            stories_html += f"""
            <div class="story-item" role="listitem">
                {UIComponents.render_avatar_html(current_user, 60, False)}
                <div class="story-username">Your Story</div>
            </div>
            """
        
        for user_data in active_users:
            if user_data["username"] != current_user:
                stories_html += f"""
                <div class="story-item" role="listitem">
                    {UIComponents.render_avatar_html(user_data['username'], 60, user_data.get('has_story', False))}
                    <div class="story-username">@{html.escape(user_data['username'][:12])}</div>
                </div>
                """
        
        stories_html += '</div>'
        st.markdown(stories_html, unsafe_allow_html=True)
    
    @staticmethod
    def render_feed_card(msg: Dict):
        """Render a standard feed card with action buttons"""
        username = msg.get("username", "unknown")
        msg_id = msg.get("id", str(uuid.uuid4()))
        is_owner = (username == st.session_state.get('user', ''))
        
        card_html = f"""
        <div class="feed-card animate-fade-in" role="article" aria-label="Post by {html.escape(username)}">
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
            card_html += f'<img src="{html.escape(msg["attachment"])}" class="card-image" alt="Shared image">'
        
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
        action_cols = st.columns([1, 1, 1, 2, 3, 2])
        
        with action_cols[0]:
            if st.button("❤️", key=f"like_{msg_id}", help="Like this post", 
                        aria_label=f"Like post by {username}"):
                success, message = MessageHandler.add_reaction(msg_id, "❤️")
                if not success and message:
                    st.toast(message, icon="⚠️")
                st.rerun()
        
        with action_cols[1]:
            if st.button("💬", key=f"comment_{msg_id}", help="Comment on this post"):
                st.session_state.reply_to = msg_id
                st.rerun()
        
        with action_cols[2]:
            if st.button("🔖", key=f"bookmark_{msg_id}", help="Bookmark this post"):
                success, message = MessageHandler.add_reaction(msg_id, "🔖")
                if not success and message:
                    st.toast(message, icon="⚠️")
                st.rerun()
        
        # Show reactions
        with action_cols[3]:
            if msg.get("reactions"):
                reaction_html = ""
                for emoji, users in msg["reactions"].items():
                    count = len(users)
                    reaction_html += f'<span class="action-button">{emoji} {count}</span>'
                st.markdown(reaction_html, unsafe_allow_html=True)
        
        # Owner actions
        if is_owner:
            with action_cols[4]:
                if st.button("✏️", key=f"edit_{msg_id}", help="Edit post"):
                    st.session_state.edit_id = msg_id
                    st.rerun()
            
            with action_cols[5]:
                if st.button("🗑️", key=f"delete_{msg_id}", help="Delete post"):
                    if st.session_state.get(f"confirm_delete_{msg_id}", False):
                        success, message = MessageHandler.delete_message(msg_id)
                        if success:
                            st.toast(message, icon="✅")
                        else:
                            st.toast(message, icon="❌")
                        st.session_state[f"confirm_delete_{msg_id}"] = False
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{msg_id}"] = True
                        st.warning("Click again to confirm delete")
                        st.rerun()
        
        # Edit form
        if st.session_state.get('edit_id') == msg_id:
            with st.form(key=f"edit_form_{msg_id}"):
                new_text = st.text_area("Edit your post", value=msg.get("text", ""), max_chars=2000)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update"):
                        success, message = MessageHandler.edit_message(msg_id, new_text)
                        st.session_state.edit_id = None
                        st.toast(message, icon="✅" if success else "❌")
                        st.rerun()
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.edit_id = None
                        st.rerun()
        
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
        <div class="feed-card animate-fade-in" role="article" aria-label="Poll by {html.escape(username)}">
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
        vote_cols = st.columns(min(len(options), 4))
        for i, option_name in enumerate(options.keys()):
            safe_option = html.escape(option_name)
            with vote_cols[i % 4]:
                if st.button(f"Vote {safe_option[:15]}", 
                           key=f"vote_{msg_id}_{i}",
                           help=f"Vote for {safe_option}"):
                    success, message = MessageHandler.vote_poll(msg_id, option_name)
                    st.toast(message, icon="✅" if success else "❌")
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
            <h2 style="color:#f1f5f9;margin-top:0.8rem;font-size:1.2rem;">@{html.escape(current_user)}</h2>
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
                avatar_file = st.file_uploader(
                    "Avatar", 
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    help="Upload a profile picture (max 5MB)"
                )
                
                if st.form_submit_button("Save Profile", use_container_width=True):
                    profiles = DataManager.get_profiles()
                    if current_user in profiles:
                        profiles[current_user]["bio"] = html.escape(bio) if bio else ""
                        profiles[current_user]["status"] = html.escape(status) if status else ""
                        
                        if avatar_file:
                            try:
                                # Check file size
                                if avatar_file.size > 5 * 1024 * 1024:
                                    st.error("File too large (max 5MB)")
                                else:
                                    img = Image.open(avatar_file)
                                    
                                    # Convert RGBA to RGB
                                    if img.mode in ('RGBA', 'LA', 'P'):
                                        bg = Image.new('RGB', img.size, (255, 255, 255))
                                        if img.mode == 'P':
                                            img = img.convert('RGBA')
                                        bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                                        img = bg
                                    else:
                                        img = img.convert("RGB")
                                    
                                    # Resize
                                    img.thumbnail((200, 200))
                                    
                                    # Save
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
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_members_view():
        """Render members/directory page with search"""
        all_users = MessageHandler.get_all_users()
        
        st.markdown('<div class="content-inner">', unsafe_allow_html=True)
        
        # Search bar
        search_query = st.text_input(
            "Search members", 
            label_visibility="collapsed", 
            placeholder="🔍 Search members...",
            key="members_search",
            value=st.session_state.get('search_query', '')
        )
        
        st.session_state.search_query = search_query
        
        filtered_users = [u for u in all_users 
                        if search_query.lower() in u.lower()] if search_query else all_users
        
        if filtered_users:
            for username in filtered_users[:30]:
                profile = DataManager.get_user_profile(username)
                is_online = False
                if profile.get("last_seen"):
                    try:
                        last_seen = datetime.fromisoformat(profile["last_seen"])
                        is_online = (datetime.now() - last_seen).total_seconds() < 60
                    except:
                        pass
                
                dot_class = "online-dot" if is_online else "offline-dot"
                status_text = "Online now" if is_online else html.escape(profile.get("status", "Offline"))
                
                st.markdown(f"""
                <div class="member-card" role="button" tabindex="0">
                    {UIComponents.render_avatar_html(username, 44)}
                    <div class="member-info">
                        <div class="member-username">@{html.escape(username)}</div>
                        <div class="member-status">{status_text[:50]}</div>
                    </div>
                    <div class="{dot_class}" aria-label="{'Online' if is_online else 'Offline'}"></div>
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
            
            if st.button(f"Apply {theme['name']}", key=f"theme_{i}"):
                st.toast(f"{theme['name']} theme applied!", icon="✅")
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
                text = st.text_area(
                    "What's on your mind?", 
                    max_chars=2000, 
                    height=80,
                    placeholder="Share your thoughts..."
                )
                attachment = st.file_uploader(
                    "Add image", 
                    type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                    help="Max 10MB"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Post", use_container_width=True):
                        att_data = None
                        att_name = None
                        
                        if attachment:
                            if attachment.size > 10 * 1024 * 1024:
                                st.error("File too large (max 10MB)")
                            else:
                                try:
                                    file_bytes = attachment.read()
                                    if not MessageHandler.validate_image_data(file_bytes):
                                        st.error("Invalid image file")
                                    else:
                                        att_data = base64.b64encode(file_bytes).decode()
                                        att_name = attachment.name
                                except Exception as e:
                                    st.error(f"Failed to process attachment: {e}")
                        
                        if text.strip() or att_data:
                            success, message = MessageHandler.send_message(text, att_data, att_name)
                            if success:
                                st.toast(message, icon="✅")
                                st.session_state.show_create_modal = False
                                st.rerun()
                            else:
                                st.error(message)
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        with tab2:
            with st.form("create_poll", clear_on_submit=True):
                question = st.text_input(
                    "Poll question", 
                    max_chars=500,
                    placeholder="What do you want to ask?"
                )
                options_text = st.text_area(
                    "Options (one per line)", 
                    height=80,
                    placeholder="Option 1\nOption 2\nOption 3",
                    help="Add 2-10 options, one per line"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Create Poll", use_container_width=True):
                        if question and options_text:
                            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                            if len(options) < 2:
                                st.error("Add at least 2 options")
                            elif len(options) > 10:
                                st.error("Maximum 10 options allowed")
                            else:
                                success, message = MessageHandler.create_poll(question, options)
                                if success:
                                    st.toast(message, icon="✅")
                                    st.session_state.show_create_modal = False
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.error("Fill all fields")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_bottom_navigation():
        """Render the fixed bottom navigation bar"""
        current = st.session_state.get('current_view', 'feed')
        
        st.markdown('<div class="bottom-nav" role="navigation" aria-label="Main navigation">', unsafe_allow_html=True)
        
        nav_cols = st.columns([1, 1, 1.2, 1, 1])
        
        nav_items = [
            ("feed", "🏠", "Feed"),
            ("members", "👥", "Members"),
            (None, "➕", "Create"),
            ("themes", "🎨", "Themes"),
            ("profile", "👤", "Profile"),
        ]
        
        for i, (view, icon, label) in enumerate(nav_items):
            with nav_cols[i]:
                if view:
                    if st.button(icon, key=f"nav_{view}", use_container_width=True, 
                               help=label, aria_label=label):
                        st.session_state.current_view = view
                        st.session_state.show_create_modal = False
                        st.rerun()
                    if current == view:
                        st.markdown(
                            f'<div style="text-align:center;color:#667eea;font-size:0.55rem;margin-top:-8px;">{label}</div>', 
                            unsafe_allow_html=True
                        )
                else:
                    if st.button(icon, key="nav_create", use_container_width=True, 
                               help="Create post", aria_label="Create new post"):
                        st.session_state.show_create_modal = not st.session_state.get('show_create_modal', False)
                        st.rerun()
                    st.markdown(
                        '<div style="text-align:center;color:#f093fb;font-size:0.55rem;margin-top:-8px;">Create</div>', 
                        unsafe_allow_html=True
                    )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def format_timestamp(ts: str) -> str:
        """Format timestamp for display with relative time"""
        if not ts:
            return ""
        try:
            t = datetime.fromisoformat(ts)
            diff = (datetime.now() - t).total_seconds()
            
            if diff < 5:
                return "just now"
            elif diff < 60:
                return f"{int(diff)}s"
            elif diff < 3600:
                return f"{int(diff // 60)}m"
            elif diff < 86400:
                return f"{int(diff // 3600)}h"
            elif diff < 604800:
                return f"{int(diff // 86400)}d"
            else:
                return t.strftime("%b %d")
        except (ValueError, TypeError):
            return ""

# ========== AUTHENTICATION ==========
class AuthHandler:
    """Secure authentication logic"""
    
    @staticmethod
    def sign_up(username: str, password: str, confirm: str) -> Tuple[bool, str]:
        """Sign up with validation"""
        # Validate username
        if not username or not password:
            return False, "Fill all fields"
        if password != confirm:
            return False, "Passwords don't match"
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if len(username) < 3 or len(username) > 20:
            return False, "Username must be 3-20 characters"
        if not username.isalnum():
            return False, "Only letters and numbers allowed"
        
        # Password strength check
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_upper and has_lower and has_digit):
            return False, "Password needs uppercase, lowercase, and numbers"
        
        users = DataManager.get_users()
        if username.lower() in [u.lower() for u in users]:
            return False, "Username already exists"
        
        # Hash password
        hashed_pw, salt = DataManager.hash_password(password)
        users[username] = {
            "password": hashed_pw,
            "salt": salt,
            "created_at": datetime.now().isoformat()
        }
        DataManager.save_users(users)
        
        # Create profile
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager.get_user_profile(username)
        DataManager.save_profiles(profiles)
        
        logger.info(f"New user registered: {username}")
        return True, "Account created successfully!"
    
    @staticmethod
    def sign_in(username: str, password: str) -> Tuple[bool, str]:
        """Sign in with password verification"""
        if not username or not password:
            return False, "Fill all fields"
        
        users = DataManager.get_users()
        
        for un, user_data in users.items():
            if un.lower() == username.lower():
                # Handle old format (just hash) and new format (with salt)
                if isinstance(user_data, dict):
                    stored_hash = user_data.get("password", "")
                    salt = user_data.get("salt", "")
                    if salt and DataManager.verify_password(password, stored_hash, salt):
                        return True, un
                else:
                    # Legacy: direct SHA256 hash
                    if user_data == DataManager.hash_password(password)[0]:
                        # Upgrade to new format
                        hashed_pw, salt = DataManager.hash_password(password)
                        users[un] = {
                            "password": hashed_pw,
                            "salt": salt,
                            "created_at": datetime.now().isoformat()
                        }
                        DataManager.save_users(users)
                        return True, un
                
                return False, "Incorrect password"
        
        return False, "User not found"

# ========== MAIN APP ==========
def main():
    """Main application entry point"""
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
    .scrollable-content, .bottom-nav, .top-header {
        display: none !important;
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
                username = st.text_input("Username", autocomplete="username")
                password = st.text_input("Password", type="password", autocomplete="current-password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    success, result = AuthHandler.sign_in(username, password)
                    if success:
                        st.session_state.auth = True
                        st.session_state.user = result
                        st.session_state.current_view = "feed"
                        st.session_state.page = 1
                        messages, has_more = DataManager.get_messages()
                        st.session_state.messages = messages
                        st.session_state.has_more = has_more
                        st.rerun()
                    else:
                        st.error(result)
        
        with tab2:
            with st.form("signup_form"):
                username = st.text_input("Username", autocomplete="username")
                password = st.text_input("Password", type="password", autocomplete="new-password")
                confirm = st.text_input("Confirm Password", type="password", autocomplete="new-password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    success, message = AuthHandler.sign_up(username, password, confirm)
                    if success:
                        st.success(message)
                        st.info("You can now sign in!")
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
        
        if not messages:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">✨</div>
                <p style="color:#94a3b8;">No messages yet</p>
                <p style="color:#64748b;font-size:0.8rem;">Be the first to post!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display messages in reverse chronological order
            for msg in reversed(messages):
                msg_type = msg.get("type", "text")
                
                if msg_type in ["text", "image", "file"]:
                    UIComponents.render_feed_card(msg)
                elif msg_type == "poll":
                    UIComponents.render_poll_card(msg)
                elif msg_type == "media":
                    UIComponents.render_feed_card(msg)
            
            # Load more button
            if st.session_state.get('has_more', False):
                if st.button("Load More", use_container_width=True):
                    st.session_state.page += 1
                    new_messages, has_more = DataManager.get_messages(st.session_state.page)
                    st.session_state.messages = st.session_state.messages + new_messages
                    st.session_state.has_more = has_more
                    st.rerun()
    
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
