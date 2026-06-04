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
st.set_page_config(
    page_title="SocialHub Pro", 
    page_icon="🌐", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

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

# Theme definitions with wallpapers
THEMES = {
    "midnight": {
        "name": "Midnight", "icon": "🌙",
        "bg": "#0a0a1a", "card_bg": "rgba(255,255,255,0.03)",
        "text": "#f1f5f9", "secondary": "#64748b", "accent": "#818cf8",
        "wallpaper": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"
    },
    "ocean": {
        "name": "Ocean", "icon": "🌊",
        "bg": "#0a192f", "card_bg": "rgba(255,255,255,0.05)",
        "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda",
        "wallpaper": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"
    },
    "sunset": {
        "name": "Sunset", "icon": "🌅",
        "bg": "#1a0a2e", "card_bg": "rgba(255,255,255,0.04)",
        "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081",
        "wallpaper": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)"
    },
    "forest": {
        "name": "Forest", "icon": "🌲",
        "bg": "#0a1a0a", "card_bg": "rgba(255,255,255,0.04)",
        "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50",
        "wallpaper": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)"
    },
    "neon": {
        "name": "Neon Night", "icon": "💜",
        "bg": "#0a0a2e", "card_bg": "rgba(255,255,255,0.04)",
        "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff",
        "wallpaper": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"
    },
    "coffee": {
        "name": "Coffee", "icon": "☕",
        "bg": "#1a0f0a", "card_bg": "rgba(255,255,255,0.04)",
        "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#8d6e63",
        "wallpaper": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)"
    }
}

