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
import random
import shutil
from functools import lru_cache

# Must be first Streamlit command
st.set_page_config(
    page_title="SocialHub Pro", 
    page_icon="🌐", 
    layout="wide", 
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "SocialHub Pro - All-in-One Social Platform"
    }
)

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('socialhub.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== CONSTANTS & CONFIGURATION ==========
APP_NAME = "SocialHub Pro"
APP_ICON = "🌐"
APP_VERSION = "2.0.0"
MAX_POST_LENGTH = 2000
MAX_COMMENT_LENGTH = 500
MAX_BIO_LENGTH = 200
MAX_MESSAGE_LENGTH = 1000
MAX_GROUP_NAME_LENGTH = 50
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 6
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
STORY_EXPIRY_HOURS = 24
MAX_FEED_POSTS = 1000
MAX_CHAT_MESSAGES = 500
MAX_NOTIFICATIONS = 50
ONLINE_THRESHOLD_SECONDS = 300  # 5 minutes
ACTIVE_THRESHOLD_SECONDS = 60  # 1 minute
CACHE_TTL_SECONDS = 30

# Data directory
DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Data files
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
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Cloud sync configuration
try:
    JSONBIN_KEY = st.secrets.get("jsonbin", {}).get("api_key", "")
    JSONBIN_ID = st.secrets.get("jsonbin", {}).get("bin_id", "")
    CLOUD_SYNC = bool(JSONBIN_KEY and JSONBIN_ID)
except:
    JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
    JSONBIN_ID = os.environ.get("JSONBIN_ID", "")
    CLOUD_SYNC = bool(JSONBIN_KEY and JSONBIN_ID)

# Rate limiting configuration
RATE_LIMITS = {
    "post": 5.0,        # 1 post per 5 seconds
    "story": 10.0,      # 1 story per 10 seconds
    "message": 1.0,     # 1 message per second
    "reaction": 0.5,    # 2 reactions per second
    "comment": 2.0,     # 1 comment per 2 seconds
    "follow": 1.0,      # 1 follow per second
    "vote": 0.5,        # 2 votes per second
}

# Avatar colors for placeholder avatars
AVATAR_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7B787', '#FF8A80', '#B388FF',
    '#FF5722', '#9C27B0', '#3F51B5', '#009688', '#FF9800',
    '#795548', '#607D8B', '#E91E63', '#00BCD4', '#8BC34A'
]

# Theme presets
THEMES = {
    "midnight": {
        "name": "Midnight",
        "colors": ["#0b0813", "#1a1030", "#2d1b4e"],
        "icon": "🌙",
        "bg": "#0a0a1a",
        "card_bg": "rgba(255,255,255,0.03)",
        "text": "#f1f5f9",
        "secondary": "#64748b",
        "accent": "#818cf8"
    },
    "ocean": {
        "name": "Ocean",
        "colors": ["#0a192f", "#112240", "#233554"],
        "icon": "🌊",
        "bg": "#0a192f",
        "card_bg": "rgba(255,255,255,0.05)",
        "text": "#e2e8f0",
        "secondary": "#8892b0",
        "accent": "#64ffda"
    },
    "sunset": {
        "name": "Sunset",
        "colors": ["#1a0a2e", "#2d1b4e", "#4a1942"],
        "icon": "🌅",
        "bg": "#1a0a2e",
        "card_bg": "rgba(255,255,255,0.04)",
        "text": "#fce4ec",
        "secondary": "#ce93d8",
        "accent": "#ff4081"
    }
}

# ========== UTILITY FUNCTIONS ==========
def validate_image(data: bytes) -> bool:
    """Validate that binary data is a valid image file"""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except Exception:
        return False

def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize and truncate text input"""
    if not text:
        return ""
    # Remove control characters except newlines
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    # Escape HTML entities
    text = html.escape(str(text).strip())
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length-3] + "..."
    return text

def format_timestamp(ts: str) -> str:
    """Format ISO timestamp to human-readable relative time"""
    if not ts:
        return ""
    try:
        t = datetime.fromisoformat(ts)
        now = datetime.now()
        diff = (now - t).total_seconds()
        
        if diff < 5:
            return "just now"
        elif diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff // 60)}m ago"
        elif diff < 86400:
            return f"{int(diff // 3600)}h ago"
        elif diff < 604800:
            return f"{int(diff // 86400)}d ago"
        elif diff < 2592000:
            weeks = int(diff // 604800)
            return f"{weeks}w ago"
        else:
            return t.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "unknown"

def generate_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())

def get_avatar_color(username: str) -> str:
    """Get a consistent color for a user's avatar placeholder"""
    if not username:
        return AVATAR_COLORS[0]
    return AVATAR_COLORS[hash(username) % len(AVATAR_COLORS)]

def get_user_initials(username: str) -> str:
    """Get initials from username for avatar placeholder"""
    if not username:
        return "?"
    # Take first character, or first two if username has multiple parts
    parts = username.split('_')
    if len(parts) > 1:
        return (parts[0][0] + parts[1][0]).upper()[:2]
    return username[0].upper()

def create_backup(filepath: pathlib.Path) -> bool:
    """Create a backup of a file"""
    try:
        if filepath.exists():
            timestamp = int(time.time())
            backup_path = BACKUP_DIR / f"{filepath.stem}_{timestamp}.bak"
            shutil.copy2(filepath, backup_path)
            
            # Keep only last 5 backups
            backups = sorted(BACKUP_DIR.glob(f"{filepath.stem}_*.bak"))
            if len(backups) > 5:
                for old_backup in backups[:-5]:
                    old_backup.unlink()
            return True
    except Exception as e:
        logger.error(f"Backup failed for {filepath}: {e}")
    return False

