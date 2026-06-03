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

# Must be first
st.set_page_config(page_title="SocialHub Pro", page_icon="🌐", layout="wide", initial_sidebar_state="collapsed")

# ========== LOGGING ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== CONFIGURATION ==========
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
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# Cloud sync
try:
    JSONBIN_KEY = st.secrets["jsonbin"]["api_key"]
    JSONBIN_ID = st.secrets["jsonbin"]["bin_id"]
    CLOUD_SYNC = True
except:
    JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
    JSONBIN_ID = os.environ.get("JSONBIN_ID", "")
    CLOUD_SYNC = bool(JSONBIN_KEY and JSONBIN_ID)

# Rate limits per action type
RATE_LIMITS = {
    "post": 5.0,
    "story": 10.0,
    "message": 1.0,
    "reaction": 0.5,
    "comment": 2.0,
    "follow": 1.0,
}

# ========== UTILITIES ==========
def validate_image(data: bytes) -> bool:
    """Validate image data"""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except:
        return False

def sanitize(text: str, max_len: int = 2000) -> str:
    """Sanitize text input"""
    if not text:
        return ""
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    return html.escape(str(text).strip())[:max_len]

def format_time(ts: str) -> str:
    """Format timestamp"""
    if not ts:
        return ""
    try:
        t = datetime.fromisoformat(ts)
        diff = (datetime.now() - t).total_seconds()
        if diff < 5: return "just now"
        elif diff < 60: return f"{int(diff)}s"
        elif diff < 3600: return f"{int(diff//60)}m"
        elif diff < 86400: return f"{int(diff//3600)}h"
        elif diff < 604800: return f"{int(diff//86400)}d"
        return t.strftime("%b %d, %Y")
    except:
        return ""

def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())

def get_avatar_color(username: str) -> str:
    """Get consistent color for user avatar"""
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
              '#DDA0DD', '#98D8C8', '#F7B787', '#FF8A80', '#B388FF',
              '#FF5722', '#9C27B0', '#3F51B5', '#009688', '#FF9800']
    return colors[hash(username) % len(colors)]

# ========== DATA MANAGER ==========
class DataManager:
    """Centralized data layer"""
    
    @staticmethod
    def load(filepath: pathlib.Path, default=None):
        if default is None:
            default = {}
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Load error {filepath}: {e}")
        return default
    
    @staticmethod
    def save(filepath: pathlib.Path, data) -> bool:
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            # Backup
            if filepath.exists():
                import shutil
                backup = BACKUP_DIR / f"{filepath.stem}_{int(time.time())}.bak"
                shutil.copy2(filepath, backup)
            # Save
            tmp = filepath.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp.replace(filepath)
            return True
        except Exception as e:
            logger.error(f"Save error {filepath}: {e}")
            return False
    
    @staticmethod
    def hash_password(pwd: str, salt: str = None) -> Tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000)
        return h.hex(), salt
    
    @staticmethod
    def verify_password(pwd: str, stored_hash: str, salt: str) -> bool:
        h, _ = DataManager.hash_password(pwd, salt)
        return h == stored_hash
    
    # Users
    @staticmethod
    def get_users() -> Dict:
        return DataManager.load(USERS_FILE, {})
    
    @staticmethod
    def save_users(data: Dict):
        DataManager.save(USERS_FILE, data)
    
    # Profiles
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
            profiles[username] = {
                "display_name": username,
                "bio": "",
                "avatar": None,
                "website": "",
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
                "created_at": datetime.now().isoformat()
            }
        return profiles[username]
    
    # Feed Posts (Twitter/Instagram style)
    @staticmethod
    def get_feed_posts() -> List:
        posts = DataManager.load(FEED_POSTS_FILE, [])
        return posts if isinstance(posts, list) else []
    
    @staticmethod
    def save_feed_posts(data: List):
        if len(data) > 1000:
            data = data[-500:]
        DataManager.save(FEED_POSTS_FILE, data)
    
    # Stories (Instagram/WhatsApp style)
    @staticmethod
    def get_stories() -> Dict:
        return DataManager.load(STORIES_FILE, {})
    
    @staticmethod
    def save_stories(data: Dict):
        DataManager.save(STORIES_FILE, data)
    
    # Direct Messages (WhatsApp/Telegram style)
    @staticmethod
    def get_direct_messages() -> Dict:
        return DataManager.load(DIRECT_MESSAGES_FILE, {})
    
    @staticmethod
    def save_direct_messages(data: Dict):
        DataManager.save(DIRECT_MESSAGES_FILE, data)
    
    # Group Chats (WhatsApp/Telegram style)
    @staticmethod
    def get_group_chats() -> Dict:
        return DataManager.load(GROUP_CHATS_FILE, {})
    
    @staticmethod
    def save_group_chats(data: Dict):
        DataManager.save(GROUP_CHATS_FILE, data)
    
    # Channels (Telegram style)
    @staticmethod
    def get_channels() -> Dict:
        return DataManager.load(CHANNELS_FILE, {})
    
    @staticmethod
    def save_channels(data: Dict):
        DataManager.save(CHANNELS_FILE, data)
    
    # Comments
    @staticmethod
    def get_comments() -> Dict:
        return DataManager.load(COMMENTS_FILE, {})
    
    @staticmethod
    def save_comments(data: Dict):
        DataManager.save(COMMENTS_FILE, data)
    
    # Notifications
    @staticmethod
    def get_notifications() -> Dict:
        return DataManager.load(NOTIFICATIONS_FILE, {})
    
    @staticmethod
    def save_notifications(data: Dict):
        DataManager.save(NOTIFICATIONS_FILE, data)
    
    @staticmethod
    def add_notification(username: str, notif_type: str, message: str, from_user: str = ""):
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
        # Keep last 50
        notifs[username] = notifs[username][:50]
        DataManager.save_notifications(notifs)

# ========== RATE LIMITER ==========
class RateLimiter:
    def __init__(self):
        self.actions = {}
    
    def can_act(self, user: str, action: str) -> bool:
        limit = RATE_LIMITS.get(action, 2.0)
        key = f"{user}_{action}"
        now = time.time()
        if key in self.actions and now - self.actions[key] < limit:
            return False
        self.actions[key] = now
        return True

