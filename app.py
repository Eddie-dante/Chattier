import streamlit as st
import json
import os
import html
import hashlib
import pathlib
from datetime import datetime, timedelta
import uuid
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageColor, ImageEnhance, ImageOps
import time
import requests
from typing import Dict, List, Optional, Any, Tuple, Set, Union
import secrets
import logging
import io
import shutil
import re
import math
import random
import colorsys
from functools import lru_cache
from dataclasses import dataclass, field, asdict
from collections import defaultdict, OrderedDict
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from contextlib import contextmanager
import sys

# Must be first Streamlit command
st.set_page_config(
    page_title="Socialite - Premium Social Network",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Socialite - The Premium Social Experience v4.0"
    }
)

# ========== CONFIGURATION ==========
class Config:
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "4.0.0"
    
    DATA_DIR = pathlib.Path("data")
    DB_PATH = DATA_DIR / "socialite.db"
    UPLOADS_DIR = DATA_DIR / "uploads"
    BACKUP_DIR = DATA_DIR / "backups"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"
    
    MAX_POST_LENGTH = 5000
    MAX_COMMENT_LENGTH = 1000
    MAX_BIO_LENGTH = 500
    MAX_MESSAGE_LENGTH = 10000
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 8
    MAX_FILE_SIZE = 50 * 1024 * 1024
    MAX_AVATAR_SIZE = 10 * 1024 * 1024
    
    STORY_EXPIRY_HOURS = 24
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    SESSION_TIMEOUT_HOURS = 24
    ONLINE_THRESHOLD_SECONDS = 300
    CACHE_TTL_SECONDS = 60
    
    MAX_FEED_ITEMS = 1000
    MAX_CHAT_MESSAGES = 5000
    MAX_NOTIFICATIONS = 200
    MAX_FOLLOWING = 5000
    MAX_BLOCKED = 1000

# Create directories
for dir_path in [Config.DATA_DIR, Config.UPLOADS_DIR, Config.BACKUP_DIR, 
                 Config.CACHE_DIR, Config.LOGS_DIR, Config.TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'socialite.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== UTILITIES ==========
class Utils:
    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(32)
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 300000)
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        try:
            h, _ = Utils.hash_password(password, salt)
            return h == stored_hash
        except:
            return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        if not text:
            return ""
        text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
        text = html.escape(str(text).strip())
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        return text
    
    @staticmethod
    def format_timestamp(ts) -> str:
        if not ts:
            return ""
        try:
            if isinstance(ts, str):
                t = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                t = ts
            if t.tzinfo is not None:
                from datetime import timezone
                t = t.replace(tzinfo=None)
            now = datetime.now()
            diff = (now - t).total_seconds()
            if diff < 5: return "just now"
            elif diff < 60: return f"{int(diff)}s"
            elif diff < 3600: return f"{int(diff//60)}m"
            elif diff < 86400: return f"{int(diff//3600)}h"
            elif diff < 604800: return f"{int(diff//86400)}d"
            elif diff < 2592000: return f"{int(diff//604800)}w"
            elif diff < 31536000: return f"{int(diff//2592000)}mo"
            else: return f"{int(diff//31536000)}y"
        except:
            return "unknown"
    
    @staticmethod
    def format_number(num: int) -> str:
        if num is None: return "0"
        if num < 1000: return str(num)
        elif num < 1000000: return f"{num/1000:.1f}K"
        elif num < 1000000000: return f"{num/1000000:.1f}M"
        else: return f"{num/1000000000:.1f}B"
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        if not text: return []
        return re.findall(r'#(\w+)', text)
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        if not text: return []
        return re.findall(r'@(\w+)', text)
    
    @staticmethod
    def validate_image(data: bytes) -> bool:
        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
            return img.format.lower() in ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
        except:
            return False
    
    @staticmethod
    def optimize_image(data: bytes, max_size: Tuple[int, int] = (800, 800), quality: int = 85) -> bytes:
        try:
            img = Image.open(io.BytesIO(data))
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P': img = img.convert('RGBA')
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA': background.paste(img, mask=img.split()[3])
                else: background.paste(img)
                img = background
            elif img.mode != 'RGB': img = img.convert('RGB')
            img.thumbnail(max_size, Image.LANCZOS)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
        except:
            return data
    
    @staticmethod
    def get_avatar_color(username: str) -> str:
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#DDA0DD',
                  '#FF8A80', '#B388FF', '#FF5722', '#9C27B0', '#3F51B5',
                  '#009688', '#FF9800', '#795548', '#607D8B', '#E91E63']
        if not username: return colors[0]
        return colors[hash(username) % len(colors)]
    
    @staticmethod
    def get_initials(username: str) -> str:
        if not username: return "?"
        parts = username.replace('_', ' ').replace('.', ' ').split()
        if len(parts) >= 2: return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if len(username) >= 2 else username[0].upper()