# ========== UTILITY FUNCTIONS ==========
def validate_image(data: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp']
    except:
        return False

def sanitize_text(text: str, max_length: int = 2000) -> str:
    if not text: return ""
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    text = html.escape(str(text).strip())
    return text[:max_length]

def format_timestamp(ts: str) -> str:
    if not ts: return ""
    try:
        t = datetime.fromisoformat(ts)
        diff = (datetime.now() - t).total_seconds()
        if diff < 5: return "just now"
        elif diff < 60: return f"{int(diff)}s"
        elif diff < 3600: return f"{int(diff//60)}m"
        elif diff < 86400: return f"{int(diff//3600)}h"
        elif diff < 604800: return f"{int(diff//86400)}d"
        return t.strftime("%b %d")
    except:
        return ""

def generate_id() -> str:
    return str(uuid.uuid4())

def get_avatar_color(username: str) -> str:
    if not username: return AVATAR_COLORS[0]
    return AVATAR_COLORS[hash(username) % len(AVATAR_COLORS)]

def get_initials(username: str) -> str:
    if not username: return "?"
    parts = username.split('_')
    if len(parts) > 1: return (parts[0][0] + parts[1][0]).upper()[:2]
    return username[0].upper()

def atomic_save(filepath: pathlib.Path, data: Any) -> bool:
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        if filepath.exists():
            backup = BACKUP_DIR / f"{filepath.stem}_{int(time.time())}.bak"
            shutil.copy2(filepath, backup)
        tmp = filepath.with_suffix('.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(filepath)
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
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
        except: pass
        return default
    
    @staticmethod
    def save(filepath: pathlib.Path, data) -> bool:
        return atomic_save(filepath, data)
    
    @staticmethod
    def hash_password(pwd: str, salt: str = None) -> Tuple[str, str]:
        if salt is None: salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000)
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
            return False, "Username exists"
        users = DataManager.get_users()
        h, s = DataManager.hash_password(password)
        users[username] = {"password": h, "salt": s, "created_at": datetime.now().isoformat()}
        DataManager.save_users(users)
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager._default_profile(username)
        DataManager.save_profiles(profiles)
        return True, "Account created!"
    
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
                return False, "Wrong password"
        return False, "User not found"
    
    @staticmethod
    def _default_profile(username: str) -> Dict:
        return {
            "display_name": username, "bio": "", "avatar": None,
            "website": "", "location": "", "is_verified": False,
            "last_seen": "", "followers": [], "following": [],
            "blocked": [], "post_count": 0, "wallpaper": "midnight",
            "created_at": datetime.now().isoformat()
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
        for k, v in DataManager._default_profile(username).items():
            if k not in p: p[k] = v
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
        if len(data) > 500: data = data[-300:]
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
            if a: active[u] = a
        return active
    
    @staticmethod
    def get_direct_messages() -> Dict:
        return DataManager.load(DIRECT_MESSAGES_FILE, {})
    
    @staticmethod
    def save_direct_messages(data: Dict):
        DataManager.save(DIRECT_MESSAGES_FILE, data)
    
    @staticmethod
    def get_chat_id(u1: str, u2: str) -> str:
        return f"chat_{'_'.join(sorted([u1, u2]))}"
    
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
        if username not in notifs: notifs[username] = []
        notifs[username].insert(0, {
            "id": generate_id(), "type": ntype, "message": message,
            "from_user": from_user, "timestamp": datetime.now().isoformat(), "read": False
        })
        notifs[username] = notifs[username][:50]
        DataManager.save_notifications(notifs)
    
    @staticmethod
    def get_unread_count(username: str) -> int:
        notifs = DataManager.get_notifications().get(username, [])
        return sum(1 for n in notifs if not n.get("read"))
    
    @staticmethod
    def get_online_users() -> List[str]:
        profiles = DataManager.get_profiles()
        now = datetime.now()
        online = []
        for u, p in profiles.items():
            if p.get("last_seen"):
                try:
                    if (now - datetime.fromisoformat(p["last_seen"])).seconds < 300:
                        online.append(u)
                except: pass
        return online

# ========== HANDLERS ==========
class PostHandler:
    @staticmethod
    def create(text: str, media_data: str = None, media_name: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_POST_LENGTH) if text else ""
        if not text and not media_data: return False, "Empty post"
        
        posts = DataManager.get_feed_posts()
        post = {
            "id": generate_id(), "username": st.session_state.user,
            "text": text, "timestamp": datetime.now().isoformat(),
            "type": "post", "likes": [], "reposts": 0
        }
        if media_data:
            post["media"] = media_data
            post["media_name"] = sanitize_text(media_name, 100) if media_name else "file"
            post["media_type"] = "image" if media_name and media_name.lower().endswith(('.png','.jpg','.jpeg','.gif','.webp')) else "file"
        
        posts.append(post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        
        p = DataManager.get_profile(st.session_state.user)
        p["post_count"] = p.get("post_count", 0) + 1
        DataManager.save_profiles(DataManager.get_profiles())
        return True, "Posted!"
    
    @staticmethod
    def like(post_id: str):
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id:
                u = st.session_state.user
                if u in post.get("likes", []): post["likes"].remove(u)
                else: post["likes"].append(u)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return
    
    @staticmethod
    def delete(post_id: str) -> bool:
        posts = DataManager.get_feed_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True
        return False
    
    @staticmethod
    def create_poll(question: str, options: List[str]) -> Tuple[bool, str]:
        question = sanitize_text(question, 500)
        options = [sanitize_text(o, 100) for o in options if o.strip()]
        if len(options) < 2: return False, "Need 2+ options"
        
        posts = DataManager.get_feed_posts()
        posts.append({
            "id": generate_id(), "username": st.session_state.user,
            "text": question, "timestamp": datetime.now().isoformat(),
            "type": "poll", "poll_data": {"options": {o: [] for o in options}, "total_votes": 0}
        })
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
                    if u in v: v.remove(u); pd["total_votes"] -= 1
                if option in pd["options"]:
                    pd["options"][option].append(u); pd["total_votes"] += 1
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return

class StoryHandler:
    @staticmethod
    def create(media_data: str, media_name: str) -> Tuple[bool, str]:
        stories = DataManager.get_stories()
        u = st.session_state.user
        if u not in stories: stories[u] = []
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        stories[u] = [s for s in stories[u] if s["timestamp"] > cutoff]
        stories[u].append({
            "id": generate_id(), "username": u, "media": media_data,
            "media_name": sanitize_text(media_name, 100),
            "timestamp": datetime.now().isoformat(), "views": []
        })
        DataManager.save_stories(stories)
        st.session_state.stories = stories
        return True, "Story posted!"

class ChatHandler:
    @staticmethod
    def send(to_user: str, text: str) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text: return False, "Empty message"
        
        from_user = st.session_state.user
        chat_id = DataManager.get_chat_id(from_user, to_user)
        dms = DataManager.get_direct_messages()
        
        if chat_id not in dms:
            dms[chat_id] = {"participants": [from_user, to_user], "messages": [], "created_at": datetime.now().isoformat()}
        
        dms[chat_id]["messages"].append({
            "id": generate_id(), "from": from_user, "to": to_user,
            "text": text, "timestamp": datetime.now().isoformat(), "read": False
        })
        DataManager.save_direct_messages(dms)
        DataManager.add_notification(to_user, "message", f"New message from @{from_user}", from_user)
        return True, "Sent!"
    
    @staticmethod
    def get_messages(with_user: str) -> List:
        chat_id = DataManager.get_chat_id(st.session_state.user, with_user)
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            for m in dms[chat_id]["messages"]:
                if m.get("to") == st.session_state.user: m["read"] = True
            DataManager.save_direct_messages(dms)
            return dms[chat_id]["messages"]
        return []
    
    @staticmethod
    def get_chat_list() -> List[Dict]:
        u = st.session_state.user
        dms = DataManager.get_direct_messages()
        online = DataManager.get_online_users()
        chats = []
        for cid, cd in dms.items():
            if u in cd["participants"]:
                other = [p for p in cd["participants"] if p != u][0]
                msgs = cd["messages"]
                last = msgs[-1] if msgs else None
                unread = sum(1 for m in msgs if m.get("to") == u and not m.get("read"))
                chats.append({
                    "with_user": other,
                    "last_message": last["text"][:40] if last and last.get("text") else "📷 Media",
                    "last_time": last["timestamp"] if last else cd["created_at"],
                    "unread": unread, "is_online": other in online
                })
        chats.sort(key=lambda x: x["last_time"], reverse=True)
        return chats

class GroupHandler:
    @staticmethod
    def create_group(name: str, members: List[str], is_channel: bool = False) -> Tuple[bool, str]:
        name = sanitize_text(name, 50)
        if not name: return False, "Name required"
        all_members = list(set(members + [st.session_state.user]))
        gid = f"{'channel' if is_channel else 'group'}_{generate_id()[:8]}"
        
        data = {"name": name, "admins": [st.session_state.user], "messages": [], "created_at": datetime.now().isoformat()}
        
        if is_channel:
            data["owner"] = st.session_state.user
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
                    DataManager.add_notification(m, "group_invite", f"Added to '{name}'", st.session_state.user)
        return True, f"{'Channel' if is_channel else 'Group'} created!"
    
    @staticmethod
    def send_message(group_id: str, text: str, is_channel: bool = False) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text: return False, "Empty message"
        
        data = DataManager.get_channels() if is_channel else DataManager.get_group_chats()
        if group_id not in data: return False, "Not found"
        
        data[group_id]["messages"].append({
            "id": generate_id(), "from": st.session_state.user,
            "text": text, "timestamp": datetime.now().isoformat()
        })
        
        if is_channel: DataManager.save_channels(data)
        else: DataManager.save_group_chats(data)
        return True, "Sent!"
    
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
                    "id": gid, "name": gd["name"], "members": len(gd.get("members", [])),
                    "last_message": last["text"][:30] if last and last.get("text") else "No messages",
                    "last_time": last["timestamp"] if last else gd["created_at"]
                })
        result.sort(key=lambda x: x["last_time"], reverse=True)
        return result
    
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
                    "id": cid, "name": cd["name"], "subscribers": len(cd.get("subscribers", [])),
                    "last_message": last["text"][:30] if last and last.get("text") else "No posts",
                    "last_time": last["timestamp"] if last else cd["created_at"]
                })
        result.sort(key=lambda x: x["last_time"], reverse=True)
        return result
    
    @staticmethod
    def get_group_messages(group_id: str) -> List:
        return DataManager.get_group_chats().get(group_id, {}).get("messages", [])
    
    @staticmethod
    def get_channel_messages(channel_id: str) -> List:
        return DataManager.get_channels().get(channel_id, {}).get("messages", [])