def atomic_save(filepath: pathlib.Path, data: Any) -> bool:
    """Save data atomically using a temporary file"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup
        create_backup(filepath)
        
        # Write to temporary file
        temp_path = filepath.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Atomic rename
        temp_path.replace(filepath)
        return True
    except Exception as e:
        logger.error(f"Save failed for {filepath}: {e}")
        return False

# ========== RATE LIMITER ==========
class RateLimiter:
    """Rate limiter for user actions to prevent spam"""
    
    def __init__(self):
        self._actions: Dict[str, float] = {}
    
    def can_act(self, user: str, action: str, custom_limit: float = None) -> bool:
        """Check if user can perform an action based on rate limits"""
        limit = custom_limit or RATE_LIMITS.get(action, 2.0)
        key = f"{user}:{action}"
        now = time.time()
        
        if key in self._actions:
            elapsed = now - self._actions[key]
            if elapsed < limit:
                return False
        
        self._actions[key] = now
        return True
    
    def time_until_next(self, user: str, action: str) -> float:
        """Get seconds until user can perform action again"""
        limit = RATE_LIMITS.get(action, 2.0)
        key = f"{user}:{action}"
        
        if key not in self._actions:
            return 0.0
        
        elapsed = time.time() - self._actions[key]
        return max(0.0, limit - elapsed)
    
    def reset_user(self, user: str):
        """Reset all rate limits for a user"""
        keys_to_remove = [k for k in self._actions if k.startswith(f"{user}:")]
        for key in keys_to_remove:
            del self._actions[key]

# ========== DATA MANAGER ==========
class DataManager:
    """Centralized data management with caching and cloud sync"""
    
    _cache: Dict[str, Tuple[Any, float]] = {}
    
    @staticmethod
    def load_json(filepath: pathlib.Path, default: Any = None) -> Any:
        """Load JSON data from file with caching"""
        if default is None:
            default = {}
        
        cache_key = str(filepath)
        
        # Check cache
        if cache_key in DataManager._cache:
            data, timestamp = DataManager._cache[cache_key]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                return data
        
        # Load from file
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                DataManager._cache[cache_key] = (data, time.time())
                logger.debug(f"Loaded {filepath.name}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Corrupt JSON in {filepath}: {e}")
            # Try to restore from most recent backup
            backups = sorted(BACKUP_DIR.glob(f"{filepath.stem}_*.bak"), reverse=True)
            for backup in backups:
                try:
                    with open(backup, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"Restored from backup: {backup.name}")
                    DataManager._cache[cache_key] = (data, time.time())
                    return data
                except:
                    continue
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
        
        return default
    
    @staticmethod
    def save_json(filepath: pathlib.Path, data: Any) -> bool:
        """Save JSON data to file with atomic write"""
        success = atomic_save(filepath, data)
        if success:
            cache_key = str(filepath)
            DataManager._cache[cache_key] = (data, time.time())
        return success
    
    @staticmethod
    def clear_cache():
        """Clear all cached data"""
        DataManager._cache.clear()
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password using PBKDF2 with SHA-256"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return hash_obj.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        computed_hash, _ = DataManager.hash_password(password, salt)
        return computed_hash == stored_hash
    
    # ========== USER MANAGEMENT ==========
    @staticmethod
    def get_users() -> Dict:
        """Get all users"""
        return DataManager.load_json(USERS_FILE, {})
    
    @staticmethod
    def save_users(users: Dict):
        """Save users data"""
        DataManager.save_json(USERS_FILE, users)
    
    @staticmethod
    def user_exists(username: str) -> bool:
        """Check if a username exists"""
        users = DataManager.get_users()
        return username.lower() in [u.lower() for u in users]
    
    @staticmethod
    def create_user(username: str, password: str) -> Tuple[bool, str]:
        """Create a new user"""
        users = DataManager.get_users()
        
        if DataManager.user_exists(username):
            return False, "Username already exists"
        
        password_hash, salt = DataManager.hash_password(password)
        users[username] = {
            "password": password_hash,
            "salt": salt,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        DataManager.save_users(users)
        
        # Create profile
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager._create_default_profile(username)
        DataManager.save_profiles(profiles)
        
        logger.info(f"User created: {username}")
        return True, "Account created successfully"
    
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, str]:
        """Authenticate a user"""
        users = DataManager.get_users()
        
        for un, user_data in users.items():
            if un.lower() == username.lower():
                # New format with salt
                if isinstance(user_data, dict) and "salt" in user_data:
                    if DataManager.verify_password(password, user_data["password"], user_data["salt"]):
                        # Update last login
                        user_data["last_login"] = datetime.now().isoformat()
                        users[un] = user_data
                        DataManager.save_users(users)
                        return True, un
                # Legacy format (plain SHA256)
                elif isinstance(user_data, str):
                    legacy_hash = hashlib.sha256(password.encode()).hexdigest()
                    if user_data == legacy_hash:
                        # Upgrade to new format
                        new_hash, salt = DataManager.hash_password(password)
                        users[un] = {
                            "password": new_hash,
                            "salt": salt,
                            "created_at": datetime.now().isoformat(),
                            "last_login": datetime.now().isoformat()
                        }
                        DataManager.save_users(users)
                        return True, un
                
                return False, "Incorrect password"
        
        return False, "User not found"
    
    # ========== PROFILE MANAGEMENT ==========
    @staticmethod
    def _create_default_profile(username: str) -> Dict:
        """Create a default profile for a new user"""
        return {
            "display_name": username,
            "bio": "",
            "avatar": None,
            "cover_photo": None,
            "website": "",
            "location": "",
            "is_private": False,
            "is_verified": False,
            "last_seen": "",
            "status": "",
            "followers": [],
            "following": [],
            "blocked": [],
            "muted": [],
            "saved_posts": [],
            "highlights": [],
            "post_count": 0,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_profiles() -> Dict:
        """Get all user profiles"""
        return DataManager.load_json(PROFILES_FILE, {})
    
    @staticmethod
    def save_profiles(profiles: Dict):
        """Save profiles data"""
        DataManager.save_json(PROFILES_FILE, profiles)
    
    @staticmethod
    def get_profile(username: str) -> Dict:
        """Get a user's profile, creating default if not exists"""
        profiles = DataManager.get_profiles()
        
        if username not in profiles:
            profiles[username] = DataManager._create_default_profile(username)
            DataManager.save_profiles(profiles)
        
        # Ensure all required keys exist
        profile = profiles[username]
        defaults = DataManager._create_default_profile(username)
        for key, value in defaults.items():
            if key not in profile:
                profile[key] = value
        
        return profile
    
    @staticmethod
    def update_profile(username: str, updates: Dict) -> bool:
        """Update a user's profile"""
        profiles = DataManager.get_profiles()
        
        if username not in profiles:
            return False
        
        profiles[username].update(updates)
        DataManager.save_profiles(profiles)
        return True
    
    @staticmethod
    def update_last_seen(username: str):
        """Update user's last seen timestamp"""
        profiles = DataManager.get_profiles()
        if username in profiles:
            profiles[username]["last_seen"] = datetime.now().isoformat()
            DataManager.save_profiles(profiles)
    
    @staticmethod
    def get_online_users() -> List[str]:
        """Get list of currently online users"""
        profiles = DataManager.get_profiles()
        online = []
        now = datetime.now()
        
        for username, profile in profiles.items():
            last_seen = profile.get("last_seen", "")
            if last_seen:
                try:
                    last_seen_time = datetime.fromisoformat(last_seen)
                    if (now - last_seen_time).total_seconds() < ONLINE_THRESHOLD_SECONDS:
                        online.append(username)
                except:
                    pass
        
        return online
    
    @staticmethod
    def get_active_users() -> List[Dict]:
        """Get users active in last 5 minutes with details"""
        profiles = DataManager.get_profiles()
        active = []
        now = datetime.now()
        
        for username, profile in profiles.items():
            last_seen = profile.get("last_seen", "")
            if last_seen:
                try:
                    last_seen_time = datetime.fromisoformat(last_seen)
                    diff = (now - last_seen_time).total_seconds()
                    
                    if diff < ONLINE_THRESHOLD_SECONDS:
                        active.append({
                            "username": username,
                            "avatar": profile.get("avatar"),
                            "is_active": diff < ACTIVE_THRESHOLD_SECONDS,
                            "has_story": bool(hash(username) % 3 == 0),  # Simulated
                            "status": profile.get("status", ""),
                            "last_seen": last_seen
                        })
                except:
                    pass
        
        active.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return active[:15]
    
    # ========== FEED POSTS ==========
    @staticmethod
    def get_feed_posts() -> List[Dict]:
        """Get all feed posts"""
        posts = DataManager.load_json(FEED_POSTS_FILE, [])
        return posts if isinstance(posts, list) else []
    
    @staticmethod
    def save_feed_posts(posts: List[Dict]):
        """Save feed posts with size limit"""
        if len(posts) > MAX_FEED_POSTS:
            posts = posts[-MAX_FEED_POSTS:]
        DataManager.save_json(FEED_POSTS_FILE, posts)
    
    @staticmethod
    def get_user_posts(username: str) -> List[Dict]:
        """Get posts by a specific user"""
        posts = DataManager.get_feed_posts()
        return [p for p in posts if p.get("username") == username]
    
    # ========== STORIES ==========
    @staticmethod
    def get_stories() -> Dict:
        """Get all stories"""
        return DataManager.load_json(STORIES_FILE, {})
    
    @staticmethod
    def save_stories(stories: Dict):
        """Save stories data"""
        DataManager.save_json(STORIES_FILE, stories)
    
    @staticmethod
    def get_active_stories() -> Dict:
        """Get stories that haven't expired"""
        stories = DataManager.get_stories()
        active = {}
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        
        for username, user_stories in stories.items():
            active_stories = [s for s in user_stories if s.get("timestamp", "") > cutoff]
            if active_stories:
                active[username] = active_stories
        
        return active
    
    # ========== DIRECT MESSAGES ==========
    @staticmethod
    def get_direct_messages() -> Dict:
        """Get all direct messages"""
        return DataManager.load_json(DIRECT_MESSAGES_FILE, {})
    
    @staticmethod
    def save_direct_messages(dms: Dict):
        """Save direct messages"""
        DataManager.save_json(DIRECT_MESSAGES_FILE, dms)
    
    @staticmethod
    def get_chat_id(user1: str, user2: str) -> str:
        """Generate a consistent chat ID for two users"""
        sorted_users = sorted([user1, user2])
        return f"chat_{sorted_users[0]}_{sorted_users[1]}"
    
    # ========== GROUP CHATS ==========
    @staticmethod
    def get_group_chats() -> Dict:
        """Get all group chats"""
        return DataManager.load_json(GROUP_CHATS_FILE, {})
    
    @staticmethod
    def save_group_chats(groups: Dict):
        """Save group chats"""
        DataManager.save_json(GROUP_CHATS_FILE, groups)
    
    # ========== CHANNELS ==========
    @staticmethod
    def get_channels() -> Dict:
        """Get all channels"""
        return DataManager.load_json(CHANNELS_FILE, {})
    
    @staticmethod
    def save_channels(channels: Dict):
        """Save channels"""
        DataManager.save_json(CHANNELS_FILE, channels)
    
    # ========== COMMENTS ==========
    @staticmethod
    def get_comments() -> Dict:
        """Get all comments"""
        return DataManager.load_json(COMMENTS_FILE, {})
    
    @staticmethod
    def save_comments(comments: Dict):
        """Save comments"""
        DataManager.save_json(COMMENTS_FILE, comments)
    
    @staticmethod
    def get_post_comments(post_id: str) -> List[Dict]:
        """Get comments for a specific post"""
        comments = DataManager.get_comments()
        return comments.get(post_id, [])
    
    # ========== NOTIFICATIONS ==========
    @staticmethod
    def get_notifications() -> Dict:
        """Get all notifications"""
        return DataManager.load_json(NOTIFICATIONS_FILE, {})
    
    @staticmethod
    def save_notifications(notifs: Dict):
        """Save notifications"""
        DataManager.save_json(NOTIFICATIONS_FILE, notifs)
    
    @staticmethod
    def add_notification(username: str, notif_type: str, message: str, from_user: str = ""):
        """Add a notification for a user"""
        notifs = DataManager.get_notifications()
        
        if username not in notifs:
            notifs[username] = []
        
        notifs[username].insert(0, {
            "id": generate_id(),
            "type": notif_type,
            "message": message,
            "from_user": from_user,
            "timestamp": datetime.now().isoformat(),
            "read": False
        })
        
        # Limit notifications
        if len(notifs[username]) > MAX_NOTIFICATIONS:
            notifs[username] = notifs[username][:MAX_NOTIFICATIONS]
        
        DataManager.save_notifications(notifs)
    
    @staticmethod
    def get_user_notifications(username: str) -> List[Dict]:
        """Get notifications for a user"""
        notifs = DataManager.get_notifications()
        return notifs.get(username, [])
    
    @staticmethod
    def mark_notifications_read(username: str):
        """Mark all notifications as read"""
        notifs = DataManager.get_notifications()
        if username in notifs:
            for n in notifs[username]:
                n["read"] = True
            DataManager.save_notifications(notifs)
    
    @staticmethod
    def get_unread_notification_count(username: str) -> int:
        """Get count of unread notifications"""
        notifs = DataManager.get_user_notifications(username)
        return sum(1 for n in notifs if not n.get("read", False))
    
    # ========== SAVED POSTS ==========
    @staticmethod
    def get_saved_posts() -> Dict:
        """Get saved posts for all users"""
        return DataManager.load_json(SAVED_POSTS_FILE, {})
    
    @staticmethod
    def save_saved_posts(data: Dict):
        """Save saved posts"""
        DataManager.save_json(SAVED_POSTS_FILE, data)
    
    @staticmethod
    def get_user_saved_posts(username: str) -> List[str]:
        """Get saved post IDs for a user"""
        saved = DataManager.get_saved_posts()
        return saved.get(username, [])

# ========== FEATURE HANDLERS ==========

