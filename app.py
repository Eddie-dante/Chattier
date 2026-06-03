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
CHATS_FILE = DATA_DIR / "chats.json"
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

# Rate limiting
RATE_LIMITS = {
    "post": 3.0,
    "reaction": 1.0,
    "vote": 0.5,
    "chat_message": 1.0,
}

# ========== UTILITY FUNCTIONS ==========
def validate_image_bytes(data: bytes) -> bool:
    """Validate uploaded file is actually an image"""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except Exception:
        return False

def format_timestamp(ts: str) -> str:
    """Format timestamp for display"""
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
            return t.strftime("%b %d, %Y")
    except:
        return ""

def sanitize_text(text: str, max_length: int = 2000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    text = ''.join(char for char in text if ord(char) >= 32 or char == '\n')
    text = html.escape(str(text).strip())
    return text[:max_length]

# ========== DATA MANAGER ==========
class DataManager:
    """Centralized data operations"""
    
    @staticmethod
    def load_json(filepath: pathlib.Path, default: Any = None) -> Any:
        if default is None:
            default = {}
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            backup_path = BACKUP_DIR / f"{filepath.stem}_backup.json"
            if backup_path.exists():
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
        return default
    
    @staticmethod
    def save_json(filepath: pathlib.Path, data: Any) -> bool:
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            if filepath.exists():
                backup_path = BACKUP_DIR / f"{filepath.stem}_backup.json"
                try:
                    import shutil
                    shutil.copy2(filepath, backup_path)
                except:
                    pass
            temp_path = filepath.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(filepath)
            return True
        except Exception as e:
            logger.error(f"Failed to save {filepath}: {e}")
            return False
    
    @staticmethod
    def hash_password(pwd: str, salt: Optional[str] = None) -> Tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt
    
    @staticmethod
    def verify_password(pwd: str, stored_hash: str, salt: str) -> bool:
        computed_hash, _ = DataManager.hash_password(pwd, salt)
        return computed_hash == stored_hash
    
    # Users
    @staticmethod
    def get_users() -> Dict:
        return DataManager.load_json(USERS_FILE, {})
    
    @staticmethod
    def save_users(users: Dict) -> None:
        DataManager.save_json(USERS_FILE, users)
    
    # Profiles
    @staticmethod
    def get_profiles() -> Dict:
        return DataManager.load_json(PROFILES_FILE, {})
    
    @staticmethod
    def save_profiles(profiles: Dict) -> None:
        DataManager.save_json(PROFILES_FILE, profiles)
    
    @staticmethod
    def get_user_profile(username: str) -> Dict:
        profiles = DataManager.get_profiles()
        if username not in profiles:
            profiles[username] = {
                "bio": "",
                "avatar": None,
                "status": "",
                "last_seen": "",
                "stats": {"posts": 0, "followers": 0, "following": 0},
                "created_at": datetime.now().isoformat()
            }
        return profiles[username]
    
    # Feed Messages
    @staticmethod
    def get_feed_messages() -> List:
        if CLOUD:
            try:
                r = requests.get(
                    f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}/latest",
                    headers={"X-Master-Key": JSONBIN_KEY, "X-Bin-Meta": "false"},
                    timeout=5
                )
                r.raise_for_status()
                data = r.json()
                return data if isinstance(data, list) else data.get("messages", [])
            except:
                pass
        return DataManager.load_json(MESSAGES_FILE, [])
    
    @staticmethod
    def save_feed_messages(messages: List) -> None:
        if len(messages) > 500:
            messages = messages[-300:]
        messages = [msg for msg in messages if isinstance(msg, dict) and 'id' in msg]
        DataManager.save_json(MESSAGES_FILE, messages)
        if CLOUD:
            try:
                requests.put(
                    f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}",
                    json={"messages": messages},
                    headers={"Content-Type": "application/json", "X-Master-Key": JSONBIN_KEY},
                    timeout=5
                )
            except:
                pass
    
    # Chat Messages
    @staticmethod
    def get_chats() -> Dict:
        return DataManager.load_json(CHATS_FILE, {"direct": {}, "groups": {}})
    
    @staticmethod
    def save_chats(chats: Dict) -> None:
        DataManager.save_json(CHATS_FILE, chats)
    
    @staticmethod
    def get_active_users() -> List[Dict]:
        profiles = DataManager.get_profiles()
        active = []
        now = datetime.now()
        for username, profile in profiles.items():
            if profile.get("last_seen"):
                try:
                    last_seen = datetime.fromisoformat(profile["last_seen"])
                    if (now - last_seen).total_seconds() < 300:
                        active.append({
                            "username": username,
                            "avatar": profile.get("avatar"),
                            "is_active": (now - last_seen).total_seconds() < 60,
                            "has_story": bool(hash(username) % 3 == 0),
                            "status": profile.get("status", ""),
                            "last_seen": profile["last_seen"]
                        })
                except:
                    pass
        active.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return active[:15]