class CommentHandler:
    @staticmethod
    def add(post_id: str, text: str) -> Tuple[bool, str]:
        text = sanitize_text(text, 500)
        if not text: return False, "Empty comment"
        comments = DataManager.get_comments()
        if post_id not in comments: comments[post_id] = []
        comments[post_id].append({
            "id": generate_id(), "username": st.session_state.user,
            "text": text, "timestamp": datetime.now().isoformat(), "likes": []
        })
        DataManager.save_comments(comments)
        return True, "Comment added!"
    
    @staticmethod
    def get(post_id: str) -> List:
        return DataManager.get_comments().get(post_id, [])

class FollowHandler:
    @staticmethod
    def follow(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user: return False, "Cannot follow yourself"
        profiles = DataManager.get_profiles()
        up = DataManager.get_profile(st.session_state.user)
        tp = DataManager.get_profile(target)
        
        for p in [up, tp]:
            if "following" not in p: p["following"] = []
            if "followers" not in p: p["followers"] = []
            if "blocked" not in p: p["blocked"] = []
        
        if target in up["following"]:
            up["following"].remove(target)
            tp["followers"].remove(st.session_state.user)
            action = "Unfollowed"
        else:
            up["following"].append(target)
            tp["followers"].append(st.session_state.user)
            action = "Following"
            DataManager.add_notification(target, "follow", f"@{st.session_state.user} followed you", st.session_state.user)
        
        profiles[st.session_state.user] = up
        profiles[target] = tp
        DataManager.save_profiles(profiles)
        return True, f"{action}!"
    
    @staticmethod
    def is_following(target: str) -> bool:
        return target in DataManager.get_profile(st.session_state.user).get("following", [])

# ========== SESSION STATE ==========
def init_session():
    defaults = {
        'feed_posts': [], 'stories': {}, 'auth': False, 'user': "",
        'current_tab': "feed", 'active_chat': None, 'active_group': None,
        'active_channel': None, 'show_create_modal': False,
        'show_new_chat': False, 'show_new_group': False, 'show_new_channel': False,
        'show_comments_for': None, 'selected_theme': 'midnight'
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
    if not st.session_state.feed_posts:
        st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories:
        st.session_state.stories = DataManager.get_stories()

init_session()
if st.session_state.get('auth'):
    st.session_state.feed_posts = DataManager.get_feed_posts()
    st.session_state.stories = DataManager.get_stories()
    DataManager.update_last_seen(st.session_state.user)

# ========== GET CURRENT THEME ==========
def get_theme() -> Dict:
    theme_key = st.session_state.get('selected_theme', 'midnight')
    # Also check user's saved wallpaper preference
    if st.session_state.get('auth'):
        profile = DataManager.get_profile(st.session_state.user)
        saved_theme = profile.get('wallpaper', 'midnight')
        if saved_theme in THEMES:
            theme_key = saved_theme
    return THEMES.get(theme_key, THEMES['midnight'])

# ========== CSS STYLES ==========
def inject_styles():
    theme = get_theme()
    
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    #MainMenu, footer, header {{ visibility: hidden !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stDeployButton, [data-testid="stDecoration"] {{ display: none !important; }}
    
    html, body {{
        overflow: hidden !important;
        height: 100vh !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    .stApp {{
        background: {theme['wallpaper']} !important;
        background-attachment: fixed !important;
        height: 100vh !important;
        overflow: hidden !important;
    }}
    
    .block-container {{
        height: 100vh !important;
        overflow: hidden !important;
        padding: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Fixed Top Header */
    .app-header {{
        position: fixed;
        top: 0; left: 0; right: 0;
        height: 50px;
        background: {theme['bg']}ee;
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
        font-size: 1.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    .header-actions {{
        display: flex;
        align-items: center;
        gap: 1rem;
        color: {theme['text']};
    }}
    
    .badge {{
        background: #ef4444;
        color: white;
        border-radius: 50%;
        padding: 1px 6px;
        font-size: 0.6rem;
        font-weight: 700;
        margin-left: -5px;
        margin-top: -10px;
        position: absolute;
    }}
    
    /* Scrollable Content Area */
    .main-content {{
        position: fixed;
        top: 50px;
        bottom: 60px;
        left: 0;
        right: 0;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0.5rem 1rem;
    }}
    
    .content-wrapper {{
        max-width: 650px;
        margin: 0 auto;
        padding-bottom: 0.5rem;
    }}
    
    /* Fixed Bottom Navigation */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: {theme['bg']}ee;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex;
        align-items: center;
        justify-content: space-around;
        z-index: 1000;
    }}
    
    .nav-btn {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        cursor: pointer;
        color: {theme['secondary']};
        font-size: 0.55rem;
        font-weight: 500;
        padding: 6px 10px;
        border-radius: 8px;
        transition: all 0.2s;
        background: none;
        border: none;
        width: 100%;
    }}
    
    .nav-btn:hover {{
        color: {theme['accent']};
        background: rgba(255,255,255,0.05);
    }}
    
    .nav-btn.active {{
        color: {theme['accent']};
    }}
    
    .nav-icon {{
        font-size: 1.3rem;
        transition: transform 0.2s;
    }}
    
    .nav-btn:active .nav-icon {{
        transform: scale(0.9);
    }}
    
    /* Cards */
    .card {{
        background: {theme['card_bg']};
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        margin-bottom: 0.7rem;
        overflow: hidden;
    }}
    
    .card-header {{
        display: flex;
        align-items: center;
        padding: 0.6rem 0.8rem;
        gap: 0.6rem;
    }}
    
    .avatar {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid {theme['accent']}44;
    }}
    
    .avatar-placeholder {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 0.8rem;
        border: 2px solid {theme['accent']}44;
    }}
    
    .username-text {{
        color: {theme['text']};
        font-weight: 600;
        font-size: 0.8rem;
    }}
    
    .timestamp {{
        color: {theme['secondary']};
        font-size: 0.6rem;
    }}
    
    .post-text {{
        color: #e2e8f0;
        font-size: 0.85rem;
        line-height: 1.5;
        padding: 0 0.8rem 0.5rem 0.8rem;
    }}
    
    .post-media {{
        width: 100%;
        max-height: 350px;
        object-fit: cover;
    }}
    
    .post-actions {{
        display: flex;
        align-items: center;
        padding: 0.4rem 0.8rem;
        gap: 0.2rem;
        border-top: 1px solid rgba(255,255,255,0.04);
    }}
    
    /* Chat bubbles */
    .chat-bubble {{
        max-width: 80%;
        padding: 0.6rem 0.9rem;
        border-radius: 14px;
        font-size: 0.82rem;
        line-height: 1.4;
        margin: 0.15rem 0;
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
    
    /* Stories */
    .stories-row {{
        display: flex;
        gap: 0.7rem;
        padding: 0.4rem 0;
        overflow-x: auto;
        margin-bottom: 0.5rem;
    }}
    
    .stories-row::-webkit-scrollbar {{ height: 0; }}
    
    .story-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.2rem;
        min-width: 62px;
        cursor: pointer;
    }}
    
    .story-ring {{
        width: 56px;
        height: 56px;
        border-radius: 50%;
        padding: 2px;
        background: linear-gradient(45deg, #f093fb, #f5576c, #fda085);
    }}
    
    .story-ring.viewed {{
        background: rgba(255,255,255,0.2);
    }}
    
    .story-ring-inner {{
        width: 100%;
        height: 100%;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid {theme['bg']};
    }}
    
    .story-ring-inner-placeholder {{
        width: 100%;
        height: 100%;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: white;
        font-size: 1rem;
        border: 2px solid {theme['bg']};
    }}
    
    .story-name {{
        color: {theme['secondary']};
        font-size: 0.6rem;
        max-width: 60px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    /* User list item */
    .user-row {{
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.6rem 0.7rem;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s;
    }}
    
    .user-row:hover {{
        background: rgba(255,255,255,0.04);
    }}
    
    .online-dot {{
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 6px rgba(16,185,129,0.5);
        flex-shrink: 0;
    }}
    
    .unread-count {{
        background: {theme['accent']};
        color: white;
        border-radius: 10px;
        padding: 1px 7px;
        font-size: 0.65rem;
        font-weight: 600;
    }}
    
    /* Modal */
    .modal-overlay {{
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.75);
        backdrop-filter: blur(6px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
    }}
    
    .modal-box {{
        background: {theme['bg']}fa;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 18px;
        width: 92%;
        max-width: 480px;
        max-height: 80vh;
        overflow-y: auto;
        padding: 1.2rem;
    }}
    
    /* Theme grid */
    .theme-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.6rem;
        padding: 0.5rem 0;
    }}
    
    .theme-card {{
        border-radius: 12px;
        padding: 1.2rem 0.5rem;
        text-align: center;
        cursor: pointer;
        border: 2px solid transparent;
        transition: all 0.2s;
    }}
    
    .theme-card:hover {{
        transform: scale(1.03);
    }}
    
    .theme-card.selected {{
        border-color: {theme['accent']};
        box-shadow: 0 0 15px {theme['accent']}44;
    }}
    
    /* Streamlit overrides */
    .stButton > button {{
        background: {theme['accent']}22 !important;
        border: 1px solid {theme['accent']}33 !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
        padding: 0.3rem 0.7rem !important;
        font-size: 0.78rem !important;
        transition: all 0.2s !important;
        min-height: auto !important;
    }}
    
    .stButton > button:hover {{
        background: {theme['accent']}33 !important;
        border-color: {theme['accent']}55 !important;
    }}
    
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: {theme['text']} !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.7rem !important;
        font-size: 0.82rem !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: {theme['secondary']} !important;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.3rem;
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {theme['secondary']};
        border-radius: 6px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
    }}
    
    .stTabs [aria-selected="true"] {{
        color: {theme['accent']};
        background: {theme['accent']}15;
    }}
    
    .stExpander {{
        background: {theme['card_bg']} !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
    }}
    
    ::-webkit-scrollbar {{ width: 3px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {theme['accent']}44; border-radius: 2px; }}
    </style>
    """, unsafe_allow_html=True)

# ========== AVATAR RENDERER ==========
def render_avatar(username: str, size: int = 34) -> str:
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f'<img src="data:image/jpeg;base64,{b64}" class="avatar" style="width:{size}px;height:{size}px;" alt="{username}">'
        except: pass
    color = get_avatar_color(username)
    return f'<div class="avatar-placeholder" style="width:{size}px;height:{size}px;font-size:{size*0.38}px;background:{color};">{get_initials(username)}</div>'

def render_story_ring(username: str, size: int = 56, has_new: bool = False) -> str:
    ring_class = "story-ring" if has_new else "story-ring viewed"
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<div class="{ring_class}"><img src="data:image/jpeg;base64,{b64}" class="story-ring-inner" alt="{username}"></div>'
    color = get_avatar_color(username)
    return f'<div class="{ring_class}"><div class="story-ring-inner-placeholder" style="font-size:{size*0.32}px;background:{color};">{get_initials(username)}</div></div>'

# ========== UI COMPONENTS ==========
def render_header():
    user = st.session_state.user
    unread = DataManager.get_unread_count(user)
    
    st.markdown(f"""
    <div class="app-header">
        <div class="app-logo">🌐 SocialHub</div>
        <div class="header-actions">
            <span style="position:relative;">
                🔔
                {f'<span class="badge">{unread}</span>' if unread > 0 else ''}
            </span>
            {render_avatar(user, 28)}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_stories_bar():
    user = st.session_state.user
    active = DataManager.get_active_stories()
    
    html = '<div class="stories-row">'
    
    has_own = user in active
    html += f"""
    <div class="story-item">
        {render_story_ring(user, 56, not has_own)}
        <div class="story-name">You</div>
    </div>
    """
    
    for u, ss in active.items():
        if u != user:
            has_new = any(st.session_state.user not in s.get("views", []) for s in ss)
            html += f"""
            <div class="story-item">
                {render_story_ring(u, 56, has_new)}
                <div class="story-name">@{u[:9]}</div>
            </div>
            """
    
    if len(active) <= 1:
        html += '<div style="color:#64748b;display:flex;align-items:center;font-size:0.75rem;padding-left:0.5rem;">No stories yet</div>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def render_post_card(post: Dict):
    username = post.get("username", "")
    pid = post.get("id", "")
    is_owner = username == st.session_state.user
    is_liked = st.session_state.user in post.get("likes", [])
    likes = len(post.get("likes", []))
    
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            {render_avatar(username)}
            <div style="flex:1;">
                <div class="username-text">@{html.escape(username)}</div>
                <div class="timestamp">{format_timestamp(post.get('timestamp', ''))}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if post.get("text"):
        st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
    
    if post.get("media") and post.get("media_type") == "image":
        st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post">', unsafe_allow_html=True)
    
    st.markdown('<div class="post-actions">', unsafe_allow_html=True)
    
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 2])
    
    with c1:
        if st.button(f"{'❤️' if is_liked else '🤍'} {likes}", key=f"lk_{pid}"):
            PostHandler.like(pid)
            st.rerun()
    
    with c2:
        if st.button("💬", key=f"cm_{pid}"):
            st.session_state.show_comments_for = None if st.session_state.show_comments_for == pid else pid
            st.rerun()
    
    with c3:
        if st.button("🔄", key=f"rp_{pid}"):
            st.toast("Reposted!")
    
    with c4:
        if st.button("📤", key=f"sh_{pid}"):
            st.toast("Link copied!")
    
    if is_owner:
        with c5:
            if st.button("🗑️", key=f"dl_{pid}"):
                PostHandler.delete(pid)
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.show_comments_for == pid:
        render_comments(pid)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(post: Dict):
    username = post.get("username", "")
    pid = post.get("id", "")
    pd = post.get("poll_data", {})
    total = pd.get("total_votes", 0)
    options = pd.get("options", {})
    
    st.markdown(f"""
    <div class="card">
        <div class="card-header">
            {render_avatar(username)}
            <div style="flex:1;">
                <div class="username-text">@{html.escape(username)}</div>
                <div class="timestamp">📊 Poll • {format_timestamp(post.get('timestamp', ''))}</div>
            </div>
        </div>
        <div class="post-text" style="font-weight:600;">{html.escape(post.get('text', ''))}</div>
        <div style="padding:0 0.8rem 0.5rem 0.8rem;">
    """, unsafe_allow_html=True)
    
    for opt, voters in options.items():
        pct = (len(voters) / total * 100) if total > 0 else 0
        voted = st.session_state.user in voters
        
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:0.4rem 0.6rem;margin:0.2rem 0;cursor:pointer;{'border:1px solid #818cf8;' if voted else ''}">
            <div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.8rem;">
                <span>{'✓ ' if voted else ''}{html.escape(opt)}</span>
                <span>{pct:.0f}%</span>
            </div>
            <div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;margin-top:3px;">
                <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:2px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Vote {html.escape(opt[:15])}", key=f"pv_{pid}_{opt[:10]}"):
            PostHandler.vote_poll(pid, opt)
            st.rerun()
    
    st.markdown(f'<div style="color:#64748b;font-size:0.65rem;margin-top:0.3rem;">{total} votes</div></div></div>', unsafe_allow_html=True)