class PostHandler:
    """Handle feed posts (Twitter/Instagram/Facebook style)"""
    
    @staticmethod
    def create_post(text: str, media_data: str = None, media_name: str = None,
                   post_type: str = "post") -> Tuple[bool, str]:
        """Create a new feed post"""
        # Rate limiting
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "post"):
            wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "post")
            return False, f"Please wait {wait:.1f}s before posting again"
        
        # Validate text
        text = sanitize_text(text, MAX_POST_LENGTH) if text else ""
        if not text and not media_data:
            return False, "Post cannot be empty"
        
        # Validate media
        if media_data:
            if len(media_data) > MAX_FILE_SIZE:
                return False, f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)"
            
            if media_name and media_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                try:
                    file_bytes = base64.b64decode(media_data)
                    if not validate_image(file_bytes):
                        return False, "Invalid image file"
                except Exception:
                    return False, "Failed to process image"
        
        # Create post
        posts = DataManager.get_feed_posts()
        post = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "type": post_type,
            "likes": [],
            "reposts": 0,
            "views": 0,
            "is_pinned": False,
            "is_edited": False,
            "edited_at": None
        }
        
        if media_data:
            post["media"] = media_data
            post["media_name"] = sanitize_text(media_name, 100) if media_name else "media"
            post["media_type"] = "image" if media_name and media_name.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            ) else "file"
        
        posts.append(post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        
        # Update post count in profile
        profile = DataManager.get_profile(st.session_state.user)
        profile["post_count"] = profile.get("post_count", 0) + 1
        profiles = DataManager.get_profiles()
        profiles[st.session_state.user] = profile
        DataManager.save_profiles(profiles)
        
        return True, "Posted successfully!"
    
    @staticmethod
    def edit_post(post_id: str, new_text: str) -> Tuple[bool, str]:
        """Edit an existing post"""
        if not new_text.strip():
            return False, "Post cannot be empty"
        
        new_text = sanitize_text(new_text, MAX_POST_LENGTH)
        posts = DataManager.get_feed_posts()
        
        for post in posts:
            if post["id"] == post_id and post["username"] == st.session_state.user:
                post["text"] = new_text
                post["is_edited"] = True
                post["edited_at"] = datetime.now().isoformat()
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Post updated!"
        
        return False, "Post not found or unauthorized"
    
    @staticmethod
    def delete_post(post_id: str) -> Tuple[bool, str]:
        """Delete a post"""
        posts = DataManager.get_feed_posts()
        
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                
                # Update post count
                profile = DataManager.get_profile(st.session_state.user)
                profile["post_count"] = max(0, profile.get("post_count", 0) - 1)
                profiles = DataManager.get_profiles()
                profiles[st.session_state.user] = profile
                DataManager.save_profiles(profiles)
                
                return True, "Post deleted!"
        
        return False, "Post not found or unauthorized"
    
    @staticmethod
    def like_post(post_id: str) -> Tuple[bool, str]:
        """Like or unlike a post"""
        posts = DataManager.get_feed_posts()
        user = st.session_state.user
        
        for post in posts:
            if post["id"] == post_id:
                if user in post.get("likes", []):
                    post["likes"].remove(user)
                    action = "unliked"
                else:
                    post["likes"].append(user)
                    action = "liked"
                    # Notify post owner
                    if post["username"] != user:
                        DataManager.add_notification(
                            post["username"], "like",
                            f"@{user} liked your post", user
                        )
                
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, f"Post {action}!"
        
        return False, "Post not found"
    
    @staticmethod
    def save_post(post_id: str) -> Tuple[bool, str]:
        """Save or unsave a post"""
        user = st.session_state.user
        saved = DataManager.get_saved_posts()
        
        if user not in saved:
            saved[user] = []
        
        if post_id in saved[user]:
            saved[user].remove(post_id)
            DataManager.save_saved_posts(saved)
            return True, "Post removed from saved"
        else:
            saved[user].append(post_id)
            DataManager.save_saved_posts(saved)
            return True, "Post saved!"
    
    @staticmethod
    def is_post_saved(post_id: str) -> bool:
        """Check if a post is saved by current user"""
        saved = DataManager.get_user_saved_posts(st.session_state.user)
        return post_id in saved
    
    @staticmethod
    def create_poll(question: str, options: List[str]) -> Tuple[bool, str]:
        """Create a poll post"""
        if not question.strip():
            return False, "Question cannot be empty"
        
        options = [opt.strip() for opt in options if opt.strip()]
        if len(options) < 2:
            return False, "Need at least 2 options"
        if len(options) > 10:
            return False, "Maximum 10 options"
        
        question = sanitize_text(question, 500)
        options = [sanitize_text(opt, 100) for opt in options]
        
        posts = DataManager.get_feed_posts()
        poll_post = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": question,
            "timestamp": datetime.now().isoformat(),
            "type": "poll",
            "likes": [],
            "poll_data": {
                "options": {opt: [] for opt in options},
                "total_votes": 0
            }
        }
        
        posts.append(poll_post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        return True, "Poll created!"
    
    @staticmethod
    def vote_poll(post_id: str, option: str) -> Tuple[bool, str]:
        """Vote on a poll"""
        posts = DataManager.get_feed_posts()
        user = st.session_state.user
        
        for post in posts:
            if post["id"] == post_id and post.get("type") == "poll":
                poll_data = post["poll_data"]
                
                # Remove previous vote
                for opt, voters in poll_data["options"].items():
                    if user in voters:
                        voters.remove(user)
                        poll_data["total_votes"] -= 1
                
                # Add new vote
                if option in poll_data["options"]:
                    poll_data["options"][option].append(user)
                    poll_data["total_votes"] += 1
                
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Vote recorded!"
        
        return False, "Poll not found"

class StoryHandler:
    """Handle stories (Instagram/WhatsApp style)"""
    
    @staticmethod
    def create_story(media_data: str, media_name: str) -> Tuple[bool, str]:
        """Create a new story"""
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "story"):
            wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "story")
            return False, f"Please wait {wait:.1f}s"
        
        if len(media_data) > MAX_FILE_SIZE:
            return False, f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)"
        
        stories = DataManager.get_stories()
        user = st.session_state.user
        
        if user not in stories:
            stories[user] = []
        
        # Remove expired stories
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        stories[user] = [s for s in stories[user] if s["timestamp"] > cutoff]
        
        story = {
            "id": generate_id(),
            "username": user,
            "media": media_data,
            "media_name": sanitize_text(media_name, 100),
            "timestamp": datetime.now().isoformat(),
            "views": [],
            "likes": [],
            "expires_at": (datetime.now() + timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        }
        
        stories[user].append(story)
        DataManager.save_stories(stories)
        st.session_state.stories = stories
        return True, "Story posted!"
    
    @staticmethod
    def view_story(username: str, story_id: str):
        """Mark a story as viewed"""
        stories = DataManager.get_stories()
        if username in stories:
            for story in stories[username]:
                if story["id"] == story_id:
                    if st.session_state.user not in story["views"]:
                        story["views"].append(st.session_state.user)
                    break
            DataManager.save_stories(stories)
            st.session_state.stories = stories
    
    @staticmethod
    def delete_story(story_id: str) -> Tuple[bool, str]:
        """Delete a story"""
        stories = DataManager.get_stories()
        user = st.session_state.user
        
        if user in stories:
            for i, story in enumerate(stories[user]):
                if story["id"] == story_id:
                    stories[user].pop(i)
                    DataManager.save_stories(stories)
                    st.session_state.stories = stories
                    return True, "Story deleted!"
        
        return False, "Story not found"

class ChatHandler:
    """Handle direct messages (WhatsApp/Telegram style)"""
    
    @staticmethod
    def send_message(to_user: str, text: str, media_data: str = None,
                    media_name: str = None, reply_to: str = None) -> Tuple[bool, str]:
        """Send a direct message"""
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "message"):
            wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "message")
            return False, f"Please wait {wait:.1f}s"
        
        text = sanitize_text(text, MAX_MESSAGE_LENGTH) if text else ""
        if not text and not media_data:
            return False, "Message cannot be empty"
        
        from_user = st.session_state.user
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
            "delivered": True,
            "reply_to": reply_to,
            "forwarded_from": None
        }
        
        if media_data:
            msg["media"] = media_data
            msg["media_name"] = sanitize_text(media_name, 100) if media_name else "file"
            msg["media_type"] = "image" if media_name and media_name.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            ) else "file"
        
        dms[chat_id]["messages"].append(msg)
        DataManager.save_direct_messages(dms)
        
        # Notify recipient
        DataManager.add_notification(
            to_user, "message",
            f"New message from @{from_user}", from_user
        )
        
        return True, "Message sent!"
    
    @staticmethod
    def get_messages(with_user: str) -> List[Dict]:
        """Get messages between current user and another user"""
        current_user = st.session_state.user
        chat_id = DataManager.get_chat_id(current_user, with_user)
        dms = DataManager.get_direct_messages()
        
        if chat_id in dms:
            messages = dms[chat_id]["messages"]
            
            # Mark messages as read
            for msg in messages:
                if msg.get("to") == current_user:
                    msg["read"] = True
            
            DataManager.save_direct_messages(dms)
            return messages
        
        return []
    
    @staticmethod
    def get_chat_list() -> List[Dict]:
        """Get list of chat conversations for current user"""
        current_user = st.session_state.user
        dms = DataManager.get_direct_messages()
        online_users = DataManager.get_online_users()
        chats = []
        
        for chat_id, chat_data in dms.items():
            if current_user in chat_data["participants"]:
                other_user = [p for p in chat_data["participants"] if p != current_user][0]
                messages = chat_data["messages"]
                
                last_msg = messages[-1] if messages else None
                unread = sum(
                    1 for m in messages 
                    if m.get("to") == current_user and not m.get("read", False)
                )
                
                chats.append({
                    "with_user": other_user,
                    "last_message": last_msg["text"][:50] if last_msg and last_msg.get("text") else "📷 Media",
                    "last_time": last_msg["timestamp"] if last_msg else chat_data["created_at"],
                    "unread": unread,
                    "is_online": other_user in online_users,
                    "message_count": len(messages)
                })
        
        chats.sort(key=lambda x: x["last_time"], reverse=True)
        return chats
    
    @staticmethod
    def delete_message(chat_id: str, msg_id: str) -> Tuple[bool, str]:
        """Delete a message (for current user only)"""
        dms = DataManager.get_direct_messages()
        
        if chat_id in dms:
            messages = dms[chat_id]["messages"]
            for i, msg in enumerate(messages):
                if msg["id"] == msg_id and msg["from"] == st.session_state.user:
                    messages.pop(i)
                    DataManager.save_direct_messages(dms)
                    return True, "Message deleted"
        
        return False, "Message not found"

class GroupHandler:
    """Handle group chats and channels (WhatsApp/Telegram style)"""
    
    @staticmethod
    def create_group(name: str, members: List[str], is_channel: bool = False,
                    description: str = "") -> Tuple[bool, str]:
        """Create a new group or channel"""
        name = sanitize_text(name, MAX_GROUP_NAME_LENGTH)
        if not name:
            return False, "Group name required"
        
        all_members = list(set(members + [st.session_state.user]))
        if len(all_members) < 2 and not is_channel:
            return False, "Add at least 1 other member"
        
        group_id = f"{'channel' if is_channel else 'group'}_{generate_id()[:8]}"
        
        if is_channel:
            channels = DataManager.get_channels()
            channels[group_id] = {
                "name": name,
                "owner": st.session_state.user,
                "subscribers": all_members,
                "admins": [st.session_state.user],
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "description": sanitize_text(description, 200),
                "is_public": False,
                "icon": None
            }
            DataManager.save_channels(channels)
            return True, f"Channel '{name}' created!"
        else:
            groups = DataManager.get_group_chats()
            groups[group_id] = {
                "name": name,
                "members": all_members,
                "admins": [st.session_state.user],
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "icon": None,
                "description": sanitize_text(description, 200),
                "is_encrypted": True
            }
            DataManager.save_group_chats(groups)
            
            # Notify members
            for member in members:
                if member != st.session_state.user:
                    DataManager.add_notification(
                        member, "group_invite",
                        f"Added to group '{name}'", st.session_state.user
                    )
            
            return True, f"Group '{name}' created!"
    
    @staticmethod
    def send_group_message(group_id: str, text: str, is_channel: bool = False) -> Tuple[bool, str]:
        """Send a message to a group or channel"""
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "message"):
            wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "message")
            return False, f"Please wait {wait:.1f}s"
        
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text:
            return False, "Message cannot be empty"
        
        if is_channel:
            data = DataManager.get_channels()
            if group_id not in data:
                return False, "Channel not found"
            if st.session_state.user not in data[group_id].get("admins", []):
                return False, "Only admins can post in channels"
        else:
            data = DataManager.get_group_chats()
            if group_id not in data:
                return False, "Group not found"
            if st.session_state.user not in data[group_id].get("members", []):
                return False, "Not a member of this group"
        
        msg = {
            "id": generate_id(),
            "from": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "read_by": []
        }
        
        data[group_id]["messages"].append(msg)
        
        if is_channel:
            DataManager.save_channels(data)
        else:
            DataManager.save_group_chats(data)
        
        return True, "Message sent!"
    
    @staticmethod
    def get_user_groups() -> List[Dict]:
        """Get groups the current user belongs to"""
        user = st.session_state.user
        groups = DataManager.get_group_chats()
        user_groups = []
        
        for gid, gdata in groups.items():
            if user in gdata.get("members", []):
                msgs = gdata.get("messages", [])
                last = msgs[-1] if msgs else None
                user_groups.append({
                    "id": gid,
                    "name": gdata["name"],
                    "members": len(gdata.get("members", [])),
                    "last_message": last["text"][:30] + "..." if last and last.get("text") else "No messages",
                    "last_time": last["timestamp"] if last else gdata["created_at"],
                    "is_admin": user in gdata.get("admins", []),
                    "description": gdata.get("description", "")
                })
        
        user_groups.sort(key=lambda x: x["last_time"], reverse=True)
        return user_groups
    
    @staticmethod
    def get_user_channels() -> List[Dict]:
        """Get channels the current user is subscribed to"""
        user = st.session_state.user
        channels = DataManager.get_channels()
        user_channels = []
        
        for cid, cdata in channels.items():
            if user in cdata.get("subscribers", []):
                msgs = cdata.get("messages", [])
                last = msgs[-1] if msgs else None
                user_channels.append({
                    "id": cid,
                    "name": cdata["name"],
                    "subscribers": len(cdata.get("subscribers", [])),
                    "last_message": last["text"][:30] + "..." if last and last.get("text") else "No posts",
                    "last_time": last["timestamp"] if last else cdata["created_at"],
                    "is_owner": user == cdata.get("owner"),
                    "is_admin": user in cdata.get("admins", []),
                    "description": cdata.get("description", "")
                })
        
        user_channels.sort(key=lambda x: x["last_time"], reverse=True)
        return user_channels
    
    @staticmethod
    def get_group_messages(group_id: str) -> List[Dict]:
        """Get messages from a group"""
        groups = DataManager.get_group_chats()
        return groups.get(group_id, {}).get("messages", [])
    
    @staticmethod
    def get_channel_messages(channel_id: str) -> List[Dict]:
        """Get messages from a channel"""
        channels = DataManager.get_channels()
        return channels.get(channel_id, {}).get("messages", [])