# ========== DATABASE MANAGER ==========
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized: return
        self._initialized = True
        self._local = threading.local()
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(Config.DB_PATH), check_same_thread=False, timeout=30
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
        try:
            yield self._local.connection
        except Exception as e:
            try: self._local.connection.rollback()
            except: pass
            logger.error(f"Database error: {e}")
            raise
    
    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    email TEXT DEFAULT '',
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_premium BOOLEAN DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    total_posts INTEGER DEFAULT 0,
                    total_likes_received INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 0.0
                )
            """)
            
            # Profiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    display_name TEXT,
                    bio TEXT DEFAULT '',
                    avatar_path TEXT,
                    cover_path TEXT,
                    website TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    birthday TEXT DEFAULT '',
                    gender TEXT DEFAULT 'male',
                    is_private BOOLEAN DEFAULT 0,
                    theme TEXT DEFAULT 'midnight',
                    wallpaper TEXT DEFAULT 'default',
                    language TEXT DEFAULT 'en',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Follows
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_accepted BOOLEAN DEFAULT 1,
                    PRIMARY KEY (follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Blocks
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    blocker_id INTEGER NOT NULL,
                    blocked_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (blocker_id, blocked_id),
                    FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (blocked_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Posts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    text TEXT DEFAULT '',
                    media_data TEXT,
                    media_name TEXT,
                    media_type TEXT DEFAULT 'image',
                    post_type TEXT DEFAULT 'post',
                    location TEXT DEFAULT '',
                    price REAL DEFAULT 0,
                    currency TEXT DEFAULT 'USD',
                    marketplace_status TEXT DEFAULT 'none',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    view_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Polls
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS polls (
                    post_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    ends_at TIMESTAMP,
                    total_votes INTEGER DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poll_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    option_text TEXT NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poll_votes (
                    option_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (option_id, user_id),
                    FOREIGN KEY (option_id) REFERENCES poll_options(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Reactions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reactions (
                    post_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    reaction_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (post_id, user_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Comments
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    parent_id TEXT,
                    text TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Stories
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    media_data TEXT NOT NULL,
                    media_name TEXT,
                    caption TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS story_views (
                    story_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (story_id, user_id),
                    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Messages
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    from_id INTEGER NOT NULL,
                    to_id INTEGER NOT NULL,
                    text TEXT DEFAULT '',
                    media_data TEXT,
                    media_name TEXT,
                    reply_to TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Groups
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    description TEXT DEFAULT '',
                    icon_path TEXT,
                    is_channel BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    member_count INTEGER DEFAULT 0,
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (group_id, user_id),
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    from_id INTEGER NOT NULL,
                    text TEXT DEFAULT '',
                    media_data TEXT,
                    media_name TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Notifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    from_user_id INTEGER,
                    link TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # Indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at)",
                "CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id)",
                "CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id)",
            ]
            for idx in indexes:
                try: cursor.execute(idx)
                except: pass
            
            conn.commit()

# ========== USER MANAGER ==========
class UserManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        username = username.strip().lower()
        if len(username) < 3 or len(username) > Config.MAX_USERNAME_LENGTH:
            return False, f"Username must be 3-{Config.MAX_USERNAME_LENGTH} characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Only letters, numbers, and underscores"
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, "Username already exists"
                
                password_hash, salt = Utils.hash_password(password)
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, salt))
                user_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO profiles (user_id, display_name) VALUES (?, ?)
                """, (user_id, username))
                
                conn.commit()
                return True, "Account created successfully!"
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False, "An error occurred"
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Union[str, int]]:
        username = username.strip()
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, password_hash, salt, login_attempts, 
                           locked_until, is_banned, is_deleted
                    FROM users WHERE username = ? OR LOWER(username) = LOWER(?)
                """, (username, username))
                user = cursor.fetchone()
                
                if not user: return False, "User not found"
                if user['is_deleted']: return False, "Account deleted"
                if user['is_banned']: return False, "Account banned"
                
                if user['locked_until']:
                    try:
                        lock_time = datetime.fromisoformat(user['locked_until'])
                        if datetime.now() < lock_time:
                            remaining = (lock_time - datetime.now()).seconds // 60
                            return False, f"Account locked for {remaining} more minutes"
                    except: pass
                
                if Utils.verify_password(password, user['password_hash'], user['salt']):
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP, login_attempts = 0 WHERE id = ?
                    """, (user['id'],))
                    conn.commit()
                    return True, user['username']
                else:
                    attempts = user['login_attempts'] + 1
                    if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        lock_until = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
                        cursor.execute("""
                            UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?
                        """, (attempts, lock_until.isoformat(), user['id']))
                    else:
                        cursor.execute("UPDATE users SET login_attempts = ? WHERE id = ?", (attempts, user['id']))
                    conn.commit()
                    return False, "Incorrect password"
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return False, "An error occurred"
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.* FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.username = ? AND u.is_deleted = 0
                """, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except: return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.* FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.id = ? AND u.is_deleted = 0
                """, (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except: return None
    
    def update_profile(self, user_id: int, updates: Dict) -> bool:
        valid_fields = ['display_name', 'bio', 'avatar_path', 'cover_path',
                       'website', 'location', 'birthday', 'gender',
                       'is_private', 'theme', 'wallpaper', 'language']
        filtered = {k: v for k, v in updates.items() if k in valid_fields}
        if not filtered: return False
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{k} = ?" for k in filtered.keys()])
                values = list(filtered.values()) + [user_id]
                cursor.execute(f"""
                    UPDATE profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?
                """, values)
                conn.commit()
                return True
        except: return False
    
    def update_last_seen(self, user_id: int):
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
                conn.commit()
        except: pass
    
    def get_online_users(self) -> List[str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now() - timedelta(seconds=Config.ONLINE_THRESHOLD_SECONDS)
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE last_login >= ? AND is_banned = 0 AND is_deleted = 0
                """, (cutoff.isoformat(),))
                return [row['username'] for row in cursor.fetchall()]
        except: return []
    
    def search_users(self, query: str, limit: int = 50, exclude_user_id: int = None) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                params = [f"%{query}%", f"%{query}%"]
                sql = """
                    SELECT u.username, u.is_verified, u.is_premium, u.id,
                           p.display_name, p.bio, p.avatar_path, p.gender,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id AND is_accepted = 1) as follower_count
                    FROM users u LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.is_banned = 0 AND u.is_deleted = 0
                    AND (u.username LIKE ? OR p.display_name LIKE ?)
                """
                if exclude_user_id:
                    sql += " AND u.id != ?"
                    params.append(exclude_user_id)
                sql += " ORDER BY follower_count DESC LIMIT ?"
                params.append(limit)
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def follow_user(self, follower_id: int, following_username: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM users WHERE username = ? AND is_deleted = 0", (following_username,))
                target = cursor.fetchone()
                if not target: return False, "User not found"
                following_id = target['id']
                if follower_id == following_id: return False, "Cannot follow yourself"
                
                cursor.execute("SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (following_id, follower_id))
                if cursor.fetchone(): return False, "You are blocked"
                
                cursor.execute("SELECT 1 FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                if cursor.fetchone():
                    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                    conn.commit()
                    return True, f"Unfollowed @{following_username}"
                else:
                    cursor.execute("""
                        INSERT INTO follows (follower_id, following_id, is_accepted) VALUES (?, ?, 1)
                    """, (follower_id, following_id))
                    nid = Utils.generate_id()
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                        VALUES (?, ?, 'follow', 'started following you', ?, ?)
                    """, (nid, following_id, follower_id, f"/profile/{following_username}"))
                    conn.commit()
                    return True, f"Following @{following_username}"
        except Exception as e:
            logger.error(f"Follow error: {e}")
            return False, "An error occurred"