def render_comments(post_id: str):
    comments = CommentHandler.get(post_id)
    st.markdown('<div style="padding:0.3rem 0.8rem;border-top:1px solid rgba(255,255,255,0.04);">', unsafe_allow_html=True)
    
    for c in comments[-15:]:
        st.markdown(f"""
        <div style="margin:0.3rem 0;display:flex;gap:0.4rem;align-items:flex-start;">
            {render_avatar(c['username'], 22)}
            <div>
                <span style="color:#f1f5f9;font-weight:600;font-size:0.72rem;">@{html.escape(c['username'])}</span>
                <span style="color:#e2e8f0;font-size:0.75rem;">{html.escape(c['text'])}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with st.form(f"cmf_{post_id}", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            txt = st.text_input("Comment", label_visibility="collapsed", placeholder="Add comment...", key=f"ci_{post_id}")
        with c2:
            if st.form_submit_button("Post"):
                if txt.strip():
                    CommentHandler.add(post_id, txt)
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    active_chat = st.session_state.get('active_chat')
    active_group = st.session_state.get('active_group')
    active_channel = st.session_state.get('active_channel')
    
    if st.button("← Back", use_container_width=True, key="back_btn"):
        st.session_state.active_chat = None
        st.session_state.active_group = None
        st.session_state.active_channel = None
        st.rerun()
    
    if active_chat:
        msgs = ChatHandler.get_messages(active_chat)
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;margin-bottom:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);">
            {render_avatar(active_chat, 36)}
            <div class="username-text">@{html.escape(active_chat)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        for m in msgs:
            sent = m.get("from") == st.session_state.user
            cls = "sent" if sent else "received"
            align = "flex-end" if sent else "flex-start"
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:{align};padding:0 0.3rem;">
                <div class="chat-bubble {cls}">
                    {html.escape(m.get('text', ''))}
                    <div style="font-size:0.6rem;opacity:0.7;text-align:right;">{format_timestamp(m['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"dmf_{active_chat}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input("Message", label_visibility="collapsed", placeholder="Type...", key=f"dmt_{active_chat}")
            with c2:
                if st.form_submit_button("➤"):
                    if txt.strip():
                        ChatHandler.send(active_chat, txt)
                        st.rerun()
    
    elif active_group:
        msgs = GroupHandler.get_group_messages(active_group)
        groups = DataManager.get_group_chats()
        g = groups.get(active_group, {})
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;margin-bottom:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);">
            <div class="avatar-placeholder" style="width:36px;height:36px;background:#667eea;">👥</div>
            <div>
                <div class="username-text">{html.escape(g.get('name', 'Group'))}</div>
                <div style="color:#64748b;font-size:0.6rem;">{len(g.get('members', []))} members</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for m in msgs:
            sent = m.get("from") == st.session_state.user
            cls = "sent" if sent else "received"
            align = "flex-end" if sent else "flex-start"
            st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:{align};padding:0 0.3rem;">
                <div class="chat-bubble {cls}">
                    {'' if sent else f'<div style="color:#818cf8;font-size:0.65rem;">@{html.escape(m.get("from",""))}</div>'}
                    {html.escape(m.get('text', ''))}
                    <div style="font-size:0.6rem;opacity:0.7;text-align:right;">{format_timestamp(m['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"grpf_{active_group}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input("Message", label_visibility="collapsed", placeholder="Type...", key=f"grpt_{active_group}")
            with c2:
                if st.form_submit_button("➤"):
                    if txt.strip():
                        GroupHandler.send_message(active_group, txt)
                        st.rerun()
    
    elif active_channel:
        msgs = GroupHandler.get_channel_messages(active_channel)
        channels = DataManager.get_channels()
        ch = channels.get(active_channel, {})
        is_admin = st.session_state.user in ch.get("admins", [])
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;margin-bottom:0.5rem;border-bottom:1px solid rgba(255,255,255,0.05);">
            <div class="avatar-placeholder" style="width:36px;height:36px;background:#f093fb;">📢</div>
            <div>
                <div class="username-text">{html.escape(ch.get('name', 'Channel'))}</div>
                <div style="color:#64748b;font-size:0.6rem;">{len(ch.get('subscribers', []))} subscribers</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for m in msgs:
            st.markdown(f"""
            <div class="card" style="margin:0.4rem 0;padding:0.5rem 0.7rem;">
                <div style="display:flex;align-items:center;gap:0.5rem;">
                    {render_avatar(m.get('from', ''), 28)}
                    <div>
                        <div class="username-text">@{html.escape(m.get('from', ''))}</div>
                        <div class="timestamp">{format_timestamp(m['timestamp'])}</div>
                    </div>
                </div>
                <div style="color:#e2e8f0;font-size:0.82rem;margin-top:0.3rem;">{html.escape(m.get('text', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if is_admin:
            with st.form(f"chnf_{active_channel}", clear_on_submit=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    txt = st.text_input("Broadcast", label_visibility="collapsed", placeholder="Post to channel...", key=f"chnt_{active_channel}")
                with c2:
                    if st.form_submit_button("📢"):
                        if txt.strip():
                            GroupHandler.send_message(active_channel, txt, is_channel=True)
                            st.rerun()

def render_create_modal():
    if not st.session_state.get('show_create_modal'): return
    
    st.markdown('<div class="modal-overlay"><div class="modal-box">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#f1f5f9;text-align:center;margin-bottom:0.8rem;">Create</h3>', unsafe_allow_html=True)
    
    t1, t2, t3 = st.tabs(["📝 Post", "📊 Poll", "📷 Story"])
    
    with t1:
        with st.form("cpf", clear_on_submit=True):
            text = st.text_area("What's happening?", max_chars=MAX_POST_LENGTH, height=80)
            media = st.file_uploader("Image", type=['png','jpg','jpeg','gif','webp'], key="mup")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post", use_container_width=True):
                    md, mn = None, None
                    if media and media.size <= MAX_FILE_SIZE:
                        fb = media.read()
                        if validate_image(fb):
                            md = base64.b64encode(fb).decode()
                            mn = media.name
                    if text.strip() or md:
                        PostHandler.create(text, md, mn)
                        st.session_state.show_create_modal = False
                        st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    with t2:
        with st.form("cplf", clear_on_submit=True):
            q = st.text_input("Question", max_chars=500)
            opts = st.text_area("Options (one per line)", height=80, placeholder="Option 1\nOption 2\nOption 3")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Create Poll", use_container_width=True):
                    if q and opts:
                        olist = [o.strip() for o in opts.split('\n') if o.strip()]
                        if len(olist) >= 2:
                            PostHandler.create_poll(q, olist)
                            st.session_state.show_create_modal = False
                            st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
    
    with t3:
        with st.form("csf", clear_on_submit=True):
            sm = st.file_uploader("Story image", type=['png','jpg','jpeg','gif','webp'], key="sup")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("Post Story", use_container_width=True):
                    if sm and sm.size <= MAX_FILE_SIZE:
                        fb = sm.read()
                        if validate_image(fb):
                            StoryHandler.create(base64.b64encode(fb).decode(), sm.name)
                            st.session_state.show_create_modal = False
                            st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True):
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
            active = "active" if current == tab else ""
            if st.button(icon, key=f"nav_{tab}", use_container_width=True, help=label):
                if tab == "create":
                    st.session_state.show_create_modal = True
                else:
                    st.session_state.current_tab = tab
                    st.session_state.show_create_modal = False
                    st.session_state.active_chat = None
                    st.session_state.active_group = None
                    st.session_state.active_channel = None
                st.rerun()
            if current == tab:
                st.markdown(f'<div style="text-align:center;color:{theme["accent"]};font-size:0.5rem;margin-top:-6px;">{label}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== PAGES ==========
def render_feed_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    render_stories_bar()
    
    # Quick post
    if st.button("✨ What's on your mind?", use_container_width=True, key="qp"):
        st.session_state.show_create_modal = True
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    posts = st.session_state.feed_posts
    if not posts:
        st.markdown("""
        <div style="text-align:center;padding:2rem;color:#64748b;">
            <div style="font-size:3rem;">📝</div>
            <p>No posts yet. Follow users or create your first post!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for post in reversed(posts[-40:]):
            if post.get("type") == "poll": render_poll_card(post)
            else: render_post_card(post)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_explore_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:0.5rem;">🔍 Explore</h3>', unsafe_allow_html=True)
    
    search = st.text_input("Search", placeholder="Search users...", label_visibility="collapsed", key="es")
    users = list(DataManager.get_users().keys())
    filtered = [u for u in users if u != st.session_state.user and (not search or search.lower() in u.lower())]
    
    for u in filtered[:25]:
        is_following = FollowHandler.is_following(u)
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0;">
                {render_avatar(u, 38)}
                <div class="username-text">@{html.escape(u)}</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("✓ Following" if is_following else "+ Follow", key=f"ef_{u}", use_container_width=True):
                FollowHandler.follow(u)
                st.rerun()
        with c3:
            if st.button("💬", key=f"em_{u}", use_container_width=True):
                st.session_state.active_chat = u
                st.session_state.current_tab = "chats"
                st.rerun()
        st.markdown("<hr style='border-color:rgba(255,255,255,0.03);margin:0;'>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_chats_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    if st.session_state.get('active_chat') or st.session_state.get('active_group') or st.session_state.get('active_channel'):
        render_chat_interface()
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    st.markdown('<h3 style="color:#f1f5f9;margin-bottom:0.5rem;">💬 Messages</h3>', unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💬 New Chat", use_container_width=True, key="nc"): st.session_state.show_new_chat = True
    with c2:
        if st.button("👥 New Group", use_container_width=True, key="ng"): st.session_state.show_new_group = True
    with c3:
        if st.button("📢 New Channel", use_container_width=True, key="nch"): st.session_state.show_new_channel = True
    
    t1, t2, t3 = st.tabs(["📱 DMs", "👥 Groups", "📢 Channels"])
    
    with t1:
        chats = ChatHandler.get_chat_list()
        if chats:
            for c in chats:
                dot = '<span class="online-dot"></span>' if c['is_online'] else ''
                unread = f'<span class="unread-count">{c["unread"]}</span>' if c['unread'] > 0 else ''
                st.markdown(f"""
                <div class="user-row" style="justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:0.6rem;flex:1;">
                        {render_avatar(c['with_user'], 40)}
                        <div style="flex:1;">
                            <div style="display:flex;align-items:center;gap:0.3rem;">
                                <span class="username-text">@{html.escape(c['with_user'])}</span>{dot}
                            </div>
                            <div style="color:#94a3b8;font-size:0.7rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:180px;">{html.escape(c['last_message'])}</div>
                        </div>
                    </div>
                    <div style="text-align:right;">
                        <div class="timestamp">{format_timestamp(c['last_time'])}</div>{unread}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Open", key=f"oc_{c['with_user']}", label_visibility="collapsed"):
                    st.session_state.active_chat = c['with_user']
                    st.rerun()
        else:
            st.info("No conversations yet")
        
        if st.session_state.get('show_new_chat'):
            with st.expander("New Chat", expanded=True):
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                if avail:
                    sel = st.selectbox("User", avail, key="ncs")
                    if st.button("Start", use_container_width=True):
                        st.session_state.active_chat = sel
                        st.session_state.show_new_chat = False
                        st.rerun()
    
    with t2:
        groups = GroupHandler.get_user_groups()
        if groups:
            for g in groups:
                st.markdown(f"""
                <div class="user-row">
                    <div class="avatar-placeholder" style="width:40px;height:40px;background:#667eea;">👥</div>
                    <div>
                        <div class="username-text">{html.escape(g['name'])}</div>
                        <div style="color:#94a3b8;font-size:0.7rem;">{g['members']} members</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Open", key=f"og_{g['id']}", label_visibility="collapsed"):
                    st.session_state.active_group = g['id']
                    st.rerun()
        else:
            st.info("No groups yet")
        
        if st.session_state.get('show_new_group'):
            with st.expander("New Group", expanded=True):
                gn = st.text_input("Name", max_chars=50, key="ngn")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                mems = st.multiselect("Members", avail, key="ngm")
                if st.button("Create", use_container_width=True) and gn:
                    GroupHandler.create_group(gn, mems)
                    st.session_state.show_new_group = False
                    st.rerun()
    
    with t3:
        channels = GroupHandler.get_user_channels()
        if channels:
            for ch in channels:
                st.markdown(f"""
                <div class="user-row">
                    <div class="avatar-placeholder" style="width:40px;height:40px;background:#f093fb;">📢</div>
                    <div>
                        <div class="username-text">{html.escape(ch['name'])}</div>
                        <div style="color:#94a3b8;font-size:0.7rem;">{ch['subscribers']} subscribers</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("Open", key=f"och_{ch['id']}", label_visibility="collapsed"):
                    st.session_state.active_channel = ch['id']
                    st.rerun()
        else:
            st.info("No channels yet")
        
        if st.session_state.get('show_new_channel'):
            with st.expander("New Channel", expanded=True):
                cn = st.text_input("Name", max_chars=50, key="nchn")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                subs = st.multiselect("Subscribers", avail, key="nchs")
                if st.button("Create", use_container_width=True) and cn:
                    GroupHandler.create_group(cn, subs or [], is_channel=True)
                    st.session_state.show_new_channel = False
                    st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_profile_page():
    user = st.session_state.user
    profile = DataManager.get_profile(user)
    theme = get_theme()
    
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0;">
        {render_avatar(user, 70)}
        <h2 style="color:{theme['text']};margin-top:0.5rem;">@{html.escape(user)}</h2>
        <p style="color:{theme['secondary']};font-size:0.85rem;">{html.escape(profile.get('bio', 'No bio'))}</p>
    </div>
    
    <div style="display:flex;justify-content:space-around;text-align:center;padding:0.8rem;border-top:1px solid rgba(255,255,255,0.05);border-bottom:1px solid rgba(255,255,255,0.05);margin-bottom:0.8rem;">
        <div><div style="color:{theme['text']};font-size:1.2rem;font-weight:700;">{profile.get('post_count', 0)}</div><div style="color:{theme['secondary']};font-size:0.6rem;">Posts</div></div>
        <div><div style="color:{theme['text']};font-size:1.2rem;font-weight:700;">{len(profile.get('followers', []))}</div><div style="color:{theme['secondary']};font-size:0.6rem;">Followers</div></div>
        <div><div style="color:{theme['text']};font-size:1.2rem;font-weight:700;">{len(profile.get('following', []))}</div><div style="color:{theme['secondary']};font-size:0.6rem;">Following</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Edit Profile
    with st.expander("✏️ Edit Profile"):
        with st.form("epf"):
            bio = st.text_area("Bio", value=profile.get("bio", ""), max_chars=MAX_BIO_LENGTH)
            website = st.text_input("Website", value=profile.get("website", ""))
            location = st.text_input("Location", value=profile.get("location", ""))
            avatar_file = st.file_uploader("Avatar", type=['png','jpg','jpeg'], key="pau")
            
            if st.form_submit_button("Save", use_container_width=True):
                updates = {"bio": sanitize_text(bio, MAX_BIO_LENGTH), "website": sanitize_text(website, 100), "location": sanitize_text(location, 100)}
                if avatar_file and avatar_file.size <= MAX_AVATAR_SIZE:
                    try:
                        img = Image.open(avatar_file)
                        if img.mode in ('RGBA','LA','P'):
                            bg = Image.new('RGB', img.size, (255,255,255))
                            bg.paste(img.convert('RGBA'), mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = bg
                        else: img = img.convert("RGB")
                        img.thumbnail((200, 200))
                        path = UPLOADS_DIR / f"{user}_avatar.jpg"
                        img.save(path, "JPEG", quality=80)
                        updates["avatar"] = str(path)
                    except: st.error("Image error")
                DataManager.update_profile(user, updates)
                st.success("Updated!")
                st.rerun()
    
    # Wallpaper/Theme Selection
    with st.expander("🎨 Wallpaper & Theme"):
        st.markdown('<div class="theme-grid">', unsafe_allow_html=True)
        current_wp = profile.get('wallpaper', 'midnight')
        
        for tkey, tdata in THEMES.items():
            selected = "selected" if (current_wp == tkey or st.session_state.get('selected_theme') == tkey) else ""
            st.markdown(f"""
            <div class="theme-card {selected}" style="background:{tdata['wallpaper']};">
                <div style="font-size:1.5rem;">{tdata['icon']}</div>
                <div style="color:white;font-size:0.7rem;margin-top:0.2rem;">{tdata['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Apply {tdata['name']}", key=f"th_{tkey}", use_container_width=True):
                st.session_state.selected_theme = tkey
                DataManager.update_profile(user, {"wallpaper": tkey})
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    # User's posts
    posts = [p for p in st.session_state.feed_posts if p.get("username") == user]
    if posts:
        st.markdown(f'<h4 style="color:{theme["text"]};margin-top:0.8rem;">Your Posts</h4>', unsafe_allow_html=True)
        for post in reversed(posts[-20:]):
            if post.get("type") == "poll": render_poll_card(post)
            else: render_post_card(post)
    
    if st.button("🚪 Sign Out", use_container_width=True, key="so"):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTH ==========
def render_auth():
    st.markdown("""
    <style>html,body{overflow:auto!important;height:auto!important;}</style>
    """, unsafe_allow_html=True)
    
    _, c, _ = st.columns([1, 2, 1])
    with c:
        st.markdown("""
        <div style="text-align:center;padding:2rem 0;">
            <div style="font-size:4rem;">🌐</div>
            <h1 style="background:linear-gradient(135deg,#667eea,#764ba2,#f093fb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2rem;">SocialHub Pro</h1>
            <p style="color:#64748b;">Feed • Stories • Chat • Groups • Channels</p>
        </div>
        """, unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["Sign In", "Sign Up"])
        
        with t1:
            with st.form("li"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    if u and p:
                        ok, res = DataManager.authenticate(u, p)
                        if ok:
                            st.session_state.auth = True
                            st.session_state.user = res
                            st.session_state.feed_posts = DataManager.get_feed_posts()
                            st.rerun()
                        else: st.error(res)
        
        with t2:
            with st.form("su"):
                u = st.text_input("Username", placeholder="3-20 chars")
                p = st.text_input("Password", type="password", placeholder="Min 6 chars")
                cp = st.text_input("Confirm", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if not u or not p: st.error("Fill all fields")
                    elif p != cp: st.error("Passwords don't match")
                    elif len(p) < MIN_PASSWORD_LENGTH: st.error(f"Password too short")
                    elif len(u) < 3 or len(u) > MAX_USERNAME_LENGTH: st.error("Username 3-20 chars")
                    elif not u.isalnum(): st.error("Letters/numbers only")
                    else:
                        ok, msg = DataManager.create_user(u, p)
                        if ok: st.success(msg); st.info("Sign in now!")
                        else: st.error(msg)

# ========== MAIN ==========
def main():
    init_session()
    inject_styles()
    
    if not st.session_state.get('auth'):
        render_auth()
        return
    
    render_header()
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    tab = st.session_state.get('current_tab', 'feed')
    if tab == "feed": render_feed_page()
    elif tab == "explore": render_explore_page()
    elif tab == "chats": render_chats_page()
    elif tab == "profile": render_profile_page()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.get('show_create_modal'):
        render_create_modal()
    
    render_bottom_nav()

if __name__ == "__main__":
    main()
    
