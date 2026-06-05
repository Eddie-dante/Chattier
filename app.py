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
import pickle
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
        'About': "Socialite - The Premium Social Experience v5.0"
    }
)

# ========== CONFIGURATION ==========
class Config:
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "5.0.0"
    LOGO_URL = "https://drive.google.com/uc?export=view&id=1Rxb3t3yLEdrqS6hWZJw4DPg6T1PNSkKb"
    
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
    ONLINE_THRESHOLD_SECONDS = 300
    CACHE_TTL_SECONDS = 60

for dir_path in [Config.DATA_DIR, Config.UPLOADS_DIR, Config.BACKUP_DIR, 
                 Config.CACHE_DIR, Config.LOGS_DIR, Config.TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(Config.LOGS_DIR / 'socialite.log'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ========== UTILITY FUNCTIONS ==========
class Utils:
    @staticmethod
    def generate_id() -> str: return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 12) -> str: return str(uuid.uuid4())[:length]
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        if salt is None: salt = secrets.token_hex(32)
        h = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 300000)
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        try:
            h, _ = Utils.hash_password(password, salt)
            return h == stored_hash
        except: return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        if not text: return ""
        text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
        text = html.escape(str(text).strip())
        if len(text) > max_length: text = text[:max_length-3] + "..."
        return text
    
    @staticmethod
    def format_timestamp(ts) -> str:
        if not ts: return ""
        try:
            if isinstance(ts, str): t = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else: t = ts
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
        except: return "unknown"
    
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
        except: return False
    
    @staticmethod
    def optimize_image(data: bytes, max_size: Tuple[int, int] = (1200, 1200), quality: int = 85) -> bytes:
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
        except: return data
    
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

# ========== CACHE SYSTEM ==========
class CacheSystem:
    def __init__(self, max_size: int = 1000):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    self._cache.move_to_end(key)
                    return value
                else: del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = Config.CACHE_TTL_SECONDS):
        with self._lock:
            if key in self._cache: del self._cache[key]
            elif len(self._cache) >= self._max_size: self._cache.popitem(last=False)
            self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        with self._lock: self._cache.pop(key, None)
    
    def clear(self):
        with self._lock: self._cache.clear()