# ========== POST MANAGER ==========
class PostManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_post(self, user_id: int, text: str = "", media_data: str = None,
                   media_name: str = None, post_type: str = "post",
                   location: str = "", price: float = 0, 
                   marketplace_status: str = "none") -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_POST_LENGTH) if text else ""
        if not text and not media_data: return False, "Post cannot be empty"
        
        try:
            post_id = Utils.generate_id()
            hashtags = Utils.extract_hashtags(text)
            mentions = Utils.extract_mentions(text)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO posts (id, user_id, text, media_data, media_name, 
                                      post_type, location, price, marketplace_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (post_id, user_id, text, media_data, media_name,
                      post_type, location, price, marketplace_status))
                
                for mentioned_username in mentions:
                    cursor.execute("SELECT id FROM users WHERE username = ? AND is_deleted = 0", (mentioned_username,))
                    mentioned_user = cursor.fetchone()
                    if mentioned_user and mentioned_user['id'] != user_id:
                        nid = Utils.generate_id()
                        cursor.execute("""
                            INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                            VALUES (?, ?, 'mention', 'mentioned you in a post', ?, ?)
                        """, (nid, mentioned_user['id'], user_id, f"/post/{post_id}"))
                
                cursor.execute("UPDATE users SET total_posts = total_posts + 1 WHERE id = ?", (user_id,))
                conn.commit()
                return True, post_id
        except Exception as e:
            logger.error(f"Create post error: {e}")
            return False, "Failed to create post"
    
    def get_feed(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], bool]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                offset = (page - 1) * per_page
                cursor.execute("""
                    SELECT p.*, u.username, u.is_verified, u.is_premium,
                           pr.display_name, pr.avatar_path, pr.gender
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE p.is_deleted = 0
                    AND (p.user_id = ? OR p.user_id IN (
                        SELECT following_id FROM follows WHERE follower_id = ? AND is_accepted = 1
                    ))
                    AND p.user_id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = ?)
                    ORDER BY p.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (user_id, user_id, user_id, per_page + 1, offset))
                
                posts = [dict(row) for row in cursor.fetchall()]
                has_more = len(posts) > per_page
                if has_more: posts = posts[:per_page]
                
                for post in posts:
                    cursor.execute("""
                        SELECT reaction_type, COUNT(*) as count FROM reactions
                        WHERE post_id = ? GROUP BY reaction_type
                    """, (post['id'],))
                    post['reactions'] = {row['reaction_type']: row['count'] for row in cursor.fetchall()}
                    
                    cursor.execute("""
                        SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?
                    """, (post['id'], user_id))
                    ur = cursor.fetchone()
                    post['user_reaction'] = ur['reaction_type'] if ur else None
                    
                    cursor.execute("SELECT COUNT(*) as count FROM comments WHERE post_id = ? AND is_deleted = 0", (post['id'],))
                    post['comment_count'] = cursor.fetchone()['count']
                
                return posts, has_more
        except Exception as e:
            logger.error(f"Feed error: {e}")
            return [], False
    
    def add_reaction(self, post_id: str, user_id: int, reaction_type: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                existing = cursor.fetchone()
                
                if existing:
                    if existing['reaction_type'] == reaction_type:
                        cursor.execute("DELETE FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                        conn.commit()
                        return True, "Reaction removed"
                    else:
                        cursor.execute("""
                            UPDATE reactions SET reaction_type = ?, created_at = CURRENT_TIMESTAMP
                            WHERE post_id = ? AND user_id = ?
                        """, (reaction_type, post_id, user_id))
                        conn.commit()
                        return True, "Reaction updated"
                else:
                    cursor.execute("""
                        INSERT INTO reactions (post_id, user_id, reaction_type) VALUES (?, ?, ?)
                    """, (post_id, user_id, reaction_type))
                    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                    post = cursor.fetchone()
                    if post and post['user_id'] != user_id:
                        nid = Utils.generate_id()
                        cursor.execute("""
                            INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                            VALUES (?, ?, 'reaction', 'reacted to your post', ?, ?)
                        """, (nid, post['user_id'], user_id, f"/post/{post_id}"))
                    conn.commit()
                    return True, "Reaction added"
        except: return False, "Failed"
    
    def get_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.username, u.is_verified, pr.display_name, pr.avatar_path, pr.gender
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE c.post_id = ? AND c.is_deleted = 0
                    ORDER BY c.timestamp ASC LIMIT ?
                """, (post_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def add_comment(self, post_id: str, user_id: int, text: str, parent_id: str = None) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_COMMENT_LENGTH)
        if not text: return False, "Comment cannot be empty"
        
        try:
            comment_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO comments (id, post_id, user_id, parent_id, text) VALUES (?, ?, ?, ?, ?)
                """, (comment_id, post_id, user_id, parent_id, text))
                
                cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                post = cursor.fetchone()
                if post and post['user_id'] != user_id:
                    nid = Utils.generate_id()
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                        VALUES (?, ?, 'comment', 'commented on your post', ?, ?)
                    """, (nid, post['user_id'], user_id, f"/post/{post_id}"))
                
                conn.commit()
                return True, comment_id
        except: return False, "Failed to add comment"
    
    def delete_post(self, post_id: str, user_id: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM posts WHERE id = ? AND is_deleted = 0", (post_id,))
                post = cursor.fetchone()
                if not post: return False, "Post not found"
                if post['user_id'] != user_id: return False, "Not your post"
                
                cursor.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (post_id,))
                cursor.execute("UPDATE users SET total_posts = MAX(0, total_posts - 1) WHERE id = ?", (user_id,))
                conn.commit()
                return True, "Post deleted"
        except: return False, "Failed"