# ========== RATE LIMITER ==========
class RateLimiter:
    def __init__(self):
        self.last_action = {}
    
    def check_limit(self, user: str, action: str) -> bool:
        limit = RATE_LIMITS.get(action, 2.0)
        key = f"{user}_{action}"
        now = time.time()
        if key in self.last_action and now - self.last_action[key] < limit:
            return False
        self.last_action[key] = now
        return True
    
    def time_until_next(self, user: str, action: str) -> float:
        key = f"{user}_{action}"
        if key not in self.last_action:
            return 0
        return max(0, RATE_LIMITS.get(action, 2.0) - (time.time() - self.last_action[key]))

# ========== MESSAGE HANDLERS ==========
class FeedHandler:
    """Feed/Public message operations"""
    
    @staticmethod
    def send_message(text: str, attachment_data: Optional[str] = None,
                    attachment_name: Optional[str] = None) -> Tuple[bool, str]:
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(st.session_state.user, "post"):
                wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "post")
                return False, f"Please wait {wait:.1f}s"
        
        if not text and not attachment_data:
            return False, "Message cannot be empty"
        
        text = sanitize_text(text) if text else ""
        
        if attachment_data:
            if len(attachment_data) > 10 * 1024 * 1024:
                return False, "File too large (max 10MB)"
            if attachment_name and attachment_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                try:
                    file_bytes = base64.b64decode(attachment_data)
                    if not validate_image_bytes(file_bytes):
                        return False, "Invalid image file"
                except:
                    return False, "Failed to process image"
        
        messages = DataManager.get_feed_messages()
        msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "reactions": {},
            "type": "text",
            "edited": False
        }
        
        if attachment_data:
            msg["attachment"] = attachment_data
            msg["attachment_name"] = html.escape(attachment_name) if attachment_name else "file"
            msg["type"] = "image" if attachment_name and attachment_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')) else "file"
        
        messages.append(msg)
        
        profile = DataManager.get_user_profile(st.session_state.user)
        profile.setdefault("stats", {})["posts"] = profile.get("stats", {}).get("posts", 0) + 1
        profiles = DataManager.get_profiles()
        profiles[st.session_state.user] = profile
        DataManager.save_profiles(profiles)
        DataManager.save_feed_messages(messages)
        st.session_state.feed_messages = messages
        return True, "Message sent!"
    
    @staticmethod
    def add_reaction(msg_id: str, emoji: str) -> bool:
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(st.session_state.user, "reaction"):
                return False
        
        messages = DataManager.get_feed_messages()
        for msg in messages:
            if msg.get("id") == msg_id:
                msg.setdefault("reactions", {}).setdefault(emoji, [])
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
        
        DataManager.save_feed_messages(messages)
        st.session_state.feed_messages = messages
        return True
    
    @staticmethod
    def delete_message(msg_id: str) -> bool:
        messages = DataManager.get_feed_messages()
        for i, msg in enumerate(messages):
            if msg.get("id") == msg_id and msg.get("username") == st.session_state.user:
                messages.pop(i)
                DataManager.save_feed_messages(messages)
                st.session_state.feed_messages = messages
                return True
        return False
    
    @staticmethod
    def create_poll(question: str, options: List[str]) -> Tuple[bool, str]:
        if not question.strip():
            return False, "Question cannot be empty"
        options = [opt.strip() for opt in options if opt.strip()]
        if len(options) < 2:
            return False, "Need at least 2 options"
        
        messages = DataManager.get_feed_messages()
        poll_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.user,
            "text": sanitize_text(question, 500),
            "timestamp": datetime.now().isoformat(),
            "type": "poll",
            "poll_data": {
                "options": {html.escape(opt[:100]): [] for opt in options},
                "total_votes": 0
            }
        }
        messages.append(poll_msg)
        DataManager.save_feed_messages(messages)
        st.session_state.feed_messages = messages
        return True, "Poll created!"
    
    @staticmethod
    def vote_poll(msg_id: str, option: str) -> bool:
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(st.session_state.user, "vote"):
                return False
        
        messages = DataManager.get_feed_messages()
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
        
        DataManager.save_feed_messages(messages)
        st.session_state.feed_messages = messages
        return True