# ========== RATE LIMITER ==========
class RateLimiter:
    def __init__(self):
        self._limits = defaultdict(lambda: defaultdict(list))
        self._lock = threading.Lock()
    
    def can_act(self, user_id: Any, action: str, limit: int = 5, window: float = 60.0) -> bool:
        now = time.time()
        with self._lock:
            self._limits[user_id][action] = [t for t in self._limits[user_id][action] if now - t < window]
            if len(self._limits[user_id][action]) >= limit: return False
            self._limits[user_id][action].append(now)
            return True

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
            self._local.connection = sqlite3.connect(str(Config.DB_PATH), check_same_thread=False, timeout=30)
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            self._local.connection.execute("PRAGMA cache_size=-20000")
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
                    reputation_score REAL DEFAULT 0.0,
                    account_status TEXT DEFAULT 'active',
                    wallet_balance REAL DEFAULT 0.0
                )
            """)
            
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
                    wallpaper TEXT DEFAULT '🌈 Gradient',
                    language TEXT DEFAULT 'en',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
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
                    price REAL DEFAULT 0.0,
                    is_for_sale BOOLEAN DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
                    edited_at TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    visibility TEXT DEFAULT 'public',
                    view_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
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
                    is_delivered BOOLEAN DEFAULT 1,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups_chat (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    description TEXT DEFAULT '',
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
                    FOREIGN KEY (group_id) REFERENCES groups_chat(id) ON DELETE CASCADE,
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
                    FOREIGN KEY (group_id) REFERENCES groups_chat(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketplace (
                    id TEXT PRIMARY KEY,
                    seller_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price REAL NOT NULL,
                    category TEXT DEFAULT 'other',
                    condition TEXT DEFAULT 'new',
                    media_data TEXT,
                    media_name TEXT,
                    location TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_posts_time ON posts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_marketplace_seller ON marketplace(seller_id)",
            ]
            for idx in indexes:
                try: cursor.execute(idx)
                except: pass
            
            conn.commit()

# ========== USER MANAGER ==========
class UserManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = CacheSystem(max_size=500)
    
    def create_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        username = username.strip().lower()
        if len(username) < 3: return False, "Username must be at least 3 characters"
        if len(username) > Config.MAX_USERNAME_LENGTH: return False, f"Username must be {Config.MAX_USERNAME_LENGTH} characters or less"
        if not re.match(r'^[a-zA-Z0-9_]+$', username): return False, "Username can only contain letters, numbers, and underscores"
        if len(password) < Config.MIN_PASSWORD_LENGTH: return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone(): return False, "Username already exists"
                
                password_hash, salt = Utils.hash_password(password)
                cursor.execute("INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)", (username, email, password_hash, salt))
                user_id = cursor.lastrowid
                cursor.execute("INSERT INTO profiles (user_id, display_name) VALUES (?, ?)", (user_id, username))
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
                cursor.execute("SELECT id, username, password_hash, salt, login_attempts, locked_until, is_banned, is_deleted FROM users WHERE username = ? OR LOWER(username) = LOWER(?)", (username, username))
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
                        else:
                            cursor.execute("UPDATE users SET locked_until = NULL, login_attempts = 0 WHERE id = ?", (user['id'],))
                    except: pass
                
                if Utils.verify_password(password, user['password_hash'], user['salt']):
                    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP, login_attempts = 0 WHERE id = ?", (user['id'],))
                    conn.commit()
                    self.cache.delete(f"user_{user['username']}")
                    return True, user['username']
                else:
                    attempts = user['login_attempts'] + 1
                    if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        lock_until = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
                        cursor.execute("UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?", (attempts, lock_until.isoformat(), user['id']))
                    else:
                        cursor.execute("UPDATE users SET login_attempts = ? WHERE id = ?", (attempts, user['id']))
                    conn.commit()
                    remaining = Config.MAX_LOGIN_ATTEMPTS - attempts
                    return False, f"Incorrect password. {remaining} attempts remaining"
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False, "An error occurred"
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        cache_key = f"user_{username}"
        cached = self.cache.get(cache_key)
        if cached: return cached
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT u.*, p.* FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.username = ? AND u.is_deleted = 0", (username,))
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    self.cache.set(cache_key, user_data, ttl=300)
                    return user_data
        except: pass
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        cache_key = f"user_id_{user_id}"
        cached = self.cache.get(cache_key)
        if cached: return cached
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT u.*, p.* FROM users u LEFT JOIN profiles p ON u.id = p.user_id WHERE u.id = ? AND u.is_deleted = 0", (user_id,))
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    self.cache.set(cache_key, user_data, ttl=300)
                    return user_data
        except: pass
        return None
    
    def update_profile(self, user_id: int, updates: Dict) -> bool:
        try:
            valid_fields = ['display_name', 'bio', 'avatar_path', 'cover_path', 'website', 'location', 'birthday', 'gender', 'is_private', 'theme', 'wallpaper', 'language']
            filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
            if not filtered_updates: return False
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
                values = list(filtered_updates.values()) + [user_id]
                cursor.execute(f"UPDATE profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", values)
                conn.commit()
                user = self.get_user_by_id(user_id)
                if user:
                    self.cache.delete(f"user_{user['username']}")
                    self.cache.delete(f"user_id_{user_id}")
                return True
        except: return False
    
    def update_last_seen(self, user_id: int):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
                conn.commit()
        except: pass
    
    def get_online_users(self) -> List[str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now() - timedelta(seconds=Config.ONLINE_THRESHOLD_SECONDS)
                cursor.execute("SELECT username FROM users WHERE last_login >= ? AND is_banned = 0 AND is_deleted = 0", (cutoff.isoformat(),))
                return [row['username'] for row in cursor.fetchall()]
        except: return []
    
    def search_users(self, query: str, limit: int = 50, exclude_user_id: int = None) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                query_params = [f"%{query}%", f"%{query}%"]
                sql = """SELECT DISTINCT u.username, u.is_verified, u.is_premium, u.id, p.display_name, p.bio, p.avatar_path, p.gender,
                         (SELECT COUNT(*) FROM follows WHERE following_id = u.id AND is_accepted = 1) as follower_count
                         FROM users u LEFT JOIN profiles p ON u.id = p.user_id
                         WHERE u.is_banned = 0 AND u.is_deleted = 0 AND u.account_status = 'active'
                         AND (u.username LIKE ? OR p.display_name LIKE ?)"""
                if exclude_user_id:
                    sql += " AND u.id != ?"
                    query_params.append(exclude_user_id)
                sql += " ORDER BY follower_count DESC LIMIT ?"
                query_params.append(limit)
                cursor.execute(sql, query_params)
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def follow_user(self, follower_id: int, following_username: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, is_private FROM users WHERE username = ? AND is_deleted = 0", (following_username,))
                target = cursor.fetchone()
                if not target: return False, "User not found"
                following_id = target['id']
                if follower_id == following_id: return False, "Cannot follow yourself"
                cursor.execute("SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (following_id, follower_id))
                if cursor.fetchone(): return False, "You are blocked"
                cursor.execute("SELECT is_accepted FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                    conn.commit()
                    return True, f"Unfollowed @{following_username}"
                else:
                    is_accepted = not target['is_private']
                    cursor.execute("INSERT INTO follows (follower_id, following_id, is_accepted) VALUES (?, ?, ?)", (follower_id, following_id, 1 if is_accepted else 0))
                    if is_accepted:
                        self._create_notification(cursor, following_id, 'follow', "started following you", follower_id)
                    conn.commit()
                    return True, f"Now following @{following_username}" if is_accepted else "Follow request sent"
        except: return False, "An error occurred"
    
    def _create_notification(self, cursor, user_id: int, ntype: str, message: str, from_user_id: int = None):
        try:
            cursor.execute("INSERT INTO notifications (id, user_id, type, message, from_user_id) VALUES (?, ?, ?, ?, ?)", (Utils.generate_id(), user_id, ntype, message, from_user_id))
        except: pass

# ========== POST MANAGER ==========
class PostManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = CacheSystem(max_size=300)
    
    def create_post(self, user_id: int, text: str = "", media_data: str = None, media_name: str = None, post_type: str = "post", location: str = "", poll_data: Dict = None, price: float = 0.0, is_for_sale: bool = False) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_POST_LENGTH) if text else ""
        if not text and not media_data and not poll_data: return False, "Post cannot be empty"
        try:
            post_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO posts (id, user_id, text, media_data, media_name, post_type, location, price, is_for_sale) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (post_id, user_id, text, media_data, media_name, post_type, location, price, is_for_sale))
                if poll_data and post_type == 'poll':
                    cursor.execute("INSERT INTO polls (post_id, question, ends_at) VALUES (?, ?, ?)", (post_id, poll_data['question'], poll_data.get('ends_at')))
                    for option in poll_data.get('options', []):
                        cursor.execute("INSERT INTO poll_options (post_id, option_text) VALUES (?, ?)", (post_id, option))
                cursor.execute("UPDATE users SET total_posts = total_posts + 1 WHERE id = ?", (user_id,))
                conn.commit()
                return True, post_id
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return False, "Failed to create post"
    
    def get_post(self, post_id: str, user_id: int = None) -> Optional[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT p.*, u.username, u.is_verified, u.is_premium, pr.display_name, pr.avatar_path, pr.gender FROM posts p JOIN users u ON p.user_id = u.id LEFT JOIN profiles pr ON u.id = pr.user_id WHERE p.id = ? AND p.is_deleted = 0", (post_id,))
                post = cursor.fetchone()
                if post:
                    post_dict = dict(post)
                    if post_dict['post_type'] == 'poll':
                        cursor.execute("SELECT po.*, (SELECT COUNT(*) FROM poll_votes WHERE option_id = po.id) as vote_count FROM poll_options po WHERE po.post_id = ?", (post_id,))
                        post_dict['poll_options'] = [dict(row) for row in cursor.fetchall()]
                    cursor.execute("SELECT reaction_type, COUNT(*) as count FROM reactions WHERE post_id = ? GROUP BY reaction_type", (post_id,))
                    post_dict['reactions'] = {row['reaction_type']: row['count'] for row in cursor.fetchall()}
                    if user_id:
                        cursor.execute("SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                        user_reaction = cursor.fetchone()
                        post_dict['user_reaction'] = user_reaction['reaction_type'] if user_reaction else None
                    cursor.execute("SELECT COUNT(*) as count FROM comments WHERE post_id = ? AND is_deleted = 0", (post_id,))
                    post_dict['comment_count'] = cursor.fetchone()['count']
                    return post_dict
        except: pass
        return None
    
    def get_feed(self, user_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], bool]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                offset = (page - 1) * per_page
                cursor.execute("""SELECT p.id FROM posts p WHERE p.is_deleted = 0 AND p.visibility = 'public'
                    AND (p.user_id = ? OR p.user_id IN (SELECT following_id FROM follows WHERE follower_id = ? AND is_accepted = 1))
                    AND p.user_id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = ?)
                    ORDER BY p.timestamp DESC LIMIT ? OFFSET ?""", (user_id, user_id, user_id, per_page + 1, offset))
                post_ids = [row['id'] for row in cursor.fetchall()]
                has_more = len(post_ids) > per_page
                if has_more: post_ids = post_ids[:per_page]
                posts = []
                for pid in post_ids:
                    post = self.get_post(pid, user_id)
                    if post: posts.append(post)
                return posts, has_more
        except: return [], False
    
    def add_reaction(self, post_id: str, user_id: int, reaction_type: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("DELETE FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                    conn.commit()
                    return True, "Reaction removed"
                else:
                    cursor.execute("INSERT INTO reactions (post_id, user_id, reaction_type) VALUES (?, ?, ?)", (post_id, user_id, reaction_type))
                    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                    post = cursor.fetchone()
                    if post and post['user_id'] != user_id:
                        self._create_notification(cursor, post['user_id'], 'reaction', "reacted to your post", user_id)
                    conn.commit()
                    return True, "Reaction added"
        except: return False, "Failed"
    
    def get_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT c.*, u.username, u.is_verified, pr.display_name, pr.avatar_path, pr.gender
                    FROM comments c JOIN users u ON c.user_id = u.id LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE c.post_id = ? AND c.is_deleted = 0 ORDER BY c.timestamp ASC LIMIT ?""", (post_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def add_comment(self, post_id: str, user_id: int, text: str) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_COMMENT_LENGTH)
        if not text: return False, "Comment cannot be empty"
        try:
            comment_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO comments (id, post_id, user_id, text) VALUES (?, ?, ?, ?)", (comment_id, post_id, user_id, text))
                cursor.execute("UPDATE users SET total_comments = total_comments + 1 WHERE id = ?", (user_id,))
                cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                post = cursor.fetchone()
                if post and post['user_id'] != user_id:
                    self._create_notification(cursor, post['user_id'], 'comment', "commented on your post", user_id)
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
                if post['user_id'] != user_id: return False, "You can only delete your own posts"
                cursor.execute("UPDATE posts SET is_deleted = 1 WHERE id = ?", (post_id,))
                cursor.execute("UPDATE users SET total_posts = MAX(0, total_posts - 1) WHERE id = ?", (user_id,))
                conn.commit()
                return True, "Post deleted"
        except: return False, "Failed to delete post"
    
    def _create_notification(self, cursor, user_id: int, ntype: str, message: str, from_user_id: int = None):
        try:
            cursor.execute("INSERT INTO notifications (id, user_id, type, message, from_user_id) VALUES (?, ?, ?, ?, ?)", (Utils.generate_id(), user_id, ntype, message, from_user_id))
        except: pass