# ========== FEATURE HANDLERS ==========

class PostHandler:
    """Handle feed posts (Twitter/Instagram style)"""
    
    @staticmethod
    def create_post(text: str, media_data: str = None, media_name: str = None, 
                   post_type: str = "post") -> Tuple[bool, str]:
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "post"):
            return False, "Slow down! Please wait before posting."
        
        text = sanitize(text, 2000) if text else ""
        if not text and not media_data:
            return False, "Post cannot be empty"
        
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
            "is_pinned": False
        }
        
        if media_data:
            post["media"] = media_data
            post["media_name"] = sanitize(media_name, 100) if media_name else "media"
            post["media_type"] = "image" if media_name and media_name.lower().endswith(('.png','.jpg','.jpeg','.gif','.webp')) else "file"
        
        posts.append(post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        
        # Update post count
        profile = DataManager.get_profile(st.session_state.user)
        profile.setdefault("post_count", 0)
        profile["post_count"] += 1
        profiles = DataManager.get_profiles()
        profiles[st.session_state.user] = profile
        DataManager.save_profiles(profiles)
        
        return True, "Posted!"
    
    @staticmethod
    def like_post(post_id: str) -> bool:
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id:
                user = st.session_state.user
                if user in post["likes"]:
                    post["likes"].remove(user)
                else:
                    post["likes"].append(user)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True
        return False
    
    @staticmethod
    def delete_post(post_id: str) -> bool:
        posts = DataManager.get_feed_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True
        return False

class StoryHandler:
    """Handle stories (Instagram/WhatsApp style)"""
    
    @staticmethod
    def create_story(media_data: str, media_name: str) -> Tuple[bool, str]:
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "story"):
            return False, "Please wait before posting another story"
        
        stories = DataManager.get_stories()
        user = st.session_state.user
        
        if user not in stories:
            stories[user] = []
        
        # Remove stories older than 24 hours
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        stories[user] = [s for s in stories[user] if s["timestamp"] > cutoff]
        
        story = {
            "id": generate_id(),
            "username": user,
            "media": media_data,
            "media_name": sanitize(media_name, 100),
            "timestamp": datetime.now().isoformat(),
            "views": [],
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        stories[user].append(story)
        DataManager.save_stories(stories)
        st.session_state.stories = stories
        return True, "Story posted!"
    
    @staticmethod
    def view_story(username: str, story_id: str):
        stories = DataManager.get_stories()
        if username in stories:
            for story in stories[username]:
                if story["id"] == story_id and st.session_state.user not in story["views"]:
                    story["views"].append(st.session_state.user)
            DataManager.save_stories(stories)
            st.session_state.stories = stories

class ChatHandler:
    """Handle direct messages (WhatsApp/Telegram style)"""
    
    @staticmethod
    def get_chat_id(user1: str, user2: str) -> str:
        return "_".join(sorted([user1, user2]))
    
    @staticmethod
    def send_message(to_user: str, text: str, media_data: str = None, media_name: str = None) -> Tuple[bool, str]:
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "message"):
            return False, "Sending too fast"
        
        text = sanitize(text, 1000) if text else ""
        if not text and not media_data:
            return False, "Message empty"
        
        from_user = st.session_state.user
        chat_id = ChatHandler.get_chat_id(from_user, to_user)
        dms = DataManager.get_direct_messages()
        
        if chat_id not in dms:
            dms[chat_id] = {
                "participants": [from_user, to_user],
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
        
        msg = {
            "id": generate_id(),
            "from": from_user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "read": False,
            "delivered": True,
            "reply_to": None,
            "forwarded_from": None
        }
        
        if media_data:
            msg["media"] = media_data
            msg["media_name"] = sanitize(media_name, 100) if media_name else "file"
        
        dms[chat_id]["messages"].append(msg)
        DataManager.save_direct_messages(dms)
        
        # Notification
        DataManager.add_notification(to_user, "message", f"New message from @{from_user}", from_user)
        
        return True, "Sent!"
    
    @staticmethod
    def get_messages(with_user: str) -> List:
        chat_id = ChatHandler.get_chat_id(st.session_state.user, with_user)
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            # Mark as read
            for msg in dms[chat_id]["messages"]:
                if msg["to"] == st.session_state.user if "to" in msg else msg["from"] != st.session_state.user:
                    msg["read"] = True
            DataManager.save_direct_messages(dms)
            return dms[chat_id]["messages"]
        return []
    
    @staticmethod
    def get_chat_list() -> List[Dict]:
        user = st.session_state.user
        dms = DataManager.get_direct_messages()
        chats = []
        
        for chat_id, chat_data in dms.items():
            if user in chat_data["participants"]:
                other = [p for p in chat_data["participants"] if p != user][0]
                msgs = chat_data["messages"]
                last = msgs[-1] if msgs else None
                unread = sum(1 for m in msgs if m.get("from") != user and not m.get("read", False))
                
                chats.append({
                    "with_user": other,
                    "last_message": last["text"][:50] if last and last.get("text") else "Media",
                    "last_time": last["timestamp"] if last else chat_data["created_at"],
                    "unread": unread,
                    "is_online": False
                })
        
        chats.sort(key=lambda x: x["last_time"], reverse=True)
        return chats

class GroupHandler:
    """Handle group chats (WhatsApp/Telegram style)"""
    
    @staticmethod
    def create_group(name: str, members: List[str], is_channel: bool = False) -> Tuple[bool, str]:
        if not name.strip():
            return False, "Group name required"
        if len(members) < 1:
            return False, "Add at least 1 member"
        
        name = sanitize(name, 50)
        all_members = list(set(members + [st.session_state.user]))
        group_id = f"group_{generate_id()[:8]}"
        
        if is_channel:
            channels = DataManager.get_channels()
            channels[group_id] = {
                "name": name,
                "owner": st.session_state.user,
                "subscribers": all_members,
                "admins": [st.session_state.user],
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "description": "",
                "is_public": False
            }
            DataManager.save_channels(channels)
        else:
            groups = DataManager.get_group_chats()
            groups[group_id] = {
                "name": name,
                "members": all_members,
                "admins": [st.session_state.user],
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "icon": None,
                "description": ""
            }
            DataManager.save_group_chats(groups)
        
        return True, f"{'Channel' if is_channel else 'Group'} created!"
    
    @staticmethod
    def send_group_message(group_id: str, text: str, is_channel: bool = False) -> Tuple[bool, str]:
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "message"):
            return False, "Sending too fast"
        
        text = sanitize(text, 1000)
        if not text:
            return False, "Message empty"
        
        if is_channel:
            data = DataManager.get_channels()
            if group_id not in data or st.session_state.user not in data[group_id].get("admins", []):
                return False, "Only admins can post"
        else:
            data = DataManager.get_group_chats()
            if group_id not in data or st.session_state.user not in data[group_id]["members"]:
                return False, "Not a member"
        
        msg = {
            "id": generate_id(),
            "from": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        
        data[group_id]["messages"].append(msg)
        
        if is_channel:
            DataManager.save_channels(data)
        else:
            DataManager.save_group_chats(data)
        
        return True, "Sent!"
    
    @staticmethod
    def get_user_groups() -> List[Dict]:
        user = st.session_state.user
        groups = DataManager.get_group_chats()
        user_groups = []
        
        for gid, gdata in groups.items():
            if user in gdata["members"]:
                msgs = gdata["messages"]
                last = msgs[-1] if msgs else None
                user_groups.append({
                    "id": gid,
                    "name": gdata["name"],
                    "members": len(gdata["members"]),
                    "last_message": last["text"][:30] if last else "No messages",
                    "last_time": last["timestamp"] if last else gdata["created_at"]
                })
        
        return sorted(user_groups, key=lambda x: x["last_time"], reverse=True)
    
    @staticmethod
    def get_user_channels() -> List[Dict]:
        user = st.session_state.user
        channels = DataManager.get_channels()
        user_channels = []
        
        for cid, cdata in channels.items():
            if user in cdata["subscribers"]:
                msgs = cdata["messages"]
                last = msgs[-1] if msgs else None
                user_channels.append({
                    "id": cid,
                    "name": cdata["name"],
                    "subscribers": len(cdata["subscribers"]),
                    "last_message": last["text"][:30] if last else "No posts",
                    "last_time": last["timestamp"] if last else cdata["created_at"],
                    "is_owner": user == cdata["owner"]
                })
        
        return sorted(user_channels, key=lambda x: x["last_time"], reverse=True)

class CommentHandler:
    """Handle comments on posts"""
    
    @staticmethod
    def add_comment(post_id: str, text: str) -> Tuple[bool, str]:
        if not text.strip():
            return False, "Comment empty"
        
        text = sanitize(text, 500)
        comments = DataManager.get_comments()
        
        if post_id not in comments:
            comments[post_id] = []
        
        comment = {
            "id": generate_id(),
            "username": st.session_state.user,
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "likes": []
        }
        
        comments[post_id].append(comment)
        DataManager.save_comments(comments)
        
        # Notify post owner
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id:
                DataManager.add_notification(post["username"], "comment", 
                    f"@{st.session_state.user} commented on your post", st.session_state.user)
                break
        
        return True, "Comment added!"
    
    @staticmethod
    def get_comments(post_id: str) -> List:
        comments = DataManager.get_comments()
        return comments.get(post_id, [])

class FollowHandler:
    """Handle followers system (Instagram/Twitter style)"""
    
    @staticmethod
    def follow_user(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user:
            return False, "Cannot follow yourself"
        
        profiles = DataManager.get_profiles()
        user_profile = DataManager.get_profile(st.session_state.user)
        target_profile = DataManager.get_profile(target)
        
        if target in user_profile.get("blocked", []):
            return False, "Unblock user first"
        
        if target in user_profile.get("following", []):
            user_profile["following"].remove(target)
            target_profile["followers"].remove(st.session_state.user)
            message = "Unfollowed"
        else:
            user_profile["following"].append(target)
            target_profile["followers"].append(st.session_state.user)
            DataManager.add_notification(target, "follow", 
                f"@{st.session_state.user} started following you", st.session_state.user)
            message = "Following"
        
        profiles[st.session_state.user] = user_profile
        profiles[target] = target_profile
        DataManager.save_profiles(profiles)
        return True, message
    
    @staticmethod
    def is_following(target: str) -> bool:
        profile = DataManager.get_profile(st.session_state.user)
        return target in profile.get("following", [])

# ========== SESSION STATE ==========
def init_session():
    defaults = {
        'feed_posts': [],
        'stories': {},
        'auth': False,
        'user': "",
        'current_tab': "feed",  # feed, chats, explore, reels, profile
        'active_chat': None,
        'active_group': None,
        'active_channel': None,
        'rate_limiter': RateLimiter(),
        'show_create_post': False,
        'show_create_story': False,
        'show_new_chat': False,
        'show_new_group': False,
        'unread_notifications': 0,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if not st.session_state.feed_posts:
        st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories:
        st.session_state.stories = DataManager.get_stories()

init_session()

# Update on auth
if st.session_state.get('auth'):
    st.session_state.feed_posts = DataManager.get_feed_posts()
    st.session_state.stories = DataManager.get_stories()
    
    # Update last seen
    profiles = DataManager.get_profiles()
    if st.session_state.user in profiles:
        profiles[st.session_state.user]["last_seen"] = datetime.now().isoformat()
        DataManager.save_profiles(profiles)

# ========== CSS STYLES ==========
def inject_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    #MainMenu, footer, header { visibility: hidden; }
    section[data-testid="stSidebar"] { display: none; }
    
    html, body {
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        background: #0a0a1a;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%);
        height: 100vh !important;
        overflow: hidden !important;
    }
    
    .block-container {
        height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
    }
    
    /* Top Header */
    .app-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 56px;
        background: rgba(10, 10, 26, 0.95);
        backdrop-filter: blur(20px);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 0 1rem;
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .app-logo {
        font-size: 1.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-icons {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .notif-badge {
        position: relative;
    }
    
    .notif-count {
        position: absolute;
        top: -5px;
        right: -5px;
        background: #ef4444;
        color: white;
        border-radius: 50%;
        width: 16px;
        height: 16px;
        font-size: 0.6rem;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    /* Content Area */
    .main-content {
        position: fixed;
        top: 56px;
        bottom: 64px;
        left: 0;
        right: 0;
        overflow-y: auto;
        padding: 0.5rem;
    }
    
    .content-wrapper {
        max-width: 650px;
        margin: 0 auto;
    }
    
    /* Stories Bar */
    .stories-bar {
        display: flex;
        gap: 0.8rem;
        padding: 0.5rem 0;
        overflow-x: auto;
        margin-bottom: 0.5rem;
    }
    
    .stories-bar::-webkit-scrollbar { height: 0; }
    
    .story-circle {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.2rem;
        min-width: 65px;
        cursor: pointer;
    }
    
    .story-ring {
        width: 62px;
        height: 62px;
        border-radius: 50%;
        padding: 2px;
        background: linear-gradient(45deg, #f093fb, #f5576c, #fda085, #f093fb);
    }
    
    .story-ring.viewed {
        background: rgba(255,255,255,0.2);
    }
    
    .story-img {
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #0a0a1a;
    }
    
    .story-name {
        color: #94a3b8;
        font-size: 0.65rem;
        text-align: center;
        max-width: 65px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    /* Post Card */
    .post-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        margin-bottom: 0.8rem;
        overflow: hidden;
        transition: all 0.2s;
    }
    
    .post-card:hover {
        background: rgba(255,255,255,0.05);
    }
    
    .post-header {
        display: flex;
        align-items: center;
        padding: 0.7rem 1rem;
        gap: 0.7rem;
    }
    
    .post-avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
    }
    
    .post-avatar-placeholder {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 0.9rem;
    }
    
    .post-user {
        flex: 1;
    }
    
    .post-username {
        color: #f1f5f9;
        font-weight: 600;
        font-size: 0.85rem;
    }
    
    .post-time {
        color: #64748b;
        font-size: 0.65rem;
    }
    
    .verified-badge {
        color: #3b82f6;
        font-size: 0.7rem;
    }
    
    .post-text {
        color: #e2e8f0;
        font-size: 0.9rem;
        line-height: 1.5;
        padding: 0 1rem 0.5rem 1rem;
    }
    
    .post-media {
        width: 100%;
        max-height: 400px;
        object-fit: cover;
    }
    
    .post-actions {
        display: flex;
        align-items: center;
        padding: 0.5rem 1rem;
        gap: 0.3rem;
        border-top: 1px solid rgba(255,255,255,0.05);
    }
    
    .action-btn {
        color: #94a3b8;
        font-size: 1.2rem;
        cursor: pointer;
        padding: 0.2rem 0.5rem;
        border-radius: 8px;
        transition: all 0.2s;
        background: none;
        border: none;
        display: inline-flex;
        align-items: center;
        gap: 0.2rem;
    }
    
    .action-btn:hover {
        color: #818cf8;
        background: rgba(129,140,248,0.1);
    }
    
    .action-btn.liked {
        color: #ef4444;
    }
    
    /* Chat Styles */
    .chat-bubble {
        max-width: 80%;
        padding: 0.7rem 1rem;
        border-radius: 16px;
        margin: 0.2rem 0;
        font-size: 0.85rem;
        line-height: 1.4;
        animation: fadeIn 0.2s ease;
    }
    
    .chat-bubble.sent {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
        margin-left: auto;
    }
    
    .chat-bubble.received {
        background: rgba(255,255,255,0.08);
        color: #e2e8f0;
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    
    .chat-time {
        font-size: 0.6rem;
        opacity: 0.7;
        text-align: right;
        margin-top: 0.2rem;
    }
    
    /* User List Item */
    .user-item {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.7rem;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .user-item:hover {
        background: rgba(255,255,255,0.05);
    }
    
    .online-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 8px rgba(16,185,129,0.5);
    }
    
    /* Bottom Nav */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 64px;
        background: rgba(10, 10, 26, 0.95);
        backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex;
        align-items: center;
        justify-content: space-around;
        z-index: 1000;
        padding: 0 0.5rem;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        color: #64748b;
        font-size: 0.6rem;
        transition: all 0.2s;
        padding: 4px 8px;
        border-radius: 8px;
    }
    
    .nav-item.active {
        color: #818cf8;
    }
    
    .nav-icon {
        font-size: 1.4rem;
    }
    
    /* Modal */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.8);
        backdrop-filter: blur(8px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }
    
    .modal {
        background: rgba(20, 15, 40, 0.98);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        width: 90%;
        max-width: 500px;
        max-height: 85vh;
        overflow-y: auto;
        padding: 1.5rem;
        animation: slideUp 0.3s ease;
    }
    
    @keyframes slideUp {
        from { transform: translateY(50px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Button Overrides */
    .stButton > button {
        background: rgba(129,140,248,0.15) !important;
        border: 1px solid rgba(129,140,248,0.2) !important;
        color: #818cf8 !important;
        border-radius: 8px !important;
        padding: 0.3rem 0.8rem !important;
        font-size: 0.8rem !important;
        transition: all 0.2s !important;
        min-height: auto !important;
    }
    
    .stButton > button:hover {
        background: rgba(129,140,248,0.25) !important;
        transform: translateY(-1px);
    }
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.8rem !important;
        font-size: 0.85rem !important;
    }
    
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #667eea; border-radius: 2px; }
    </style>
    """, unsafe_allow_html=True)

# ========== UI COMPONENTS ==========
def avatar_html(username: str, size: int = 40) -> str:
    """Generate avatar HTML"""
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/jpeg;base64,{b64}" class="post-avatar" style="width:{size}px;height:{size}px;">'
    
    color = get_avatar_color(username)
    initial = username[0].upper() if username else "?"
    return f'<div class="post-avatar-placeholder" style="width:{size}px;height:{size}px;font-size:{size*0.4}px;background:{color};">{initial}</div>'

def render_header():
    """Render top header with notifications"""
    notifs = DataManager.get_notifications().get(st.session_state.user, [])
    unread = sum(1 for n in notifs if not n.get("read", False))
    
    st.markdown(f"""
    <div class="app-header">
        <div class="app-logo">🌐 SocialHub</div>
        <div class="header-icons">
            <span style="font-size:1.2rem;position:relative;">
                🔔
                {f'<span class="notif-count">{unread}</span>' if unread > 0 else ''}
            </span>
            {avatar_html(st.session_state.user, 32)}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stories_bar():
    """Render stories bar (Instagram style)"""
    stories = st.session_state.stories
    profiles = DataManager.get_profiles()
    
    # Get users with stories
    story_users = []
    for username, user_stories in stories.items():
        # Filter active stories
        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
        active = [s for s in user_stories if s["timestamp"] > cutoff]
        if active:
            viewed = all(st.session_state.user in s.get("views", []) for s in active)
            story_users.append({
                "username": username,
                "has_new": not viewed,
                "avatar": profiles.get(username, {}).get("avatar")
            })
    
    if not story_users and st.session_state.user:
        # Show "Your Story" option
        st.markdown(f"""
        <div class="stories-bar">
            <div class="story-circle">
                <div class="story-ring viewed">
                    {avatar_html(st.session_state.user, 58)}
                </div>
                <div class="story-name">Your Story</div>
            </div>
            <div style="color:#64748b;display:flex;align-items:center;font-size:0.8rem;">
                No stories yet • Tap + to add
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    html = '<div class="stories-bar">'
    
    # Your story
    html += f"""
    <div class="story-circle">
        <div class="story-ring viewed">
            {avatar_html(st.session_state.user, 58)}
        </div>
        <div class="story-name">Your Story</div>
    </div>
    """
    
    for su in story_users[:10]:
        ring_class = "story-ring" if su["has_new"] else "story-ring viewed"
        html += f"""
        <div class="story-circle">
            <div class="{ring_class}">
                {avatar_html(su['username'], 58)}
            </div>
            <div class="story-name">@{su['username'][:10]}</div>
        </div>
        """
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_post_card(post: Dict):
    """Render a feed post (Twitter/Instagram style)"""
    username = post.get("username", "")
    post_id = post.get("id", "")
    is_owner = username == st.session_state.user
    is_liked = st.session_state.user in post.get("likes", [])
    like_count = len(post.get("likes", []))
    
    profile = DataManager.get_profile(username)
    
    st.markdown(f"""
    <div class="post-card">
        <div class="post-header">
            {avatar_html(username)}
            <div class="post-user">
                <div class="post-username">
                    @{html.escape(username)}
                    {f'<span class="verified-badge">✓</span>' if profile.get('is_verified') else ''}
                </div>
                <div class="post-time">{format_time(post.get('timestamp', ''))}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if post.get("text"):
        st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
    
    if post.get("media"):
        st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post media">', unsafe_allow_html=True)
    
    # Actions row
    st.markdown('<div class="post-actions">', unsafe_allow_html=True)
    
    cols = st.columns([1, 1, 1, 1, 3, 2])
    
    with cols[0]:
        heart = "❤️" if is_liked else "🤍"
        if st.button(f"{heart} {like_count}", key=f"like_{post_id}"):
            PostHandler.like_post(post_id)
            st.rerun()
    
    with cols[1]:
        if st.button("💬", key=f"comment_{post_id}"):
            st.session_state[f"show_comments_{post_id}"] = not st.session_state.get(f"show_comments_{post_id}", False)
            st.rerun()
    
    with cols[2]:
        if st.button("🔄", key=f"repost_{post_id}"):
            st.info("Reposted!")
    
    with cols[3]:
        if st.button("📤", key=f"share_{post_id}"):
            st.info("Shared!")
    
    # Delete for owner
    if is_owner:
        with cols[5]:
            if st.button("🗑️", key=f"del_{post_id}"):
                PostHandler.delete_post(post_id)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Comments section
    if st.session_state.get(f"show_comments_{post_id}"):
        comments = CommentHandler.get_comments(post_id)
        st.markdown('<div style="padding:0 1rem;">', unsafe_allow_html=True)
        
        for comment in comments[-10:]:
            st.markdown(f"""
            <div style="display:flex;gap:0.5rem;margin:0.3rem 0;font-size:0.8rem;">
                <strong style="color:#f1f5f9;">@{html.escape(comment['username'])}</strong>
                <span style="color:#e2e8f0;">{html.escape(comment['text'])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Add comment
        with st.form(f"comment_form_{post_id}", clear_on_submit=True):
            ccol1, ccol2 = st.columns([4, 1])
            with ccol1:
                comment_text = st.text_input("Add comment", label_visibility="collapsed", placeholder="Write a comment...")
            with ccol2:
                if st.form_submit_button("Post"):
                    if comment_text:
                        CommentHandler.add_comment(post_id, comment_text)
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    """Render chat messaging interface (WhatsApp/Telegram style)"""
    active_chat = st.session_state.active_chat
    active_group = st.session_state.active_group
    active_channel = st.session_state.active_channel
    
    # Back button
    if st.button("← Back"):
        st.session_state.active_chat = None
        st.session_state.active_group = None
        st.session_state.active_channel = None
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if active_chat:
        # Direct Message
        messages = ChatHandler.get_messages(active_chat)
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:0.5rem;">
            {avatar_html(active_chat, 40)}
            <div>
                <div style="color:#f1f5f9;font-weight:600;">@{html.escape(active_chat)}</div>
                <div style="color:#64748b;font-size:0.7rem;">Online</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Messages
        for msg in messages:
            is_sent = msg.get("from") == st.session_state.user
            bubble = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;padding:0 0.5rem;">
                <div class="chat-bubble {bubble}">
                    {html.escape(msg.get('text', ''))}
                    <div class="chat-time">{format_time(msg['timestamp'])} {'✓✓' if is_sent and msg.get('read') else '✓' if is_sent else ''}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Input
        with st.form("dm_input", clear_on_submit=True):
            cols = st.columns([5, 1, 1])
            with cols[0]:
                text = st.text_input("Message", label_visibility="collapsed", placeholder="Message...")
            with cols[1]:
                file = st.file_uploader("📎", label_visibility="collapsed", type=['png','jpg','jpeg','gif'])
            with cols[2]:
                if st.form_submit_button("➤"):
                    media_data, media_name = None, None
                    if file:
                        media_data = base64.b64encode(file.read()).decode()
                        media_name = file.name
                    if text or media_data:
                        ChatHandler.send_message(active_chat, text, media_data, media_name)
                        st.rerun()
    
    elif active_group:
        # Group Chat
        groups = DataManager.get_group_chats()
        group = groups.get(active_group, {})
        messages = group.get("messages", [])
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:0.5rem;">
            <div class="post-avatar-placeholder" style="width:40px;height:40px;background:#667eea;">👥</div>
            <div>
                <div style="color:#f1f5f9;font-weight:600;">{html.escape(group.get('name', 'Group'))}</div>
                <div style="color:#64748b;font-size:0.7rem;">{len(group.get('members', []))} members</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for msg in messages:
            is_sent = msg.get("from") == st.session_state.user
            bubble = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;padding:0 0.5rem;">
                <div class="chat-bubble {bubble}">
                    {'' if is_sent else f'<div style="color:#818cf8;font-size:0.7rem;">@{html.escape(msg.get("from", ""))}</div>'}
                    {html.escape(msg.get('text', ''))}
                    <div class="chat-time">{format_time(msg['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form("group_input", clear_on_submit=True):
            cols = st.columns([5, 1])
            with cols[0]:
                text = st.text_input("Message", label_visibility="collapsed", placeholder="Message...")
            with cols[1]:
                if st.form_submit_button("➤"):
                    if text:
                        GroupHandler.send_group_message(active_group, text)
                        st.rerun()
    
    elif active_channel:
        # Channel (Telegram style)
        channels = DataManager.get_channels()
        channel = channels.get(active_channel, {})
        messages = channel.get("messages", [])
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:0.5rem;">
            <div class="post-avatar-placeholder" style="width:40px;height:40px;background:#f093fb;">📢</div>
            <div>
                <div style="color:#f1f5f9;font-weight:600;">{html.escape(channel.get('name', 'Channel'))}</div>
                <div style="color:#64748b;font-size:0.7rem;">{len(channel.get('subscribers', []))} subscribers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for msg in messages:
            st.markdown(f"""
            <div class="post-card" style="margin:0.5rem;">
                <div class="post-header">
                    {avatar_html(msg.get('from', ''))}
                    <div>
                        <div class="post-username">@{html.escape(msg.get('from', ''))}</div>
                        <div class="post-time">{format_time(msg['timestamp'])}</div>
                    </div>
                </div>
                <div class="post-text">{html.escape(msg.get('text', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Only admins can post
        if st.session_state.user in channel.get("admins", []):
            with st.form("channel_input", clear_on_submit=True):
                cols = st.columns([5, 1])
                with cols[0]:
                    text = st.text_input("Broadcast message", label_visibility="collapsed", placeholder="Post to channel...")
                with cols[1]:
                    if st.form_submit_button("📢"):
                        if text:
                            GroupHandler.send_group_message(active_channel, text, is_channel=True)
                            st.rerun()

def render_bottom_nav():
    """Render bottom navigation with 5 tabs"""
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
            is_active = "active" if current == tab else ""
            if st.button(icon, key=f"tab_{tab}", use_container_width=True):
                if tab == "create":
                    st.session_state.show_create_post = True
                else:
                    st.session_state.current_tab = tab
                    st.session_state.show_create_post = False
                    st.session_state.active_chat = None
                    st.session_state.active_group = None
                    st.session_state.active_channel = None
                st.rerun()
            
            if current == tab:
                st.markdown(f'<div style="text-align:center;color:#818cf8;font-size:0.55rem;margin-top:-8px;">{label}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_feed_page():
    """Main feed page"""
    render_stories_bar()
    
    # Create post quick bar
    col1, col2, col3 = st.columns([5, 1, 1])
    with col1:
        if st.button("What's on your mind? ✨", use_container_width=True):
            st.session_state.show_create_post = True
            st.rerun()
    with col2:
        if st.button("📷", help="Add Story"):
            st.session_state.show_create_story = True
            st.rerun()
    with col3:
        if st.button("📊", help="Create Poll"):
            st.info("Polls coming soon!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Feed posts
    posts = st.session_state.feed_posts
    if not posts:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#64748b;">
            <div style="font-size:3rem;">📝</div>
            <p style="font-size:1rem;">Welcome to SocialHub!</p>
            <p style="font-size:0.8rem;">Follow users to see their posts here</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for post in reversed(posts[-30:]):
            render_post_card(post)

def render_explore_page():
    """Explore page - discover users and content"""
    st.markdown('<h3 style="color:#f1f5f9;">🔍 Explore</h3>', unsafe_allow_html=True)
    
    # Search users
    search = st.text_input("Search users", placeholder="Search by username...", label_visibility="collapsed")
    
    users = DataManager.get_users()
    profiles = DataManager.get_profiles()
    
    # Filter users
    if search:
        filtered = {u: d for u, d in users.items() if search.lower() in u.lower()}
    else:
        filtered = users
    
    # Exclude current user
    filtered = {u: d for u, d in filtered.items() if u != st.session_state.user}
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if filtered:
        for username in list(filtered.keys())[:20]:
            profile = profiles.get(username, {})
            is_following = FollowHandler.is_following(username)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.7rem;">
                    {avatar_html(username, 40)}
                    <div>
                        <div style="color:#f1f5f9;font-weight:600;">@{html.escape(username)}</div>
                        <div style="color:#64748b;font-size:0.7rem;">{html.escape(profile.get('bio', '')[:50])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Following" if is_following else "Follow", key=f"follow_{username}"):
                    FollowHandler.follow_user(username)
                    st.rerun()
            
            with col3:
                if st.button("💬", key=f"msg_{username}", help="Message"):
                    st.session_state.active_chat = username
                    st.session_state.current_tab = "chats"
                    st.rerun()
            
            st.markdown("<hr style='border-color:rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    else:
        st.info("No users found")

def render_chats_page():
    """Chats page - DM, Groups, Channels"""
    st.markdown('<h3 style="color:#f1f5f9;">💬 Messages</h3>', unsafe_allow_html=True)
    
    # If in active conversation
    if st.session_state.active_chat or st.session_state.active_group or st.session_state.active_channel:
        render_chat_interface()
        return
    
    # Chat list
    tab1, tab2, tab3 = st.tabs(["Direct", "Groups", "Channels"])
    
    with tab1:
        # New chat button
        if st.button("💬 New Message", use_container_width=True):
            st.session_state.show_new_chat = True
            st.rerun()
        
        # Direct message list
        chats = ChatHandler.get_chat_list()
        if chats:
            for chat in chats:
                unread_badge = f'<span class="notif-count" style="position:static;display:inline-block;">{chat["unread"]}</span>' if chat["unread"] > 0 else ''
                
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem;cursor:pointer;"
                     onclick="document.getElementById('open_{chat['with_user']}').click();">
                    {avatar_html(chat['with_user'], 44)}
                    <div style="flex:1;">
                        <div style="display:flex;justify-content:space-between;">
                            <span style="color:#f1f5f9;font-weight:600;">@{html.escape(chat['with_user'])}</span>
                            <span style="color:#64748b;font-size:0.65rem;">{format_time(chat['last_time'])}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span style="color:#94a3b8;font-size:0.75rem;">{html.escape(chat['last_message'])}</span>
                            {unread_badge}
                        </div>
                    </div>
                </div>
                <hr style='border-color:rgba(255,255,255,0.03);margin:0;'>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open {chat['with_user']}", key=f"open_{chat['with_user']}", label_visibility="collapsed"):
                    st.session_state.active_chat = chat['with_user']
                    st.rerun()
        else:
            st.info("No conversations yet. Start a new chat!")
    
    with tab2:
        # New group button
        if st.button("👥 New Group", use_container_width=True):
            st.session_state.show_new_group = True
            st.rerun()
        
        groups = GroupHandler.get_user_groups()
        if groups:
            for group in groups:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem;">
                    <div class="post-avatar-placeholder" style="width:44px;height:44px;background:#667eea;">👥</div>
                    <div style="flex:1;">
                        <div style="color:#f1f5f9;font-weight:600;">{html.escape(group['name'])}</div>
                        <div style="color:#94a3b8;font-size:0.75rem;">{group['members']} members • {html.escape(group['last_message'])}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open {group['name']}", key=f"open_group_{group['id']}", label_visibility="collapsed"):
                    st.session_state.active_group = group['id']
                    st.rerun()
    
    with tab3:
        # New channel button
        if st.button("📢 New Channel", use_container_width=True):
            st.session_state.show_new_channel = True
            st.rerun()
        
        channels = GroupHandler.get_user_channels()
        if channels:
            for channel in channels:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.8rem;padding:0.5rem;">
                    <div class="post-avatar-placeholder" style="width:44px;height:44px;background:#f093fb;">📢</div>
                    <div style="flex:1;">
                        <div style="color:#f1f5f9;font-weight:600;">{html.escape(channel['name'])}</div>
                        <div style="color:#94a3b8;font-size:0.75rem;">{channel['subscribers']} subscribers</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Open {channel['name']}", key=f"open_channel_{channel['id']}", label_visibility="collapsed"):
                    st.session_state.active_channel = channel['id']
                    st.rerun()
    
    # New Chat Modal
    if st.session_state.get('show_new_chat'):
        with st.expander("New Message", expanded=True):
            all_users = list(DataManager.get_users().keys())
            available = [u for u in all_users if u != st.session_state.user]
            if available:
                selected = st.selectbox("Select user", available)
                if st.button("Start Chat", use_container_width=True):
                    st.session_state.active_chat = selected
                    st.session_state.show_new_chat = False
                    st.rerun()
    
    # New Group Modal
    if st.session_state.get('show_new_group'):
        with st.expander("New Group", expanded=True):
            name = st.text_input("Group name")
            all_users = list(DataManager.get_users().keys())
            available = [u for u in all_users if u != st.session_state.user]
            members = st.multiselect("Add members", available)
            if st.button("Create Group", use_container_width=True):
                if name and members:
                    success, msg = GroupHandler.create_group(name, members)
                    st.success(msg)
                    st.session_state.show_new_group = False
                    st.rerun()
    
    # New Channel Modal
    if st.session_state.get('show_new_channel'):
        with st.expander("New Channel", expanded=True):
            name = st.text_input("Channel name")
            all_users = list(DataManager.get_users().keys())
            available = [u for u in all_users if u != st.session_state.user]
            subscribers = st.multiselect("Add subscribers", available)
            if st.button("Create Channel", use_container_width=True):
                if name:
                    success, msg = GroupHandler.create_group(name, subscribers or [], is_channel=True)
                    st.success(msg)
                    st.session_state.show_new_channel = False
                    st.rerun()

def render_profile_page():
    """Profile page"""
    user = st.session_state.user
    profile = DataManager.get_profile(user)
    followers = len(profile.get("followers", []))
    following = len(profile.get("following", []))
    posts = [p for p in st.session_state.feed_posts if p["username"] == user]
    
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0;">
        {avatar_html(user, 80)}
        <h2 style="color:#f1f5f9;margin-top:0.5rem;">
            @{html.escape(user)}
            {f'<span class="verified-badge">✓</span>' if profile.get('is_verified') else ''}
        </h2>
        <p style="color:#94a3b8;">{html.escape(profile.get('bio', 'No bio yet'))}</p>
        <p style="color:#64748b;font-size:0.8rem;">{html.escape(profile.get('website', ''))}</p>
    </div>
    
    <div style="display:flex;justify-content:space-around;text-align:center;padding:0.8rem;">
        <div>
            <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{len(posts)}</div>
            <div style="color:#64748b;font-size:0.7rem;">Posts</div>
        </div>
        <div>
            <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{followers}</div>
            <div style="color:#64748b;font-size:0.7rem;">Followers</div>
        </div>
        <div>
            <div style="color:#f1f5f9;font-size:1.2rem;font-weight:700;">{following}</div>
            <div style="color:#64748b;font-size:0.7rem;">Following</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Edit profile
    with st.expander("✏️ Edit Profile"):
        with st.form("edit_profile"):
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=200)
            website = st.text_input("Website", value=profile.get("website", ""))
            avatar_file = st.file_uploader("Avatar", type=['png','jpg','jpeg'])
            
            if st.form_submit_button("Save", use_container_width=True):
                profiles = DataManager.get_profiles()
                profiles[user]["bio"] = sanitize(bio, 200) if bio else ""
                profiles[user]["website"] = sanitize(website, 100) if website else ""
                
                if avatar_file and avatar_file.size <= 5 * 1024 * 1024:
                    try:
                        img = Image.open(avatar_file)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            bg = Image.new('RGB', img.size, (255,255,255))
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
                        st.error("Failed to process image")
                
                DataManager.save_profiles(profiles)
                st.success("Profile updated!")
                st.rerun()
    
    # User's posts
    if posts:
        st.markdown("<h4 style='color:#f1f5f9;'>Your Posts</h4>", unsafe_allow_html=True)
        for post in reversed(posts[-20:]):
            render_post_card(post)
    
    # Sign out
    if st.button("🚪 Sign Out", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def render_create_modal():
    """Create post/story modal"""
    if not st.session_state.get('show_create_post'):
        return
    
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal">
            <h3 style="color:#f1f5f9;text-align:center;">Create</h3>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Post", "📷 Story"])
    
    with tab1:
        with st.form("create_post_form"):
            text = st.text_area("What's happening?", max_chars=2000, height=100)
            media = st.file_uploader("Add media", type=['png','jpg','jpeg','gif','webp'])
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post", use_container_width=True):
                    media_data, media_name = None, None
                    if media and media.size <= 10 * 1024 * 1024:
                        try:
                            file_bytes = media.read()
                            if validate_image(file_bytes):
                                media_data = base64.b64encode(file_bytes).decode()
                                media_name = media.name
                        except:
                            st.error("Failed to process media")
                    
                    if text.strip() or media_data:
                        success, msg = PostHandler.create_post(text, media_data, media_name)
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
        with st.form("create_story_form"):
            media = st.file_uploader("Story image", type=['png','jpg','jpeg','gif','webp'])
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post Story", use_container_width=True):
                    if media and media.size <= 10 * 1024 * 1024:
                        try:
                            file_bytes = media.read()
                            if validate_image(file_bytes):
                                media_data = base64.b64encode(file_bytes).decode()
                                success, msg = StoryHandler.create_story(media_data, media.name)
                                if success:
                                    st.session_state.show_create_post = False
                                    st.rerun()
                                else:
                                    st.error(msg)
                        except:
                            st.error("Failed to process image")
            
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_post = False
                    st.rerun()
    
    st.markdown('</div></div>', unsafe_allow_html=True)

# ========== AUTH ==========
def render_auth():
    """Authentication screen"""
    st.markdown("""
    <style>
    html, body { overflow: auto !important; height: auto !important; }
    </style>
    """, unsafe_allow_html=True)
    
    _, center, _ = st.columns([1, 2, 1])
    
    with center:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;">
            <div style="font-size:4rem;">🌐</div>
            <h1 style="font-size:2.5rem;background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                SocialHub Pro
            </h1>
            <p style="color:#64748b;">One App. Everything Social.</p>
            <p style="color:#94a3b8;font-size:0.8rem;">Feed • Stories • Chat • Groups • Channels</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            with st.form("login"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Sign In", use_container_width=True):
                    if username and password:
                        users = DataManager.get_users()
                        found = False
                        for un, data in users.items():
                            if un.lower() == username.lower():
                                found = True
                                if isinstance(data, dict):
                                    if DataManager.verify_password(password, data.get("password", ""), data.get("salt", "")):
                                        st.session_state.auth = True
                                        st.session_state.user = un
                                        st.session_state.feed_posts = DataManager.get_feed_posts()
                                        st.session_state.stories = DataManager.get_stories()
                                        st.rerun()
                                elif isinstance(data, str) and data == hashlib.sha256(password.encode()).hexdigest():
                                    # Upgrade old hash
                                    h, s = DataManager.hash_password(password)
                                    users[un] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
                                    DataManager.save_users(users)
                                    st.session_state.auth = True
                                    st.session_state.user = un
                                    st.rerun()
                                st.error("Wrong password")
                                break
                        if not found:
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
                        st.error("Password too short")
                    elif len(username) < 3 or len(username) > 20:
                        st.error("Username: 3-20 characters")
                    elif not username.isalnum():
                        st.error("Only letters and numbers")
                    else:
                        users = DataManager.get_users()
                        if username.lower() in [u.lower() for u in users]:
                            st.error("Username taken")
                        else:
                            h, s = DataManager.hash_password(password)
                            users[username] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
                            DataManager.save_users(users)
                            
                            profiles = DataManager.get_profiles()
                            profiles[username] = DataManager.get_profile(username)
                            DataManager.save_profiles(profiles)
                            
                            st.success("Account created! Sign in now.")

# ========== MAIN ==========
def main():
    init_session()
    inject_styles()
    
    if not st.session_state.get('auth'):
        render_auth()
    else:
        render_header()
        
        st.markdown('<div class="main-content"><div class="content-wrapper">', unsafe_allow_html=True)
        
        tab = st.session_state.get('current_tab', 'feed')
        
        if tab == "feed":
            render_feed_page()
        elif tab == "explore":
            render_explore_page()
        elif tab == "chats":
            render_chats_page()
        elif tab == "profile":
            render_profile_page()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # Modals
        if st.session_state.get('show_create_post'):
            render_create_modal()
        
        render_bottom_nav()

if __name__ == "__main__":
    main()