class ChatHandler:
    """Private and Group chat operations"""
    
    @staticmethod
    def get_chat_id(user1: str, user2: str) -> str:
        """Generate consistent chat ID for two users"""
        users = sorted([user1, user2])
        return f"dm_{users[0]}_{users[1]}"
    
    @staticmethod
    def send_direct_message(to_user: str, text: str) -> Tuple[bool, str]:
        """Send a private message to another user"""
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(st.session_state.user, "chat_message"):
                wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "chat_message")
                return False, f"Please wait {wait:.1f}s"
        
        if not text.strip():
            return False, "Message cannot be empty"
        
        from_user = st.session_state.user
        chat_id = ChatHandler.get_chat_id(from_user, to_user)
        text = sanitize_text(text, 1000)
        
        chats = DataManager.get_chats()
        if chat_id not in chats["direct"]:
            chats["direct"][chat_id] = {
                "participants": [from_user, to_user],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
        
        msg = {
            "id": str(uuid.uuid4()),
            "from": from_user,
            "to": to_user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        chats["direct"][chat_id]["messages"].append(msg)
        DataManager.save_chats(chats)
        return True, "Message sent!"
    
    @staticmethod
    def get_direct_messages(with_user: str) -> List[Dict]:
        """Get messages between current user and another user"""
        current_user = st.session_state.user
        chat_id = ChatHandler.get_chat_id(current_user, with_user)
        chats = DataManager.get_chats()
        
        if chat_id in chats["direct"]:
            # Mark messages as read
            for msg in chats["direct"][chat_id]["messages"]:
                if msg["to"] == current_user:
                    msg["read"] = True
            DataManager.save_chats(chats)
            return chats["direct"][chat_id]["messages"]
        return []
    
    @staticmethod
    def get_user_chat_list() -> List[Dict]:
        """Get list of users who have chatted with current user"""
        current_user = st.session_state.user
        chats = DataManager.get_chats()
        chat_users = []
        
        for chat_id, chat_data in chats["direct"].items():
            if current_user in chat_data["participants"]:
                other_user = [p for p in chat_data["participants"] if p != current_user][0]
                messages = chat_data["messages"]
                last_msg = messages[-1] if messages else None
                unread = sum(1 for m in messages if m["to"] == current_user and not m["read"])
                
                chat_users.append({
                    "username": other_user,
                    "last_message": last_msg["text"][:50] if last_msg else "No messages",
                    "last_time": last_msg["timestamp"] if last_msg else chat_data["created_at"],
                    "unread": unread,
                    "is_active": False  # Will be checked separately
                })
        
        # Sort by last message time
        chat_users.sort(key=lambda x: x.get("last_time", ""), reverse=True)
        return chat_users
    
    @staticmethod
    def create_group(group_name: str, members: List[str]) -> Tuple[bool, str]:
        """Create a new group chat"""
        if not group_name.strip():
            return False, "Group name required"
        if len(members) < 2:
            return False, "Need at least 2 members"
        
        group_name = sanitize_text(group_name, 50)
        all_members = list(set(members + [st.session_state.user]))
        
        chats = DataManager.get_chats()
        group_id = f"group_{str(uuid.uuid4())[:8]}"
        
        chats["groups"][group_id] = {
            "name": group_name,
            "members": all_members,
            "messages": [],
            "created_by": st.session_state.user,
            "created_at": datetime.now().isoformat()
        }
        
        DataManager.save_chats(chats)
        return True, f"Group '{group_name}' created!"
    
    @staticmethod
    def send_group_message(group_id: str, text: str) -> Tuple[bool, str]:
        """Send a message to a group"""
        if 'rate_limiter' in st.session_state:
            if not st.session_state.rate_limiter.check_limit(st.session_state.user, "chat_message"):
                wait = st.session_state.rate_limiter.time_until_next(st.session_state.user, "chat_message")
                return False, f"Please wait {wait:.1f}s"
        
        if not text.strip():
            return False, "Message cannot be empty"
        
        text = sanitize_text(text, 1000)
        chats = DataManager.get_chats()
        
        if group_id not in chats["groups"]:
            return False, "Group not found"
        
        if st.session_state.user not in chats["groups"][group_id]["members"]:
            return False, "Not a member of this group"
        
        msg = {
            "id": str(uuid.uuid4()),
            "from": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        
        chats["groups"][group_id]["messages"].append(msg)
        DataManager.save_chats(chats)
        return True, "Message sent!"
    
    @staticmethod
    def get_user_groups() -> List[Dict]:
        """Get groups where current user is a member"""
        current_user = st.session_state.user
        chats = DataManager.get_chats()
        user_groups = []
        
        for group_id, group_data in chats["groups"].items():
            if current_user in group_data["members"]:
                messages = group_data["messages"]
                last_msg = messages[-1] if messages else None
                user_groups.append({
                    "id": group_id,
                    "name": group_data["name"],
                    "members": group_data["members"],
                    "member_count": len(group_data["members"]),
                    "last_message": last_msg["text"][:30] if last_msg else "No messages",
                    "last_time": last_msg["timestamp"] if last_msg else group_data["created_at"]
                })
        
        user_groups.sort(key=lambda x: x.get("last_time", ""), reverse=True)
        return user_groups
    
    @staticmethod
    def get_group_messages(group_id: str) -> List[Dict]:
        """Get messages from a group"""
        chats = DataManager.get_chats()
        if group_id in chats["groups"]:
            return chats["groups"][group_id]["messages"]
        return []

# ========== SESSION STATE ==========
def init_session_state():
    """Initialize session state"""
    defaults = {
        'feed_messages': [],
        'auth': False,
        'user': "",
        'current_view': "feed",
        'show_create_modal': False,
        'rate_limiter': RateLimiter(),
        'active_chat': None,  # Username for DM or group_id for group
        'chat_type': None,  # 'direct' or 'group'
        'show_new_group': False,
        'show_new_chat': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if not st.session_state.feed_messages:
        st.session_state.feed_messages = DataManager.get_feed_messages()

init_session_state()

# Update last seen
if st.session_state.get('auth') and st.session_state.get('user'):
    st.session_state.feed_messages = DataManager.get_feed_messages()
    profiles = DataManager.get_profiles()
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        DataManager.save_profiles(profiles)

# ========== CSS STYLES ==========
def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    section[data-testid="stSidebar"] { display: none; }
    
    html, body {
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
    }
    
    .stApp {
        background: #0f0a1a;
        height: 100vh !important;
        overflow: hidden !important;
    }
    
    .block-container {
        height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
    }
    
    /* Top Bar */
    .top-bar {
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
    
    .top-bar-title {
        color: #f1f5f9;
        font-size: 1.1rem;
        font-weight: 700;
    }
    
    /* Bottom Nav */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: rgba(15, 10, 25, 0.95);
        backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        justify-content: space-around;
        z-index: 100;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        padding: 4px 12px;
        border-radius: 8px;
        transition: all 0.2s;
        color: #64748b;
        font-size: 0.65rem;
        background: none;
        border: none;
    }
    
    .nav-item.active {
        color: #818cf8;
    }
    
    .nav-icon {
        font-size: 1.4rem;
    }
    
    /* Content Area */
    .content-area {
        position: fixed;
        top: 56px;
        bottom: 64px;
        left: 0;
        right: 0;
        overflow-y: auto;
        padding: 1rem;
    }
    
    .content-inner {
        max-width: 700px;
        margin: 0 auto;
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        margin-bottom: 0.5rem;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid rgba(129, 140, 248, 0.3);
    }
    
    .avatar-placeholder {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 1rem;
        background: linear-gradient(135deg, #667eea, #764ba2);
    }
    
    .username {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .timestamp {
        color: #64748b;
        font-size: 0.7rem;
    }
    
    .message-text {
        color: #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 0.5rem 0;
    }
    
    .actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Chat Styles */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
    }
    
    .chat-messages {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .chat-bubble {
        max-width: 75%;
        padding: 0.8rem 1rem;
        border-radius: 16px;
        font-size: 0.85rem;
        line-height: 1.4;
        animation: fadeIn 0.2s ease;
    }
    
    .chat-bubble.sent {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }
    
    .chat-bubble.received {
        background: rgba(255, 255, 255, 0.08);
        color: #e2e8f0;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    
    .chat-bubble .bubble-time {
        font-size: 0.65rem;
        opacity: 0.7;
        margin-top: 0.2rem;
        text-align: right;
    }
    
    .chat-input-area {
        padding: 1rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(15, 10, 25, 0.95);
    }
    
    /* User List */
    .user-list-item {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.8rem;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s;
        margin-bottom: 0.3rem;
    }
    
    .user-list-item:hover {
        background: rgba(255, 255, 255, 0.05);
    }
    
    .unread-badge {
        background: #818cf8;
        color: white;
        border-radius: 10px;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    
    .online-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
    }
    
    /* Modal */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(5px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1001;
    }
    
    .modal-content {
        background: rgba(20, 15, 35, 0.98);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        width: 90%;
        max-width: 500px;
        max-height: 80vh;
        overflow-y: auto;
        padding: 1.5rem;
    }
    
    /* Buttons */
    .stButton > button {
        background: rgba(129, 140, 248, 0.2) !important;
        border: 1px solid rgba(129, 140, 248, 0.3) !important;
        color: #818cf8 !important;
        border-radius: 8px !important;
        padding: 0.4rem 1rem !important;
        font-size: 0.85rem !important;
        transition: all 0.2s !important;
    }
    
    .stButton > button:hover {
        background: rgba(129, 140, 248, 0.3) !important;
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.8rem !important;
        font-size: 0.85rem !important;
    }
    
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #667eea; border-radius: 2px; }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

# ========== UI COMPONENTS ==========
def render_avatar(username: str, size: int = 40) -> str:
    """Generate avatar HTML"""
    profile = DataManager.get_user_profile(username)
    avatar_path = profile.get("avatar")
    
    if avatar_path and os.path.exists(avatar_path):
        try:
            with open(avatar_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/jpeg;base64,{b64}" class="avatar" style="width:{size}px;height:{size}px;" alt="{username}">'
        except:
            pass
    
    initial = username[0].upper() if username else "?"
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    color = colors[hash(username) % len(colors)]
    return f'<div class="avatar-placeholder" style="width:{size}px;height:{size}px;font-size:{size*0.4}px;background:{color};">{initial}</div>'

def render_top_bar():
    """Render top navigation bar"""
    view_titles = {
        "feed": "📱 Feed",
        "chats": "💬 Chats",
        "profile": "👤 Profile"
    }
    title = view_titles.get(st.session_state.get('current_view', 'feed'), "Chattier Pro")
    
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-title">{title}</div>
        <div>{render_avatar(st.session_state.get('user', ''), 32)}</div>
    </div>
    """, unsafe_allow_html=True)

def render_bottom_nav():
    """Render bottom navigation"""
    current = st.session_state.get('current_view', 'feed')
    
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    
    cols = st.columns(3)
    
    nav_items = [
        ("feed", "🏠", "Feed"),
        ("chats", "💬", "Chats"),
        ("profile", "👤", "Profile")
    ]
    
    for i, (view, icon, label) in enumerate(nav_items):
        with cols[i]:
            active_class = "active" if current == view else ""
            if st.button(f"{icon}\n{label}", key=f"nav_{view}", use_container_width=True):
                st.session_state.current_view = view
                st.session_state.active_chat = None
                st.session_state.chat_type = None
                st.rerun()
            if current == view:
                st.markdown(f'<div style="text-align:center;color:#818cf8;font-size:0.6rem;margin-top:-8px;">{label}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_feed():
    """Render public feed"""
    st.markdown('<div class="content-inner">', unsafe_allow_html=True)
    
    # Create post button
    if st.button("✨ Create Post", use_container_width=True):
        st.session_state.show_create_modal = True
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display messages
    messages = st.session_state.get('feed_messages', [])
    
    if not messages:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#64748b;">
            <div style="font-size:3rem;">📝</div>
            <p>No posts yet</p>
            <p style="font-size:0.8rem;">Be the first to share something!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in reversed(messages[-50:]):
            if msg.get("type") == "poll":
                render_poll_card(msg)
            else:
                render_feed_card(msg)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_feed_card(msg: Dict):
    """Render a feed post card"""
    username = msg.get("username", "")
    msg_id = msg.get("id", "")
    is_owner = (username == st.session_state.user)
    
    st.markdown(f"""
    <div class="card" style="animation: fadeIn 0.3s ease;">
        <div class="card-header">
            {render_avatar(username)}
            <div>
                <div class="username">@{html.escape(username)}</div>
                <div class="timestamp">{format_timestamp(msg.get('timestamp', ''))}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if msg.get("text"):
        edited = ' <span style="color:#64748b;font-size:0.7rem;">(edited)</span>' if msg.get("edited") else ""
        st.markdown(f'<div class="message-text">{html.escape(msg["text"])}{edited}</div>', unsafe_allow_html=True)
    
    if msg.get("attachment") and msg.get("type") == "image":
        st.markdown(f'<img src="{msg["attachment"]}" style="width:100%;max-height:300px;object-fit:cover;border-radius:12px;margin:0.5rem 0;">', unsafe_allow_html=True)
    
    # Actions
    cols = st.columns([1, 1, 1, 3, 2])
    
    with cols[0]:
        if st.button("❤️", key=f"like_{msg_id}"):
            FeedHandler.add_reaction(msg_id, "❤️")
            st.rerun()
    
    with cols[1]:
        if st.button("💬", key=f"reply_{msg_id}"):
            st.info("Reply feature coming soon!")
    
    with cols[2]:
        if st.button("🔖", key=f"save_{msg_id}"):
            FeedHandler.add_reaction(msg_id, "🔖")
            st.rerun()
    
    # Show reactions
    if msg.get("reactions"):
        with cols[3]:
            reaction_text = " ".join([f"{emoji} {len(users)}" for emoji, users in msg["reactions"].items()])
            st.markdown(f'<span style="color:#94a3b8;font-size:0.75rem;">{reaction_text}</span>', unsafe_allow_html=True)
    
    # Delete button for owner
    if is_owner:
        with cols[4]:
            if st.button("🗑️", key=f"del_{msg_id}"):
                FeedHandler.delete_message(msg_id)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(msg: Dict):
    """Render a poll card"""
    username = msg.get("username", "")
    msg_id = msg.get("id", "")
    poll_data = msg.get("poll_data", {})
    total_votes = poll_data.get("total_votes", 0)
    options = poll_data.get("options", {})
    
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            {render_avatar(username)}
            <div>
                <div class="username">@{html.escape(username)}</div>
                <div class="timestamp">Poll • {format_timestamp(msg.get('timestamp', ''))}</div>
            </div>
        </div>
        <div class="message-text" style="font-weight:600;">{html.escape(msg.get('text', ''))}</div>
    """, unsafe_allow_html=True)
    
    for option_name, voters in options.items():
        percentage = (len(voters) / total_votes * 100) if total_votes > 0 else 0
        st.markdown(f"""
        <div style="margin:0.3rem 0;">
            <div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.85rem;">
                <span>{html.escape(option_name)}</span>
                <span>{percentage:.0f}%</span>
            </div>
            <div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;margin-top:2px;">
                <div style="width:{percentage}%;height:100%;background:linear-gradient(135deg,#667eea,#764ba2);border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Vote {html.escape(option_name[:20])}", key=f"vote_{msg_id}_{option_name[:20]}"):
            FeedHandler.vote_poll(msg_id, option_name)
            st.rerun()
    
    st.markdown(f'<div style="color:#64748b;font-size:0.7rem;margin-top:0.5rem;">{total_votes} total votes</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_create_modal():
    """Render create post modal"""
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content">
            <h3 style="color:#f1f5f9;text-align:center;margin-bottom:1rem;">Create Post</h3>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Text", "📊 Poll"])
    
    with tab1:
        with st.form("create_text"):
            text = st.text_area("What's on your mind?", max_chars=2000, height=80)
            attachment = st.file_uploader("Add image", type=['png', 'jpg', 'jpeg', 'gif', 'webp'])
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post", use_container_width=True):
                    att_data, att_name = None, None
                    if attachment and attachment.size <= 10 * 1024 * 1024:
                        try:
                            file_bytes = attachment.read()
                            if validate_image_bytes(file_bytes):
                                att_data = base64.b64encode(file_bytes).decode()
                                att_name = attachment.name
                        except:
                            st.error("Failed to process image")
                    
                    if text.strip() or att_data:
                        success, msg = FeedHandler.send_message(text, att_data, att_name)
                        if success:
                            st.session_state.show_create_modal = False
                            st.rerun()
                        else:
                            st.error(msg)
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    with tab2:
        with st.form("create_poll"):
            question = st.text_input("Question", max_chars=500)
            options = st.text_area("Options (one per line)", height=80, placeholder="Option 1\nOption 2\nOption 3")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Create Poll", use_container_width=True):
                    if question and options:
                        opts = [o.strip() for o in options.split('\n') if o.strip()]
                        if len(opts) >= 2:
                            success, msg = FeedHandler.create_poll(question, opts)
                            if success:
                                st.session_state.show_create_modal = False
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.error("Need at least 2 options")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_chats():
    """Render chat interface"""
    st.markdown('<div class="content-inner">', unsafe_allow_html=True)
    
    # If in an active chat, show chat interface
    if st.session_state.get('active_chat') and st.session_state.get('chat_type'):
        render_chat_interface()
    else:
        render_chat_list()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_list():
    """Render list of chats"""
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:1rem;">Messages</h3>', unsafe_allow_html=True)
    
    # New chat buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💬 New Chat", use_container_width=True):
            st.session_state.show_new_chat = True
            st.rerun()
    with col2:
        if st.button("👥 New Group", use_container_width=True):
            st.session_state.show_new_group = True
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Direct messages
    st.markdown('<p style="color:#94a3b8;font-size:0.8rem;font-weight:600;">DIRECT MESSAGES</p>', unsafe_allow_html=True)
    
    chat_users = ChatHandler.get_user_chat_list()
    active_users = DataManager.get_active_users()
    active_usernames = [u['username'] for u in active_users]
    
    if chat_users:
        for chat in chat_users:
            is_online = chat['username'] in active_usernames
            dot = '<div class="online-dot"></div>' if is_online else ''
            
            st.markdown(f"""
            <div class="user-list-item" style="justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:0.8rem;flex:1;" 
                     onclick="document.getElementById('btn_{chat['username']}').click();">
                    {render_avatar(chat['username'])}
                    <div>
                        <div class="username">@{html.escape(chat['username'])} {dot}</div>
                        <div style="color:#64748b;font-size:0.75rem;">{html.escape(chat['last_message'])}</div>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#64748b;font-size:0.65rem;">{format_timestamp(chat['last_time'])}</div>
                    {f'<div class="unread-badge">{chat["unread"]}</div>' if chat['unread'] > 0 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Open chat with {chat['username']}", key=f"btn_{chat['username']}", label_visibility="collapsed"):
                st.session_state.active_chat = chat['username']
                st.session_state.chat_type = 'direct'
                st.rerun()
    else:
        st.markdown('<p style="color:#64748b;text-align:center;padding:1rem;">No conversations yet</p>', unsafe_allow_html=True)
    
    # Group chats
    groups = ChatHandler.get_user_groups()
    if groups:
        st.markdown('<p style="color:#94a3b8;font-size:0.8rem;font-weight:600;margin-top:1rem;">GROUP CHATS</p>', unsafe_allow_html=True)
        
        for group in groups:
            st.markdown(f"""
            <div class="user-list-item" style="justify-content:space-between;">
                <div style="display:flex;align-items:center;gap:0.8rem;flex:1;">
                    <div class="avatar-placeholder" style="width:40px;height:40px;font-size:1.2rem;">👥</div>
                    <div>
                        <div class="username">{html.escape(group['name'])}</div>
                        <div style="color:#64748b;font-size:0.75rem;">{group['member_count']} members • {html.escape(group['last_message'])}</div>
                    </div>
                </div>
                <div style="color:#64748b;font-size:0.65rem;">{format_timestamp(group['last_time'])}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Open {group['name']}", key=f"group_{group['id']}", label_visibility="collapsed"):
                st.session_state.active_chat = group['id']
                st.session_state.chat_type = 'group'
                st.rerun()
    
    # New Chat Modal
    if st.session_state.get('show_new_chat'):
        with st.container():
            st.markdown("---")
            st.markdown("**Start New Conversation**")
            all_users = list(DataManager.get_users().keys())
            available = [u for u in all_users if u != st.session_state.user]
            
            if available:
                selected_user = st.selectbox("Select user", available)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Start Chat", use_container_width=True):
                        st.session_state.active_chat = selected_user
                        st.session_state.chat_type = 'direct'
                        st.session_state.show_new_chat = False
                        st.rerun()
                with c2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.show_new_chat = False
                        st.rerun()
            else:
                st.info("No other users available")
    
    # New Group Modal
    if st.session_state.get('show_new_group'):
        with st.container():
            st.markdown("---")
            st.markdown("**Create New Group**")
            group_name = st.text_input("Group name", max_chars=50)
            all_users = list(DataManager.get_users().keys())
            available = [u for u in all_users if u != st.session_state.user]
            selected_members = st.multiselect("Select members", available)
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Create Group", use_container_width=True):
                    if group_name and selected_members:
                        success, msg = ChatHandler.create_group(group_name, selected_members)
                        if success:
                            st.success(msg)
                            st.session_state.show_new_group = False
                            st.rerun()
                        else:
                            st.error(msg)
            with c2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.show_new_group = False
                    st.rerun()

def render_chat_interface():
    """Render the actual chat conversation"""
    active_chat = st.session_state.active_chat
    chat_type = st.session_state.chat_type
    
    # Back button
    if st.button("← Back to Chats"):
        st.session_state.active_chat = None
        st.session_state.chat_type = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if chat_type == 'direct':
        # Direct message chat
        messages = ChatHandler.get_direct_messages(active_chat)
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem;margin-bottom:1rem;">
            {render_avatar(active_chat, 40)}
            <div class="username">@{html.escape(active_chat)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display messages
        for msg in messages:
            is_sent = (msg['from'] == st.session_state.user)
            bubble_class = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <div>{html.escape(msg['text'])}</div>
                <div class="bubble-time">{format_timestamp(msg['timestamp'])}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Input
        with st.form(key="dm_input", clear_on_submit=True):
            cols = st.columns([5, 1])
            with cols[0]:
                text = st.text_input("Message", label_visibility="collapsed", placeholder="Type a message...")
            with cols[1]:
                if st.form_submit_button("Send", use_container_width=True):
                    if text.strip():
                        success, msg = ChatHandler.send_direct_message(active_chat, text)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)
    
    elif chat_type == 'group':
        # Group chat
        messages = ChatHandler.get_group_messages(active_chat)
        chats = DataManager.get_chats()
        group_data = chats["groups"].get(active_chat, {})
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem;margin-bottom:1rem;">
            <div class="avatar-placeholder" style="width:40px;height:40px;font-size:1.2rem;">👥</div>
            <div>
                <div class="username">{html.escape(group_data.get('name', 'Group'))}</div>
                <div style="color:#64748b;font-size:0.7rem;">{len(group_data.get('members', []))} members</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display messages
        for msg in messages:
            is_sent = (msg['from'] == st.session_state.user)
            bubble_class = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                {'' if is_sent else f'<div style="color:#818cf8;font-size:0.7rem;margin-bottom:0.2rem;">@{html.escape(msg["from"])}</div>'}
                <div>{html.escape(msg['text'])}</div>
                <div class="bubble-time">{format_timestamp(msg['timestamp'])}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Input
        with st.form(key="group_input", clear_on_submit=True):
            cols = st.columns([5, 1])
            with cols[0]:
                text = st.text_input("Message", label_visibility="collapsed", placeholder="Type a message...")
            with cols[1]:
                if st.form_submit_button("Send", use_container_width=True):
                    if text.strip():
                        success, msg = ChatHandler.send_group_message(active_chat, text)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)

def render_profile():
    """Render profile page"""
    user = st.session_state.user
    profile = DataManager.get_user_profile(user)
    stats = profile.get("stats", {})
    
    st.markdown(f"""
    <div class="content-inner">
        <div class="card" style="text-align:center;">
            {render_avatar(user, 80)}
            <h2 style="color:#f1f5f9;margin-top:0.8rem;">@{html.escape(user)}</h2>
            <p style="color:#94a3b8;">{html.escape(profile.get('status', 'No status'))}</p>
            <p style="color:#64748b;margin-top:0.5rem;">{html.escape(profile.get('bio', 'No bio yet'))}</p>
        </div>
        
        <div class="card">
            <div style="display:grid;grid-template-columns:repeat(3,1fr);text-align:center;gap:1rem;">
                <div>
                    <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{stats.get('posts', 0)}</div>
                    <div style="color:#64748b;font-size:0.7rem;">Posts</div>
                </div>
                <div>
                    <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{stats.get('followers', 0)}</div>
                    <div style="color:#64748b;font-size:0.7rem;">Followers</div>
                </div>
                <div>
                    <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{stats.get('following', 0)}</div>
                    <div style="color:#64748b;font-size:0.7rem;">Following</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Edit profile
    with st.expander("✏️ Edit Profile"):
        with st.form("edit_profile"):
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200)
            status = st.text_input("Status", value=profile.get("status", ""), max_chars=60)
            avatar = st.file_uploader("Avatar", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("Save", use_container_width=True):
                profiles = DataManager.get_profiles()
                profiles[user]["bio"] = sanitize_text(bio, 200) if bio else ""
                profiles[user]["status"] = sanitize_text(status, 60) if status else ""
                
                if avatar and avatar.size <= 5 * 1024 * 1024:
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
                        path = UPLOADS_DIR / f"{user}_avatar.jpg"
                        img.save(path, "JPEG", quality=75)
                        profiles[user]["avatar"] = str(path)
                    except:
                        st.error("Failed to process avatar")
                
                DataManager.save_profiles(profiles)
                st.success("Profile updated!")
                st.rerun()
    
    # Sign out
    if st.button("🚪 Sign Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTH ==========
def render_auth_screen():
    """Authentication screen"""
    st.markdown("""
    <style>
    html, body { overflow: auto !important; height: auto !important; }
    </style>
    """, unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    
    with center:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0;">
            <div style="font-size:4rem;">💬</div>
            <h1 style="background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2rem;">Chattier Pro</h1>
            <p style="color:#64748b;">Chat, Share, Connect</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    if not username or not password:
                        st.error("Fill all fields")
                    else:
                        users = DataManager.get_users()
                        user_found = False
                        for un, data in users.items():
                            if un.lower() == username.lower():
                                user_found = True
                                if isinstance(data, dict):
                                    if DataManager.verify_password(password, data.get("password", ""), data.get("salt", "")):
                                        st.session_state.auth = True
                                        st.session_state.user = un
                                        st.session_state.feed_messages = DataManager.get_feed_messages()
                                        st.rerun()
                                else:
                                    if data == hashlib.sha256(password.encode()).hexdigest():
                                        st.session_state.auth = True
                                        st.session_state.user = un
                                        st.session_state.feed_messages = DataManager.get_feed_messages()
                                        st.rerun()
                                st.error("Wrong password")
                                break
                        if not user_found:
                            st.error("User not found")
        
        with tab2:
            with st.form("signup"):
                username = st.text_input("Choose username")
                password = st.text_input("Choose password", type="password")
                confirm = st.text_input("Confirm password", type="password")
                
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not username or not password:
                        st.error("Fill all fields")
                    elif password != confirm:
                        st.error("Passwords don't match")
                    elif len(password) < 6:
                        st.error("Password too short (min 6 characters)")
                    elif len(username) < 3 or len(username) > 20:
                        st.error("Username must be 3-20 characters")
                    elif not username.isalnum():
                        st.error("Only letters and numbers")
                    else:
                        users = DataManager.get_users()
                        if username.lower() in [u.lower() for u in users]:
                            st.error("Username taken")
                        else:
                            hashed_pw, salt = DataManager.hash_password(password)
                            users[username] = {"password": hashed_pw, "salt": salt, "created_at": datetime.now().isoformat()}
                            DataManager.save_users(users)
                            
                            profiles = DataManager.get_profiles()
                            profiles[username] = DataManager.get_user_profile(username)
                            DataManager.save_profiles(profiles)
                            
                            st.success("Account created! You can now sign in.")

# ========== MAIN APP ==========
def main():
    init_session_state()
    inject_styles()
    
    if not st.session_state.get('auth', False):
        render_auth_screen()
    else:
        render_top_bar()
        
        st.markdown('<div class="content-area">', unsafe_allow_html=True)
        
        current_view = st.session_state.get('current_view', 'feed')
        
        if current_view == "feed":
            render_feed()
        elif current_view == "chats":
            render_chats()
        elif current_view == "profile":
            render_profile()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Modals
        if st.session_state.get('show_create_modal'):
            render_create_modal()
        
        render_bottom_nav()

if __name__ == "__main__":
    main()