# ========== CHAT MANAGER ==========
class ChatManager:
    def __init__(self, db: DatabaseManager): self.db = db
    
    def send_message(self, from_id: int, to_username: str, text: str = "") -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_MESSAGE_LENGTH) if text else ""
        if not text: return False, "Message cannot be empty"
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ? AND is_deleted = 0", (to_username,))
                to_user = cursor.fetchone()
                if not to_user: return False, "User not found"
                to_id = to_user['id']
                cursor.execute("SELECT 1 FROM blocks WHERE blocker_id = ? AND blocked_id = ?", (to_id, from_id))
                if cursor.fetchone(): return False, "You are blocked"
                chat_id = self._get_chat_id(from_id, to_id)
                message_id = Utils.generate_id()
                cursor.execute("INSERT INTO messages (id, chat_id, from_id, to_id, text) VALUES (?, ?, ?, ?, ?)", (message_id, chat_id, from_id, to_id, text))
                cursor.execute("INSERT INTO notifications (id, user_id, type, message, from_user_id) VALUES (?, ?, ?, ?, ?)", (Utils.generate_id(), to_id, 'message', "sent you a message", from_id))
                conn.commit()
                return True, message_id
        except: return False, "Failed to send message"
    
    def get_messages(self, user_id: int, with_user_id: int, limit: int = 50) -> List[Dict]:
        try:
            chat_id = self._get_chat_id(user_id, with_user_id)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE messages SET is_read = 1 WHERE chat_id = ? AND to_id = ? AND is_read = 0", (chat_id, user_id))
                cursor.execute("""SELECT m.*, u.username as from_username, pr.avatar_path, pr.gender
                    FROM messages m JOIN users u ON m.from_id = u.id LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE m.chat_id = ? AND m.is_deleted = 0 ORDER BY m.timestamp DESC LIMIT ?""", (chat_id, limit))
                messages = [dict(row) for row in cursor.fetchall()]
                messages.reverse()
                conn.commit()
                return messages
        except: return []
    
    def get_chat_list(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT CASE WHEN m.from_id = ? THEN m.to_id ELSE m.from_id END as other_user_id,
                    u.username as other_username, u.is_verified, MAX(m.timestamp) as last_message_time,
                    COUNT(CASE WHEN m.to_id = ? AND m.is_read = 0 THEN 1 END) as unread_count
                    FROM messages m JOIN users u ON (CASE WHEN m.from_id = ? THEN m.to_id = u.id ELSE m.from_id = u.id END)
                    WHERE (m.from_id = ? OR m.to_id = ?) AND m.is_deleted = 0
                    GROUP BY other_user_id ORDER BY last_message_time DESC""", (user_id, user_id, user_id, user_id, user_id))
                chats = []
                online_users = set(UserManager(self.db).get_online_users())
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
    def __init__(self, db: DatabaseManager): self.db = db
    
    def create_group(self, name: str, owner_id: int, description: str = "", is_channel: bool = False) -> Tuple[bool, str]:
        name = Utils.sanitize_text(name, 100)
        if not name: return False, "Name required"
        try:
            group_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO groups_chat (id, name, owner_id, description, is_channel) VALUES (?, ?, ?, ?, ?)", (group_id, name, owner_id, description, is_channel))
                cursor.execute("INSERT INTO group_members (group_id, user_id, role) VALUES (?, ?, 'admin')", (group_id, owner_id))
                conn.commit()
                return True, group_id
        except Exception as e: return False, f"Failed: {e}"
    
    def add_member(self, group_id: str, username: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                user = cursor.fetchone()
                if not user: return False, "User not found"
                cursor.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user['id']))
                cursor.execute("UPDATE groups_chat SET member_count = member_count + 1 WHERE id = ?", (group_id,))
                conn.commit()
                return True, "Member added"
        except: return False, "Failed"
    
    def send_message(self, group_id: str, from_id: int, text: str) -> Tuple[bool, str]:
        text = Utils.sanitize_text(text, Config.MAX_MESSAGE_LENGTH)
        if not text: return False, "Message cannot be empty"
        try:
            message_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO group_messages (id, group_id, from_id, text) VALUES (?, ?, ?, ?)", (message_id, group_id, from_id, text))
                conn.commit()
                return True, message_id
        except: return False, "Failed"
    
    def get_user_groups(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT g.* FROM groups_chat g JOIN group_members gm ON g.id = gm.group_id WHERE gm.user_id = ? AND g.is_channel = 0 ORDER BY g.created_at DESC", (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def get_user_channels(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT g.* FROM groups_chat g JOIN group_members gm ON g.id = gm.group_id WHERE gm.user_id = ? AND g.is_channel = 1 ORDER BY g.created_at DESC", (user_id,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []
    
    def get_group_messages(self, group_id: str, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""SELECT gm.*, u.username, pr.avatar_path, pr.gender
                    FROM group_messages gm JOIN users u ON gm.from_id = u.id LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE gm.group_id = ? ORDER BY gm.timestamp ASC LIMIT ?""", (group_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except: return []

# ========== MARKETPLACE MANAGER ==========
class MarketplaceManager:
    def __init__(self, db: DatabaseManager): self.db = db
    
    def create_listing(self, seller_id: int, title: str, description: str, price: float, category: str = "other", condition: str = "new", media_data: str = None, media_name: str = None, location: str = "") -> Tuple[bool, str]:
        title = Utils.sanitize_text(title, 200)
        if not title: return False, "Title required"
        if price <= 0: return False, "Price must be positive"
        try:
            listing_id = Utils.generate_id()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO marketplace (id, seller_id, title, description, price, category, condition, media_data, media_name, location) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (listing_id, seller_id, title, description, price, category, condition, media_data, media_name, location))
                conn.commit()
                return True, listing_id
        except: return False, "Failed to create listing"
    
    def get_listings(self, category: str = None, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                if category:
                    cursor.execute("SELECT m.*, u.username as seller_username, u.is_verified FROM marketplace m JOIN users u ON m.seller_id = u.id WHERE m.status = 'active' AND m.category = ? ORDER BY m.created_at DESC LIMIT ?", (category, limit))
                else:
                    cursor.execute("SELECT m.*, u.username as seller_username, u.is_verified FROM marketplace m JOIN users u ON m.seller_id = u.id WHERE m.status = 'active' ORDER BY m.created_at DESC LIMIT ?", (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except: return []

# ========== NOTIFICATION MANAGER ==========
class NotificationManager:
    def __init__(self, db: DatabaseManager): self.db = db
    
    def get_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT n.*, u.username as from_username FROM notifications n LEFT JOIN users u ON n.from_user_id = u.id WHERE n.user_id = ? ORDER BY n.timestamp DESC LIMIT ?", (user_id, limit))
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
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
                conn.commit()
        except: pass

# ========== THEMES & WALLPAPERS ==========
THEMES = {
    "midnight": {"name": "Midnight Galaxy", "icon": "🌌", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"},
    "ocean": {"name": "Deep Ocean", "icon": "🌊", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"},
    "sunset": {"name": "Golden Sunset", "icon": "🌅", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)"},
    "forest": {"name": "Enchanted Forest", "icon": "🌲", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50", "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)"},
    "royal": {"name": "Royal Purple", "icon": "👑", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)"},
    "crimson": {"name": "Crimson Red", "icon": "❤️", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336", "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)"},
    "arctic": {"name": "Arctic Frost", "icon": "❄️", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)"},
    "neon": {"name": "Neon Nights", "icon": "💜", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
}

WALLPAPERS = {
    "🌈 Gradient": "gradient",
    "✨ Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&q=60",
    "🌌 Nebula": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60",
    "🌊 Ocean": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=800&q=60",
    "🏔️ Stars": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60",
    "🌸 Cherry": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=60",
    "🌅 Sunset": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&q=60",
    "🌿 Forest": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=60",
    "🏙️ City": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=60",
    "🔥 Lava": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=60",
    "🎨 Cyber": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=800&q=60",
    "🏝️ Beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=60",
    "❄️ Aurora": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60",
    "🍁 Autumn": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=800&q=60",
    "💜 Lavender": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=800&q=60",
    "🏔️ Alpine": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60",
    "🌄 Desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800&q=60",
    "🌻 Sunflower": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=800&q=60",
    "🏰 Northern": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=800&q=60",
    "🎆 Fireworks": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=800&q=60",
    "🌊 Storm": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800&q=60",
    "🏖️ Crystal": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=800&q=60",
    "🏜️ Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=800&q=60",
    "🌊 Turquoise": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=800&q=60",
    "🌸 Meadow": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=800&q=60",
    "🎭 Abstract": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=800&q=60",
    "🏯 Temple": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=800&q=60",
    "🏛️ Greece": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&q=60",
    "🌋 Volcano": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=800&q=60",
    "🏜️ Sahara": "https://images.unsplash.com/photo-1451337516015-6b6e9a44a8a3?w=800&q=60",
    "🏔️ Mountains": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60",
    "🌌 Galaxy": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60",
    "❄️ Winter": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60",
    "🌌 Cosmic": "https://images.unsplash.com/photo-1506318137071-a8e0634197b3?w=800&q=60",
    "🌲 Pine Forest": "https://images.unsplash.com/photo-1511497584788-876760111969?w=800&q=60",
    "🏙️ Neon City": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=800&q=60",
    "🌅 Golden Hour": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800&q=60",
    "🌊 Waves": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=800&q=60",
    "🪐 Space": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=60",
    "🌨️ Snow": "https://images.unsplash.com/photo-1519904984715-0d5e2f4d7a3f?w=800&q=60",
    "🌺 Tropical": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=60",
    "🎇 Northern Lights": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60",
    "🌿 Jungle": "https://images.unsplash.com/photo-1464820453369-31d2c0b236f0?w=800&q=60",
    "🪄 Magic": "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=800&q=60",
    "🌅 Pastel Sky": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&q=60",
    "🔮 Crystal": "https://images.unsplash.com/photo-1557672172-298e090bd0f8?w=800&q=60",
    "🌌 Deep Space": "https://images.unsplash.com/photo-1462331940025-5ec7d0c8f1c8?w=800&q=60",
    "🏔️ Snowy Peaks": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60",
    "🌸 Blossom": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=60",
    "🌃 Cyberpunk Night": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=800&q=60",
    "🧘 Zen": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&q=60",
    "🌾 Field": "https://images.unsplash.com/photo-1500595046743-6c0c8a8c5c5e?w=800&q=60",
    "🌄 Epic Mountains": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60",
    "🌅 Dreamy Sunset": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800&q=60",
    "🌌 Milky Way": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60",
    "🏔️ Snowy Majesty": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60",
    "🌊 Mystic Ocean": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=800&q=60",
    "🌲 Enchanted Forest": "https://images.unsplash.com/photo-1511497584788-876760111969?w=800&q=60",
    "❄️ Aurora Borealis": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&q=60",
    "🌺 Blooming Valley": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=800&q=60",
    "🏜️ Golden Desert": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=800&q=60",
    "🌃 Neon Dream City": "https://images.unsplash.com/photo-1519501025264-65ba15a82390?w=800&q=60",
    "🪐 Cosmic Nebula": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=800&q=60",
    "🌾 Golden Fields": "https://images.unsplash.com/photo-1500595046743-6c0c8a8c5c5e?w=800&q=60",
    "🌫️ Misty Lake": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=60",
    "🏞️ Majestic Canyon": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=800&q=60",
    "🌸 Cherry Blossom Path": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=800&q=60",
    "🔥 Ethereal Lava": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&q=60",
    "🧘 Serene Zen Garden": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800&q=60",
    "🌌 Starry Night Sky": "https://images.unsplash.com/photo-1506318137071-a8e0634197b3?w=800&q=60",
    "🏔️ Alpine Glow": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=800&q=60",
    "🌊 Turquoise Paradise": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=800&q=60",
    "🍂 Autumn Magic": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=800&q=60",
    "🌋 Volcanic Sunrise": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=800&q=60",
    "🏙️ Futuristic Cityscape": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=800&q=60",
    "🌿 Lush Rainforest": "https://images.unsplash.com/photo-1464820453369-31d2c0b236f0?w=800&q=60",
    "❄️ Crystal Winter Wonderland": "https://images.unsplash.com/photo-1519904984715-0d5e2f4d7a3f?w=800&q=60",
    "🌅 Pastel Horizon": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=800&q=60",
}

# ========== STREAMLIT UI ==========
class SocialiteUI:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self.group_manager = GroupManager(self.db)
        self.marketplace_manager = MarketplaceManager(self.db)
        self.notification_manager = NotificationManager(self.db)
        self.rate_limiter = RateLimiter()
        self._init_session()
    
    def _init_session(self):
        defaults = {
            'auth': False, 'user_id': None, 'username': None,
            'current_tab': 'feed', 'active_chat': None,
            'active_group': None, 'show_create_modal': False,
            'show_notifications': False, 'feed_page': 1,
            'show_comments_for': None, 'show_create_group': False,
            'show_create_channel': False, 'show_create_listing': False
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
        self.render_top_nav()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        tab = st.session_state.current_tab
        if tab == 'feed': self.render_feed()
        elif tab == 'explore': self.render_explore()
        elif tab == 'chats': self.render_chats()
        elif tab == 'marketplace': self.render_marketplace()
        elif tab == 'notifications': self.render_notifications()
        elif tab == 'profile': self.render_profile()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.show_create_modal:
            self.render_create_modal()
        if st.session_state.show_create_group:
            self.render_create_group_modal()
        if st.session_state.show_create_channel:
            self.render_create_channel_modal()
        if st.session_state.show_create_listing:
            self.render_create_listing_modal()
    
    def render_top_nav(self):
        """Render fixed top navigation bar"""
        current_tab = st.session_state.current_tab
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        unread = self.notification_manager.get_unread_count(user['user_id'])
        badge = f'<span style="background:#FFD700;color:#000;border-radius:50%;padding:1px 5px;font-size:0.6rem;position:absolute;top:-6px;right:-8px;">{unread}</span>' if unread > 0 else ''
        
        st.markdown(f"""
        <div class="top-nav">
            <div style="display:flex;align-items:center;gap:6px;font-weight:800;font-size:0.95rem;
                 background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                👑 Socialite
            </div>
            <div style="display:flex;align-items:center;gap:4px;">
                <span style="cursor:pointer;position:relative;font-size:1.1rem;">🔔{badge}</span>
                {self.render_avatar_html(user, 28)}
            </div>
        </div>
        <div class="nav-tabs">
        """, unsafe_allow_html=True)
        
        tabs = [
            ('feed', '🏠'),
            ('explore', '🔍'),
            ('chats', '💬'),
            ('marketplace', '🛒'),
            ('profile', '👤')
        ]
        
        for tab, icon in tabs:
            active = "active" if current_tab == tab else ""
            st.markdown(f"""
            <button class="nav-tab {active}" onclick="document.getElementById('nav_{tab}').click()">
                <span style="font-size:1.1rem;">{icon}</span>
                <span style="font-size:0.55rem;">{tab.title()}</span>
            </button>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Hidden buttons for navigation
        for tab, _ in tabs:
            if st.button(f"Nav {tab}", key=f"nav_{tab}", help=f"Go to {tab}"):
                st.session_state.current_tab = tab
                st.session_state.active_chat = None
                st.session_state.active_group = None
                st.rerun()
    
    def inject_styles(self):
        """Inject all CSS styles with fixed positioning and visible inputs"""
        theme = self._get_current_theme()
        wallpaper = self._get_current_wallpaper()
        
        if wallpaper == "gradient" or wallpaper == "🌈 Gradient":
            bg = theme['gradient']
        else:
            bg = f"url('{wallpaper}') center/cover no-repeat fixed"
        
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        * {{ font-family: 'Inter', sans-serif !important; }}
        
        #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
        
        html, body {{ height: 100% !important; width: 100% !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }}
        
        .stApp {{
            background: {bg} !important;
            height: 100vh !important;
            width: 100vw !important;
            overflow: hidden !important;
            position: relative !important;
        }}
        
        .main {{ height: 100vh !important; overflow: hidden !important; }}
        .block-container {{ height: 100vh !important; overflow: hidden !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important; }}
        
        /* Fixed Top Navigation */
        .top-nav {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 44px !important;
            background: {theme['bg']}fa !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-bottom: 1px solid rgba(255,215,0,0.15) !important;
            padding: 0 16px !important;
            z-index: 9999 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
        }}
        
        .nav-tabs {{
            position: fixed !important;
            top: 44px !important;
            left: 0 !important;
            right: 0 !important;
            height: 48px !important;
            background: {theme['bg']}f5 !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            border-bottom: 1px solid rgba(255,215,0,0.1) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-around !important;
            z-index: 9998 !important;
            padding: 0 !important;
            gap: 0 !important;
        }}
        
        .nav-tab {{
            background: transparent !important;
            border: none !important;
            color: {theme['secondary']} !important;
            cursor: pointer !important;
            padding: 6px 0 !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 1px !important;
            flex: 1 !important;
            height: 100% !important;
            transition: all 0.2s !important;
            font-size: 0.7rem !important;
            border-bottom: 2px solid transparent !important;
        }}
        
        .nav-tab:hover {{ color: #FFD700 !important; background: rgba(255,215,0,0.05) !important; }}
        .nav-tab.active {{ color: #FFD700 !important; border-bottom-color: #FFD700 !important; }}
        
        /* Main content - scrollable area */
        .main-content {{
            position: fixed !important;
            top: 92px !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding: 10px 12px !important;
            -webkit-overflow-scrolling: touch !important;
            background: transparent !important;
        }}
        
        .content-wrapper {{
            max-width: 650px !important;
            margin: 0 auto !important;
            padding-bottom: 20px !important;
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
            padding: 10px 12px !important;
            gap: 10px !important;
        }}
        
        .username-text {{
            color: {theme['text']} !important;
            font-weight: 600 !important;
            font-size: 0.85rem !important;
        }}
        
        .timestamp {{
            color: {theme['secondary']} !important;
            font-size: 0.65rem !important;
        }}
        
        .post-text {{
            color: #e2e8f0 !important;
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
            padding: 0 12px 10px 12px !important;
            word-wrap: break-word !important;
        }}
        
        /* VISIBLE INPUT FIELDS */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background: rgba(255, 255, 255, 0.08) !important;
            border: 2px solid rgba(255, 215, 0, 0.3) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
            font-size: 0.9rem !important;
            caret-color: #FFD700 !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: #FFD700 !important;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.2) !important;
            background: rgba(255, 255, 255, 0.12) !important;
        }}
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {{
            color: #64748b !important;
            font-size: 0.85rem !important;
        }}
        
        /* SELECT BOXES */
        .stSelectbox > div > div {{
            background: rgba(255, 255, 255, 0.08) !important;
            border: 2px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 10px !important;
            color: #ffffff !important;
        }}
        
        /* BUTTONS */
        .stButton > button {{
            background: rgba(255, 215, 0, 0.1) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            color: {theme['text']} !important;
            border-radius: 10px !important;
            padding: 8px 16px !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
            min-height: auto !important;
        }}
        
        .stButton > button:hover {{
            background: rgba(255, 215, 0, 0.2) !important;
            border-color: #FFD700 !important;
            box-shadow: 0 0 15px rgba(255, 215, 0, 0.25) !important;
            transform: translateY(-1px) !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 4px !important; }}
        ::-webkit-scrollbar-track {{ background: transparent !important; }}
        ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #FFD70088 !important; }}
        
        /* Expanders */
        .stExpander {{
            background: {theme['card']} !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 12px !important;
        }}
        
        .streamlit-expanderHeader {{
            color: {theme['text']} !important;
            font-size: 0.85rem !important;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 2px !important;
            background: transparent !important;
            border-bottom: 1px solid rgba(255,215,0,0.1) !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            color: {theme['secondary']} !important;
            border-radius: 8px 8px 0 0 !important;
            padding: 8px 16px !important;
            font-size: 0.8rem !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            color: #FFD700 !important;
            background: rgba(255,215,0,0.1) !important;
        }}
        
        /* Form submit button */
        div[data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(135deg, #FFD700, #FFA500) !important;
            color: #1a0033 !important;
            font-weight: 700 !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 10px !important;
        }}
        
        /* Alerts */
        .stAlert {{
            border-radius: 10px !important;
            border: 1px solid !important;
        }}
        
        /* Hide HTML display of raw data */
        [data-testid="stMarkdown"] pre,
        .element-container:has(pre) {{
            display: none !important;
        }}
        
        @media (max-width: 480px) {{
            .main-content {{ padding: 8px 8px !important; }}
            .card {{ border-radius: 10px !important; margin-bottom: 8px !important; }}
            .top-nav {{ height: 40px !important; }}
            .nav-tabs {{ top: 40px !important; height: 44px !important; }}
            .main-content {{ top: 84px !important; }}
            .nav-tab {{ font-size: 0.65rem !important; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_auth(self):
        """Render authentication page"""
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #0a0015 0%, #1a0033 50%, #0a0015 100%) !important; overflow: auto !important; }
        .main { height: auto !important; overflow: visible !important; }
        .block-container { height: auto !important; overflow: visible !important; padding: 2rem 1rem !important; }
        </style>
        """, unsafe_allow_html=True)
        
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.markdown(f"""
            <div style="text-align:center;padding:2rem 0;">
                <img src="{Config.LOGO_URL}" style="width:120px;height:120px;border-radius:50%;object-fit:cover;border:3px solid #FFD700;box-shadow:0 0 30px rgba(255,215,0,0.4);" alt="Socialite">
                <h1 style="font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:900;background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:0.5rem;">Socialite</h1>
                <p style="color:#94a3b8;font-size:1rem;">Where Luxury Meets Connection</p>
            </div>
            """, unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="Enter your username")
                    password = st.text_input("Password", type="password", placeholder="Enter your password")
                    if st.form_submit_button("🔓 Sign In", use_container_width=True):
                        if username and password:
                            success, result = self.user_manager.authenticate(username, password)
                            if success:
                                st.session_state.auth = True
                                st.session_state.username = result
                                user = self.user_manager.get_user_by_username(result)
                                if user: st.session_state.user_id = user['user_id']
                                st.rerun()
                            else: st.error(result)
                        else: st.error("Please fill all fields")
            
            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Choose Username", placeholder="3-30 characters, letters/numbers only")
                    email = st.text_input("Email (optional)", placeholder="your@email.com")
                    new_password = st.text_input("Choose Password", type="password", placeholder=f"Min {Config.MIN_PASSWORD_LENGTH} characters")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                    if st.form_submit_button("✨ Create Account", use_container_width=True):
                        if not new_username or not new_password: st.error("Username and password required")
                        elif new_password != confirm: st.error("Passwords don't match")
                        elif len(new_password) < Config.MIN_PASSWORD_LENGTH: st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                        else:
                            success, message = self.user_manager.create_user(new_username, new_password, email)
                            if success: st.success(message); st.info("Please sign in!"); st.balloons()
                            else: st.error(message)
    
    def render_feed(self):
        """Render feed page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Quick post button
        if st.button("✨ What's on your mind? Tap to post...", use_container_width=True, key="quick_post"):
            st.session_state.show_create_modal = True
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        posts, has_more = self.post_manager.get_feed(user['user_id'], page=st.session_state.feed_page)
        
        if not posts:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">
                <div style="font-size:4rem;">👑</div>
                <h3 style="color:#FFD700;margin-top:1rem;">Welcome to Socialite</h3>
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
        """Render a single post card"""
        with st.container():
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            
            # Header
            st.markdown(f"""
            <div class="card-header">
                {self.render_avatar_html(post, 36)}
                <div style="flex:1;">
                    <div class="username-text">
                        @{html.escape(post['username'])}
                        {"<span style='color:#FFD700;'> ✓</span>" if post.get('is_verified') else ""}
                    </div>
                    <div class="timestamp">{Utils.format_timestamp(post['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Text
            if post.get('text'):
                st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
            
            # Media
            if post.get('media_data'):
                try:
                    image_bytes = base64.b64decode(post['media_data'])
                    st.image(image_bytes, use_column_width=True)
                except: pass
            
            # Price tag
            if post.get('is_for_sale') and post.get('price'):
                st.markdown(f'<div style="padding:0 12px 8px 12px;color:#FFD700;font-weight:600;">💰 ${post["price"]:.2f}</div>', unsafe_allow_html=True)
            
            # Poll
            if post.get('post_type') == 'poll' and post.get('poll_options'):
                self.render_poll(post)
            
            # Actions
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 3])
            with col1:
                if st.button(f"❤️ {sum(post.get('reactions', {}).values())}", key=f"react_{post['id']}", use_container_width=True):
                    self.post_manager.add_reaction(post['id'], st.session_state.user_id, 'like')
                    st.rerun()
            with col2:
                if st.button(f"💬 {post.get('comment_count', 0)}", key=f"cmt_{post['id']}", use_container_width=True):
                    st.session_state.show_comments_for = post['id'] if st.session_state.show_comments_for != post['id'] else None
                    st.rerun()
            with col3:
                if st.button("🔄", key=f"share_{post['id']}", use_container_width=True):
                    st.toast("Shared!")
            with col4:
                if st.button("🔖", key=f"save_{post['id']}", use_container_width=True):
                    st.toast("Saved!")
            with col5:
                if post['username'] == st.session_state.username:
                    if st.button("🗑️", key=f"del_{post['id']}", use_container_width=True):
                        self.post_manager.delete_post(post['id'], st.session_state.user_id)
                        st.rerun()
            
            # Comments
            if st.session_state.show_comments_for == post['id']:
                self.render_comments_section(post['id'])
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_poll(self, post: Dict):
        """Render poll"""
        total_votes = sum(opt.get('vote_count', 0) for opt in post.get('poll_options', []))
        for option in post.get('poll_options', []):
            vote_count = option.get('vote_count', 0)
            pct = (vote_count / total_votes * 100) if total_votes > 0 else 0
            st.markdown(f"""
            <div style="padding:5px 12px;">
                <div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.85rem;">
                    <span>{html.escape(option['option_text'])}</span><span>{pct:.0f}%</span>
                </div>
                <div style="height:4px;background:rgba(255,255,255,0.1);border-radius:2px;">
                    <div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#FFD700,#FFA500);border-radius:2px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Vote", key=f"poll_{post['id']}_{option['id']}"):
                st.toast("Voted!")
    
    def render_comments_section(self, post_id: str):
        """Render comments"""
        st.markdown('<div style="padding:8px 12px;border-top:1px solid rgba(255,215,0,0.1);">', unsafe_allow_html=True)
        comments = self.post_manager.get_comments(post_id)
        for c in comments:
            st.markdown(f"""
            <div style="margin:4px 0;display:flex;gap:8px;">
                {self.render_avatar_html(c, 24)}
                <div>
                    <span style="color:#FFD700;font-weight:600;font-size:0.75rem;">@{html.escape(c['username'])}</span>
                    <span style="color:#e2e8f0;font-size:0.8rem;">{html.escape(c['text'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"cmt_form_{post_id}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                text = st.text_input("Comment", placeholder="Write...", key=f"cmt_input_{post_id}", label_visibility="collapsed")
            with col2:
                if st.form_submit_button("Post"):
                    if text.strip():
                        self.post_manager.add_comment(post_id, st.session_state.user_id, text)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_explore(self):
        """Render explore page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">🔍 Explore Users</h3>', unsafe_allow_html=True)
        query = st.text_input("Search", placeholder="Search users...", label_visibility="collapsed")
        if query:
            users = self.user_manager.search_users(query, exclude_user_id=st.session_state.user_id)
            for u in users:
                col1, col2 = st.columns([4, 2])
                with col1:
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:8px 0;">
                        {self.render_avatar_html(u, 40)}
                        <div>
                            <div style="color:#f1f5f9;font-weight:600;">@{html.escape(u['username'])}</div>
                            <div style="color:#94a3b8;font-size:0.7rem;">{Utils.format_number(u.get('follower_count', 0))} followers</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("Follow", key=f"ef_{u['username']}", use_container_width=True):
                        self.user_manager.follow_user(st.session_state.user_id, u['username'])
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chats(self):
        """Render chats page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        if st.session_state.active_chat:
            self.render_chat_interface()
        elif st.session_state.active_group:
            self.render_group_interface()
        else:
            st.markdown('<h3 style="color:#FFD700;">💬 Messages</h3>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👥 Create Group", use_container_width=True):
                    st.session_state.show_create_group = True
                    st.rerun()
            with col2:
                if st.button("📢 Create Channel", use_container_width=True):
                    st.session_state.show_create_channel = True
                    st.rerun()
            
            # Direct messages
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                chats = self.chat_manager.get_chat_list(user['user_id'])
                for chat in chats:
                    online = "🟢" if chat.get('is_online') else ""
                    unread = f" ({chat['unread_count']})" if chat.get('unread_count', 0) > 0 else ""
                    st.markdown(f"""
                    <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid rgba(255,215,0,0.05);">
                        {self.render_avatar_html(chat, 40)}
                        <div style="flex:1;">
                            <span style="color:#f1f5f9;font-weight:600;">@{html.escape(chat.get('other_username',''))} {online}{unread}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Open", key=f"och_{chat.get('other_username')}"):
                        st.session_state.active_chat = chat['other_username']
                        st.rerun()
            
            # Groups
            groups = self.group_manager.get_user_groups(user['user_id']) if user else []
            if groups:
                st.markdown('<h4 style="color:#FFD700;margin-top:15px;">👥 Groups</h4>', unsafe_allow_html=True)
                for gr in groups:
                    if st.button(f"👥 {html.escape(gr['name'])}", key=f"ogr_{gr['id']}", use_container_width=True):
                        st.session_state.active_group = gr['id']
                        st.rerun()
            
            # Channels
            channels = self.group_manager.get_user_channels(user['user_id']) if user else []
            if channels:
                st.markdown('<h4 style="color:#FFD700;margin-top:15px;">📢 Channels</h4>', unsafe_allow_html=True)
                for ch in channels:
                    if st.button(f"📢 {html.escape(ch['name'])}", key=f"och_{ch['id']}", use_container_width=True):
                        st.session_state.active_group = ch['id']
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chat_interface(self):
        """Render direct chat"""
        if st.button("← Back", key="back_chat", use_container_width=True):
            st.session_state.active_chat = None
            st.rerun()
        
        with_user = self.user_manager.get_user_by_username(st.session_state.active_chat)
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not with_user or not user: return
        
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,215,0,0.1);">
            {self.render_avatar_html(with_user, 36)}
            <div style="color:#f1f5f9;font-weight:600;">@{html.escape(with_user['username'])}</div>
        </div>
        """, unsafe_allow_html=True)
        
        messages = self.chat_manager.get_messages(user['user_id'], with_user['user_id'])
        for msg in messages:
            is_sent = msg['from_id'] == user['user_id']
            align = 'flex-end' if is_sent else 'flex-start'
            bg = 'linear-gradient(135deg,#667eea,#764ba2)' if is_sent else 'rgba(255,255,255,0.07)'
            st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin:4px 8px;">
                <div style="max-width:70%;padding:8px 14px;border-radius:16px;background:{bg};color:white;font-size:0.85rem;">
                    {html.escape(msg.get('text',''))}
                    <div style="font-size:0.55rem;opacity:0.7;text-align:right;">{Utils.format_timestamp(msg['timestamp'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"msg_form_{with_user['user_id']}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                text = st.text_input("Message", placeholder="Type...", key=f"msg_{with_user['user_id']}", label_visibility="collapsed")
            with col2:
                if st.form_submit_button("Send"):
                    if text.strip():
                        self.chat_manager.send_message(user['user_id'], with_user['username'], text)
                        st.rerun()
    
    def render_group_interface(self):
        """Render group/channel chat"""
        if st.button("← Back", key="back_group", use_container_width=True):
            st.session_state.active_group = None
            st.rerun()
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        messages = self.group_manager.get_group_messages(st.session_state.active_group)
        for msg in messages:
            is_sent = msg['from_id'] == user['user_id']
            align = 'flex-end' if is_sent else 'flex-start'
            bg = 'linear-gradient(135deg,#667eea,#764ba2)' if is_sent else 'rgba(255,255,255,0.07)'
            sender = "" if is_sent else f"<div style='color:#FFD700;font-size:0.6rem;'>@{html.escape(msg.get('username',''))}</div>"
            st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin:4px 8px;">
                <div style="max-width:70%;padding:8px 14px;border-radius:16px;background:{bg};color:white;font-size:0.85rem;">
                    {sender}{html.escape(msg.get('text',''))}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with st.form(f"grp_msg_{st.session_state.active_group}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                text = st.text_input("Message", placeholder="Type...", key=f"grp_msg_input", label_visibility="collapsed")
            with col2:
                if st.form_submit_button("Send"):
                    if text.strip():
                        self.group_manager.send_message(st.session_state.active_group, user['user_id'], text)
                        st.rerun()
    
    def render_marketplace(self):
        """Render marketplace page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">🛒 Marketplace</h3>', unsafe_allow_html=True)
        
        if st.button("📦 Create Listing", use_container_width=True):
            st.session_state.show_create_listing = True
            st.rerun()
        
        listings = self.marketplace_manager.get_listings()
        if listings:
            for listing in listings:
                st.markdown(f"""
                <div class="card" style="padding:12px;">
                    <div style="display:flex;justify-content:space-between;align-items:start;">
                        <div>
                            <div style="color:#f1f5f9;font-weight:600;font-size:0.9rem;">{html.escape(listing['title'])}</div>
                            <div style="color:#94a3b8;font-size:0.7rem;">@{html.escape(listing.get('seller_username',''))}</div>
                            <div style="color:#94a3b8;font-size:0.75rem;margin-top:4px;">{html.escape(listing.get('description','')[:100])}</div>
                        </div>
                        <div style="color:#FFD700;font-weight:700;font-size:1.1rem;">${listing['price']:.2f}</div>
                    </div>
                    <div style="display:flex;gap:8px;margin-top:8px;">
                        <span style="background:rgba(255,215,0,0.1);color:#FFD700;padding:2px 8px;border-radius:10px;font-size:0.65rem;">{listing.get('category','other')}</span>
                        <span style="background:rgba(255,215,0,0.1);color:#FFD700;padding:2px 8px;border-radius:10px;font-size:0.65rem;">{listing.get('condition','new')}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No listings yet. Create one!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_notifications(self):
        """Render notifications"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">🔔 Notifications</h3>', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user: return
        
        notifications = self.notification_manager.get_notifications(user['user_id'])
        if notifications:
            if st.button("Mark All Read", use_container_width=True):
                self.notification_manager.mark_all_read(user['user_id'])
                st.rerun()
        
        for n in notifications:
            icon = {'follow': '👤', 'reaction': '❤️', 'comment': '💬', 'message': '💬', 'mention': '@️'}.get(n['type'], '🔔')
            bg = 'rgba(255,215,0,0.05)' if not n['is_read'] else 'transparent'
            st.markdown(f"""
            <div style="padding:10px;margin:4px 0;background:{bg};border-radius:8px;display:flex;align-items:center;gap:10px;">
                <span>{icon}</span>
                <div style="flex:1;">
                    <span style="color:#e2e8f0;font-size:0.85rem;">{html.escape(n['message'])}</span>
                    {'<span style="color:#FFD700;">@' + html.escape(n['from_username']) + '</span>' if n.get('from_username') else ''}
                </div>
                <span style="color:#64748b;font-size:0.65rem;">{Utils.format_timestamp(n['timestamp'])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        if not notifications:
            st.info("No notifications yet")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_profile(self):
        """Render profile page - FIXED"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            st.error("User not found")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Profile header
        follower_count = self._get_follower_count(user['user_id'])
        following_count = self._get_following_count(user['user_id'])
        
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
            {self.render_avatar_html(user, 80)}
            <h2 style="color:#FFD700;margin-top:10px;">@{html.escape(user['username'])}</h2>
            <p style="color:#94a3b8;font-size:0.9rem;">{html.escape(user.get('display_name', user['username']))}</p>
            <p style="color:#94a3b8;font-size:0.85rem;">{html.escape(user.get('bio', 'No bio yet'))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Posts", user.get('total_posts', 0))
        with col2:
            st.metric("Followers", follower_count)
        with col3:
            st.metric("Following", following_count)
        
        # Edit Profile
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile_form"):
                display_name = st.text_input("Display Name", value=user.get('display_name', '') or '')
                bio = st.text_area("Bio", value=user.get('bio', '') or '', max_chars=Config.MAX_BIO_LENGTH)
                col1, col2 = st.columns(2)
                with col1:
                    website = st.text_input("Website", value=user.get('website', '') or '')
                with col2:
                    location = st.text_input("Location", value=user.get('location', '') or '')
                gender = st.selectbox("Gender", ['male', 'female'], index=0 if user.get('gender') == 'male' else 1)
                avatar = st.file_uploader("Profile Picture", type=['png','jpg','jpeg','webp'])
                
                if st.form_submit_button("💾 Save", use_container_width=True):
                    updates = {
                        'display_name': Utils.sanitize_text(display_name, 50),
                        'bio': Utils.sanitize_text(bio, Config.MAX_BIO_LENGTH),
                        'website': Utils.sanitize_text(website, 200),
                        'location': Utils.sanitize_text(location, 100),
                        'gender': gender
                    }
                    if avatar:
                        try:
                            img_data = avatar.read()
                            optimized = Utils.optimize_image(img_data, (400, 400))
                            path = Config.UPLOADS_DIR / f"avatar_{user['user_id']}.jpg"
                            with open(path, 'wb') as f:
                                f.write(optimized)
                            updates['avatar_path'] = str(path)
                        except:
                            st.error("Failed to process image")
                    
                    if self.user_manager.update_profile(user['user_id'], updates):
                        st.success("Profile updated!")
                        st.rerun()
        
        # Themes
        with st.expander("🎨 Themes"):
            cols = st.columns(4)
            for i, (tk, td) in enumerate(THEMES.items()):
                with cols[i % 4]:
                    if st.button(f"{td['icon']} {td['name']}", key=f"th_{tk}", use_container_width=True):
                        self.user_manager.update_profile(user['user_id'], {'theme': tk})
                        st.rerun()
        
        # Wallpapers
        with st.expander("🖼️ Wallpapers"):
            current_wp = user.get('wallpaper', '🌈 Gradient')
            st.selectbox("Select Wallpaper", list(WALLPAPERS.keys()), 
                        index=list(WALLPAPERS.keys()).index(current_wp) if current_wp in WALLPAPERS else 0,
                        key="wp_selector",
                        on_change=lambda: self.user_manager.update_profile(user['user_id'], {'wallpaper': st.session_state.wp_selector}))
        
        # Sign Out
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_create_modal(self):
        """Create post modal"""
        st.markdown(f"""
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);z-index:10001;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:1px solid rgba(255,215,0,0.2);border-radius:18px;width:90%;max-width:480px;max-height:80vh;overflow-y:auto;padding:20px;">
                <h3 style="color:#FFD700;text-align:center;">✨ Create Post</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_post_form", clear_on_submit=True):
            text = st.text_area("What's on your mind?", max_chars=Config.MAX_POST_LENGTH, height=100)
            media = st.file_uploader("Image", type=['png','jpg','jpeg','gif'], key="post_media")
            location = st.text_input("Location", placeholder="Add location")
            price = st.number_input("Price ($)", min_value=0.0, step=0.01, help="Set price for marketplace")
            is_for_sale = st.checkbox("List for sale")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Post", use_container_width=True):
                    if text or media:
                        md, mn = None, None
                        if media:
                            img_data = media.read()
                            if Utils.validate_image(img_data):
                                optimized = Utils.optimize_image(img_data)
                                md = base64.b64encode(optimized).decode()
                                mn = media.name
                        
                        success, _ = self.post_manager.create_post(
                            st.session_state.user_id, text, md, mn,
                            location=location, price=price, is_for_sale=is_for_sale
                        )
                        if success:
                            st.session_state.show_create_modal = False
                            st.rerun()
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_create_group_modal(self):
        """Create group modal"""
        st.markdown(f"""
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);z-index:10001;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:1px solid rgba(255,215,0,0.2);border-radius:18px;width:90%;max-width:480px;padding:20px;">
                <h3 style="color:#FFD700;text-align:center;">👥 Create Group</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_group_form", clear_on_submit=True):
            name = st.text_input("Group Name", placeholder="Enter group name")
            description = st.text_area("Description", placeholder="Group description")
            if st.form_submit_button("Create", use_container_width=True):
                if name:
                    success, _ = self.group_manager.create_group(name, st.session_state.user_id, description)
                    if success:
                        st.session_state.show_create_group = False
                        st.rerun()
        
        if st.button("Cancel", key="cancel_group"):
            st.session_state.show_create_group = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_create_channel_modal(self):
        """Create channel modal"""
        st.markdown(f"""
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);z-index:10001;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:1px solid rgba(255,215,0,0.2);border-radius:18px;width:90%;max-width:480px;padding:20px;">
                <h3 style="color:#FFD700;text-align:center;">📢 Create Channel</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_channel_form", clear_on_submit=True):
            name = st.text_input("Channel Name", placeholder="Enter channel name")
            description = st.text_area("Description", placeholder="Channel description")
            if st.form_submit_button("Create", use_container_width=True):
                if name:
                    success, _ = self.group_manager.create_group(name, st.session_state.user_id, description, is_channel=True)
                    if success:
                        st.session_state.show_create_channel = False
                        st.rerun()
        
        if st.button("Cancel", key="cancel_channel"):
            st.session_state.show_create_channel = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_create_listing_modal(self):
        """Create marketplace listing modal"""
        st.markdown(f"""
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);z-index:10001;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:1px solid rgba(255,215,0,0.2);border-radius:18px;width:90%;max-width:480px;max-height:80vh;overflow-y:auto;padding:20px;">
                <h3 style="color:#FFD700;text-align:center;">📦 Create Listing</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_listing_form", clear_on_submit=True):
            title = st.text_input("Title", placeholder="Item title")
            description = st.text_area("Description")
            price = st.number_input("Price ($)", min_value=0.01, step=0.01)
            category = st.selectbox("Category", ["electronics", "fashion", "home", "beauty", "sports", "books", "other"])
            condition = st.selectbox("Condition", ["new", "like new", "good", "fair", "poor"])
            location = st.text_input("Location", placeholder="City, State")
            media = st.file_uploader("Image", type=['png','jpg','jpeg'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("List Item", use_container_width=True):
                    if title and price > 0:
                        md, mn = None, None
                        if media:
                            img_data = media.read()
                            if Utils.validate_image(img_data):
                                optimized = Utils.optimize_image(img_data)
                                md = base64.b64encode(optimized).decode()
                                mn = media.name
                        
                        self.marketplace_manager.create_listing(
                            st.session_state.user_id, title, description, price,
                            category, condition, md, mn, location
                        )
                        st.session_state.show_create_listing = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Cancel", use_container_width=True):
                    st.session_state.show_create_listing = False
                    st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_avatar_html(self, user_data: Dict, size: int = 36) -> str:
        """Generate avatar HTML"""
        if isinstance(user_data, dict):
            username = user_data.get('username', '')
            avatar_path = user_data.get('avatar_path')
            gender = user_data.get('gender', 'male')
            is_premium = user_data.get('is_premium', False)
        else:
            username = str(user_data)
            avatar_path = None
            gender = 'male'
            is_premium = False
        
        if avatar_path and os.path.exists(avatar_path):
            try:
                with open(avatar_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                border = "3px solid #FFD700" if is_premium else "2px solid #FFD700"
                return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border};flex-shrink:0;" alt="{username}">'
            except: pass
        
        color = Utils.get_avatar_color(username)
        initials = Utils.get_initials(username)
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:{size*0.4}px;flex-shrink:0;border:2px solid #FFD700;">{initials}</div>'
    
    def _get_current_theme(self) -> Dict:
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                theme_key = user.get('theme', 'midnight')
                return THEMES.get(theme_key, THEMES['midnight'])
        return THEMES['midnight']
    
    def _get_current_wallpaper(self) -> str:
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                wp_key = user.get('wallpaper', '🌈 Gradient')
                return WALLPAPERS.get(wp_key, WALLPAPERS['🌈 Gradient'])
        return WALLPAPERS['🌈 Gradient']
    
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
        db = DatabaseManager()
        app = SocialiteUI()
        app.render()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error("An error occurred. Please refresh the page.")

if __name__ == "__main__":
    main()