class CommentHandler:
    """Handle comments on posts (Facebook/Instagram style)"""
    
    @staticmethod
    def add_comment(post_id: str, text: str, parent_comment_id: str = None) -> Tuple[bool, str]:
        """Add a comment to a post"""
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "comment"):
            wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "comment")
            return False, f"Please wait {wait:.1f}s"
        
        text = sanitize_text(text, MAX_COMMENT_LENGTH)
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
            "parent_id": parent_comment_id,
            "replies": []
        }
        
        if parent_comment_id:
            # Add as reply
            for c in comments[post_id]:
                if c["id"] == parent_comment_id:
                    c["replies"].append(comment)
                    break
        else:
            comments[post_id].append(comment)
        
        DataManager.save_comments(comments)
        
        # Notify post owner
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id and post["username"] != st.session_state.user:
                DataManager.add_notification(
                    post["username"], "comment",
                    f"@{st.session_state.user} commented on your post", st.session_state.user
                )
                break
        
        return True, "Comment added!"
    
    @staticmethod
    def get_comments(post_id: str) -> List[Dict]:
        """Get comments for a post"""
        comments = DataManager.get_comments()
        return comments.get(post_id, [])

class FollowHandler:
    """Handle follow/unfollow system (Instagram/Twitter style)"""
    
    @staticmethod
    def follow_user(target: str) -> Tuple[bool, str]:
        """Follow or unfollow a user"""
        if target == st.session_state.user:
            return False, "Cannot follow yourself"
        
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "follow"):
            return False, "Too fast, please wait"
        
        profiles = DataManager.get_profiles()
        user_profile = DataManager.get_profile(st.session_state.user)
        target_profile = DataManager.get_profile(target)
        
        # Ensure all required keys exist
        for profile in [user_profile, target_profile]:
            if "following" not in profile:
                profile["following"] = []
            if "followers" not in profile:
                profile["followers"] = []
            if "blocked" not in profile:
                profile["blocked"] = []
        
        # Check if blocked
        if st.session_state.user in target_profile.get("blocked", []):
            return False, "You are blocked by this user"
        if target in user_profile.get("blocked", []):
            return False, "Unblock user first"
        
        if target in user_profile["following"]:
            # Unfollow
            user_profile["following"].remove(target)
            target_profile["followers"].remove(st.session_state.user)
            action = "Unfollowed"
        else:
            # Follow
            user_profile["following"].append(target)
            target_profile["followers"].append(st.session_state.user)
            action = "Following"
            
            # Notify
            DataManager.add_notification(
                target, "follow",
                f"@{st.session_state.user} started following you", st.session_state.user
            )
        
        profiles[st.session_state.user] = user_profile
        profiles[target] = target_profile
        DataManager.save_profiles(profiles)
        
        return True, f"{action} @{target}!"
    
    @staticmethod
    def is_following(target: str) -> bool:
        """Check if current user follows target"""
        profile = DataManager.get_profile(st.session_state.user)
        return target in profile.get("following", [])
    
    @staticmethod
    def block_user(target: str) -> Tuple[bool, str]:
        """Block a user"""
        if target == st.session_state.user:
            return False, "Cannot block yourself"
        
        profiles = DataManager.get_profiles()
        user_profile = DataManager.get_profile(st.session_state.user)
        
        if "blocked" not in user_profile:
            user_profile["blocked"] = []
        
        if target in user_profile["blocked"]:
            user_profile["blocked"].remove(target)
            action = "Unblocked"
        else:
            user_profile["blocked"].append(target)
            # Also unfollow
            if target in user_profile.get("following", []):
                user_profile["following"].remove(target)
            action = "Blocked"
        
        profiles[st.session_state.user] = user_profile
        DataManager.save_profiles(profiles)
        
        return True, f"{action} @{target}!"
    
    @staticmethod
    def get_followers(username: str) -> List[str]:
        """Get followers of a user"""
        profile = DataManager.get_profile(username)
        return profile.get("followers", [])
    
    @staticmethod
    def get_following(username: str) -> List[str]:
        """Get users that a user follows"""
        profile = DataManager.get_profile(username)
        return profile.get("following", [])

# ========== SESSION STATE ==========
def init_session_state():
    """Initialize all session state variables"""
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
        'rate_limiter': RateLimiter(),
        'show_create_post': False,
        'show_create_story': False,
        'show_new_chat': False,
        'show_new_group': False,
        'show_new_channel': False,
        'show_notifications': False,
        'show_comments_for': None,
        'editing_post': None,
        'selected_theme': 'midnight',
        'viewing_profile': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Load data on first run
    if not st.session_state.feed_posts:
        st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories:
        st.session_state.stories = DataManager.get_stories()

# Initialize session
init_session_state()

# Update data and last seen for authenticated users
if st.session_state.get('auth') and st.session_state.get('user'):
    st.session_state.feed_posts = DataManager.get_feed_posts()
    st.session_state.stories = DataManager.get_stories()
    DataManager.update_last_seen(st.session_state.user)

