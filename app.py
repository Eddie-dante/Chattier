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
from functools import lru_cache
from dataclasses import dataclass, field, asdict
from collections import defaultdict, OrderedDict
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, quote, unquote
import pickle
from contextlib import contextmanager
import sys
import mimetypes
import hashlib as hash_lib
import hmac
import struct
import queue

# Must be first Streamlit command
st.set_page_config(
    page_title="Socialite - Premium Social Network",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Socialite - The Premium Social Experience v7.0"
    }
)

# ========== ENHANCED CONFIGURATION ==========
class Config:
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "7.0.0"
    
    LOGO_URL = "https://drive.google.com/uc?export=view&id=1Rxb3t3yLEdrqS6hWZJw4DPg6T1PNSkKb"
    
    DATA_DIR = pathlib.Path("data")
    DB_PATH = DATA_DIR / "socialite_v7.db"
    UPLOADS_DIR = DATA_DIR / "uploads"
    BACKUP_DIR = DATA_DIR / "backups"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"
    
    MAX_POST_LENGTH = 10000
    MAX_COMMENT_LENGTH = 2000
    MAX_BIO_LENGTH = 500
    MAX_MESSAGE_LENGTH = 25000
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 8
    MAX_FILE_SIZE = 100 * 1024 * 1024
    MAX_AVATAR_SIZE = 15 * 1024 * 1024
    
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCKOUT_MINUTES = 30
    SESSION_TIMEOUT_HOURS = 12
    PASSWORD_HASH_ITERATIONS = 600000
    ENCRYPTION_KEY_LENGTH = 32
    MAX_SESSIONS_PER_USER = 5
    
    STORY_EXPIRY_HOURS = 24
    ONLINE_THRESHOLD_SECONDS = 180
    CACHE_TTL_SECONDS = 30
    MESSAGE_EDIT_WINDOW = 300
    
    MAX_FEED_ITEMS = 5000
    MAX_CHAT_MESSAGES = 10000
    MAX_NOTIFICATIONS = 500
    MAX_FOLLOWING = 10000
    MAX_BLOCKED = 2000
    MAX_SAVED_POSTS = 10000
    
    DB_POOL_SIZE = 10
    DB_POOL_TIMEOUT = 5

# Create all directories
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

# ========== CUSTOM EXCEPTIONS ==========
class SocialiteError(Exception):
    pass

class AuthenticationError(SocialiteError):
    pass

class ValidationError(SocialiteError):
    pass

class DatabaseError(SocialiteError):
    pass

# ========== UTILITY CLASSES ==========
class SecurityUtils:
    @staticmethod
    def generate_session_token() -> str:
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_csrf_token() -> str:
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        if salt is None:
            salt = secrets.token_hex(32)
        
        h = hashlib.pbkdf2_hmac(
            'sha512',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            Config.PASSWORD_HASH_ITERATIONS
        )
        
        h = hashlib.pbkdf2_hmac(
            'sha256',
            h,
            salt.encode('utf-8'),
            100000
        )
        
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        try:
            h, _ = SecurityUtils.hash_password(password, salt)
            return hmac.compare_digest(h, stored_hash)
        except Exception:
            return False
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 5000, allow_html: bool = False) -> str:
        if not text:
            return ""
        
        text = text.replace('\x00', '')
        text = ''.join(c for c in text if ord(c) >= 32 or c in ['\n', '\r', '\t'])
        
        if not allow_html:
            text = html.escape(text)
        
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text.strip()