# ========== CHAT MANAGER ==========
class ChatManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def send_message(self, from_id: int, to_username: str, text: str = "",
                    media_data: str = None) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_MESSAGE_LENGTH) if text else ""
        if not text and not media_data: return False, "Message cannot be empty"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username FROM users WHERE username = ? AND is_deleted = 0", (to_username,))
                to_user = cursor.fetchone()
                if not to_user: return False, "User not found"
                
                to_id = to_user['id']
                cursor.execute("SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (to_id, from_id))
                if cursor.fetchone(): return False, "You are blocked"
                
                chat_id = self._get_chat_id(from_id, to_id)
                message_id = Utils.generate_id()
                cursor.execute("""
                    INSERT INTO messages (id, chat_id, from_id, to_id, text, media_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (message_id, chat_id, from_id, to_id, text, media_data))
                
                nid = Utils.generate_id()
                cursor.execute("""
                    INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                    VALUES (?, ?, 'message', 'sent you a message', ?, ?)
                """, (nid, to_id, from_id, f"/chat/{from_id}"))
                
                conn.commit()
                return True, message_id
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False, "Failed"
    
    def get_messages(self, user_id: int, with_user_id: int, limit: int = 50) -> List[Dict]:
        try:
            chat_id = self._get_chat_id(user_id, with_user_id)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE messages SET is_read = 1 WHERE chat_id = ? AND to_id = ? AND is_read = 0
                """, (chat_id, user_id))
                
                cursor.execute("""
                    SELECT m.*, u.username as from_username, pr.avatar_path, pr.gender
                    FROM messages m
                    JOIN users u ON m.from_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE m.chat_id = ? AND m.is_deleted = 0
                    ORDER BY m.timestamp DESC LIMIT ?
                """, (chat_id, limit))
                
                messages = [dict(row) for row in cursor.fetchall()]
                messages.reverse()
                conn.commit()
                return messages
        except: return []
    
    def get_chat_list(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        CASE WHEN m.from_id = ? THEN m.to_id ELSE m.from_id END as other_user_id,
                        u.username as other_username, u.is_verified, u.is_premium,
                        MAX(m.timestamp) as last_message_time,
                        COUNT(CASE WHEN m.to_id = ? AND m.is_read = 0 THEN 1 END) as unread_count
                    FROM messages m
                    JOIN users u ON (CASE WHEN m.from_id = ? THEN m.to_id = u.id ELSE m.from_id = u.id END)
                    WHERE (m.from_id = ? OR m.to_id = ?) AND m.is_deleted = 0
                    GROUP BY other_user_id ORDER BY last_message_time DESC
                """, (user_id, user_id, user_id, user_id, user_id))
                
                online_users = set(UserManager(self.db).get_online_users())
                chats = []
                for row in cursor.fetchall():
                    chat = dict(row)
                    chat['is_online'] = chat['other_username'] in online_users
                    chats.append(chat)
                return chats
        except: return []
    
    def _get_chat_id(self, user1_id: int, user2_id: int) -> str:
        ids = sorted([user1_id, user2_id])
        return f"chat_{ids[0]}_{ids[1]}"

# ========== GROUP MANAGER ==========
class GroupManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_group(self, name: str, owner_id: int, description: str = "",
                    is_channel: bool = False) -> Tuple[bool, str]:
        name = Utils.sanitize_text(name, 100)
        if not name: return False, "Name required"
        
        try:
            group_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO groups (id, name, owner_id, description, is_channel)
                    VALUES (?, ?, ?, ?, ?)
                """, (group_id, name, owner_id, description, 1 if is_channel else 0))
                
                cursor.execute("""
                    INSERT INTO group_members (group_id, user_id, role)
                    VALUES (?, ?, 'admin')
                """, (group_id, owner_id))
                
                conn.commit()
                return True, group_id
        except Exception as e:
            logger.error(f"Create group error: {e}")
            return False, "Failed"
    
    def join_group(self, group_id: str, user_id: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
                if cursor.fetchone(): return False, "Already a member"
                
                cursor.execute("""
                    INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'member')
                """, (group_id, user_id))
                
                cursor.execute("UPDATE groups SET member_count = member_count + 1 WHERE id = ?", (group_id,))
                conn.commit()
                return True, "Joined!"
        except: return False, "Failed"
    
    def send_message(self, group_id: str, from_id: int, text: str) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_MESSAGE_LENGTH)
        if not text: return False, "Message cannot be empty"
        
        try:
            message_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO group_messages (id, group_id, from_id, text) VALUES (?, ?, ?, ?)
                """, (message_id, group_id, from_id, text))
                conn.commit()
                return True, message_id
        except: return False, "Failed"
    
    def get_user_groups(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT g.*, gm.role FROM groups g
                    JOIN group_members gm ON g.id = gm.group_id
                    WHERE gm.user_id = ? ORDER BY g.created_at DESC
                """, (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def get_group_messages(self, group_id: str, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT gm.*, u.username, pr.avatar_path, pr.gender
                    FROM group_messages gm
                    JOIN users u ON gm.from_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE gm.group_id = ? ORDER BY gm.timestamp ASC LIMIT ?
                """, (group_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except: return []

# ========== NOTIFICATION MANAGER ==========
class NotificationManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT n.*, u.username as from_username
                    FROM notifications n
                    LEFT JOIN users u ON n.from_user_id = u.id
                    WHERE n.user_id = ? ORDER BY n.timestamp DESC LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def get_unread_count(self, user_id: int) -> int:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
                return cursor.fetchone()['count']
        except: return 0
    
    def mark_all_read(self, user_id: int):
        try:
            with self.db.get_connection() as conn:
                conn.cursor().execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
                conn.commit()
        except: pass

# ========== THEMES ==========
THEMES = {
    "midnight": {"name": "Midnight", "icon": "🌌", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8"},
    "ocean": {"name": "Ocean", "icon": "🌊", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda"},
    "sunset": {"name": "Sunset", "icon": "🌅", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081"},
    "forest": {"name": "Forest", "icon": "🌲", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50"},
    "neon": {"name": "Neon", "icon": "💜", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff"},
    "royal": {"name": "Royal", "icon": "👑", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0"},
    "crimson": {"name": "Crimson", "icon": "❤️", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336"},
    "arctic": {"name": "Arctic", "icon": "❄️", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3"},
}

# ========== MAIN UI ==========
class SocialiteUI:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self.group_manager = GroupManager(self.db)
        self.notification_manager = NotificationManager(self.db)
        self._init_session()
    
    def _init_session(self):
        defaults = {
            'auth': False, 'user_id': None, 'username': None,
            'current_tab': 'feed', 'active_chat': None,
            'active_group': None, 'show_create_modal': False,
            'feed_page': 1, 'show_comments_for': None,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def render(self):
        if not st.session_state.auth:
            self.render_auth()
            return
        
        if st.session_state.user_id:
            self.user_manager.update_last_seen(st.session_state.user_id)
        
        self.inject_styles()
        self.render_header()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        tab = st.session_state.current_tab
        if tab == 'feed': self.render_feed()
        elif tab == 'explore': self.render_explore()
        elif tab == 'marketplace': self.render_marketplace()
        elif tab == 'chats': self.render_chats()
        elif tab == 'groups': self.render_groups()
        elif tab == 'notifications': self.render_notifications()
        elif tab == 'profile': self.render_profile()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.show_create_modal:
            self.render_create_modal()
        
        self.render_bottom_nav()
    
    def inject_styles(self):
        theme = THEMES.get(self._get_current_theme(), THEMES['midnight'])
        
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        * {{ font-family: 'Inter', sans-serif; }}
        
        #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"], 
        [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
        
        html, body {{
            height: 100% !important; width: 100% !important;
            margin: 0 !important; padding: 0 !important;
            overflow: hidden !important;
        }}
        
        .stApp {{
            background: {theme['bg']} !important;
            height: 100vh !important; width: 100vw !important;
            overflow: hidden !important; position: relative !important;
        }}
        
        .main {{ height: 100vh !important; overflow: hidden !important; }}
        .block-container {{ height: 100vh !important; overflow: hidden !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important; }}
        
        /* Header */
        .app-header {{
            position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
            height: 48px !important; background: {theme['bg']}f0 !important;
            backdrop-filter: blur(20px) !important;
            border-bottom: 1px solid rgba(255,215,0,0.15) !important;
            padding: 0 16px !important; z-index: 9999 !important;
            display: flex !important; align-items: center !important; justify-content: space-between !important;
        }}
        
        /* Main content */
        .main-content {{
            position: fixed !important; top: 48px !important; bottom: 56px !important;
            left: 0 !important; right: 0 !important;
            overflow-y: auto !important; overflow-x: hidden !important;
            padding: 8px 12px !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        
        .content-wrapper {{ max-width: 650px !important; margin: 0 auto !important; }}
        
        /* Bottom Nav - Fixed & Responsive */
        .bottom-nav {{
            position: fixed !important; bottom: 0 !important; left: 0 !important; right: 0 !important;
            height: 56px !important;
            background: {theme['bg']}fa !important;
            backdrop-filter: blur(20px) !important;
            border-top: 2px solid rgba(255,215,0,0.25) !important;
            display: flex !important; align-items: center !important;
            justify-content: space-around !important;
            z-index: 9999 !important;
            padding: 0 !important;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
        }}
        
        .nav-item {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            flex: 1 !important;
            height: 100% !important;
            cursor: pointer !important;
            transition: all 0.2s !important;
            text-decoration: none !important;
            padding: 4px 0 !important;
        }}
        
        .nav-icon {{
            font-size: 1.3rem !important;
            line-height: 1 !important;
        }}
        
        .nav-label {{
            font-size: 0.55rem !important;
            font-weight: 500 !important;
            margin-top: 2px !important;
            line-height: 1 !important;
        }}
        
        .nav-item.active .nav-icon,
        .nav-item.active .nav-label {{
            color: #FFD700 !important;
        }}
        
        .nav-item:not(.active) .nav-icon,
        .nav-item:not(.active) .nav-label {{
            color: {theme['secondary']} !important;
        }}
        
        /* Cards */
        .card {{
            background: {theme['card']} !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 14px !important;
            margin-bottom: 10px !important;
            overflow: hidden !important;
        }}
        
        .username-text {{ color: {theme['text']} !important; font-weight: 600 !important; font-size: 0.82rem !important; }}
        .timestamp {{ color: {theme['secondary']} !important; font-size: 0.62rem !important; }}
        .post-text {{ color: #e2e8f0 !important; font-size: 0.85rem !important; line-height: 1.5 !important; padding: 8px 12px !important; word-wrap: break-word !important; }}
        
        /* Form inputs - FIX TEXT VISIBILITY */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background: rgba(255,255,255,0.08) !important;
            border: 1px solid rgba(255,215,0,0.2) !important;
            color: #FFFFFF !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 0.9rem !important;
        }}
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {{
            color: #94a3b8 !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: #FFD700 !important;
            box-shadow: 0 0 10px rgba(255,215,0,0.2) !important;
        }}
        
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
        
        /* Form submit button */
        div[data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(135deg, #FFD700, #FFA500) !important;
            color: #1a0033 !important;
            font-weight: 700 !important;
            border: none !important;
        }}
        
        /* Chat bubbles */
        .chat-bubble {{
            max-width: 75% !important;
            padding: 8px 14px !important;
            border-radius: 16px !important;
            font-size: 0.85rem !important;
            line-height: 1.4 !important;
            margin: 2px 8px !important;
            color: white !important;
        }}
        
        .chat-bubble.sent {{
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            border-bottom-right-radius: 4px !important;
        }}
        
        .chat-bubble.received {{
            background: rgba(255,255,255,0.08) !important;
            border-bottom-left-radius: 4px !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 4px !important; }}
        ::-webkit-scrollbar-track {{ background: transparent !important; }}
        ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
        
        /* Auth page */
        .auth-container {{
            background: rgba(10, 10, 26, 0.9) !important;
            backdrop-filter: blur(30px) !important;
            border: 2px solid rgba(255, 215, 0, 0.2) !important;
            border-radius: 24px !important;
            padding: 2.5rem 2rem !important;
            max-width: 420px !important;
            margin: 0 auto !important;
        }}
        
        .brand-title {{
            font-family: 'Playfair Display', 'Georgia', serif !important;
            font-size: 2.5rem !important;
            font-weight: 900 !important;
            background: linear-gradient(135deg, #FFD700, #FFA500, #FFD700) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            margin: 0.5rem 0 !important;
            letter-spacing: 2px !important;
        }}
        
        /* Modal */
        .modal-overlay {{
            position: fixed !important; top: 0 !important; left: 0 !important;
            right: 0 !important; bottom: 0 !important;
            background: rgba(0,0,0,0.85) !important;
            backdrop-filter: blur(8px) !important;
            z-index: 10000 !important;
            display: flex !important; align-items: center !important;
            justify-content: center !important;
        }}
        
        .modal-box {{
            background: {theme['bg']} !important;
            border: 1px solid rgba(255,215,0,0.2) !important;
            border-radius: 18px !important;
            width: 92% !important; max-width: 480px !important;
            max-height: 85vh !important; overflow-y: auto !important;
            padding: 20px !important;
        }}
        
        /* Responsive */
        @media (max-width: 640px) {{
            .main-content {{ padding: 6px 8px !important; }}
            .card {{ border-radius: 10px !important; margin-bottom: 8px !important; }}
            .bottom-nav {{ height: 52px !important; }}
            .main-content {{ bottom: 52px !important; }}
            .app-header {{ height: 44px !important; }}
            .main-content {{ top: 44px !important; }}
            .nav-icon {{ font-size: 1.2rem !important; }}
            .nav-label {{ font-size: 0.5rem !important; }}
            .auth-container {{ padding: 1.5rem !important; margin: 0 10px !important; }}
            .brand-title {{ font-size: 2rem !important; }}
        }}
        
        @media (min-width: 1200px) {{
            .content-wrapper {{ max-width: 700px !important; }}
            .bottom-nav {{ 
                left: 50% !important; 
                transform: translateX(-50%) !important;
                width: 700px !important;
                border-radius: 20px 20px 0 0 !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        unread = self.notification_manager.get_unread_count(user['user_id'])
        badge_html = f'<span style="background:#FFD700;color:#000;border-radius:50%;padding:1px 6px;font-size:0.6rem;position:absolute;top:-5px;right:-10px;">{unread}</span>' if unread > 0 else ''
        
        st.markdown(f"""
        <div class="app-header">
            <div style="display:flex;align-items:center;gap:8px;font-weight:800;font-size:1.1rem;
                 background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                👑 Socialite
            </div>
            <div style="display:flex;align-items:center;gap:15px;color:#94a3b8;">
                <span style="cursor:pointer;position:relative;">🔔{badge_html}</span>
                {self.render_avatar_html(user, 28)}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_feed(self):
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Quick post
        if st.button("✨ What's on your mind?", use_container_width=True, key="quick_post"):
            st.session_state.show_create_modal = True
            st.rerun()
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        posts, has_more = self.post_manager.get_feed(user['user_id'], st.session_state.feed_page)
        
        if not posts:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">
                <div style="font-size:4rem;">👑</div>
                <h3 style="color:#FFD700;">Welcome to Socialite</h3>
                <p>Follow users or create your first post!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for post in posts:
                self.render_post_card(post)
            
            if has_more:
                if st.button("Load More", use_container_width=True):
                    st.session_state.feed_page += 1
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_post_card(self, post: Dict):
        st.markdown(f'<div class="card">', unsafe_allow_html=True)
        
        # Header
        st.markdown(f"""
        <div style="display:flex;align-items:center;padding:8px 10px;gap:8px;">
            {self.render_avatar_html(post, 36)}
            <div style="flex:1;">
                <div class="username-text">
                    @{html.escape(post['username'])}
                    {" <span style='color:#FFD700;'>✓</span>" if post.get('is_verified') else ""}
                </div>
                <div class="timestamp">{Utils.format_timestamp(post['timestamp'])}</div>
            </div>
            {f"<span style='color:#4ade80;font-size:0.7rem;'>${post['price']}</span>" if post.get('marketplace_status') == 'for_sale' else ""}
        </div>
        """, unsafe_allow_html=True)
        
        # Text
        if post.get('text'):
            st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
        
        # Media
        if post.get('media_data'):
            try:
                st.image(base64.b64decode(post['media_data']), use_column_width=True)
            except: pass
        
        # Actions
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 3])
        with c1:
            if st.button(f"❤️ {sum(post.get('reactions', {}).values())}", key=f"r_{post['id']}"):
                self.post_manager.add_reaction(post['id'], st.session_state.user_id, 'like')
                st.rerun()
        with c2:
            if st.button(f"💬 {post.get('comment_count', 0)}", key=f"c_{post['id']}"):
                st.session_state.show_comments_for = post['id'] if st.session_state.show_comments_for != post['id'] else None
                st.rerun()
        with c3:
            if st.button("🔄", key=f"s_{post['id']}"): st.toast("Shared!")
        with c4:
            if st.button("🔖", key=f"sv_{post['id']}"): st.toast("Saved!")
        with c5:
            if post['username'] == st.session_state.username:
                if st.button("🗑️", key=f"d_{post['id']}"):
                    self.post_manager.delete_post(post['id'], st.session_state.user_id)
                    st.rerun()
        
        # Comments
        if st.session_state.show_comments_for == post['id']:
            self.render_comments_section(post['id'])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_comments_section(self, post_id: str):
        st.markdown('<div style="padding:8px 10px;border-top:1px solid rgba(255,215,0,0.1);">', unsafe_allow_html=True)
        
        comments = self.post_manager.get_comments(post_id)
        for comment in comments:
            st.markdown(f"""
            <div style="margin:4px 0;display:flex;gap:6px;align-items:flex-start;">
                {self.render_avatar_html(comment, 20)}
                <div>
                    <span style="color:#FFD700;font-weight:600;font-size:0.7rem;">@{html.escape(comment['username'])}</span>
                    <span style="color:#e2e8f0;font-size:0.75rem;">{html.escape(comment['text'])}</span>
                    <div style="color:#64748b;font-size:0.55rem;">{Utils.format_timestamp(comment['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"cf_{post_id}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input("Comment", placeholder="Write...", key=f"ci_{post_id}", label_visibility="collapsed")
            with c2:
                if st.form_submit_button("Post") and txt.strip():
                    self.post_manager.add_comment(post_id, st.session_state.user_id, txt)
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_explore(self):
        st.markdown('<div class="content-wrapper"><h3 style="color:#FFD700;">🔍 Explore</h3>', unsafe_allow_html=True)
        
        query = st.text_input("Search users", placeholder="Search...", key="explore_search")
        if query:
            users = self.user_manager.search_users(query, exclude_user_id=st.session_state.user_id)
            for u in users:
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:8px;">
                        {self.render_avatar_html(u, 36)}
                        <div>
                            <div style="color:#f1f5f9;font-weight:600;">@{html.escape(u['username'])}</div>
                            <div style="color:#94a3b8;font-size:0.65rem;">{Utils.format_number(u.get('follower_count', 0))} followers</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with c2:
                    if st.button("Follow", key=f"ef_{u['username']}"):
                        self.user_manager.follow_user(st.session_state.user_id, u['username'])
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_marketplace(self):
        st.markdown('<div class="content-wrapper"><h3 style="color:#FFD700;">🛒 Marketplace</h3>', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        # Create listing
        with st.expander("➕ Create Listing"):
            with st.form("marketplace_form"):
                title = st.text_input("Item title", max_chars=200)
                description = st.text_area("Description", max_chars=1000, height=80)
                price = st.number_input("Price ($)", min_value=0.0, step=0.01)
                media = st.file_uploader("Image", type=['png','jpg','jpeg','webp'])
                
                if st.form_submit_button("List Item"):
                    if title and price > 0:
                        media_data = None
                        if media and media.size <= Config.MAX_FILE_SIZE:
                            image_data = media.read()
                            if Utils.validate_image(image_data):
                                optimized = Utils.optimize_image(image_data)
                                media_data = base64.b64encode(optimized).decode()
                        
                        self.post_manager.create_post(
                            user['user_id'], f"🛒 {title}\n\n{description}",
                            media_data, media.name if media else None,
                            post_type="marketplace", price=price,
                            marketplace_status="for_sale"
                        )
                        st.success("Item listed!")
                        st.rerun()
        
        # Show marketplace posts
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, u.username, u.is_verified, pr.avatar_path, pr.gender
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE p.marketplace_status = 'for_sale' AND p.is_deleted = 0
                    ORDER BY p.timestamp DESC LIMIT 50
                """)
                
                for post in cursor.fetchall():
                    post_dict = dict(post)
                    self.render_post_card(post_dict)
        except: pass
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chats(self):
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        if st.session_state.active_chat:
            self.render_chat_interface()
        else:
            self.render_chat_list()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chat_list(self):
        st.markdown('<h3 style="color:#FFD700;">💬 Messages</h3>', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        chats = self.chat_manager.get_chat_list(user['user_id'])
        
        if not chats:
            st.info("No conversations yet")
        else:
            for chat in chats:
                online_dot = "🟢" if chat.get('is_online') else ""
                unread = f" <span style='background:#FFD700;color:#000;border-radius:50%;padding:1px 5px;font-size:0.6rem;'>{chat['unread_count']}</span>" if chat.get('unread_count', 0) > 0 else ""
                
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;padding:8px 0;
                         border-bottom:1px solid rgba(255,215,0,0.05);cursor:pointer;">
                    {self.render_avatar_html(chat, 40)}
                    <div style="flex:1;">
                        <div style="color:#f1f5f9;font-weight:600;">
                            @{html.escape(chat.get('other_username', 'unknown'))} {online_dot}{unread}
                        </div>
                        <div style="color:#94a3b8;font-size:0.65rem;">
                            {Utils.format_timestamp(chat.get('last_message_time'))}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Open", key=f"oc_{chat['other_username']}"):
                    st.session_state.active_chat = chat['other_username']
                    st.rerun()
    
    def render_chat_interface(self):
        if st.button("← Back", key="back_chat", use_container_width=True):
            st.session_state.active_chat = None
            st.rerun()
        
        with_user = self.user_manager.get_user_by_username(st.session_state.active_chat)
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not with_user or not user: return
        
        is_online = with_user['username'] in self.user_manager.get_online_users()
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;
                 border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:8px;">
            {self.render_avatar_html(with_user, 32)}
            <div>
                <div style="color:#f1f5f9;font-weight:600;">@{html.escape(with_user['username'])}</div>
                <div style="color:{'#4ade80' if is_online else '#94a3b8'};font-size:0.65rem;">
                    {'Online' if is_online else 'Offline'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        messages = self.chat_manager.get_messages(user['user_id'], with_user['user_id'])
        
        for msg in messages:
            is_sent = msg['from_id'] == user['user_id']
            align = "flex-end" if is_sent else "flex-start"
            cls = "sent" if is_sent else "received"
            
            st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin:2px 0;">
                <div class="chat-bubble {cls}">
                    {html.escape(msg.get('text', ''))}
                    <div style="font-size:0.5rem;opacity:0.7;text-align:right;margin-top:2px;">
                        {Utils.format_timestamp(msg['timestamp'])}
                        {' ✓✓' if is_sent and msg.get('is_read') else ' ✓' if is_sent else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"send_{with_user['user_id']}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input("Message", placeholder="Type...", key=f"mt_{with_user['user_id']}", label_visibility="collapsed")
            with c2:
                if st.form_submit_button("Send") and txt.strip():
                    self.chat_manager.send_message(user['user_id'], with_user['username'], txt)
                    st.rerun()
    
    def render_groups(self):
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        if st.session_state.get('active_group'):
            self.render_group_interface()
        else:
            st.markdown('<h3 style="color:#FFD700;">👥 Groups & Channels</h3>', unsafe_allow_html=True)
            
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if not user: return
            
            tab1, tab2 = st.tabs(["Groups", "Channels"])
            
            with tab1:
                groups = self.group_manager.get_user_groups(user['user_id'])
                for g in groups:
                    if not g.get('is_channel'):
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;
                                 border-bottom:1px solid rgba(255,215,0,0.05);">
                            <div style="width:36px;height:36px;border-radius:50%;background:#667eea;
                                     display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div>
                            <div style="flex:1;">
                                <div style="color:#f1f5f9;font-weight:600;">{html.escape(g['name'])}</div>
                                <div style="color:#94a3b8;font-size:0.65rem;">{g.get('member_count', 0)} members</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Open", key=f"og_{g['id']}"):
                            st.session_state.active_group = g['id']
                            st.rerun()
                
                with st.expander("➕ Create Group"):
                    with st.form("create_group_form"):
                        gn = st.text_input("Group name", max_chars=100)
                        gd = st.text_area("Description", max_chars=500)
                        if st.form_submit_button("Create") and gn:
                            self.group_manager.create_group(gn, user['user_id'], gd)
                            st.rerun()
            
            with tab2:
                channels = self.group_manager.get_user_groups(user['user_id'])
                for c in channels:
                    if c.get('is_channel'):
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:8px;padding:8px 0;
                                 border-bottom:1px solid rgba(255,215,0,0.05);">
                            <div style="width:36px;height:36px;border-radius:50%;background:#f093fb;
                                     display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div>
                            <div style="flex:1;">
                                <div style="color:#f1f5f9;font-weight:600;">{html.escape(c['name'])}</div>
                                <div style="color:#94a3b8;font-size:0.65rem;">{c.get('member_count', 0)} subscribers</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Open", key=f"och_{c['id']}"):
                            st.session_state.active_group = c['id']
                            st.rerun()
                
                with st.expander("➕ Create Channel"):
                    with st.form("create_channel_form"):
                        cn = st.text_input("Channel name", max_chars=100)
                        cd = st.text_area("Description", max_chars=500)
                        if st.form_submit_button("Create") and cn:
                            self.group_manager.create_group(cn, user['user_id'], cd, is_channel=True)
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_group_interface(self):
        if st.button("← Back", key="back_group", use_container_width=True):
            st.session_state.active_group = None
            st.rerun()
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        gid = st.session_state.active_group
        messages = self.group_manager.get_group_messages(gid)
        
        for msg in messages:
            st.markdown(f"""
            <div style="margin:4px 0;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                <div style="display:flex;align-items:center;gap:6px;">
                    {self.render_avatar_html(msg, 20)}
                    <span style="color:#FFD700;font-weight:600;font-size:0.75rem;">@{html.escape(msg.get('username', 'unknown'))}</span>
                    <span style="color:#64748b;font-size:0.55rem;">{Utils.format_timestamp(msg['timestamp'])}</span>
                </div>
                <div style="color:#e2e8f0;font-size:0.8rem;margin-top:4px;">{html.escape(msg.get('text', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"send_group_{gid}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                txt = st.text_input("Message", placeholder="Type...", key=f"gt_{gid}", label_visibility="collapsed")
            with c2:
                if st.form_submit_button("Send") and txt.strip():
                    self.group_manager.send_message(gid, user['user_id'], txt)
                    st.rerun()
    
    def render_notifications(self):
        st.markdown('<div class="content-wrapper"><h3 style="color:#FFD700;">🔔 Notifications</h3>', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        notifications = self.notification_manager.get_notifications(user['user_id'])
        
        if notifications:
            if st.button("Mark All Read", use_container_width=True):
                self.notification_manager.mark_all_read(user['user_id'])
                st.rerun()
        
        for n in notifications:
            icon = {'follow': '👤', 'like': '❤️', 'reaction': '❤️', 'comment': '💬', 'mention': '@', 'message': '💬'}.get(n['type'], '🔔')
            bg = 'rgba(255,215,0,0.05)' if not n['is_read'] else 'transparent'
            
            st.markdown(f"""
            <div style="padding:8px;margin:2px 0;background:{bg};border-radius:8px;display:flex;gap:8px;align-items:center;">
                <span>{icon}</span>
                <div style="flex:1;">
                    <span style="color:#e2e8f0;font-size:0.8rem;">{html.escape(n['message'])}</span>
                    {f"<span style='color:#FFD700;'> @{html.escape(n['from_username'])}</span>" if n.get('from_username') else ""}
                </div>
                <span style="color:#64748b;font-size:0.6rem;">{Utils.format_timestamp(n['timestamp'])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_profile(self):
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            st.error("User not found")
            return
        
        follower_count = self._get_follower_count(user['user_id'])
        following_count = self._get_following_count(user['user_id'])
        
        # Profile header - NO HTML TAGS SHOWING
        display_name = html.escape(user.get('display_name', user['username']))
        bio = html.escape(user.get('bio', ''))
        website = html.escape(user.get('website', ''))
        location = html.escape(user.get('location', ''))
        
        verified_badge = " ✓" if user.get('is_verified') else ""
        premium_badge = " 👑" if user.get('is_premium') else ""
        
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
            {self.render_avatar_html(user, 80)}
            <h2 style="color:#FFD700;margin-top:10px;">
                @{html.escape(user['username'])}
                <span style="color:#FFD700;">{verified_badge}{premium_badge}</span>
            </h2>
        """, unsafe_allow_html=True)
        
        if display_name and display_name != user['username']:
            st.markdown(f'<p style="color:#94a3b8;font-size:0.9rem;margin:5px 0;">{display_name}</p>', unsafe_allow_html=True)
        
        if bio:
            st.markdown(f'<p style="color:#94a3b8;font-size:0.85rem;margin:5px 0;">{bio}</p>', unsafe_allow_html=True)
        
        if website:
            st.markdown(f'<p style="color:#94a3b8;font-size:0.75rem;">🌐 {website}</p>', unsafe_allow_html=True)
        
        if location:
            st.markdown(f'<p style="color:#94a3b8;font-size:0.75rem;">📍 {location}</p>', unsafe_allow_html=True)
        
        st.markdown(f"""
            <div style="display:flex;justify-content:space-around;margin-top:20px;padding:15px 0;
                     border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);">
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">{Utils.format_number(user.get('total_posts', 0))}</div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Posts</div>
                </div>
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">{Utils.format_number(follower_count)}</div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Followers</div>
                </div>
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">{Utils.format_number(following_count)}</div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Following</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Edit Profile
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile_form"):
                display_name_input = st.text_input("Display Name", value=user.get('display_name', ''), max_chars=50)
                bio_input = st.text_area("Bio", value=user.get('bio', ''), max_chars=Config.MAX_BIO_LENGTH, height=80)
                
                c1, c2 = st.columns(2)
                with c1:
                    website_input = st.text_input("Website", value=user.get('website', ''))
                with c2:
                    location_input = st.text_input("Location", value=user.get('location', ''))
                
                gender_input = st.selectbox("Gender", ['male', 'female'], index=0 if user.get('gender') == 'male' else 1)
                private_input = st.checkbox("Private Account", value=user.get('is_private', False))
                
                avatar_file = st.file_uploader("Profile Picture", type=['png','jpg','jpeg','webp'])
                
                if st.form_submit_button("💾 Save", use_container_width=True):
                    updates = {
                        'display_name': Utils.sanitize_text(display_name_input, 50),
                        'bio': Utils.sanitize_text(bio_input, Config.MAX_BIO_LENGTH),
                        'website': Utils.sanitize_text(website_input, 200),
                        'location': Utils.sanitize_text(location_input, 100),
                        'gender': gender_input,
                        'is_private': private_input
                    }
                    
                    if avatar_file and avatar_file.size <= Config.MAX_AVATAR_SIZE:
                        try:
                            image_data = avatar_file.read()
                            if Utils.validate_image(image_data):
                                optimized = Utils.optimize_image(image_data, (400, 400))
                                avatar_path = Config.UPLOADS_DIR / f"avatar_{user['user_id']}.jpg"
                                with open(avatar_path, 'wb') as f:
                                    f.write(optimized)
                                updates['avatar_path'] = str(avatar_path)
                        except: pass
                    
                    if self.user_manager.update_profile(user['user_id'], updates):
                        st.success("Profile updated!")
                        st.rerun()
        
        # Themes
        with st.expander("🎨 Themes"):
            cols = st.columns(4)
            current_theme = user.get('theme', 'midnight')
            for i, (tk, td) in enumerate(THEMES.items()):
                with cols[i % 4]:
                    if st.button(f"{td['icon']} {td['name']}", key=f"th_{tk}", use_container_width=True,
                               help=f"Apply {td['name']} theme"):
                        self.user_manager.update_profile(user['user_id'], {'theme': tk})
                        st.rerun()
        
        # Sign out
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_create_modal(self):
        st.markdown('<div class="modal-overlay"><div class="modal-box">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;text-align:center;">✨ Create Post</h3>', unsafe_allow_html=True)
        
        t1, t2 = st.tabs(["📝 Post", "📊 Poll"])
        
        with t1:
            with st.form("create_post_form", clear_on_submit=True):
                text = st.text_area("What's on your mind?", max_chars=Config.MAX_POST_LENGTH, height=100)
                media = st.file_uploader("Add image", type=['png','jpg','jpeg','gif','webp'])
                location = st.text_input("Location", placeholder="Add location")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("Post", use_container_width=True):
                        md = None
                        if media and media.size <= Config.MAX_FILE_SIZE:
                            image_data = media.read()
                            if Utils.validate_image(image_data):
                                optimized = Utils.optimize_image(image_data)
                                md = base64.b64encode(optimized).decode()
                        
                        if text.strip() or md:
                            self.post_manager.create_post(
                                st.session_state.user_id, text, md,
                                media.name if media else None,
                                location=location
                            )
                            st.session_state.show_create_modal = False
                            st.rerun()
                with c2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        with t2:
            with st.form("create_poll_form", clear_on_submit=True):
                question = st.text_input("Question", max_chars=500)
                options_text = st.text_area("Options (one per line)", height=80)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("Create Poll", use_container_width=True):
                        if question and options_text:
                            opts = [o.strip() for o in options_text.split('\n') if o.strip()]
                            if len(opts) >= 2:
                                poll_data = {'question': question, 'options': opts}
                                self.post_manager.create_post(
                                    st.session_state.user_id, question,
                                    post_type='poll', poll_data=poll_data
                                )
                                st.session_state.show_create_modal = False
                                st.rerun()
                with c2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        if st.button("✕ Close", use_container_width=True):
            st.session_state.show_create_modal = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_bottom_nav(self):
        current = st.session_state.current_tab
        
        nav_items = [
            ('feed', '🏠', 'Feed'),
            ('explore', '🔍', 'Explore'),
            ('marketplace', '🛒', 'Shop'),
            ('chats', '💬', 'Chats'),
            ('groups', '👥', 'Groups'),
            ('profile', '👤', 'Profile'),
        ]
        
        # Create columns for each nav item
        cols = st.columns(len(nav_items))
        
        for i, (tab, icon, label) in enumerate(nav_items):
            with cols[i]:
                is_active = current == tab
                
                if is_active:
                    st.markdown(f"""
                    <div class="nav-item active">
                        <div class="nav-icon">{icon}</div>
                        <div class="nav-label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if st.button(icon, key=f"nav_{tab}", use_container_width=True):
                        st.session_state.current_tab = tab
                        st.session_state.show_create_modal = False
                        st.session_state.active_chat = None
                        st.session_state.active_group = None
                        st.rerun()
                    st.markdown(f"""
                    <div style="text-align:center;margin-top:-8px;">
                        <span style="color:#94a3b8;font-size:0.5rem;">{label}</span>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_auth(self):
        st.markdown("""
        <style>
        .stApp {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            background: linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%) !important;
            overflow: auto !important;
        }
        .main { height: auto !important; overflow: visible !important; }
        .block-container { height: auto !important; overflow: visible !important; padding: 2rem 1rem !important; max-width: 100% !important; }
        </style>
        """, unsafe_allow_html=True)
        
        _, center, _ = st.columns([1, 2, 1])
        
        with center:
            st.markdown('<div class="auth-container">', unsafe_allow_html=True)
            
            # Logo
            st.markdown(f"""
            <div style="text-align:center;margin-bottom:1.5rem;">
                <div style="font-size:5rem;filter:drop-shadow(0 0 30px rgba(255,215,0,0.6));animation:float 3s ease-in-out infinite;">
                    👑
                </div>
                <h1 class="brand-title">SOCIALITE</h1>
                <p style="color:#94a3b8;font-size:0.9rem;font-family:'Playfair Display',serif;">Where Luxury Meets Connection</p>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter username", key="li_u")
                    password = st.text_input("Password", type="password", placeholder="Enter password", key="li_p")
                    
                    if st.form_submit_button("Sign In", use_container_width=True):
                        if username and password:
                            success, result = self.user_manager.authenticate(username, password)
                            if success:
                                st.session_state.auth = True
                                st.session_state.username = result
                                user = self.user_manager.get_user_by_username(result)
                                if user:
                                    st.session_state.user_id = user['user_id']
                                st.rerun()
                            else:
                                st.error(result)
                        else:
                            st.error("Please fill all fields")
            
            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Choose Username", placeholder="3-30 chars, letters/numbers only", key="su_u")
                    email = st.text_input("Email (optional)", placeholder="your@email.com", key="su_e")
                    new_password = st.text_input("Choose Password", type="password", placeholder=f"Min {Config.MIN_PASSWORD_LENGTH} chars", key="su_p")
                    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="su_cp")
                    
                    if st.form_submit_button("Create Account", use_container_width=True):
                        if not new_username or not new_password:
                            st.error("Please fill required fields")
                        elif new_password != confirm_password:
                            st.error("Passwords don't match")
                        elif len(new_password) < Config.MIN_PASSWORD_LENGTH:
                            st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                        else:
                            success, message = self.user_manager.create_user(new_username, new_password, email)
                            if success:
                                st.success(message)
                                st.info("Please sign in!")
                            else:
                                st.error(message)
            
            # Features
            st.markdown("""
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(255,215,0,0.1);">
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">📝</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Posts</div>
                </div>
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">💬</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Chat</div>
                </div>
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">🛒</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Market</div>
                </div>
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">👥</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Groups</div>
                </div>
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">🎨</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Themes</div>
                </div>
                <div style="text-align:center;padding:8px;background:rgba(255,255,255,0.03);border-radius:8px;">
                    <div style="font-size:1.5rem;">🔒</div>
                    <div style="color:#94a3b8;font-size:0.65rem;">Secure</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_avatar_html(self, user_data: Dict, size: int = 36) -> str:
        if isinstance(user_data, dict):
            username = user_data.get('username', '')
            avatar_path = user_data.get('avatar_path')
        else:
            username = str(user_data)
            avatar_path = None
        
        if avatar_path and os.path.exists(avatar_path):
            try:
                with open(avatar_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #FFD700;flex-shrink:0;" alt="">'
            except: pass
        
        color = Utils.get_avatar_color(username)
        initials = Utils.get_initials(username)
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:{size*0.4}px;flex-shrink:0;border:2px solid #FFD700;">{initials}</div>'
    
    def _get_current_theme(self) -> str:
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                return user.get('theme', 'midnight')
        return 'midnight'
    
    def _get_follower_count(self, user_id: int) -> int:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE following_id = ? AND is_accepted = 1", (user_id,))
                return cursor.fetchone()['count']
        except: return 0
    
    def _get_following_count(self, user_id: int) -> int:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = ? AND is_accepted = 1", (user_id,))
                return cursor.fetchone()['count']
        except: return 0

# ========== MAIN ==========
def main():
    try:
        app = SocialiteUI()
        app.render()
    except Exception as e:
        logger.error(f"App error: {e}", exc_info=True)
        st.error("An error occurred. Please refresh.")

if __name__ == "__main__":
    main()