# ========== CSS STYLES ==========
def inject_styles():
    """Inject all CSS styles for the app"""
    theme = THEMES.get(st.session_state.get('selected_theme', 'midnight'), THEMES['midnight'])
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}
    
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stDeployButton, [data-testid="stDecoration"] {{ display: none !important; }}
    
    html, body {{
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
        background: {theme['bg']};
    }}
    
    .stApp {{
        background: {theme['bg']};
        height: 100vh !important;
        overflow: hidden !important;
    }}
    
    .block-container {{
        height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
        max-width: 100% !important;
    }}
    
    /* ===== TOP HEADER ===== */
    .app-header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: rgba(10, 10, 26, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 0 1rem;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    
    .app-logo {{
        font-size: 1.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }}
    
    .header-actions {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}
    
    .header-icon {{
        font-size: 1.3rem;
        cursor: pointer;
        position: relative;
        transition: transform 0.2s;
    }}
    
    .header-icon:hover {{
        transform: scale(1.1);
    }}
    
    .badge {{
        position: absolute;
        top: -6px;
        right: -6px;
        background: #ef4444;
        color: white;
        border-radius: 50%;
        width: 18px;
        height: 18px;
        font-size: 0.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        border: 2px solid {theme['bg']};
    }}
    
    /* ===== MAIN CONTENT ===== */
    .main-content {{
        position: fixed;
        top: 56px;
        bottom: 64px;
        left: 0;
        right: 0;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0.5rem;
    }}
    
    .content-wrapper {{
        max-width: 650px;
        margin: 0 auto;
        padding-bottom: 1rem;
    }}
    
    /* ===== STORIES BAR ===== */
    .stories-bar {{
        display: flex;
        gap: 0.8rem;
        padding: 0.5rem 0;
        overflow-x: auto;
        margin-bottom: 0.8rem;
        scroll-behavior: smooth;
        -webkit-overflow-scrolling: touch;
    }}
    
    .stories-bar::-webkit-scrollbar {{ height: 0; }}
    
    .story-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.3rem;
        min-width: 68px;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    
    .story-item:hover {{
        transform: scale(1.05);
    }}
    
    .story-ring {{
        width: 62px;
        height: 62px;
        border-radius: 50%;
        padding: 2.5px;
        background: linear-gradient(45deg, #f093fb, #f5576c, #fda085, #f093fb);
        animation: rotate 4s linear infinite;
    }}
    
    .story-ring.viewed {{
        background: rgba(255,255,255,0.2);
        animation: none;
    }}
    
    @keyframes rotate {{
        from {{ --tw-rotate: 0deg; }}
        to {{ --tw-rotate: 360deg; }}
    }}
    
    .story-avatar {{
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid {theme['bg']};
        background: {theme['card_bg']};
    }}
    
    .story-avatar-placeholder {{
        width: 100%;
        height: 100%;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 1.2rem;
        border: 2px solid {theme['bg']};
    }}
    
    .story-username {{
        color: {theme['secondary']};
        font-size: 0.65rem;
        text-align: center;
        max-width: 65px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    /* ===== POST CARDS ===== */
    .post-card {{
        background: {theme['card_bg']};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        margin-bottom: 0.8rem;
        overflow: hidden;
        transition: all 0.3s ease;
        animation: fadeInUp 0.4s ease;
    }}
    
    .post-card:hover {{
        background: rgba(255,255,255,0.05);
        border-color: rgba(255,255,255,0.1);
    }}
    
    @keyframes fadeInUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    
    .post-header {{
        display: flex;
        align-items: center;
        padding: 0.7rem 1rem;
        gap: 0.7rem;
    }}
    
    .post-avatar {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(129,140,248,0.3);
    }}
    
    .post-avatar-placeholder {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 0.85rem;
        border: 2px solid rgba(129,140,248,0.3);
    }}
    
    .post-user-info {{
        flex: 1;
    }}
    
    .post-username {{
        color: {theme['text']};
        font-weight: 600;
        font-size: 0.85rem;
    }}
    
    .verified-badge {{
        color: #3b82f6;
        font-size: 0.7rem;
        margin-left: 2px;
    }}
    
    .post-time {{
        color: {theme['secondary']};
        font-size: 0.65rem;
    }}
    
    .post-text {{
        color: #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.6;
        padding: 0 1rem 0.5rem 1rem;
        word-wrap: break-word;
        white-space: pre-wrap;
    }}
    
    .post-media {{
        width: 100%;
        max-height: 450px;
        object-fit: cover;
        cursor: pointer;
    }}
    
    .post-actions {{
        display: flex;
        align-items: center;
        padding: 0.5rem 1rem;
        gap: 0.3rem;
        border-top: 1px solid rgba(255,255,255,0.05);
    }}
    
    .action-btn {{
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        color: #94a3b8;
        font-size: 0.85rem;
        cursor: pointer;
        padding: 0.3rem 0.6rem;
        border-radius: 8px;
        transition: all 0.2s;
        background: none;
        border: none;
    }}
    
    .action-btn:hover {{
        color: {theme['accent']};
        background: rgba(129,140,248,0.1);
    }}
    
    .action-btn.liked {{
        color: #ef4444;
    }}
    
    .action-btn.saved {{
        color: #f59e0b;
    }}
    
    /* ===== CHAT BUBBLES ===== */
    .chat-container {{
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        padding: 0.5rem;
    }}
    
    .chat-bubble {{
        max-width: 80%;
        padding: 0.7rem 1rem;
        border-radius: 16px;
        font-size: 0.85rem;
        line-height: 1.5;
        animation: messageIn 0.2s ease;
        position: relative;
    }}
    
    @keyframes messageIn {{
        from {{
            opacity: 0;
            transform: translateY(10px) scale(0.95);
        }}
        to {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
    }}
    
    .chat-bubble.sent {{
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }}
    
    .chat-bubble.received {{
        background: rgba(255,255,255,0.08);
        color: #e2e8f0;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }}
    
    .chat-time {{
        font-size: 0.6rem;
        opacity: 0.7;
        text-align: right;
        margin-top: 0.2rem;
    }}
    
    .chat-status {{
        font-size: 0.6rem;
        margin-left: 0.3rem;
    }}
    
    /* ===== USER LIST ===== */
    .user-list-item {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.7rem 0.8rem;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s;
        margin-bottom: 0.2rem;
    }}
    
    .user-list-item:hover {{
        background: rgba(255,255,255,0.05);
    }}
    
    .online-dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px rgba(16,185,129,0.5);
        flex-shrink: 0;
    }}
    
    .offline-dot {{
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #6b7280;
        flex-shrink: 0;
    }}
    
    .unread-badge {{
        background: {theme['accent']};
        color: white;
        border-radius: 12px;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: 600;
        min-width: 20px;
        text-align: center;
    }}
    
    /* ===== BOTTOM NAV ===== */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: rgba(10, 10, 26, 0.95);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex;
        align-items: center;
        justify-content: space-around;
        z-index: 1000;
        padding: 0 0.3rem;
    }}
    
    .nav-tab {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        color: {theme['secondary']};
        font-size: 0.6rem;
        font-weight: 500;
        transition: all 0.2s;
        padding: 6px 12px;
        border-radius: 8px;
        background: none;
        border: none;
        position: relative;
    }}
    
    .nav-tab.active {{
        color: {theme['accent']};
    }}
    
    .nav-tab.active::after {{
        content: '';
        position: absolute;
        top: -2px;
        width: 20px;
        height: 2px;
        background: {theme['accent']};
        border-radius: 1px;
    }}
    
    .nav-icon {{
        font-size: 1.4rem;
        transition: transform 0.2s;
    }}
    
    .nav-tab:active .nav-icon {{
        transform: scale(0.9);
    }}
    
    /* ===== MODALS ===== */
    .modal-overlay {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
        animation: fadeIn 0.2s ease;
    }}
    
    @keyframes fadeIn {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}
    
    .modal-content {{
        background: rgba(20, 15, 40, 0.98);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        width: 92%;
        max-width: 520px;
        max-height: 85vh;
        overflow-y: auto;
        padding: 1.5rem;
        animation: slideUp 0.3s ease;
    }}
    
    @keyframes slideUp {{
        from {{
            opacity: 0;
            transform: translateY(50px) scale(0.95);
        }}
        to {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
    }}
    
    .modal-header {{
        text-align: center;
        margin-bottom: 1.2rem;
    }}
    
    /* ===== POLL STYLES ===== */
    .poll-option {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.6rem 0.8rem;
        margin: 0.3rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .poll-option:hover {{
        background: rgba(129,140,248,0.1);
        border-color: rgba(129,140,248,0.2);
    }}
    
    .poll-progress-bar {{
        height: 4px;
        background: rgba(255,255,255,0.06);
        border-radius: 2px;
        margin-top: 0.3rem;
        overflow: hidden;
    }}
    
    .poll-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 2px;
        transition: width 0.5s ease;
    }}
    
    /* ===== NOTIFICATION TOAST ===== */
    .notification-toast {{
        position: fixed;
        top: 64px;
        right: 1rem;
        background: rgba(20, 15, 40, 0.98);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        color: #f1f5f9;
        font-size: 0.85rem;
        z-index: 3000;
        animation: slideInRight 0.3s ease;
        max-width: 320px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    }}
    
    @keyframes slideInRight {{
        from {{
            opacity: 0;
            transform: translateX(100%);
        }}
        to {{
            opacity: 1;
            transform: translateX(0);
        }}
    }}
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {{
        width: 4px;
        height: 4px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: transparent;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: rgba(129,140,248,0.3);
        border-radius: 2px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: rgba(129,140,248,0.5);
    }}
    
    /* ===== STREAMLIT OVERRIDES ===== */
    .stButton > button {{
        background: rgba(129,140,248,0.15) !important;
        border: 1px solid rgba(129,140,248,0.2) !important;
        color: {theme['accent']} !important;
        border-radius: 10px !important;
        padding: 0.4rem 1rem !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        min-height: auto !important;
        cursor: pointer !important;
    }}
    
    .stButton > button:hover {{
        background: rgba(129,140,248,0.25) !important;
        border-color: rgba(129,140,248,0.3) !important;
        transform: translateY(-1px);
    }}
    
    .stButton > button:active {{
        transform: translateY(0);
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: {theme['text']} !important;
        border-radius: 10px !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.85rem !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {theme['accent']} !important;
        box-shadow: 0 0 0 2px rgba(129,140,248,0.1) !important;
    }}
    
    .stSelectbox > div > div > select {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: {theme['text']} !important;
        border-radius: 10px !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.5rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {theme['secondary']};
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {theme['accent']};
        background: rgba(129,140,248,0.1);
    }}
    
    .stExpander {{
        background: {theme['card_bg']} !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }}
    
    .stExpander > div > div > div {{
        color: {theme['text']} !important;
    }}
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {{
        .content-wrapper {{
            max-width: 100%;
            padding: 0 0.3rem;
        }}
        
        .post-text {{
            font-size: 0.85rem;
        }}
        
        .chat-bubble {{
            max-width: 85%;
            font-size: 0.8rem;
        }}
        
        .modal-content {{
            width: 95%;
            max-height: 90vh;
            padding: 1rem;
        }}
    }}
    
    @media (max-width: 480px) {{
        .post-card {{
            border-radius: 12px;
            margin-bottom: 0.5rem;
        }}
        
        .post-header {{
            padding: 0.5rem 0.7rem;
        }}
        
        .post-actions {{
            padding: 0.3rem 0.7rem;
        }}
        
        .bottom-nav {{
            height: 56px;
        }}
        
        .main-content {{
            bottom: 56px;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ========== AVATAR COMPONENT ==========
def render_avatar(username: str, size: int = 40, as_html: bool = True) -> str:
    """Render user avatar as HTML"""
    profile = DataManager.get_profile(username)
    avatar_path = profile.get("avatar")
    
    if avatar_path and os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            if as_html:
                return f'<img src="data:image/jpeg;base64,{b64}" class="post-avatar" style="width:{size}px;height:{size}px;object-fit:cover;" alt="{username}">'
            return b64
        except Exception:
            pass
    
    # Fallback to placeholder
    color = get_avatar_color(username)
    initials = get_user_initials(username)
    if as_html:
        return f'<div class="post-avatar-placeholder" style="width:{size}px;height:{size}px;font-size:{size*0.35}px;background:{color};">{initials}</div>'
    return ""

def render_story_avatar(username: str, size: int = 60, has_new: bool = False) -> str:
    """Render story avatar with ring"""
    ring_class = "story-ring" if has_new else "story-ring viewed"
    profile = DataManager.get_profile(username)
    avatar_path = profile.get("avatar")
    
    if avatar_path and os.path.exists(avatar_path):
        with open(avatar_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'''
        <div class="{ring_class}">
            <img src="data:image/jpeg;base64,{b64}" class="story-avatar" alt="{username}">
        </div>
        '''
    
    color = get_avatar_color(username)
    initials = get_user_initials(username)
    return f'''
    <div class="{ring_class}">
        <div class="story-avatar-placeholder" style="font-size:{size*0.35}px;background:{color};">{initials}</div>
    </div>
    '''

# ========== UI COMPONENTS ==========
def render_header():
    """Render the top header bar"""
    user = st.session_state.user
    unread = DataManager.get_unread_notification_count(user)
    
    st.markdown(f"""
    <div class="app-header">
        <div class="app-logo">🌐 SocialHub</div>
        <div class="header-actions">
            <span class="header-icon" id="notif-icon" title="Notifications">
                🔔
                {f'<span class="badge">{unread}</span>' if unread > 0 else ''}
            </span>
            {render_avatar(user, 32)}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stories_bar():
    """Render the stories bar at top of feed"""
    user = st.session_state.user
    active_stories = DataManager.get_active_stories()
    profiles = DataManager.get_profiles()
    
    html = '<div class="stories-bar">'
    
    # Current user's story (always show "Your Story")
    has_own_story = user in active_stories
    html += f"""
    <div class="story-item" onclick="document.getElementById('add_story_btn').click()">
        {render_story_avatar(user, 60, not has_own_story)}
        <div class="story-username">Your Story</div>
    </div>
    """
    
    # Other users' stories
    for username, stories in active_stories.items():
        if username != user:
            has_new = any(st.session_state.user not in s.get("views", []) for s in stories)
            html += f"""
            <div class="story-item">
                {render_story_avatar(username, 60, has_new)}
                <div class="story-username">@{username[:10]}</div>
            </div>
            """
    
    if len(active_stories) <= 1:
        html += '<div style="color:#64748b;display:flex;align-items:center;font-size:0.8rem;padding-left:0.5rem;">No stories yet • Tap + to add</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    
    # Hidden button for story creation
    if st.button("➕", key="add_story_btn", help="Add Story", label_visibility="collapsed"):
        st.session_state.show_create_story = True
        st.rerun()

def render_post_card(post: Dict):
    """Render a single feed post card"""
    username = post.get("username", "anonymous")
    post_id = post.get("id", "")
    is_owner = username == st.session_state.user
    is_liked = st.session_state.user in post.get("likes", [])
    is_saved = PostHandler.is_post_saved(post_id)
    like_count = len(post.get("likes", []))
    profile = DataManager.get_profile(username)
    is_verified = profile.get("is_verified", False)
    
    # Post card start
    st.markdown(f"""
    <div class="post-card" id="post_{post_id}">
        <div class="post-header">
            {render_avatar(username, 36)}
            <div class="post-user-info">
                <div class="post-username">
                    @{html.escape(username)}
                    {f'<span class="verified-badge">✓</span>' if is_verified else ''}
                </div>
                <div class="post-time">{format_timestamp(post.get('timestamp', ''))}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Post text
    if post.get("text"):
        edited_mark = ' <span style="color:#64748b;font-size:0.7rem;">(edited)</span>' if post.get("is_edited") else ""
        st.markdown(f'<div class="post-text">{html.escape(post["text"])}{edited_mark}</div>', unsafe_allow_html=True)
    
    # Post media
    if post.get("media") and post.get("media_type") == "image":
        st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post image" loading="lazy">', unsafe_allow_html=True)
    
    # Post actions
    st.markdown('<div class="post-actions">', unsafe_allow_html=True)
    
    cols = st.columns([1, 1, 1, 1, 1, 2])
    
    with cols[0]:
        btn_class = "action-btn liked" if is_liked else "action-btn"
        if st.button(f"{'❤️' if is_liked else '🤍'} {like_count}", key=f"like_{post_id}"):
            PostHandler.like_post(post_id)
            st.rerun()
    
    with cols[1]:
        if st.button("💬", key=f"cmt_{post_id}"):
            if st.session_state.show_comments_for == post_id:
                st.session_state.show_comments_for = None
            else:
                st.session_state.show_comments_for = post_id
            st.rerun()
    
    with cols[2]:
        if st.button("🔄", key=f"rp_{post_id}"):
            st.toast("Reposted!", icon="🔄")
    
    with cols[3]:
        btn_class = "action-btn saved" if is_saved else "action-btn"
        if st.button("🔖" if not is_saved else "📌", key=f"sv_{post_id}"):
            PostHandler.save_post(post_id)
            st.rerun()
    
    with cols[4]:
        if st.button("📤", key=f"sh_{post_id}"):
            st.toast("Link copied!", icon="📋")
    
    if is_owner:
        with cols[5]:
            if st.button("🗑️", key=f"del_{post_id}", help="Delete post"):
                if st.session_state.get(f"confirm_del_{post_id}"):
                    PostHandler.delete_post(post_id)
                    st.session_state[f"confirm_del_{post_id}"] = False
                    st.rerun()
                else:
                    st.session_state[f"confirm_del_{post_id}"] = True
                    st.toast("Click again to confirm delete", icon="⚠️")
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Comments section
    if st.session_state.show_comments_for == post_id:
        render_comments_section(post_id)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(post: Dict):
    """Render a poll post"""
    username = post.get("username", "anonymous")
    post_id = post.get("id", "")
    poll_data = post.get("poll_data", {})
    total_votes = poll_data.get("total_votes", 0)
    options = poll_data.get("options", {})
    profile = DataManager.get_profile(username)
    
    st.markdown(f"""
    <div class="post-card">
        <div class="post-header">
            {render_avatar(username, 36)}
            <div class="post-user-info">
                <div class="post-username">
                    @{html.escape(username)}
                    {f'<span class="verified-badge">✓</span>' if profile.get('is_verified') else ''}
                </div>
                <div class="post-time">📊 Poll • {format_timestamp(post.get('timestamp', ''))}</div>
            </div>
        </div>
        <div class="post-text" style="font-weight:600;">{html.escape(post.get('text', ''))}</div>
        <div style="padding:0 1rem 0.5rem 1rem;">
    """, unsafe_allow_html=True)
    
    for option_name, voters in options.items():
        percentage = (len(voters) / total_votes * 100) if total_votes > 0 else 0
        is_voted = st.session_state.user in voters
        
        st.markdown(f"""
        <div class="poll-option" style="{'border-color:#818cf8;' if is_voted else ''}">
            <div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.85rem;">
                <span>{'✓ ' if is_voted else ''}{html.escape(option_name)}</span>
                <span>{percentage:.1f}%</span>
            </div>
            <div class="poll-progress-bar">
                <div class="poll-progress-fill" style="width:{percentage}%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Vote {html.escape(option_name[:20])}", key=f"poll_{post_id}_{option_name[:15]}"):
            PostHandler.vote_poll(post_id, option_name)
            st.rerun()
    
    st.markdown(f"""
            <div style="color:#64748b;font-size:0.7rem;margin-top:0.5rem;">
                {total_votes} total vote{'s' if total_votes != 1 else ''}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_comments_section(post_id: str):
    """Render comments for a post"""
    comments = CommentHandler.get_comments(post_id)
    
    st.markdown('<div style="padding:0.5rem 1rem;border-top:1px solid rgba(255,255,255,0.05);">', unsafe_allow_html=True)
    
    # Existing comments
    for comment in comments[-20:]:
        st.markdown(f"""
        <div style="margin:0.4rem 0;padding:0.3rem 0;">
            <div style="display:flex;gap:0.5rem;align-items:flex-start;">
                {render_avatar(comment['username'], 24)}
                <div style="flex:1;">
                    <span style="color:#f1f5f9;font-weight:600;font-size:0.8rem;">@{html.escape(comment['username'])}</span>
                    <span style="color:#e2e8f0;font-size:0.8rem;margin-left:0.3rem;">{html.escape(comment['text'])}</span>
                    <div style="color:#64748b;font-size:0.65rem;">{format_timestamp(comment['timestamp'])}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add comment form
    with st.form(f"add_comment_{post_id}", clear_on_submit=True):
        cols = st.columns([5, 1])
        with cols[0]:
            comment_text = st.text_input(
                "Add a comment...",
                label_visibility="collapsed",
                placeholder="Write a comment...",
                key=f"comment_input_{post_id}"
            )
        with cols[1]:
            if st.form_submit_button("Post", use_container_width=True):
                if comment_text.strip():
                    CommentHandler.add_comment(post_id, comment_text)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    """Render the chat/messaging interface"""
    active_chat = st.session_state.get('active_chat')
    active_group = st.session_state.get('active_group')
    active_channel = st.session_state.get('active_channel')
    
    # Back button
    if st.button("← Back to Messages", use_container_width=True):
        st.session_state.active_chat = None
        st.session_state.active_group = None
        st.session_state.active_channel = None
        st.session_state.chat_type = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if active_chat:
        # === DIRECT MESSAGE ===
        messages = ChatHandler.get_messages(active_chat)
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;margin-bottom:0.5rem;">
            {render_avatar(active_chat, 40)}
            <div>
                <div style="color:#f1f5f9;font-weight:600;">@{html.escape(active_chat)}</div>
                <div style="color:#10b981;font-size:0.7rem;">● Online</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Messages display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in messages:
            is_sent = msg.get("from") == st.session_state.user
            bubble_class = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                {html.escape(msg.get('text', ''))}
                <div class="chat-time">
                    {format_timestamp(msg['timestamp'])}
                    <span class="chat-status">{'✓✓' if is_sent and msg.get('read') else '✓' if is_sent else ''}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        with st.form(f"dm_input_{active_chat}", clear_on_submit=True):
            cols = st.columns([5, 1])
            with cols[0]:
                msg_text = st.text_input(
                    "Message",
                    label_visibility="collapsed",
                    placeholder=f"Message @{active_chat}...",
                    key=f"dm_text_{active_chat}"
                )
            with cols[1]:
                if st.form_submit_button("➤", use_container_width=True, help="Send"):
                    if msg_text.strip():
                        ChatHandler.send_message(active_chat, msg_text)
                        st.rerun()
    
    elif active_group:
        # === GROUP CHAT ===
        messages = GroupHandler.get_group_messages(active_group)
        groups = DataManager.get_group_chats()
        group = groups.get(active_group, {})
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;margin-bottom:0.5rem;">
            <div class="post-avatar-placeholder" style="width:40px;height:40px;background:#667eea;">👥</div>
            <div>
                <div style="color:#f1f5f9;font-weight:600;">{html.escape(group.get('name', 'Group'))}</div>
                <div style="color:#64748b;font-size:0.7rem;">{len(group.get('members', []))} members</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in messages:
            is_sent = msg.get("from") == st.session_state.user
            bubble_class = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                {'' if is_sent else f'<div style="color:#818cf8;font-size:0.7rem;margin-bottom:0.2rem;">@{html.escape(msg.get("from", ""))}</div>'}
                {html.escape(msg.get('text', ''))}
                <div class="chat-time">{format_timestamp(msg['timestamp'])}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form(f"group_input_{active_group}", clear_on_submit=True):
            cols = st.columns([5, 1])
            with cols[0]:
                msg_text = st.text_input(
                    "Message",
                    label_visibility="collapsed",
                    placeholder=f"Message {group.get('name', 'group')}...",
                    key=f"group_text_{active_group}"
                )
            with cols[1]:
                if st.form_submit_button("➤", use_container_width=True):
                    if msg_text.strip():
                        GroupHandler.send_group_message(active_group, msg_text)
                        st.rerun()
    
    elif active_channel:
        # === CHANNEL ===
        messages = GroupHandler.get_channel_messages(active_channel)
        channels = DataManager.get_channels()
        channel = channels.get(active_channel, {})
        is_admin = st.session_state.user in channel.get("admins", [])
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;margin-bottom:0.5rem;">
            <div class="post-avatar-placeholder" style="width:40px;height:40px;background:#f093fb;">📢</div>
            <div>
                <div style="color:#f1f5f9;font-weight:600;">{html.escape(channel.get('name', 'Channel'))}</div>
                <div style="color:#64748b;font-size:0.7rem;">{len(channel.get('subscribers', []))} subscribers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for msg in messages:
            st.markdown(f"""
            <div class="post-card" style="margin:0.5rem 0;">
                <div class="post-header">
                    {render_avatar(msg.get('from', ''), 32)}
                    <div>
                        <div class="post-username">@{html.escape(msg.get('from', ''))}</div>
                        <div class="post-time">{format_timestamp(msg['timestamp'])}</div>
                    </div>
                </div>
                <div class="post-text">{html.escape(msg.get('text', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if is_admin:
            with st.form(f"channel_input_{active_channel}", clear_on_submit=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    msg_text = st.text_input(
                        "Broadcast",
                        label_visibility="collapsed",
                        placeholder="Post to channel...",
                        key=f"channel_text_{active_channel}"
                    )
                with cols[1]:
                    if st.form_submit_button("📢", use_container_width=True):
                        if msg_text.strip():
                            GroupHandler.send_group_message(active_channel, msg_text, is_channel=True)
                            st.rerun()

def render_create_post_modal():
    """Render the create post modal"""
    if not st.session_state.get('show_create_post'):
        return
    
    st.markdown("""
    <div class="modal-overlay" id="create-modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 style="color:#f1f5f9;font-size:1.1rem;">Create Post</h3>
            </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Text", "📊 Poll", "📷 Story"])
    
    with tab1:
        with st.form("create_post_form", clear_on_submit=True):
            post_text = st.text_area(
                "What's on your mind?",
                max_chars=MAX_POST_LENGTH,
                height=100,
                placeholder="Share your thoughts..."
            )
            media_file = st.file_uploader(
                "Add image",
                type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                help=f"Max {MAX_FILE_SIZE // (1024*1024)}MB",
                key="post_media"
            )
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📤 Post", use_container_width=True):
                    media_data, media_name = None, None
                    if media_file:
                        if media_file.size > MAX_FILE_SIZE:
                            st.error(f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")
                        else:
                            try:
                                file_bytes = media_file.read()
                                if validate_image(file_bytes):
                                    media_data = base64.b64encode(file_bytes).decode()
                                    media_name = media_file.name
                                else:
                                    st.error("Invalid image file")
                            except Exception as e:
                                st.error(f"Error: {e}")
                    
                    if post_text.strip() or media_data:
                        success, msg = PostHandler.create_post(post_text, media_data, media_name)
                        if success:
                            st.session_state.show_create_post = False
                            st.rerun()
                        else:
                            st.error(msg)
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_post = False
                    st.rerun()
    
    with tab2:
        with st.form("create_poll_form", clear_on_submit=True):
            question = st.text_input("Poll question", max_chars=500)
            options_text = st.text_area(
                "Options (one per line)",
                height=100,
                placeholder="Option 1\nOption 2\nOption 3\n..."
            )
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📊 Create Poll", use_container_width=True):
                    if question and options_text:
                        options = [o.strip() for o in options_text.split('\n') if o.strip()]
                        if len(options) >= 2:
                            success, msg = PostHandler.create_poll(question, options)
                            if success:
                                st.session_state.show_create_post = False
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Need at least 2 options")
                    else:
                        st.error("Fill all fields")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_post = False
                    st.rerun()
    
    with tab3:
        with st.form("create_story_form", clear_on_submit=True):
            story_media = st.file_uploader(
                "Story image",
                type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                help=f"Max {MAX_FILE_SIZE // (1024*1024)}MB",
                key="story_media"
            )
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📷 Post Story", use_container_width=True):
                    if story_media:
                        if story_media.size > MAX_FILE_SIZE:
                            st.error(f"File too large")
                        else:
                            try:
                                file_bytes = story_media.read()
                                if validate_image(file_bytes):
                                    media_data = base64.b64encode(file_bytes).decode()
                                    success, msg = StoryHandler.create_story(media_data, story_media.name)
                                    if success:
                                        st.session_state.show_create_post = False
                                        st.rerun()
                                    else:
                                        st.error(msg)
                            except:
                                st.error("Error processing image")
                    else:
                        st.error("Select an image")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_post = False
                    st.rerun()
    
    # Close button at bottom
    if st.button("✕ Close", use_container_width=True):
        st.session_state.show_create_post = False
        st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_bottom_navigation():
    """Render the bottom navigation bar"""
    current = st.session_state.get('current_tab', 'feed')
    
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
            active_class = "active" if current == tab else ""
            if st.button(
                icon,
                key=f"nav_{tab}",
                use_container_width=True,
                help=label
            ):
                if tab == "create":
                    st.session_state.show_create_post = True
                else:
                    st.session_state.current_tab = tab
                    st.session_state.show_create_post = False
                    st.session_state.active_chat = None
                    st.session_state.active_group = None
                    st.session_state.active_channel = None
                    st.session_state.show_new_chat = False
                    st.session_state.show_new_group = False
                    st.session_state.show_new_channel = False
                st.rerun()
            
            if current == tab:
                st.markdown(
                    f'<div style="text-align:center;color:#818cf8;font-size:0.55rem;margin-top:-8px;font-weight:600;">{label}</div>',
                    unsafe_allow_html=True
                )
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== PAGES ==========
def render_feed_page():
    """Render the main feed page"""
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Stories bar
    render_stories_bar()
    
    # Quick post bar
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        if st.button("✨ What's on your mind?", use_container_width=True):
            st.session_state.show_create_post = True
            st.rerun()
    with col2:
        if st.button("📷", help="Add Story", use_container_width=True):
            st.session_state.show_create_post = True
            st.rerun()
    with col3:
        if st.button("📊", help="Create Poll", use_container_width=True):
            st.session_state.show_create_post = True
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feed posts
    posts = st.session_state.feed_posts
    
    if not posts:
        st.markdown("""
        <div style="text-align:center;padding:3rem 1rem;color:#64748b;">
            <div style="font-size:4rem;margin-bottom:1rem;">📝</div>
            <h3 style="color:#94a3b8;">Welcome to SocialHub!</h3>
            <p style="font-size:0.9rem;">Your feed is empty. Follow users or create your first post!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for post in reversed(posts[-50:]):
            post_type = post.get("type", "post")
            if post_type == "poll":
                render_poll_card(post)
            else:
                render_post_card(post)
        
        if len(posts) > 50:
            if st.button("Load More Posts", use_container_width=True):
                st.session_state.feed_posts = DataManager.get_feed_posts()
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_explore_page():
    """Render the explore/discover page"""
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:1rem;">🔍 Explore</h3>', unsafe_allow_html=True)
    
    # Search
    search_query = st.text_input(
        "Search users",
        placeholder="Search by username...",
        label_visibility="collapsed"
    )
    
    # Get users
    all_users = list(DataManager.get_users().keys())
    
    if search_query:
        filtered = [u for u in all_users if search_query.lower() in u.lower()]
    else:
        filtered = [u for u in all_users if u != st.session_state.user]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if filtered:
        for username in filtered[:30]:
            profile = DataManager.get_profile(username)
            is_following = FollowHandler.is_following(username)
            followers_count = len(profile.get("followers", []))
            
            cols = st.columns([4, 1, 1])
            
            with cols[0]:
                bio_preview = profile.get("bio", "")[:60]
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem 0;">
                    {render_avatar(username, 44)}
                    <div>
                        <div style="color:#f1f5f9;font-weight:600;">@{html.escape(username)}</div>
                        <div style="color:#64748b;font-size:0.7rem;">{followers_count} followers • {html.escape(bio_preview)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with cols[1]:
                btn_label = "✓ Following" if is_following else "+ Follow"
                if st.button(btn_label, key=f"explore_follow_{username}", use_container_width=True):
                    success, msg = FollowHandler.follow_user(username)
                    if success:
                        st.toast(msg, icon="✅")
                        st.rerun()
                    else:
                        st.toast(msg, icon="❌")
            
            with cols[2]:
                if st.button("💬", key=f"explore_msg_{username}", use_container_width=True, help="Message"):
                    st.session_state.active_chat = username
                    st.session_state.chat_type = "direct"
                    st.session_state.current_tab = "chats"
                    st.rerun()
            
            st.markdown("<hr style='border-color:rgba(255,255,255,0.03);margin:0;'>", unsafe_allow_html=True)
    else:
        st.info("No users found matching your search.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chats_page():
    """Render the chats/messages page"""
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # If in active conversation, show chat interface
    if st.session_state.get('active_chat') or st.session_state.get('active_group') or st.session_state.get('active_channel'):
        render_chat_interface()
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:1rem;">💬 Messages</h3>', unsafe_allow_html=True)
    
    # Quick action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 New Chat", use_container_width=True, help="Start a new conversation"):
            st.session_state.show_new_chat = True
    with col2:
        if st.button("👥 New Group", use_container_width=True, help="Create a group"):
            st.session_state.show_new_group = True
    with col3:
        if st.button("📢 New Channel", use_container_width=True, help="Create a channel"):
            st.session_state.show_new_channel = True
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different chat types
    tab1, tab2, tab3 = st.tabs(["📱 Direct Messages", "👥 Groups", "📢 Channels"])
    
    with tab1:
        chats = ChatHandler.get_chat_list()
        
        if chats:
            for chat in chats:
                unread_html = f'<span class="unread-badge">{chat["unread"]}</span>' if chat["unread"] > 0 else ''
                dot = '<span class="online-dot"></span>' if chat["is_online"] else ''
                
                st.markdown(f"""
                <div class="user-list-item" style="justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:0.8rem;flex:1;">
                        {render_avatar(chat['with_user'], 44)}
                        <div style="flex:1;">
                            <div style="display:flex;align-items:center;gap:0.4rem;">
                                <span style="color:#f1f5f9;font-weight:600;">@{html.escape(chat['with_user'])}</span>
                                {dot}
                            </div>
                            <div style="color:#94a3b8;font-size:0.75rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:200px;">
                                {html.escape(chat['last_message'])}
                            </div>
                        </div>
                    </div>
                    <div style="text-align:right;min-width:60px;">
                        <div style="color:#64748b;font-size:0.65rem;">{format_timestamp(chat['last_time'])}</div>
                        {unread_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    f"Open chat with {chat['with_user']}",
                    key=f"open_chat_{chat['with_user']}",
                    label_visibility="collapsed"
                ):
                    st.session_state.active_chat = chat['with_user']
                    st.session_state.chat_type = "direct"
                    st.rerun()
                
                st.markdown("<hr style='border-color:rgba(255,255,255,0.02);margin:0;'>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center;padding:2rem;color:#64748b;">
                <div style="font-size:2rem;">💬</div>
                <p>No conversations yet</p>
            </div>
            """, unsafe_allow_html=True)
        
        # New chat modal
        if st.session_state.get('show_new_chat'):
            with st.expander("Start New Chat", expanded=True):
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                if available:
                    selected = st.selectbox("Select user", available, key="new_chat_select")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Start Chat", use_container_width=True, key="confirm_new_chat"):
                            st.session_state.active_chat = selected
                            st.session_state.chat_type = "direct"
                            st.session_state.show_new_chat = False
                            st.rerun()
                    with c2:
                        if st.button("Cancel", use_container_width=True, key="cancel_new_chat"):
                            st.session_state.show_new_chat = False
                            st.rerun()
                else:
                    st.info("No other users available")
    
    with tab2:
        groups = GroupHandler.get_user_groups()
        
        if groups:
            for group in groups:
                st.markdown(f"""
                <div class="user-list-item">
                    <div style="display:flex;align-items:center;gap:0.8rem;flex:1;">
                        <div class="post-avatar-placeholder" style="width:44px;height:44px;background:#667eea;">👥</div>
                        <div>
                            <div style="color:#f1f5f9;font-weight:600;">{html.escape(group['name'])}</div>
                            <div style="color:#94a3b8;font-size:0.75rem;">{group['members']} members</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    f"Open {group['name']}",
                    key=f"open_group_{group['id']}",
                    label_visibility="collapsed"
                ):
                    st.session_state.active_group = group['id']
                    st.session_state.chat_type = "group"
                    st.rerun()
        else:
            st.info("No groups yet. Create one!")
        
        # New group modal
        if st.session_state.get('show_new_group'):
            with st.expander("Create New Group", expanded=True):
                group_name = st.text_input("Group name", max_chars=MAX_GROUP_NAME_LENGTH, key="new_group_name")
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                selected_members = st.multiselect("Add members", available, key="new_group_members")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Create Group", use_container_width=True, key="confirm_new_group"):
                        if group_name and selected_members:
                            success, msg = GroupHandler.create_group(group_name, selected_members)
                            if success:
                                st.toast(msg, icon="✅")
                                st.session_state.show_new_group = False
                                st.rerun()
                            else:
                                st.error(msg)
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_new_group"):
                        st.session_state.show_new_group = False
                        st.rerun()
    
    with tab3:
        channels = GroupHandler.get_user_channels()
        
        if channels:
            for channel in channels:
                st.markdown(f"""
                <div class="user-list-item">
                    <div style="display:flex;align-items:center;gap:0.8rem;flex:1;">
                        <div class="post-avatar-placeholder" style="width:44px;height:44px;background:#f093fb;">📢</div>
                        <div>
                            <div style="color:#f1f5f9;font-weight:600;">{html.escape(channel['name'])}</div>
                            <div style="color:#94a3b8;font-size:0.75rem;">{channel['subscribers']} subscribers</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(
                    f"Open {channel['name']}",
                    key=f"open_channel_{channel['id']}",
                    label_visibility="collapsed"
                ):
                    st.session_state.active_channel = channel['id']
                    st.session_state.chat_type = "channel"
                    st.rerun()
        else:
            st.info("No channels yet. Create one!")
        
        # New channel modal
        if st.session_state.get('show_new_channel'):
            with st.expander("Create New Channel", expanded=True):
                channel_name = st.text_input("Channel name", max_chars=MAX_GROUP_NAME_LENGTH, key="new_channel_name")
                available = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                selected_subs = st.multiselect("Add subscribers", available, key="new_channel_subs")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Create Channel", use_container_width=True, key="confirm_new_channel"):
                        if channel_name:
                            success, msg = GroupHandler.create_group(
                                channel_name, selected_subs or [], is_channel=True
                            )
                            if success:
                                st.toast(msg, icon="✅")
                                st.session_state.show_new_channel = False
                                st.rerun()
                            else:
                                st.error(msg)
                with c2:
                    if st.button("Cancel", use_container_width=True, key="cancel_new_channel"):
                        st.session_state.show_new_channel = False
                        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_profile_page():
    """Render the profile page"""
    user = st.session_state.user
    profile = DataManager.get_profile(user)
    followers = profile.get("followers", [])
    following = profile.get("following", [])
    user_posts = DataManager.get_user_posts(user)
    
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    # Profile header
    st.markdown(f"""
    <div style="text-align:center;padding:1.5rem 0;">
        {render_avatar(user, 80)}
        <h2 style="color:#f1f5f9;margin-top:0.8rem;">
            @{html.escape(user)}
            {f'<span class="verified-badge">✓</span>' if profile.get('is_verified') else ''}
        </h2>
        <p style="color:#94a3b8;font-size:0.9rem;">{html.escape(profile.get('bio', 'No bio yet'))}</p>
        {f'<p style="color:#64748b;font-size:0.8rem;">🌐 {html.escape(profile.get("website", ""))}</p>' if profile.get("website") else ''}
        {f'<p style="color:#64748b;font-size:0.8rem;">📍 {html.escape(profile.get("location", ""))}</p>' if profile.get("location") else ''}
    </div>
    
    <div style="display:flex;justify-content:space-around;text-align:center;padding:1rem;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:1rem;">
        <div>
            <div style="color:#f1f5f9;font-size:1.3rem;font-weight:700;">{len(user_posts)}</div>
            <div style="color:#64748b;font-size:0.7rem;">Posts</div>
        </div>
        <div>
            <div style="color:#f1f5f9;font-size:1.3rem;font-weight:700;">{len(followers)}</div>
            <div style="color:#64748b;font-size:0.7rem;">Followers</div>
        </div>
        <div>
            <div style="color:#f1f5f9;font-size:1.3rem;font-weight:700;">{len(following)}</div>
            <div style="color:#64748b;font-size:0.7rem;">Following</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Edit profile
    with st.expander("✏️ Edit Profile", expanded=False):
        with st.form("edit_profile_form"):
            display_name = st.text_input("Display Name", value=profile.get("display_name", user))
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=MAX_BIO_LENGTH)
            website = st.text_input("Website", value=profile.get("website", ""))
            location = st.text_input("Location", value=profile.get("location", ""))
            is_private = st.checkbox("Private Account", value=profile.get("is_private", False))
            avatar_file = st.file_uploader("Profile Picture", type=['png', 'jpg', 'jpeg', 'webp'])
            
            if st.form_submit_button("Save Changes", use_container_width=True):
                updates = {
                    "display_name": sanitize_text(display_name, 50),
                    "bio": sanitize_text(bio, MAX_BIO_LENGTH) if bio else "",
                    "website": sanitize_text(website, 100) if website else "",
                    "location": sanitize_text(location, 100) if location else "",
                    "is_private": is_private
                }
                
                if avatar_file and avatar_file.size <= MAX_AVATAR_SIZE:
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
                        avatar_path = UPLOADS_DIR / f"{user}_avatar.jpg"
                        img.save(avatar_path, "JPEG", quality=80)
                        updates["avatar"] = str(avatar_path)
                    except Exception:
                        st.error("Failed to process image")
                
                DataManager.update_profile(user, updates)
                st.success("Profile updated!")
                st.rerun()
    
    # Theme selection
    with st.expander("🎨 Theme", expanded=False):
        for theme_key, theme_data in THEMES.items():
            if st.button(f"{theme_data['icon']} {theme_data['name']}", key=f"theme_{theme_key}", use_container_width=True):
                st.session_state.selected_theme = theme_key
                st.rerun()
    
    # User's posts
    if user_posts:
        st.markdown(f'<h4 style="color:#f1f5f9;margin-top:1rem;">Your Posts ({len(user_posts)})</h4>', unsafe_allow_html=True)
        for post in reversed(user_posts[-20:]):
            if post.get("type") == "poll":
                render_poll_card(post)
            else:
                render_post_card(post)
    
    # Sign out
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚪 Sign Out", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_notifications_page():
    """Render notifications page"""
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:1rem;">🔔 Notifications</h3>', unsafe_allow_html=True)
    
    notifs = DataManager.get_user_notifications(st.session_state.user)
    
    if notifs:
        # Mark all as read button
        if st.button("✓ Mark all as read", use_container_width=True):
            DataManager.mark_notifications_read(st.session_state.user)
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        for notif in notifs:
            bg = "rgba(129,140,248,0.05)" if not notif.get("read") else "transparent"
            icon_map = {
                "like": "❤️",
                "comment": "💬",
                "follow": "👤",
                "message": "💌",
                "group_invite": "👥",
                "mention": "@️"
            }
            icon = icon_map.get(notif.get("type", ""), "🔔")
            
            st.markdown(f"""
            <div style="background:{bg};padding:0.8rem;border-radius:10px;margin-bottom:0.3rem;display:flex;gap:0.8rem;align-items:center;">
                <span style="font-size:1.2rem;">{icon}</span>
                <div style="flex:1;">
                    <span style="color:#e2e8f0;font-size:0.85rem;">{html.escape(notif.get('message', ''))}</span>
                    <div style="color:#64748b;font-size:0.65rem;">{format_timestamp(notif.get('timestamp', ''))}</div>
                </div>
                {'' if notif.get('read') else '<span style="color:#818cf8;font-size:0.5rem;">●</span>'}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#64748b;">
            <div style="font-size:3rem;">🔔</div>
            <p>No notifications yet</p>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("← Back to Feed", use_container_width=True):
        st.session_state.show_notifications = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTHENTICATION ==========
def render_auth_screen():
    """Render the authentication screen"""
    st.markdown("""
    <style>
    html, body { overflow: auto !important; height: auto !important; }
    .block-container { overflow: auto !important; height: auto !important; }
    </style>
    """, unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    
    with center:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0 2rem 0;">
            <div style="font-size:5rem;">🌐</div>
            <h1 style="font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">
                SocialHub Pro
            </h1>
            <p style="color:#94a3b8;font-size:1rem;">One App. Everything Social.</p>
            <p style="color:#64748b;font-size:0.8rem;">
                📱 Feed &nbsp;|&nbsp; 📷 Stories &nbsp;|&nbsp; 💬 Chat &nbsp;|&nbsp; 👥 Groups &nbsp;|&nbsp; 📢 Channels
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    autocomplete="username"
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    autocomplete="current-password"
                )
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    if not username or not password:
                        st.error("Please fill all fields")
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
        
        with tab2:
            with st.form("signup_form"):
                new_username = st.text_input(
                    "Choose Username",
                    placeholder="3-20 characters, letters and numbers",
                    autocomplete="username"
                )
                new_password = st.text_input(
                    "Choose Password",
                    type="password",
                    placeholder=f"Minimum {MIN_PASSWORD_LENGTH} characters",
                    autocomplete="new-password"
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    autocomplete="new-password"
                )
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    # Validation
                    if not new_username or not new_password:
                        st.error("Please fill all fields")
                    elif len(new_username) < 3 or len(new_username) > MAX_USERNAME_LENGTH:
                        st.error(f"Username must be 3-{MAX_USERNAME_LENGTH} characters")
                    elif not new_username.isalnum():
                        st.error("Username can only contain letters and numbers")
                    elif len(new_password) < MIN_PASSWORD_LENGTH:
                        st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                    elif new_password != confirm_password:
                        st.error("Passwords don't match")
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
    # Initialize session
    init_session_state()
    
    # Inject styles
    inject_styles()
    
    # Route based on auth state
    if not st.session_state.get('auth', False):
        render_auth_screen()
        return
    
    # Authenticated user experience
    if st.session_state.get('show_notifications'):
        render_notifications_page()
    else:
        render_header()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        current_tab = st.session_state.get('current_tab', 'feed')
        
        if current_tab == "feed":
            render_feed_page()
        elif current_tab == "explore":
            render_explore_page()
        elif current_tab == "chats":
            render_chats_page()
        elif current_tab == "profile":
            render_profile_page()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Modals (rendered outside main content)
    if st.session_state.get('show_create_post'):
        render_create_post_modal()
    
    # Bottom navigation
    if not st.session_state.get('show_notifications'):
        render_bottom_navigation()

if __name__ == "__main__":
    main()
    