class Utils:
    @staticmethod
    def generate_id() -> str:
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(8)
        return f"{timestamp}_{random_part}"
    
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
                t = t.replace(tzinfo=None)
            
            now = datetime.now()
            diff = (now - t).total_seconds()
            
            if diff < 5:
                return "just now"
            elif diff < 60:
                return f"{int(diff)}s ago"
            elif diff < 3600:
                return f"{int(diff//60)}m ago"
            elif diff < 86400:
                return f"{int(diff//3600)}h ago"
            elif diff < 604800:
                return f"{int(diff//86400)}d ago"
            else:
                return t.strftime("%b %d")
        except:
            return ""
    
    @staticmethod
    def format_number(num: int) -> str:
        if num is None:
            return "0"
        if num < 1000:
            return str(num)
        elif num < 1000000:
            return f"{num/1000:.1f}K"
        elif num < 1000000000:
            return f"{num/1000000:.1f}M"
        else:
            return f"{num/1000000000:.1f}B"
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r'#(\w+)', text)
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        if not text:
            return []
        return re.findall(r'@(\w+)', text)
    
    @staticmethod
    def get_avatar_color(username: str) -> str:
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#DDA0DD',
            '#FF8A80', '#B388FF', '#FF5722', '#9C27B0', '#3F51B5',
            '#009688', '#FF9800', '#795548', '#607D8B', '#E91E63'
        ]
        if not username:
            return colors[0]
        return colors[hash(username) % len(colors)]
    
    @staticmethod
    def get_initials(username: str) -> str:
        if not username:
            return "?"
        parts = username.replace('_', ' ').replace('.', ' ').split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if len(username) >= 2 else username[0].upper()
    
    @staticmethod
    def validate_image(data: bytes) -> bool:
        if len(data) < 4:
            return False
        valid_signatures = [
            b'\xff\xd8\xff',  # JPEG
            b'\x89PNG\r\n\x1a\n',  # PNG
            b'GIF87a',  # GIF
            b'GIF89a',  # GIF
            b'RIFF',  # WEBP
        ]
        return any(data.startswith(sig) for sig in valid_signatures)
    
    @staticmethod
    def optimize_image(data: bytes, max_size: Tuple[int, int] = (1920, 1920)) -> bytes:
        try:
            img = Image.open(io.BytesIO(data))
            
            if img.mode in ('RGBA', 'LA', 'P'):
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail(max_size, Image.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True, progressive=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            return data

# ========== CONNECTION POOL ==========
class DatabasePool:
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
        if self._initialized:
            return
        self._initialized = True
        self._pool = queue.Queue(maxsize=Config.DB_POOL_SIZE)
        self._created_count = 0
        self._pool_lock = threading.Lock()
    
    def _create_connection(self):
        conn = sqlite3.connect(
            str(Config.DB_PATH),
            check_same_thread=False,
            timeout=30,
            isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA cache_size=-50000")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        self._created_count += 1
        return conn
    
    def get_connection(self):
        try:
            conn = self._pool.get_nowait()
            try:
                conn.execute("SELECT 1")
                return conn
            except:
                try:
                    conn.close()
                except:
                    pass
                return self._create_connection()
        except queue.Empty:
            with self._pool_lock:
                if self._created_count < Config.DB_POOL_SIZE:
                    return self._create_connection()
                else:
                    try:
                        return self._pool.get(timeout=Config.DB_POOL_TIMEOUT)
                    except queue.Empty:
                        raise DatabaseError("Connection pool exhausted")
    
    def return_connection(self, conn):
        if conn is None:
            return
        try:
            conn.execute("SELECT 1")
            try:
                self._pool.put_nowait(conn)
            except queue.Full:
                conn.close()
                with self._pool_lock:
                    self._created_count -= 1
        except:
            try:
                conn.close()
            except:
                pass
            with self._pool_lock:
                self._created_count -= 1
    
    @contextmanager
    def connection_context(self):
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                self.return_connection(conn)
    
    def close_all(self):
        while True:
            try:
                conn = self._pool.get_nowait()
                try:
                    conn.close()
                except:
                    pass
            except queue.Empty:
                break

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
        if self._initialized:
            return
        self._initialized = True
        self.pool = DatabasePool()
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        with self.pool.connection_context() as conn:
            yield conn
    
    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                    email TEXT DEFAULT '',
                    phone TEXT DEFAULT '',
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    encryption_key TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    last_active TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    is_premium BOOLEAN DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    is_banned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    role TEXT DEFAULT 'user',
                    total_posts INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 0.0,
                    account_status TEXT DEFAULT 'active'
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
                    gender TEXT DEFAULT 'prefer_not_to_say',
                    is_private BOOLEAN DEFAULT 0,
                    theme TEXT DEFAULT 'midnight',
                    wallpaper TEXT DEFAULT 'gradient',
                    show_online_status BOOLEAN DEFAULT 1,
                    allow_messages_from TEXT DEFAULT 'everyone',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    csrf_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
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
                    video_data TEXT,
                    audio_data TEXT,
                    location TEXT DEFAULT '',
                    price REAL DEFAULT 0.0,
                    is_for_sale BOOLEAN DEFAULT 0,
                    hashtags TEXT DEFAULT '[]',
                    mentions TEXT DEFAULT '[]',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    visibility TEXT DEFAULT 'public',
                    view_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
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
                    is_edited BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
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
                    sticker_data TEXT,
                    gif_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
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
                    currency TEXT DEFAULT 'USD',
                    category TEXT DEFAULT 'other',
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_sold BOOLEAN DEFAULT 0,
                    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
                "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            ]
            
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except:
                    pass
            
            conn.commit()

# ========== USER MANAGER ==========
class UserManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = {}
        self.cache_lock = threading.Lock()
    
    def create_user(self, username: str, password: str, email: str = "", phone: str = "") -> Tuple[bool, str]:
        username = SecurityUtils.sanitize_input(username.strip().lower(), Config.MAX_USERNAME_LENGTH)
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, "Username already exists"
                
                password_hash, salt = SecurityUtils.hash_password(password)
                encryption_key = secrets.token_hex(Config.ENCRYPTION_KEY_LENGTH)
                
                cursor.execute("""
                    INSERT INTO users (username, email, phone, password_hash, salt, encryption_key)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, phone, password_hash, salt, encryption_key))
                
                user_id = cursor.lastrowid
                
                cursor.execute("""
                    INSERT INTO profiles (user_id, display_name)
                    VALUES (?, ?)
                """, (user_id, username))
                
                conn.commit()
                return True, "Account created successfully! Welcome to Socialite!"
                
        except Exception as e:
            logger.error(f"User creation error: {e}", exc_info=True)
            return False, "An error occurred during account creation"
    
    def authenticate(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Tuple[bool, Union[str, Dict]]:
        username = username.strip()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users WHERE (username = ? OR LOWER(username) = LOWER(?)) AND is_deleted = 0
                """, (username, username))
                
                user = cursor.fetchone()
                if not user:
                    SecurityUtils.hash_password("dummy_password")
                    return False, "Invalid username or password"
                
                user_dict = dict(user)
                
                if user_dict['is_banned']:
                    return False, "Account has been banned"
                if user_dict['account_status'] == 'suspended':
                    return False, "Account is suspended"
                
                if user_dict['locked_until']:
                    try:
                        lock_time = datetime.fromisoformat(user_dict['locked_until'])
                        if datetime.now() < lock_time:
                            remaining = (lock_time - datetime.now()).seconds // 60
                            return False, f"Account locked. Try again in {remaining} minutes"
                        else:
                            cursor.execute("UPDATE users SET locked_until = NULL, login_attempts = 0 WHERE id = ?", (user_dict['id'],))
                    except:
                        pass
                
                if SecurityUtils.verify_password(password, user_dict['password_hash'], user_dict['salt']):
                    session_id = Utils.generate_id()
                    session_token = SecurityUtils.generate_session_token()
                    csrf_token = SecurityUtils.generate_csrf_token()
                    expires_at = datetime.now() + timedelta(hours=Config.SESSION_TIMEOUT_HOURS)
                    
                    cursor.execute("""
                        INSERT INTO sessions (id, user_id, token, csrf_token, expires_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (session_id, user_dict['id'], session_token, csrf_token, expires_at.isoformat()))
                    
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP, last_active = CURRENT_TIMESTAMP, login_attempts = 0 WHERE id = ?
                    """, (user_dict['id'],))
                    
                    conn.commit()
                    
                    return True, {
                        'username': user_dict['username'],
                        'user_id': user_dict['id'],
                        'session_token': session_token,
                        'csrf_token': csrf_token,
                        'is_premium': user_dict['is_premium'],
                        'is_verified': user_dict['is_verified']
                    }
                else:
                    attempts = user_dict['login_attempts'] + 1
                    if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        lock_until = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
                        cursor.execute("UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?", (attempts, lock_until.isoformat(), user_dict['id']))
                    else:
                        cursor.execute("UPDATE users SET login_attempts = ? WHERE id = ?", (attempts, user_dict['id']))
                    
                    conn.commit()
                    remaining = Config.MAX_LOGIN_ATTEMPTS - attempts
                    if remaining > 0:
                        return False, f"Invalid password. {remaining} attempts remaining"
                    else:
                        return False, f"Account locked for {Config.LOGIN_LOCKOUT_MINUTES} minutes"
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return False, "An error occurred during authentication"
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        cache_key = f"user_{username}"
        
        with self.cache_lock:
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < Config.CACHE_TTL_SECONDS:
                    return cached_data
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.* FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.username = ? AND u.is_deleted = 0
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    with self.cache_lock:
                        self.cache[cache_key] = (user_data, time.time())
                    return user_data
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
        
        return None
    
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
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Error fetching user by ID: {e}")
        
        return None
    
    def update_profile(self, user_id: int, updates: Dict) -> bool:
        try:
            valid_fields = ['display_name', 'bio', 'avatar_path', 'cover_path', 'website', 'location', 'birthday', 'gender', 'is_private', 'theme', 'wallpaper']
            filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
            
            if not filtered_updates:
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
                values = list(filtered_updates.values()) + [user_id]
                
                cursor.execute(f"UPDATE profiles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", values)
                conn.commit()
                
                with self.cache_lock:
                    user = self.get_user_by_id(user_id)
                    if user:
                        self.cache.pop(f"user_{user['username']}", None)
                
                return True
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return False
    
    def update_last_active(self, user_id: int):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
                conn.commit()
        except:
            pass
    
    def search_users(self, query: str, limit: int = 50, exclude_user_id: int = None) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                params = [f"%{query}%", f"%{query}%"]
                
                sql = """
                    SELECT DISTINCT u.username, u.is_verified, u.is_premium, u.id,
                           p.display_name, p.bio, p.avatar_path, p.gender,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id AND is_accepted = 1) as follower_count
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.is_banned = 0 AND u.is_deleted = 0 AND u.account_status = 'active'
                    AND (u.username LIKE ? OR p.display_name LIKE ?)
                """
                
                if exclude_user_id:
                    sql += " AND u.id != ?"
                    params.append(exclude_user_id)
                
                sql += " ORDER BY follower_count DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def follow_user(self, follower_id: int, following_username: str) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, username, is_private FROM users 
                    WHERE username = ? AND is_deleted = 0 AND is_banned = 0
                """, (following_username,))
                target = cursor.fetchone()
                
                if not target:
                    return False, "User not found"
                
                following_id = target['id']
                
                if follower_id == following_id:
                    return False, "You cannot follow yourself"
                
                cursor.execute("""
                    SELECT is_accepted FROM follows WHERE follower_id = ? AND following_id = ?
                """, (follower_id, following_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("DELETE FROM follows WHERE follower_id = ? AND following_id = ?", (follower_id, following_id))
                    conn.commit()
                    return True, f"Unfollowed @{following_username}"
                else:
                    cursor.execute("INSERT INTO follows (follower_id, following_id) VALUES (?, ?)", (follower_id, following_id))
                    
                    notification_id = Utils.generate_id()
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, type, message, from_user_id)
                        VALUES (?, ?, 'follow', 'started following you', ?)
                    """, (notification_id, following_id, follower_id))
                    
                    conn.commit()
                    return True, f"Now following @{following_username}"
                        
        except Exception as e:
            logger.error(f"Follow error: {e}")
            return False, "An error occurred"
    
    def get_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT n.*, u.username, u.is_verified, pr.avatar_path
                    FROM notifications n
                    LEFT JOIN users u ON n.from_user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE n.user_id = ?
                    ORDER BY n.timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Get notifications error: {e}")
            return []
    
    def mark_notifications_read(self, user_id: int):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Mark read error: {e}")

# ========== POST MANAGER ==========
class PostManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_post(self, user_id: int, text: str = "", media_file=None, video_file=None, audio_file=None, location: str = "", price: float = 0.0, is_for_sale: bool = False) -> Tuple[bool, str]:
        try:
            post_id = Utils.generate_id()
            media_data = None
            media_name = None
            media_type = "image"
            
            if media_file:
                if Utils.validate_image(media_file.getvalue()):
                    optimized = Utils.optimize_image(media_file.getvalue())
                    media_data = base64.b64encode(optimized).decode()
                    media_name = media_file.name
            
            hashtags = json.dumps(Utils.extract_hashtags(text))
            mentions = json.dumps(Utils.extract_mentions(text))
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO posts (id, user_id, text, media_data, media_name, media_type,
                                     location, price, is_for_sale, hashtags, mentions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (post_id, user_id, text, media_data, media_name, media_type,
                      location, price, is_for_sale, hashtags, mentions))
                
                cursor.execute("UPDATE users SET total_posts = total_posts + 1 WHERE id = ?", (user_id,))
                
                conn.commit()
                return True, post_id
                
        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return False, str(e)
    
    def get_feed_posts(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict]:
        try:
            offset = (page - 1) * limit
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, u.username, u.is_verified, u.is_premium,
                           pr.display_name, pr.avatar_path, pr.gender,
                           (SELECT COUNT(*) FROM reactions WHERE post_id = p.id) as like_count,
                           (SELECT COUNT(*) FROM comments WHERE post_id = p.id AND is_deleted = 0) as comment_count
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE p.is_deleted = 0 AND p.visibility = 'public'
                    ORDER BY p.timestamp DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Feed error: {e}")
            return []
    
    def like_post(self, post_id: str, user_id: int) -> Tuple[bool, str]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                existing = cursor.fetchone()
                
                if existing:
                    cursor.execute("DELETE FROM reactions WHERE post_id = ? AND user_id = ?", (post_id, user_id))
                    conn.commit()
                    return True, "unliked"
                else:
                    cursor.execute("INSERT INTO reactions (post_id, user_id, reaction_type) VALUES (?, ?, 'like')", (post_id, user_id))
                    
                    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                    post_owner = cursor.fetchone()
                    
                    if post_owner and post_owner['user_id'] != user_id:
                        notification_id = Utils.generate_id()
                        cursor.execute("""
                            INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                            VALUES (?, ?, 'like', 'liked your post', ?, ?)
                        """, (notification_id, post_owner['user_id'], user_id, f"/post/{post_id}"))
                    
                    conn.commit()
                    return True, "liked"
                    
        except Exception as e:
            logger.error(f"Like error: {e}")
            return False, str(e)
    
    def add_comment(self, post_id: str, user_id: int, text: str, parent_id: str = None) -> Tuple[bool, str]:
        try:
            comment_id = Utils.generate_id()
            text = SecurityUtils.sanitize_input(text, Config.MAX_COMMENT_LENGTH)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO comments (id, post_id, user_id, parent_id, text) VALUES (?, ?, ?, ?, ?)", (comment_id, post_id, user_id, parent_id, text))
                
                cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                post_owner = cursor.fetchone()
                
                if post_owner and post_owner['user_id'] != user_id:
                    notification_id = Utils.generate_id()
                    cursor.execute("""
                        INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                        VALUES (?, ?, 'comment', 'commented on your post', ?, ?)
                    """, (notification_id, post_owner['user_id'], user_id, f"/post/{post_id}"))
                
                conn.commit()
                return True, comment_id
                
        except Exception as e:
            logger.error(f"Comment error: {e}")
            return False, str(e)
    
    def get_comments(self, post_id: str, limit: int = 50) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.*, u.username, u.is_verified, u.is_premium,
                           pr.display_name, pr.avatar_path, pr.gender
                    FROM comments c
                    JOIN users u ON c.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE c.post_id = ? AND c.is_deleted = 0
                    ORDER BY c.timestamp ASC
                    LIMIT ?
                """, (post_id, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Get comments error: {e}")
            return []

# ========== CHAT MANAGER ==========
class ChatManager:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def send_message(self, from_id: int, to_id: int, text: str, media_file=None, sticker=None, gif=None) -> Tuple[bool, str]:
        try:
            message_id = Utils.generate_id()
            chat_id = f"chat_{min(from_id, to_id)}_{max(from_id, to_id)}"
            text = SecurityUtils.sanitize_input(text, Config.MAX_MESSAGE_LENGTH)
            
            media_data = None
            if media_file:
                if Utils.validate_image(media_file.getvalue()):
                    optimized = Utils.optimize_image(media_file.getvalue())
                    media_data = base64.b64encode(optimized).decode()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO messages (id, chat_id, from_id, to_id, text, media_data, sticker_data, gif_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (message_id, chat_id, from_id, to_id, text, media_data, sticker, gif))
                
                conn.commit()
                return True, message_id
                
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False, str(e)
    
    def get_conversations(self, user_id: int) -> List[Dict]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT 
                        CASE 
                            WHEN m.from_id = ? THEN m.to_id
                            ELSE m.from_id
                        END as other_user_id,
                        u.username,
                        u.is_verified,
                        u.is_premium,
                        pr.avatar_path,
                        pr.display_name,
                        (SELECT text FROM messages WHERE chat_id = m.chat_id ORDER BY timestamp DESC LIMIT 1) as last_message,
                        (SELECT timestamp FROM messages WHERE chat_id = m.chat_id ORDER BY timestamp DESC LIMIT 1) as last_message_time,
                        (SELECT COUNT(*) FROM messages WHERE chat_id = m.chat_id AND to_id = ? AND is_read = 0) as unread_count
                    FROM messages m
                    JOIN users u ON (u.id = m.from_id OR u.id = m.to_id) AND u.id != ?
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE (m.from_id = ? OR m.to_id = ?)
                    AND u.id IS NOT NULL
                    ORDER BY last_message_time DESC
                """, (user_id, user_id, user_id, user_id, user_id))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Get conversations error: {e}")
            return []
    
    def get_messages(self, user1_id: int, user2_id: int, limit: int = 50) -> List[Dict]:
        try:
            chat_id = f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, u.username, u.is_verified, pr.avatar_path
                    FROM messages m
                    JOIN users u ON m.from_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE m.chat_id = ? AND m.is_deleted = 0
                    ORDER BY m.timestamp DESC
                    LIMIT ?
                """, (chat_id, limit))
                
                messages = [dict(row) for row in cursor.fetchall()]
                messages.reverse()
                
                cursor.execute("UPDATE messages SET is_read = 1 WHERE chat_id = ? AND to_id = ? AND is_read = 0", (chat_id, user1_id))
                
                conn.commit()
                return messages
        except Exception as e:
            logger.error(f"Get messages error: {e}")
            return []

# ========== ENHANCED STREAMLIT UI WITH WORKING NAVIGATION ==========
class SocialiteUI:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self._init_session()
    
    def _init_session(self):
        defaults = {
            'auth': False,
            'user_id': None,
            'username': None,
            'session_token': None,
            'csrf_token': None,
            'current_tab': 'feed',
            'previous_tab': None,
            'active_chat': None,
            'show_create_modal': False,
            'feed_page': 1,
            'show_comments_for': None,
            'nav_history': [],
            'search_query': '',
            'notifications_unread': 0,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def render(self):
        if not st.session_state.auth:
            self.render_auth()
            return
        
        if st.session_state.user_id:
            self.user_manager.update_last_active(st.session_state.user_id)
        
        self.handle_navigation()
        self.inject_styles()
        self.render_top_nav()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        tab = st.session_state.current_tab
        if tab == 'feed':
            self.render_feed()
        elif tab == 'explore':
            self.render_explore()
        elif tab == 'chats':
            self.render_chats()
        elif tab == 'marketplace':
            self.render_marketplace()
        elif tab == 'notifications':
            self.render_notifications()
        elif tab == 'profile':
            self.render_profile()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.show_create_modal:
            self.render_create_modal()
    
    def handle_navigation(self):
        query_params = st.query_params
        if 'tab' in query_params:
            tab = query_params['tab']
            if tab in ['feed', 'explore', 'chats', 'marketplace', 'notifications', 'profile']:
                st.session_state.current_tab = tab
        
        if st.session_state.auth and st.session_state.user_id:
            notifications = self.user_manager.get_notifications(st.session_state.user_id, 1)
            st.session_state.notifications_unread = sum(1 for n in notifications if not n.get('is_read'))
    
    def navigate_to(self, tab: str):
        if tab != st.session_state.current_tab:
            st.session_state.previous_tab = st.session_state.current_tab
            st.session_state.nav_history.append(st.session_state.current_tab)
            st.session_state.current_tab = tab
            st.query_params['tab'] = tab
            st.rerun()
    
    def go_back(self):
        if st.session_state.nav_history:
            previous = st.session_state.nav_history.pop()
            st.session_state.current_tab = previous
            st.query_params['tab'] = previous
            st.rerun()
    
    def render_top_nav(self):
        current_tab = st.session_state.current_tab
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        unread_count = st.session_state.notifications_unread
        
        st.markdown("""
        <style>
        .nav-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 16px;
            background: rgba(10, 10, 26, 0.95);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid rgba(255, 215, 0, 0.2);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .nav-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-brand img {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 2px solid #FFD700;
        }
        .nav-brand-text {
            font-weight: 800;
            font-size: 1.1rem;
            background: linear-gradient(135deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .nav-user {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        nav_items = [
            ('feed', '🏠', 'Feed'),
            ('explore', '🔍', 'Explore'),
            ('chats', '💬', 'Chats'),
            ('marketplace', '🛒', 'Shop'),
            ('notifications', f'🔔{" " + str(unread_count) if unread_count > 0 else ""}', 'Alerts'),
            ('profile', '👤', 'Profile'),
        ]
        
        cols = st.columns([1.5, 1, 1, 1, 1, 1, 1, 1.5])
        
        with cols[0]:
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0;">
                <img src="{Config.LOGO_URL}" style="width: 28px; height: 28px; border-radius: 50%; 
                     object-fit: cover; border: 2px solid #FFD700;">
                <span style="font-weight: 800; font-size: 0.95rem; 
                           background: linear-gradient(135deg, #FFD700, #FFA500);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Socialite
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        for i, (tab, icon, label) in enumerate(nav_items):
            with cols[i + 1]:
                is_active = current_tab == tab
                button_type = "primary" if is_active else "secondary"
                
                if st.button(icon, key=f"nav_btn_{tab}", use_container_width=True, 
                           type=button_type, help=label):
                    self.navigate_to(tab)
        
        with cols[-1]:
            avatar_html = self.render_avatar_html(user, 28)
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; justify-content: flex-end; padding: 4px 0;">
                {avatar_html}
                <span style="color: #f1f5f9; font-weight: 600; font-size: 0.85rem;">@{html.escape(user['username'])}</span>
            </div>
            """, unsafe_allow_html=True)
    
    def inject_styles(self):
        theme = self._get_current_theme()
        
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        * {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            -webkit-font-smoothing: antialiased !important;
        }}
        
        #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
        
        .stApp {{
            background: {theme['gradient']} !important;
            min-height: 100vh !important;
        }}
        
        .main {{ min-height: 100vh !important; }}
        .block-container {{ padding: 0 !important; margin: 0 !important; max-width: 100% !important; }}
        
        .main-content {{
            padding: 12px 16px !important;
            max-width: 800px !important;
            margin: 0 auto !important;
        }}
        
        .stButton > button {{
            border-radius: 10px !important;
            padding: 8px 16px !important;
            font-weight: 500 !important;
            transition: all 0.3s !important;
            min-height: auto !important;
            font-size: 0.9rem !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}
        
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #FFD700, #FFA500) !important;
            color: #1a0033 !important;
            border: none !important;
            font-weight: 700 !important;
        }}
        
        .stButton > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            color: {theme['text']} !important;
        }}
        
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid rgba(255, 215, 0, 0.4) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
        }}
        
        .card {{
            background: {theme['card']} !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            padding: 16px !important;
            margin-bottom: 12px !important;
            transition: all 0.3s !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .card:hover {{
            border-color: rgba(255, 215, 0, 0.2) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        ::-webkit-scrollbar {{
            width: 6px !important;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent !important;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 215, 0, 0.3) !important;
            border-radius: 3px !important;
        }}
        
        .modal-overlay {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: rgba(0, 0, 0, 0.9) !important;
            backdrop-filter: blur(10px) !important;
            z-index: 10001 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        
        .modal-box {{
            background: {theme['bg']} !important;
            border: 2px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 20px !important;
            width: 90% !important;
            max-width: 500px !important;
            max-height: 85vh !important;
            overflow-y: auto !important;
            padding: 24px !important;
        }}
        
        @media (max-width: 640px) {{
            .main-content {{
                padding: 8px 10px !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_auth(self):
        st.markdown("""
        <style>
        .stApp { 
            background: linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%) !important; 
        }
        </style>
        """, unsafe_allow_html=True)
        
        _, col, _ = st.columns([1, 2, 1])
        
        with col:
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem 0;">
                <img src="{Config.LOGO_URL}" 
                     style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover;
                            border: 3px solid #FFD700; box-shadow: 0 0 40px rgba(255, 215, 0, 0.5);">
                <h1 style="font-weight: 900; font-size: 2.5rem;
                         background: linear-gradient(135deg, #FFD700, #FFA500, #FFD700);
                         -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                         margin-top: 1rem;">SOCIALITE</h1>
                <p style="color: #94a3b8; font-size: 1.1rem;">{Config.APP_SLOGAN}</p>
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
                                st.session_state.username = result['username']
                                st.session_state.user_id = result['user_id']
                                st.session_state.session_token = result['session_token']
                                st.session_state.csrf_token = result['csrf_token']
                                st.rerun()
                            else:
                                st.error(result)
                        else:
                            st.error("Please fill in all fields")
            
            with tab2:
                with st.form("register_form"):
                    new_username = st.text_input("Choose Username", placeholder="3-30 characters")
                    email = st.text_input("Email (optional)", placeholder="your@email.com")
                    new_password = st.text_input("Choose Password", type="password", placeholder="Min 8 characters")
                    confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                    
                    if st.form_submit_button("✨ Create Account", use_container_width=True):
                        if not new_username or not new_password:
                            st.error("Username and password are required")
                        elif new_password != confirm:
                            st.error("Passwords don't match")
                        else:
                            success, message = self.user_manager.create_user(new_username, new_password, email)
                            if success:
                                st.success(message)
                                st.balloons()
                            else:
                                st.error(message)
    
    def render_feed(self):
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.session_state.previous_tab:
                if st.button("← Back", key="feed_back"):
                    self.go_back()
        with col2:
            st.markdown('<h2 style="color: #FFD700; text-align: center;">✨ Your Feed</h2>', unsafe_allow_html=True)
        with col3:
            if st.button("✚ New Post", key="create_post_btn", type="primary"):
                st.session_state.show_create_modal = True
                st.rerun()
        
        posts = self.post_manager.get_feed_posts(st.session_state.user_id, page=st.session_state.feed_page)
        
        if not posts:
            st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
                <div style="font-size: 5rem;">👑</div>
                <h3 style="color: #FFD700; margin-top: 1rem;">Welcome to Socialite!</h3>
                <p>Create your first post or explore users to follow!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for post in posts:
                self.render_post_card(post)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📜 Load More", use_container_width=True):
                    st.session_state.feed_page += 1
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_post_card(self, post: Dict):
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                    {self.render_avatar_html(post, 36)}
                    <div>
                        <div style="color: #f1f5f9; font-weight: 600;">
                            @{html.escape(post['username'])}
                            {'<span style="color: #FFD700;"> ✓</span>' if post.get('is_verified') else ''}
                        </div>
                        <div style="color: #94a3b8; font-size: 0.75rem;">
                            {Utils.format_timestamp(post['timestamp'])}
                            {' · 📍 ' + html.escape(post['location']) if post.get('location') else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if post.get('text'):
                text = html.escape(post['text'])
                text = re.sub(r'#(\w+)', r'<span style="color:#FFD700;">#\1</span>', text)
                text = re.sub(r'@(\w+)', r'<span style="color:#64ffda;">@\1</span>', text)
                st.markdown(f"""
                <div style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.6; padding: 8px 0;">
                    {text}
                </div>
                """, unsafe_allow_html=True)
            
            if post.get('media_data') and post.get('media_type') == 'image':
                try:
                    image_bytes = base64.b64decode(post['media_data'])
                    st.image(image_bytes, use_column_width=True)
                except:
                    pass
            
            like_count = post.get('like_count', 0)
            comment_count = post.get('comment_count', 0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"❤️ {Utils.format_number(like_count)}", key=f"like_{post['id']}", use_container_width=True):
                    success, result = self.post_manager.like_post(post['id'], st.session_state.user_id)
                    if success:
                        st.toast(f"Post {result}!")
                        st.rerun()
            
            with col2:
                if st.button(f"💬 {Utils.format_number(comment_count)}", key=f"comment_{post['id']}", use_container_width=True):
                    st.session_state.show_comments_for = post['id'] if st.session_state.show_comments_for != post['id'] else None
                    st.rerun()
            
            with col3:
                if st.button("🔖", key=f"save_{post['id']}", use_container_width=True):
                    st.toast("Saved!")
            
            with col4:
                if st.button("⚡", key=f"boost_{post['id']}", use_container_width=True):
                    st.toast("Boosted!")
            
            if st.session_state.get('show_comments_for') == post['id']:
                st.markdown("""<hr style="border-color: rgba(255,215,0,0.1);">""", unsafe_allow_html=True)
                
                with st.form(f"comment_form_{post['id']}", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        comment_text = st.text_input("Write a comment...", key=f"comment_input_{post['id']}", label_visibility="collapsed")
                    with col2:
                        if st.form_submit_button("Post", use_container_width=True, type="primary"):
                            if comment_text.strip():
                                success, result = self.post_manager.add_comment(post['id'], st.session_state.user_id, comment_text)
                                if success:
                                    st.toast("Comment posted!")
                                    st.rerun()
                
                comments = self.post_manager.get_comments(post['id'])
                for comment in comments[:5]:
                    st.markdown(f"""
                    <div style="display: flex; gap: 8px; padding: 8px; background: rgba(255,255,255,0.02); border-radius: 8px; margin: 4px 0;">
                        {self.render_avatar_html(comment, 24)}
                        <div>
                            <span style="color: #FFD700; font-weight: 600; font-size: 0.8rem;">@{html.escape(comment['username'])}</span>
                            <span style="color: #64748b; font-size: 0.7rem; margin-left: 8px;">{Utils.format_timestamp(comment['timestamp'])}</span>
                            <p style="color: #e2e8f0; font-size: 0.85rem; margin: 2px 0 0 0;">{html.escape(comment['text'])}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_create_modal(self):
        st.markdown("""
        <div class="modal-overlay">
        <div class="modal-box">
        <h3 style="color: #FFD700; text-align: center;">✨ Create Post</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_post_form", clear_on_submit=True):
            text = st.text_area("What's on your mind?", max_chars=Config.MAX_POST_LENGTH, height=120)
            image_file = st.file_uploader("📷 Image", type=['png', 'jpg', 'jpeg', 'gif', 'webp'])
            location = st.text_input("📍 Location", placeholder="Add location")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("📤 Post", use_container_width=True, type="primary"):
                    if text or image_file:
                        success, result = self.post_manager.create_post(
                            st.session_state.user_id, text=text, media_file=image_file, location=location
                        )
                        if success:
                            st.session_state.show_create_modal = False
                            st.toast("Post created! ✨")
                            st.rerun()
                        else:
                            st.error(f"Failed: {result}")
                    else:
                        st.error("Post cannot be empty")
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_explore(self):
        st.markdown('<h3 style="color: #FFD700;">🔍 Explore</h3>', unsafe_allow_html=True)
        
        query = st.text_input("Search users...", placeholder="Search by username or name")
        
        if query:
            users = self.user_manager.search_users(query, exclude_user_id=st.session_state.user_id)
            if users:
                for user in users:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 10px;">
                            {self.render_avatar_html(user, 40)}
                            <div>
                                <div style="color: #f1f5f9; font-weight: 600;">
                                    @{html.escape(user['username'])}
                                    {'<span style="color: #FFD700;"> ✓</span>' if user.get('is_verified') else ''}
                                </div>
                                <div style="color: #94a3b8; font-size: 0.75rem;">
                                    {Utils.format_number(user.get('follower_count', 0))} followers
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("Follow", key=f"follow_{user['username']}", use_container_width=True):
                            success, msg = self.user_manager.follow_user(st.session_state.user_id, user['username'])
                            st.toast(msg)
                            st.rerun()
                    with col3:
                        if st.button("💬", key=f"chat_{user['username']}", use_container_width=True):
                            st.session_state.active_chat = user['username']
                            self.navigate_to('chats')
            else:
                st.info("No users found")
        else:
            st.info("Search for users to connect with!")
    
    def render_chats(self):
        st.markdown('<h3 style="color: #FFD700;">💬 Messages</h3>', unsafe_allow_html=True)
        
        if st.session_state.active_chat:
            other_user = self.user_manager.get_user_by_username(st.session_state.active_chat)
            if other_user:
                if st.button("← Back to conversations"):
                    st.session_state.active_chat = None
                    st.rerun()
                
                messages = self.chat_manager.get_messages(st.session_state.user_id, other_user['user_id'])
                
                for msg in messages:
                    is_me = msg['from_id'] == st.session_state.user_id
                    align = "flex-end" if is_me else "flex-start"
                    bg = "rgba(255,215,0,0.2)" if is_me else "rgba(255,255,255,0.05)"
                    st.markdown(f"""
                    <div style="display: flex; justify-content: {align}; margin-bottom: 8px;">
                        <div style="max-width: 70%; background: {bg}; border-radius: 12px; padding: 8px 12px;">
                            <p style="margin: 0; color: #e2e8f0; font-size: 0.85rem;">{html.escape(msg['text'])}</p>
                            <p style="margin: 4px 0 0 0; color: #64748b; font-size: 0.7rem; text-align: right;">{Utils.format_timestamp(msg['timestamp'])}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with st.form("send_message_form", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        msg_text = st.text_input("Type a message...", key="msg_input", label_visibility="collapsed")
                    with col2:
                        if st.form_submit_button("Send", use_container_width=True, type="primary"):
                            if msg_text.strip():
                                self.chat_manager.send_message(st.session_state.user_id, other_user['user_id'], msg_text)
                                st.rerun()
        else:
            conversations = self.chat_manager.get_conversations(st.session_state.user_id)
            if not conversations:
                st.info("No conversations yet. Start by messaging users!")
            else:
                for conv in conversations:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"""
                        <div style="display: flex; align-items: center; gap: 10px; padding: 8px;">
                            {self.render_avatar_html(conv, 40)}
                            <div>
                                <div style="color: #f1f5f9; font-weight: 600;">@{html.escape(conv['username'])}</div>
                                <div style="color: #94a3b8; font-size: 0.75rem;">
                                    {html.escape(conv.get('last_message', 'No messages')[:50])}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("💬", key=f"open_chat_{conv['username']}", use_container_width=True):
                            st.session_state.active_chat = conv['username']
                            st.rerun()
    
    def render_marketplace(self):
        st.markdown('<h3 style="color: #FFD700;">🛒 Marketplace</h3>', unsafe_allow_html=True)
        st.info("Marketplace coming soon! Create posts with prices to list items.")
    
    def render_notifications(self):
        st.markdown('<h3 style="color: #FFD700;">🔔 Notifications</h3>', unsafe_allow_html=True)
        
        self.user_manager.mark_notifications_read(st.session_state.user_id)
        notifications = self.user_manager.get_notifications(st.session_state.user_id)
        
        if not notifications:
            st.info("No notifications yet!")
        else:
            for notif in notifications:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.04); border-radius: 12px; padding: 12px; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <p style="color: #e2e8f0; margin: 0; flex: 1;">{html.escape(notif['message'])}</p>
                        <span style="color: #64748b; font-size: 0.75rem;">{Utils.format_timestamp(notif['timestamp'])}</span>
                        {'<span style="color: #FFD700;">●</span>' if not notif['is_read'] else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    def render_profile(self):
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            st.error("User not found")
            return
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px 0;">
            {self.render_avatar_html(user, 100)}
            <h2 style="color: #FFD700; margin-top: 12px;">
                @{html.escape(user['username'])}
                {'<span style="color: #FFD700;"> ✓</span>' if user.get('is_verified') else ''}
            </h2>
            <p style="color: #94a3b8;">{html.escape(user.get('bio', 'No bio yet'))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Posts", user.get('total_posts', 0))
        with col2:
            follower_count = self._get_follower_count(user['user_id'])
            st.metric("Followers", follower_count)
        with col3:
            following_count = self._get_following_count(user['user_id'])
            st.metric("Following", following_count)
        
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile_form"):
                display_name = st.text_input("Display Name", value=user.get('display_name', '') or '', max_chars=50)
                bio = st.text_area("Bio", value=user.get('bio', '') or '', max_chars=Config.MAX_BIO_LENGTH, height=80)
                col1, col2 = st.columns(2)
                with col1:
                    website = st.text_input("Website", value=user.get('website', '') or '')
                with col2:
                    location = st.text_input("Location", value=user.get('location', '') or '')
                
                if st.form_submit_button("💾 Save", use_container_width=True, type="primary"):
                    updates = {
                        'display_name': display_name,
                        'bio': bio,
                        'website': website,
                        'location': location
                    }
                    if self.user_manager.update_profile(user['user_id'], updates):
                        st.success("Profile updated! ✨")
                        st.rerun()
        
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
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
                return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,215,0,0.5);flex-shrink:0;">'
            except:
                pass
        
        color = Utils.get_avatar_color(username)
        initials = Utils.get_initials(username)
        
        return f'''<div style="width:{size}px;height:{size}px;border-radius:50%;
                background:linear-gradient(135deg, {color}, {color}dd);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:700;font-size:{size*0.35}px;
                flex-shrink:0;border:2px solid rgba(255,215,0,0.5);">
            {initials}
        </div>'''
    
    def _get_current_theme(self) -> Dict:
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                theme_key = user.get('theme', 'midnight')
                themes = {
                    "midnight": {"name": "Midnight", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"},
                    "ocean": {"name": "Ocean", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"},
                }
                return themes.get(theme_key, themes['midnight'])
        return {"name": "Midnight", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"}
    
    def _get_follower_count(self, user_id: int) -> int:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE following_id = ? AND is_accepted = 1", (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0
    
    def _get_following_count(self, user_id: int) -> int:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = ? AND is_accepted = 1", (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0

# ========== MAIN APPLICATION ==========
def main():
    try:
        db = DatabaseManager()
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Config.BACKUP_DIR / f"socialite_backup_{timestamp}.db"
            if Config.DB_PATH.exists():
                shutil.copy2(Config.DB_PATH, backup_path)
            
            backups = sorted(Config.BACKUP_DIR.glob("socialite_backup_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")
        
        app = SocialiteUI()
        app.render()
        
    except Exception as e:
        logger.error(f"Critical application error: {e}", exc_info=True)
        st.error(f"""
        ## ⚠️ Application Error
        
        An unexpected error occurred: {str(e)}
        
        Please try:
        1. **Refresh the page**
        2. **Clear your browser cache**
        3. **Contact support** if the problem persists
        """)
    finally:
        try:
            pool = DatabasePool()
            pool.close_all()
        except:
            pass

if __name__ == "__main__":
    main()
