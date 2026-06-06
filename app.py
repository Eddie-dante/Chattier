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

# Must be first Streamlit command
st.set_page_config(
    page_title="Socialite - Premium Social Network",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Socialite - The Premium Social Experience v6.0"
    }
)

# ========== ENHANCED CONFIGURATION ==========
class Config:
    """Ultimate configuration for Socialite"""
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "6.0.0"
    APP_BUILD = "2024.3"
    
    # Brand Logo (from Google Drive)
    LOGO_URL = "https://drive.google.com/uc?export=view&id=1Rxb3t3yLEdrqS6hWZJw4DPg6T1PNSkKb"
    
    # Directory Structure
    DATA_DIR = pathlib.Path("data")
    DB_PATH = DATA_DIR / "socialite_v6.db"
    UPLOADS_DIR = DATA_DIR / "uploads"
    BACKUP_DIR = DATA_DIR / "backups"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"
    MEDIA_DIR = DATA_DIR / "media"
    STICKERS_DIR = DATA_DIR / "stickers"
    GIFS_DIR = DATA_DIR / "gifs"
    EMOJIS_DIR = DATA_DIR / "emojis"
    
    # Enhanced Content Limits
    MAX_POST_LENGTH = 10000
    MAX_COMMENT_LENGTH = 2000
    MAX_BIO_LENGTH = 500
    MAX_MESSAGE_LENGTH = 25000
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 8
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_AVATAR_SIZE = 15 * 1024 * 1024  # 15MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_MEDIA_PER_POST = 20
    MAX_GIF_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_STICKER_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Enhanced Security
    MAX_LOGIN_ATTEMPTS = 3
    LOGIN_LOCKOUT_MINUTES = 30
    SESSION_TIMEOUT_HOURS = 12
    PASSWORD_HASH_ITERATIONS = 600000
    ENCRYPTION_KEY_LENGTH = 32
    TOKEN_EXPIRY_HOURS = 24
    MAX_SESSIONS_PER_USER = 5
    RATE_LIMIT_WINDOW = 30
    MAX_REQUESTS_PER_WINDOW = 50
    
    # Time Limits
    STORY_EXPIRY_HOURS = 24
    ONLINE_THRESHOLD_SECONDS = 180
    CACHE_TTL_SECONDS = 30
    MESSAGE_EDIT_WINDOW = 300  # 5 minutes
    
    # Database Limits
    MAX_FEED_ITEMS = 5000
    MAX_CHAT_MESSAGES = 10000
    MAX_NOTIFICATIONS = 500
    MAX_GROUPS = 100
    MAX_CHANNELS = 50
    MAX_FOLLOWING = 10000
    MAX_BLOCKED = 2000
    MAX_SAVED_POSTS = 10000

# Create all directories
for dir_path in [Config.DATA_DIR, Config.UPLOADS_DIR, Config.BACKUP_DIR, 
                 Config.CACHE_DIR, Config.LOGS_DIR, Config.TEMP_DIR,
                 Config.MEDIA_DIR, Config.STICKERS_DIR, Config.GIFS_DIR, 
                 Config.EMOJIS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ========== ENHANCED LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'socialite_v6.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== SECURITY UTILITIES ==========
class SecurityUtils:
    """Enhanced security utilities"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate session token"""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Enhanced password hashing with Argon2-like parameters"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use multiple rounds of hashing for extra security
        h = hashlib.pbkdf2_hmac(
            'sha512',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            Config.PASSWORD_HASH_ITERATIONS
        )
        
        # Double hash for extra security
        h = hashlib.pbkdf2_hmac(
            'sha256',
            h,
            salt.encode('utf-8'),
            100000
        )
        
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password with constant-time comparison"""
        try:
            h, _ = SecurityUtils.hash_password(password, salt)
            return hmac.compare_digest(h, stored_hash)
        except Exception:
            return False
    
    @staticmethod
    def encrypt_data(data: str, key: str = None) -> Tuple[str, str]:
        """Encrypt sensitive data"""
        if key is None:
            key = secrets.token_hex(Config.ENCRYPTION_KEY_LENGTH)
        
        # Simple XOR encryption with key stretching
        key_bytes = hashlib.sha256(key.encode()).digest()
        data_bytes = data.encode('utf-8')
        
        encrypted = bytes([data_bytes[i] ^ key_bytes[i % len(key_bytes)] 
                          for i in range(len(data_bytes))])
        
        return base64.b64encode(encrypted).decode(), key
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: str) -> str:
        """Decrypt sensitive data"""
        try:
            key_bytes = hashlib.sha256(key.encode()).digest()
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            decrypted = bytes([encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)] 
                              for i in range(len(encrypted_bytes))])
            
            return decrypted.decode('utf-8')
        except Exception:
            return ""
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 5000, 
                      allow_html: bool = False) -> str:
        """Advanced input sanitization"""
        if not text:
            return ""
        
        # Remove null bytes and control characters
        text = text.replace('\x00', '')
        text = ''.join(c for c in text if ord(c) >= 32 or c in ['\n', '\r', '\t'])
        
        # HTML sanitization
        if not allow_html:
            text = html.escape(text)
        else:
            # Allow only safe HTML tags
            allowed_tags = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span']
            for tag in allowed_tags:
                text = text.replace(f'<{tag}>', f'&lt;{tag}&gt;')
                text = text.replace(f'</{tag}>', f'&lt;/{tag}&gt;')
        
        # Truncate
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        return text.strip()
    
    @staticmethod
    def validate_file_signature(data: bytes) -> Optional[str]:
        """Validate file type by magic bytes"""
        if len(data) < 4:
            return None
        
        # Image signatures
        if data.startswith(b'\xff\xd8\xff'):
            return 'image/jpeg'
        elif data.startswith(b'\x89PNG\r\n\x1a\n'):
            return 'image/png'
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return 'image/gif'
        elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
            return 'image/webp'
        
        # Video signatures
        elif data.startswith(b'\x00\x00\x00\x18ftypmp42') or \
             data.startswith(b'\x00\x00\x00\x20ftypmp42'):
            return 'video/mp4'
        elif data.startswith(b'\x1aE\xdf\xa3'):
            return 'video/webm'
        
        # Audio signatures
        elif data.startswith(b'ID3') or data.startswith(b'\xff\xfb') or \
             data.startswith(b'\xff\xf3') or data.startswith(b'\xff\xf2'):
            return 'audio/mpeg'
        
        return None

# ========== ENHANCED UTILITIES ==========
class Utils:
    """Enhanced utility functions"""
    
    @staticmethod
    def generate_id() -> str:
        """Generate unique ID with timestamp"""
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(8)
        return f"{timestamp}_{random_part}"
    
    @staticmethod
    def generate_short_id(length: int = 16) -> str:
        """Generate short unique ID"""
        return secrets.token_hex(length // 2)[:length]
    
    @staticmethod
    def format_timestamp(ts) -> str:
        """Format timestamp to relative time"""
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
            elif diff < 2592000:
                return f"{int(diff//604800)}w ago"
            elif diff < 31536000:
                return f"{int(diff//2592000)}mo ago"
            else:
                return f"{int(diff//31536000)}y ago"
        except:
            return ""
    
    @staticmethod
    def format_number(num: int) -> str:
        """Format large numbers"""
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
        """Extract hashtags from text"""
        if not text:
            return []
        return re.findall(r'#(\w+)', text)
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """Extract @mentions from text"""
        if not text:
            return []
        return re.findall(r'@(\w+)', text)
    
    @staticmethod
    def get_avatar_color(username: str) -> str:
        """Get consistent color for avatar"""
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#DDA0DD',
            '#FF8A80', '#B388FF', '#FF5722', '#9C27B0', '#3F51B5',
            '#009688', '#FF9800', '#795548', '#607D8B', '#E91E63',
            '#00BCD4', '#8BC34A', '#FF4081', '#536DFE', '#00BFA5',
            '#FF6E40', '#7C4DFF', '#64FFDA', '#FFD740', '#40C4FF'
        ]
        if not username:
            return colors[0]
        return colors[hash(username) % len(colors)]
    
    @staticmethod
    def get_initials(username: str) -> str:
        """Get initials from username"""
        if not username:
            return "?"
        parts = username.replace('_', ' ').replace('.', ' ').split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if len(username) >= 2 else username[0].upper()
    
    @staticmethod
    def optimize_image(data: bytes, max_size: Tuple[int, int] = (1920, 1920), 
                      quality: int = 85) -> bytes:
        """Optimize image with advanced processing"""
        try:
            img = Image.open(io.BytesIO(data))
            original_format = img.format
            
            # Convert to RGB if necessary
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
            
            # Smart resize
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Apply subtle sharpening for better quality
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, 
                    optimize=True, progressive=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            return data
    
    @staticmethod
    def validate_image(data: bytes) -> bool:
        """Validate image file"""
        file_type = SecurityUtils.validate_file_signature(data)
        return file_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    
    @staticmethod
    def validate_video(data: bytes) -> bool:
        """Validate video file"""
        file_type = SecurityUtils.validate_file_signature(data)
        return file_type in ['video/mp4', 'video/webm']
    
    @staticmethod
    def validate_audio(data: bytes) -> bool:
        """Validate audio file"""
        file_type = SecurityUtils.validate_file_signature(data)
        return file_type in ['audio/mpeg', 'audio/wav', 'audio/ogg']

# ========== EMOJI & STICKER SYSTEM ==========
EMOJI_CATEGORIES = {
    "😀 Smileys": ["😀", "😃", "😄", "😁", "😅", "😂", "🤣", "😊", "😇", "🙂", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😪", "😴", "🥱", "😷", "🤒", "🤕", "🤢", "🤮", "🥴", "😵", "🤯", "🤠"],
    "❤️ Hearts": ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "♥️", "💌", "💋", "💯", "🔥", "⭐", "🌟", "✨", "💫", "🎯", "💎"],
    "👋 Gestures": ["👋", "🤚", "✋", "🖐", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏"],
    "🎉 Celebration": ["🎉", "🎊", "🎈", "🎂", "🎀", "🎁", "🎇", "🎆", "🧨", "✨", "🥂", "🍾", "🎵", "🎶", "🎤", "🎧", "📯", "🎷", "🎸", "🎹", "🎺", "🎻", "🥁", "🎼"],
    "🐱 Animals": ["🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐔", "🐧", "🐦", "🐤", "🦆", "🦅", "🦉", "🦇", "🐺", "🐗", "🐴", "🦄", "🐝", "🐛", "🦋"],
}

# ========== ENHANCED DATABASE MANAGER ==========
class DatabaseManager:
    """Enhanced database manager with connection pooling"""
    
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
        self._local = threading.local()
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(Config.DB_PATH),
                check_same_thread=False,
                timeout=60,
                isolation_level=None
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            self._local.connection.execute("PRAGMA cache_size=-50000")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
            self._local.connection.execute("PRAGMA mmap_size=536870912")
            self._local.connection.execute("PRAGMA busy_timeout=5000")
        
        try:
            yield self._local.connection
        except Exception as e:
            try:
                self._local.connection.rollback()
            except:
                pass
            logger.error(f"Database error: {e}", exc_info=True)
            raise
    
    def _init_db(self):
        """Initialize complete database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # ========== USERS TABLE ==========
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
                    total_likes_received INTEGER DEFAULT 0,
                    total_comments INTEGER DEFAULT 0,
                    total_shares INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 0.0,
                    account_status TEXT DEFAULT 'active',
                    wallet_balance REAL DEFAULT 0.0,
                    premium_until TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    email_verified BOOLEAN DEFAULT 0,
                    phone_verified BOOLEAN DEFAULT 0
                )
            """)
            
            # ========== PROFILES TABLE ==========
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
                    wallpaper TEXT DEFAULT '🌈 Gradient',
                    language TEXT DEFAULT 'en',
                    timezone TEXT DEFAULT 'UTC',
                    custom_css TEXT DEFAULT '',
                    show_online_status BOOLEAN DEFAULT 1,
                    allow_messages_from TEXT DEFAULT 'everyone',
                    comment_filter TEXT DEFAULT 'off',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== SESSIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    csrf_token TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    device_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== FOLLOWS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_accepted BOOLEAN DEFAULT 1,
                    is_favorite BOOLEAN DEFAULT 0,
                    notifications_enabled BOOLEAN DEFAULT 1,
                    PRIMARY KEY (follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== BLOCKS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    blocker_id INTEGER NOT NULL,
                    blocked_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT DEFAULT '',
                    PRIMARY KEY (blocker_id, blocked_id),
                    FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (blocked_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== POSTS TABLE ==========
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
                    post_type TEXT DEFAULT 'post',
                    location TEXT DEFAULT '',
                    latitude REAL,
                    longitude REAL,
                    price REAL DEFAULT 0.0,
                    is_for_sale BOOLEAN DEFAULT 0,
                    hashtags TEXT DEFAULT '[]',
                    mentions TEXT DEFAULT '[]',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
                    edited_at TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    is_archived BOOLEAN DEFAULT 0,
                    visibility TEXT DEFAULT 'public',
                    view_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    language TEXT DEFAULT 'en',
                    sentiment TEXT DEFAULT 'neutral',
                    is_nsfw BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== POLLS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS polls (
                    post_id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    ends_at TIMESTAMP,
                    total_votes INTEGER DEFAULT 0,
                    is_multiple_choice BOOLEAN DEFAULT 0,
                    is_anonymous BOOLEAN DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poll_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    option_text TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
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
            
            # ========== REACTIONS TABLE ==========
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
            
            # ========== COMMENTS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    parent_id TEXT,
                    text TEXT NOT NULL,
                    media_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
                    edited_at TIMESTAMP,
                    is_deleted BOOLEAN DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE SET NULL
                )
            """)
            
            # ========== STORIES TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    media_data TEXT NOT NULL,
                    media_name TEXT,
                    media_type TEXT DEFAULT 'image',
                    video_data TEXT,
                    caption TEXT DEFAULT '',
                    stickers TEXT DEFAULT '[]',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    is_highlighted BOOLEAN DEFAULT 0,
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
            
            # ========== MESSAGES TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    from_id INTEGER NOT NULL,
                    to_id INTEGER NOT NULL,
                    text TEXT DEFAULT '',
                    media_data TEXT,
                    media_name TEXT,
                    media_type TEXT,
                    video_data TEXT,
                    audio_data TEXT,
                    sticker_data TEXT,
                    gif_data TEXT,
                    reply_to TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    is_delivered BOOLEAN DEFAULT 1,
                    is_deleted BOOLEAN DEFAULT 0,
                    is_edited BOOLEAN DEFAULT 0,
                    edited_at TIMESTAMP,
                    is_encrypted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== GROUPS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups_chat (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    owner_id INTEGER NOT NULL,
                    description TEXT DEFAULT '',
                    icon_path TEXT,
                    cover_path TEXT,
                    is_channel BOOLEAN DEFAULT 0,
                    is_public BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    member_count INTEGER DEFAULT 0,
                    is_verified BOOLEAN DEFAULT 0,
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notifications_enabled BOOLEAN DEFAULT 1,
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
                    media_type TEXT,
                    video_data TEXT,
                    audio_data TEXT,
                    sticker_data TEXT,
                    gif_data TEXT,
                    reply_to TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES groups_chat(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== HASHTAGS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hashtags (
                    tag TEXT PRIMARY KEY,
                    post_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_trending BOOLEAN DEFAULT 0,
                    category TEXT DEFAULT 'general'
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_hashtags (
                    post_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (post_id, tag),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag) REFERENCES hashtags(tag) ON DELETE CASCADE
                )
            """)
            
            # ========== NOTIFICATIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    from_user_id INTEGER,
                    link TEXT DEFAULT '',
                    metadata TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT 0,
                    is_clicked BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # ========== SAVED POSTS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS saved_posts (
                    user_id INTEGER NOT NULL,
                    post_id TEXT NOT NULL,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    collection_name TEXT DEFAULT 'default',
                    PRIMARY KEY (user_id, post_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            # ========== COLLECTIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    is_public BOOLEAN DEFAULT 0,
                    post_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== MARKETPLACE TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marketplace (
                    id TEXT PRIMARY KEY,
                    seller_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    category TEXT DEFAULT 'other',
                    condition TEXT DEFAULT 'new',
                    media_data TEXT,
                    media_name TEXT,
                    video_data TEXT,
                    location TEXT DEFAULT '',
                    latitude REAL,
                    longitude REAL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    is_sold BOOLEAN DEFAULT 0,
                    buyer_id INTEGER,
                    sold_at TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (buyer_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # ========== ANALYTICS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    user_id INTEGER,
                    target_type TEXT,
                    target_id TEXT,
                    data TEXT DEFAULT '{}',
                    ip_address TEXT,
                    user_agent TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # ========== REPORTS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    reporter_id INTEGER NOT NULL,
                    content_type TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER,
                    resolution_notes TEXT,
                    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # Create indexes
            self._create_indexes(cursor)
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _create_indexes(self, cursor):
        """Create all performance indexes"""
        indexes = [
            # Users
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(account_status)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
            
            # Sessions
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)",
            
            # Posts
            "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_visibility ON posts(visibility)",
            "CREATE INDEX IF NOT EXISTS idx_posts_deleted ON posts(is_deleted)",
            
            # Comments
            "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_timestamp ON comments(timestamp)",
            
            # Messages
            "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_from ON messages(from_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_to ON messages(to_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_messages_read ON messages(is_read)",
            
            # Notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp)",
            
            # Stories
            "CREATE INDEX IF NOT EXISTS idx_stories_user ON stories(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at)",
            
            # Hashtags
            "CREATE INDEX IF NOT EXISTS idx_hashtags_trending ON hashtags(is_trending)",
            "CREATE INDEX IF NOT EXISTS idx_hashtags_count ON hashtags(post_count)",
            
            # Marketplace
            "CREATE INDEX IF NOT EXISTS idx_marketplace_seller ON marketplace(seller_id)",
            "CREATE INDEX IF NOT EXISTS idx_marketplace_status ON marketplace(status)",
            "CREATE INDEX IF NOT EXISTS idx_marketplace_category ON marketplace(category)",
            "CREATE INDEX IF NOT EXISTS idx_marketplace_price ON marketplace(price)",
            
            # Analytics
            "CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp)",
            
            # Groups
            "CREATE INDEX IF NOT EXISTS idx_groups_owner ON groups_chat(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_messages_group ON group_messages(group_id)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

# ========== POST MANAGER ==========
class PostManager:
    """Manage posts and interactions"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_post(self, user_id: int, text: str = "", media_file=None, 
                   video_file=None, audio_file=None, location: str = "",
                   price: float = 0.0, is_for_sale: bool = False) -> Tuple[bool, str]:
        """Create a new post"""
        try:
            post_id = Utils.generate_id()
            media_data = None
            media_name = None
            media_type = "image"
            video_data = None
            audio_data = None
            
            # Process image
            if media_file:
                if Utils.validate_image(media_file.getvalue()):
                    optimized = Utils.optimize_image(media_file.getvalue())
                    media_data = base64.b64encode(optimized).decode()
                    media_name = media_file.name
                    media_type = "image"
            
            # Process video
            if video_file:
                if Utils.validate_video(video_file.getvalue()):
                    video_data = base64.b64encode(video_file.getvalue()).decode()
                    media_type = "video"
            
            # Process audio
            if audio_file:
                if Utils.validate_audio(audio_file.getvalue()):
                    audio_data = base64.b64encode(audio_file.getvalue()).decode()
                    media_type = "audio"
            
            # Extract hashtags and mentions
            hashtags = json.dumps(Utils.extract_hashtags(text))
            mentions = json.dumps(Utils.extract_mentions(text))
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO posts (id, user_id, text, media_data, media_name, media_type,
                                     video_data, audio_data, location, price, is_for_sale,
                                     hashtags, mentions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (post_id, user_id, text, media_data, media_name, media_type,
                      video_data, audio_data, location, price, is_for_sale,
                      hashtags, mentions))
                
                # Update user post count
                cursor.execute("""
                    UPDATE users SET total_posts = total_posts + 1 WHERE id = ?
                """, (user_id,))
                
                # Update hashtags
                for tag in json.loads(hashtags):
                    cursor.execute("""
                        INSERT INTO hashtags (tag, post_count, last_used)
                        VALUES (?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(tag) DO UPDATE SET
                        post_count = post_count + 1,
                        last_used = CURRENT_TIMESTAMP
                    """, (tag,))
                    
                    cursor.execute("""
                        INSERT INTO post_hashtags (post_id, tag) VALUES (?, ?)
                    """, (post_id, tag))
                
                conn.commit()
                return True, post_id
                
        except Exception as e:
            logger.error(f"Post creation error: {e}")
            return False, str(e)
    
    def get_feed_posts(self, user_id: int, page: int = 1, limit: int = 20) -> List[Dict]:
        """Get feed posts for user"""
        try:
            offset = (page - 1) * limit
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, u.username, u.is_verified, u.is_premium,
                           pr.display_name, pr.avatar_path, pr.gender,
                           (SELECT COUNT(*) FROM reactions WHERE post_id = p.id) as like_count,
                           (SELECT COUNT(*) FROM comments WHERE post_id = p.id AND is_deleted = 0) as comment_count,
                           (SELECT COUNT(*) FROM saved_posts WHERE post_id = p.id) as save_count
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
    
    def get_post(self, post_id: str) -> Optional[Dict]:
        """Get single post by ID"""
        try:
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
                    WHERE p.id = ? AND p.is_deleted = 0
                """, (post_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Get post error: {e}")
            return None
    
    def like_post(self, post_id: str, user_id: int) -> Tuple[bool, str]:
        """Like or unlike a post"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if already liked
                cursor.execute("""
                    SELECT reaction_type FROM reactions WHERE post_id = ? AND user_id = ?
                """, (post_id, user_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Unlike
                    cursor.execute("""
                        DELETE FROM reactions WHERE post_id = ? AND user_id = ?
                    """, (post_id, user_id))
                    conn.commit()
                    return True, "unliked"
                else:
                    # Like
                    cursor.execute("""
                        INSERT INTO reactions (post_id, user_id, reaction_type)
                        VALUES (?, ?, 'like')
                    """, (post_id, user_id))
                    
                    # Get post owner
                    cursor.execute("SELECT user_id FROM posts WHERE id = ?", (post_id,))
                    post_owner = cursor.fetchone()
                    
                    if post_owner and post_owner['user_id'] != user_id:
                        # Create notification
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
    
    def add_comment(self, post_id: str, user_id: int, text: str, 
                   parent_id: str = None) -> Tuple[bool, str]:
        """Add a comment to a post"""
        try:
            comment_id = Utils.generate_id()
            text = SecurityUtils.sanitize_input(text, Config.MAX_COMMENT_LENGTH)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO comments (id, post_id, user_id, parent_id, text)
                    VALUES (?, ?, ?, ?, ?)
                """, (comment_id, post_id, user_id, parent_id, text))
                
                # Get post owner
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
        """Get comments for a post"""
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
    """Manage private messages and group chats"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_or_create_chat(self, user1_id: int, user2_id: int) -> str:
        """Get or create a chat between two users"""
        try:
            chat_id = f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if chat exists
                cursor.execute("""
                    SELECT 1 FROM messages WHERE chat_id = ? LIMIT 1
                """, (chat_id,))
                
                if not cursor.fetchone():
                    # Create welcome message
                    cursor.execute("""
                        INSERT INTO messages (id, chat_id, from_id, to_id, text)
                        VALUES (?, ?, ?, ?, 'Chat started')
                    """, (Utils.generate_id(), chat_id, user1_id, user2_id))
                    conn.commit()
                
                return chat_id
        except Exception as e:
            logger.error(f"Chat creation error: {e}")
            return None
    
    def send_message(self, from_id: int, to_id: int, text: str, 
                    media_file=None, sticker=None, gif=None) -> Tuple[bool, str]:
        """Send a message"""
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
        """Get all conversations for a user"""
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
                        (SELECT text FROM messages 
                         WHERE chat_id = m.chat_id 
                         ORDER BY timestamp DESC LIMIT 1) as last_message,
                        (SELECT timestamp FROM messages 
                         WHERE chat_id = m.chat_id 
                         ORDER BY timestamp DESC LIMIT 1) as last_message_time,
                        (SELECT COUNT(*) FROM messages 
                         WHERE chat_id = m.chat_id AND to_id = ? AND is_read = 0) as unread_count
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
        """Get messages between two users"""
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
                
                # Mark messages as read
                cursor.execute("""
                    UPDATE messages 
                    SET is_read = 1 
                    WHERE chat_id = ? AND to_id = ? AND is_read = 0
                """, (chat_id, user1_id))
                
                conn.commit()
                return messages
        except Exception as e:
            logger.error(f"Get messages error: {e}")
            return []

# ========== USER MANAGER ==========
class UserManager:
    """Enhanced user management"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = {}
        self.cache_lock = threading.Lock()
    
    def create_user(self, username: str, password: str, email: str = "", 
                   phone: str = "") -> Tuple[bool, str]:
        """Create user with enhanced security"""
        username = SecurityUtils.sanitize_input(username.strip().lower(), Config.MAX_USERNAME_LENGTH)
        
        # Validate username
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        if username in ['admin', 'moderator', 'system', 'socialite', 'root', 'owner', 'support']:
            return False, "This username is reserved"
        
        # Validate password
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain both uppercase and lowercase letters"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain both uppercase and lowercase letters"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Validate email
        if email:
            email = email.strip().lower()
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return False, "Invalid email format"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check existing user
                cursor.execute("SELECT id FROM users WHERE username = ? OR (email != '' AND email = ?)", 
                             (username, email))
                if cursor.fetchone():
                    return False, "Username or email already exists"
                
                # Generate security credentials
                password_hash, salt = SecurityUtils.hash_password(password)
                encryption_key = secrets.token_hex(Config.ENCRYPTION_KEY_LENGTH)
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (username, email, phone, password_hash, salt, encryption_key)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, phone, password_hash, salt, encryption_key))
                
                user_id = cursor.lastrowid
                
                # Create profile
                cursor.execute("""
                    INSERT INTO profiles (user_id, display_name)
                    VALUES (?, ?)
                """, (user_id, username))
                
                # Create default collections
                for collection_name in ['Saved Posts', 'Favorites', 'Watch Later']:
                    collection_id = Utils.generate_id()
                    cursor.execute("""
                        INSERT INTO collections (id, user_id, name)
                        VALUES (?, ?, ?)
                    """, (collection_id, user_id, collection_name))
                
                conn.commit()
                
                logger.info(f"User created successfully: {username}")
                return True, "Account created successfully! Welcome to Socialite!"
                
        except Exception as e:
            logger.error(f"User creation error: {e}", exc_info=True)
            return False, "An error occurred during account creation"
    
    def authenticate(self, username: str, password: str, 
                    ip_address: str = "", user_agent: str = "") -> Tuple[bool, Union[str, Dict]]:
        """Enhanced authentication with session management"""
        username = username.strip()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users 
                    WHERE (username = ? OR LOWER(username) = LOWER(?)) AND is_deleted = 0
                """, (username, username))
                
                user = cursor.fetchone()
                if not user:
                    # Use constant time to prevent timing attacks
                    SecurityUtils.hash_password("dummy_password")
                    return False, "Invalid username or password"
                
                user_dict = dict(user)
                
                # Check account status
                if user_dict['is_deleted']:
                    return False, "Account has been deleted"
                if user_dict['is_banned']:
                    return False, "Account has been banned for violating terms of service"
                if user_dict['account_status'] == 'suspended':
                    return False, "Account is currently suspended"
                
                # Check lockout
                if user_dict['locked_until']:
                    try:
                        lock_time = datetime.fromisoformat(user_dict['locked_until'])
                        if datetime.now() < lock_time:
                            remaining = (lock_time - datetime.now()).seconds // 60
                            return False, f"Account is locked. Try again in {remaining} minutes"
                        else:
                            cursor.execute("""
                                UPDATE users SET locked_until = NULL, login_attempts = 0 
                                WHERE id = ?
                            """, (user_dict['id'],))
                    except:
                        pass
                
                # Verify password
                if SecurityUtils.verify_password(password, user_dict['password_hash'], 
                                                user_dict['salt']):
                    # Check existing sessions
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM sessions 
                        WHERE user_id = ? AND is_active = 1 AND expires_at > CURRENT_TIMESTAMP
                    """, (user_dict['id'],))
                    
                    active_sessions = cursor.fetchone()['count']
                    if active_sessions >= Config.MAX_SESSIONS_PER_USER:
                        # Deactivate oldest session
                        cursor.execute("""
                            UPDATE sessions SET is_active = 0 
                            WHERE user_id = ? AND is_active = 1 
                            AND id = (
                                SELECT id FROM sessions 
                                WHERE user_id = ? AND is_active = 1 
                                ORDER BY created_at ASC LIMIT 1
                            )
                        """, (user_dict['id'], user_dict['id']))
                    
                    # Create new session
                    session_id = Utils.generate_id()
                    session_token = SecurityUtils.generate_session_token()
                    csrf_token = SecurityUtils.generate_csrf_token()
                    expires_at = datetime.now() + timedelta(hours=Config.SESSION_TIMEOUT_HOURS)
                    
                    cursor.execute("""
                        INSERT INTO sessions (id, user_id, token, csrf_token, ip_address, 
                                            user_agent, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (session_id, user_dict['id'], session_token, csrf_token, 
                          ip_address, user_agent, expires_at.isoformat()))
                    
                    # Update user
                    cursor.execute("""
                        UPDATE users 
                        SET last_login = CURRENT_TIMESTAMP, 
                            last_active = CURRENT_TIMESTAMP,
                            login_attempts = 0 
                        WHERE id = ?
                    """, (user_dict['id'],))
                    
                    # Log analytics
                    cursor.execute("""
                        INSERT INTO analytics (event_type, user_id, ip_address, user_agent, session_id)
                        VALUES ('user_login', ?, ?, ?, ?)
                    """, (user_dict['id'], ip_address, user_agent, session_id))
                    
                    conn.commit()
                    
                    logger.info(f"User authenticated successfully: {user_dict['username']}")
                    
                    return True, {
                        'username': user_dict['username'],
                        'user_id': user_dict['id'],
                        'session_token': session_token,
                        'csrf_token': csrf_token,
                        'is_premium': user_dict['is_premium'],
                        'is_verified': user_dict['is_verified']
                    }
                else:
                    # Failed login
                    attempts = user_dict['login_attempts'] + 1
                    if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        lock_until = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
                        cursor.execute("""
                            UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?
                        """, (attempts, lock_until.isoformat(), user_dict['id']))
                    else:
                        cursor.execute("""
                            UPDATE users SET login_attempts = ? WHERE id = ?
                        """, (attempts, user_dict['id']))
                    
                    # Log failed attempt
                    cursor.execute("""
                        INSERT INTO analytics (event_type, user_id, ip_address, user_agent)
                        VALUES ('login_failed', ?, ?, ?)
                    """, (user_dict['id'], ip_address, user_agent))
                    
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
        """Get user with caching"""
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
        """Get user by ID"""
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
        """Update user profile"""
        try:
            valid_fields = [
                'display_name', 'bio', 'avatar_path', 'cover_path',
                'website', 'location', 'birthday', 'gender',
                'is_private', 'theme', 'wallpaper', 'language',
                'timezone', 'show_online_status', 'allow_messages_from'
            ]
            
            filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
            if not filtered_updates:
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
                values = list(filtered_updates.values()) + [user_id]
                
                cursor.execute(f"""
                    UPDATE profiles 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                    WHERE user_id = ?
                """, values)
                
                conn.commit()
                
                # Clear cache
                with self.cache_lock:
                    user = self.get_user_by_id(user_id)
                    if user:
                        self.cache.pop(f"user_{user['username']}", None)
                
                return True
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return False
    
    def update_last_active(self, user_id: int):
        """Update last active timestamp"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?
                """, (user_id,))
                conn.commit()
        except:
            pass
    
    def get_online_users(self) -> List[str]:
        """Get online users"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now() - timedelta(seconds=Config.ONLINE_THRESHOLD_SECONDS)
                cursor.execute("""
                    SELECT username FROM users 
                    WHERE last_active >= ? AND is_banned = 0 AND is_deleted = 0
                    AND account_status = 'active'
                    ORDER BY username
                """, (cutoff.isoformat(),))
                return [row['username'] for row in cursor.fetchall()]
        except:
            return []
    
    def search_users(self, query: str, limit: int = 50, 
                    exclude_user_id: int = None) -> List[Dict]:
        """Search users"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                params = [f"%{query}%", f"%{query}%", f"%{query}%"]
                
                sql = """
                    SELECT DISTINCT u.username, u.is_verified, u.is_premium, u.id,
                           p.display_name, p.bio, p.avatar_path, p.gender,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id AND is_accepted = 1) as follower_count,
                           (SELECT COUNT(*) FROM posts WHERE user_id = u.id AND is_deleted = 0) as post_count
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.is_banned = 0 AND u.is_deleted = 0 AND u.account_status = 'active'
                    AND (u.username LIKE ? OR p.display_name LIKE ? OR p.bio LIKE ?)
                """
                
                if exclude_user_id:
                    sql += " AND u.id != ?"
                    params.append(exclude_user_id)
                
                sql += " ORDER BY follower_count DESC, u.reputation_score DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                return [dict(row) for row in cursor.fetchall()]
        except:
            return []
    
    def follow_user(self, follower_id: int, following_username: str) -> Tuple[bool, str]:
        """Follow/unfollow user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get target user
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
                
                # Check if blocked
                cursor.execute("""
                    SELECT 1 FROM blocks 
                    WHERE blocker_id = ? AND blocked_id = ?
                """, (following_id, follower_id))
                if cursor.fetchone():
                    return False, "You are blocked by this user"
                
                # Check existing follow
                cursor.execute("""
                    SELECT is_accepted FROM follows 
                    WHERE follower_id = ? AND following_id = ?
                """, (follower_id, following_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Unfollow
                    cursor.execute("""
                        DELETE FROM follows 
                        WHERE follower_id = ? AND following_id = ?
                    """, (follower_id, following_id))
                    conn.commit()
                    return True, f"Unfollowed @{following_username}"
                else:
                    # Follow
                    is_accepted = not target['is_private']
                    cursor.execute("""
                        INSERT INTO follows (follower_id, following_id, is_accepted)
                        VALUES (?, ?, ?)
                    """, (follower_id, following_id, 1 if is_accepted else 0))
                    
                    if is_accepted:
                        self._create_notification(cursor, following_id, 'follow',
                                                f"started following you", follower_id)
                    
                    conn.commit()
                    
                    if is_accepted:
                        return True, f"Now following @{following_username}"
                    else:
                        return True, "Follow request sent"
                        
        except Exception as e:
            logger.error(f"Follow error: {e}")
            return False, "An error occurred"
    
    def get_notifications(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get user notifications"""
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
        """Mark all notifications as read"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0
                """, (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Mark read error: {e}")
    
    def _create_notification(self, cursor, user_id: int, ntype: str, 
                            message: str, from_user_id: int = None, 
                            link: str = "", metadata: Dict = None):
        """Create notification"""
        try:
            notification_id = Utils.generate_id()
            cursor.execute("""
                INSERT INTO notifications (id, user_id, type, message, from_user_id, link, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (notification_id, user_id, ntype, message, from_user_id, link, 
                  json.dumps(metadata or {})))
            
            # Clean old notifications
            cursor.execute("""
                DELETE FROM notifications 
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM notifications 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                )
            """, (user_id, user_id, Config.MAX_NOTIFICATIONS))
        except Exception as e:
            logger.error(f"Notification creation error: {e}")

# ========== STREAMLIT UI ==========
class SocialiteUI:
    """Enhanced Streamlit UI with all features"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self._init_session()
    
    def _init_session(self):
        """Initialize session state"""
        defaults = {
            'auth': False,
            'user_id': None,
            'username': None,
            'session_token': None,
            'csrf_token': None,
            'current_tab': 'feed',
            'active_chat': None,
            'active_group': None,
            'show_create_modal': False,
            'show_emoji_picker': False,
            'show_gif_picker': False,
            'show_sticker_picker': False,
            'feed_page': 1,
            'show_comments_for': None
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def render(self):
        """Main render method"""
        if not st.session_state.auth:
            self.render_auth()
            return
        
        # Update last active
        if st.session_state.user_id:
            self.user_manager.update_last_active(st.session_state.user_id)
        
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
    
    def render_top_nav(self):
        """Render top navigation with logo"""
        current_tab = st.session_state.current_tab
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        unread = len(self.user_manager.get_notifications(user['user_id'], 1))
        badge = f'<span class="badge">{unread}</span>' if unread > 0 else ''
        
        st.markdown(f"""
        <div class="top-nav">
            <div class="nav-brand">
                <img src="{Config.LOGO_URL}" class="nav-logo" alt="Socialite">
                <span class="nav-brand-text">Socialite</span>
            </div>
            <div class="nav-tabs">
                <button class="nav-tab {'active' if current_tab == 'feed' else ''}" 
                        onclick="document.getElementById('nav_btn_feed').click()">🏠</button>
                <button class="nav-tab {'active' if current_tab == 'explore' else ''}" 
                        onclick="document.getElementById('nav_btn_explore').click()">🔍</button>
                <button class="nav-tab {'active' if current_tab == 'chats' else ''}" 
                        onclick="document.getElementById('nav_btn_chats').click()">💬</button>
                <button class="nav-tab {'active' if current_tab == 'marketplace' else ''}" 
                        onclick="document.getElementById('nav_btn_marketplace').click()">🛒</button>
                <button class="nav-tab {'active' if current_tab == 'profile' else ''}" 
                        onclick="document.getElementById('nav_btn_profile').click()">👤</button>
            </div>
            <div class="nav-actions">
                <button class="nav-icon-btn" onclick="document.getElementById('nav_btn_notifications').click()">
                    🔔{badge}
                </button>
                {self.render_avatar_html(user, 28)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hidden navigation buttons
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            if st.button("🏠", key="nav_btn_feed"):
                st.session_state.current_tab = 'feed'
                st.rerun()
        with col2:
            if st.button("🔍", key="nav_btn_explore"):
                st.session_state.current_tab = 'explore'
                st.rerun()
        with col3:
            if st.button("💬", key="nav_btn_chats"):
                st.session_state.current_tab = 'chats'
                st.rerun()
        with col4:
            if st.button("🛒", key="nav_btn_marketplace"):
                st.session_state.current_tab = 'marketplace'
                st.rerun()
        with col5:
            if st.button("👤", key="nav_btn_profile"):
                st.session_state.current_tab = 'profile'
                st.rerun()
        with col6:
            if st.button("🔔", key="nav_btn_notifications"):
                st.session_state.current_tab = 'notifications'
                st.rerun()
    
    def inject_styles(self):
        """Inject comprehensive styles"""
        theme = self._get_current_theme()
        wallpaper = self._get_current_wallpaper()
        
        if wallpaper == "gradient" or wallpaper == "🌈 Gradient":
            bg = theme['gradient']
        else:
            bg = f"url('{wallpaper}') center/cover no-repeat fixed"
        
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;700;900&display=swap');
        
        * {{ 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            -webkit-font-smoothing: antialiased !important;
            -moz-osx-font-smoothing: grayscale !important;
        }}
        
        /* Hide Streamlit default elements */
        #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"], 
        [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
        
        /* App container */
        .stApp {{
            background: {bg} !important;
            height: 100vh !important;
            width: 100vw !important;
            overflow: hidden !important;
            position: relative !important;
        }}
        
        .main {{ height: 100vh !important; overflow: hidden !important; }}
        .block-container {{ 
            height: 100vh !important; 
            overflow: hidden !important; 
            padding: 0 !important; 
            margin: 0 !important; 
            max-width: 100% !important; 
        }}
        
        /* TOP NAVIGATION */
        .top-nav {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            height: 56px !important;
            background: {theme['bg']}fa !important;
            backdrop-filter: blur(30px) saturate(180%) !important;
            -webkit-backdrop-filter: blur(30px) saturate(180%) !important;
            border-bottom: 2px solid rgba(255, 215, 0, 0.2) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            padding: 0 16px !important;
            z-index: 10000 !important;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3) !important;
        }}
        
        .nav-brand {{
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
        }}
        
        .nav-logo {{
            width: 36px !important;
            height: 36px !important;
            border-radius: 50% !important;
            object-fit: cover !important;
            border: 2px solid #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.4) !important;
            animation: logoGlow 2s ease-in-out infinite !important;
        }}
        
        @keyframes logoGlow {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(255, 215, 0, 0.4); }}
            50% {{ box-shadow: 0 0 40px rgba(255, 215, 0, 0.8); }}
        }}
        
        .nav-brand-text {{
            font-weight: 800 !important;
            font-size: 1.1rem !important;
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            letter-spacing: 1px !important;
        }}
        
        .nav-tabs {{
            display: flex !important;
            align-items: center !important;
            gap: 2px !important;
            background: rgba(255, 255, 255, 0.03) !important;
            border-radius: 12px !important;
            padding: 3px !important;
        }}
        
        .nav-tab {{
            background: transparent !important;
            border: none !important;
            color: {theme['secondary']} !important;
            cursor: pointer !important;
            padding: 8px 14px !important;
            border-radius: 10px !important;
            font-size: 1.2rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            position: relative !important;
        }}
        
        .nav-tab:hover {{
            background: rgba(255, 215, 0, 0.1) !important;
            color: #FFD700 !important;
            transform: scale(1.1) !important;
        }}
        
        .nav-tab.active {{
            background: rgba(255, 215, 0, 0.2) !important;
            color: #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
        }}
        
        .nav-actions {{
            display: flex !important;
            align-items: center !important;
            gap: 12px !important;
        }}
        
        .nav-icon-btn {{
            background: transparent !important;
            border: none !important;
            cursor: pointer !important;
            font-size: 1.2rem !important;
            position: relative !important;
            color: {theme['secondary']} !important;
            transition: all 0.2s !important;
        }}
        
        .nav-icon-btn:hover {{
            color: #FFD700 !important;
            transform: scale(1.1) !important;
        }}
        
        .badge {{
            position: absolute !important;
            top: -8px !important;
            right: -8px !important;
            background: #FFD700 !important;
            color: #1a0033 !important;
            border-radius: 50% !important;
            padding: 2px 6px !important;
            font-size: 0.6rem !important;
            font-weight: 700 !important;
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
        }}
        
        /* MAIN CONTENT */
        .main-content {{
            position: fixed !important;
            top: 56px !important;
            bottom: 0 !important;
            left: 0 !important;
            right: 0 !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
            padding: 12px 16px !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        
        .content-wrapper {{
            max-width: 680px !important;
            margin: 0 auto !important;
            padding-bottom: 20px !important;
        }}
        
        /* CARDS */
        .card {{
            background: {theme['card']} !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 16px !important;
            margin-bottom: 12px !important;
            overflow: hidden !important;
            transition: all 0.3s !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .card:hover {{
            border-color: rgba(255, 215, 0, 0.2) !important;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        .card-header {{
            display: flex !important;
            align-items: center !important;
            padding: 12px 16px !important;
            gap: 12px !important;
        }}
        
        .username-text {{
            color: {theme['text']} !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
        }}
        
        .timestamp {{
            color: {theme['secondary']} !important;
            font-size: 0.7rem !important;
        }}
        
        .post-text {{
            color: #e2e8f0 !important;
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
            padding: 0 16px 12px 16px !important;
            word-wrap: break-word !important;
            white-space: pre-wrap !important;
        }}
        
        /* INPUT FIELDS */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid rgba(255, 215, 0, 0.4) !important;
            color: #ffffff !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            font-size: 0.95rem !important;
            caret-color: #FFD700 !important;
            transition: all 0.3s !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3), 
                       0 0 40px rgba(255, 215, 0, 0.1) !important;
            background: rgba(255, 255, 255, 0.15) !important;
        }}
        
        .stTextInput > div > div > input::placeholder,
        .stTextArea > div > div > textarea::placeholder {{
            color: #64748b !important;
            font-size: 0.9rem !important;
        }}
        
        /* BUTTONS */
        .stButton > button {{
            background: rgba(255, 215, 0, 0.1) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            color: {theme['text']} !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            min-height: auto !important;
        }}
        
        .stButton > button:hover {{
            background: rgba(255, 215, 0, 0.2) !important;
            border-color: #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
            transform: translateY(-2px) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(0) !important;
        }}
        
        /* FORM SUBMIT BUTTON */
        div[data-testid="stFormSubmitButton"] > button {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%) !important;
            color: #1a0033 !important;
            font-weight: 700 !important;
            border: none !important;
            padding: 12px 24px !important;
            border-radius: 12px !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
        }}
        
        div[data-testid="stFormSubmitButton"] > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(255, 215, 0, 0.5) !important;
        }}
        
        /* SELECT BOXES */
        .stSelectbox > div > div {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid rgba(255, 215, 0, 0.3) !important;
            border-radius: 12px !important;
            color: #ffffff !important;
        }}
        
        /* SCROLLBAR */
        ::-webkit-scrollbar {{
            width: 6px !important;
            height: 6px !important;
        }}
        
        ::-webkit-scrollbar-track {{
            background: transparent !important;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255, 215, 0, 0.3) !important;
            border-radius: 3px !important;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255, 215, 0, 0.6) !important;
        }}
        
        /* RESPONSIVE */
        @media (max-width: 480px) {{
            .top-nav {{
                height: 48px !important;
                padding: 0 10px !important;
            }}
            
            .main-content {{
                top: 48px !important;
                padding: 8px 10px !important;
            }}
            
            .nav-tab {{
                padding: 6px 10px !important;
                font-size: 1rem !important;
            }}
            
            .nav-logo {{
                width: 28px !important;
                height: 28px !important;
            }}
            
            .nav-brand-text {{
                font-size: 0.9rem !important;
            }}
        }}
        
        /* MODAL */
        .modal-overlay {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            background: rgba(0, 0, 0, 0.9) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            z-index: 10001 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            animation: fadeIn 0.3s ease !important;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
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
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5) !important;
            animation: slideUp 0.3s ease !important;
        }}
        
        @keyframes slideUp {{
            from {{ transform: translateY(30px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_auth(self):
        """Enhanced authentication page with logo"""
        st.markdown("""
        <style>
        .stApp { 
            background: linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%) !important; 
            overflow: auto !important; 
        }
        .main { height: auto !important; overflow: visible !important; }
        .block-container { height: auto !important; overflow: visible !important; padding: 2rem 1rem !important; }
        </style>
        """, unsafe_allow_html=True)
        
        _, col, _ = st.columns([1, 2, 1])
        
        with col:
            # Logo and branding
            st.markdown(f"""
            <div style="text-align:center;padding:2rem 0;">
                <img src="{Config.LOGO_URL}" 
                     style="width:120px;height:120px;border-radius:50%;object-fit:cover;
                            border:3px solid #FFD700;box-shadow:0 0 40px rgba(255,215,0,0.5);
                            animation: logoFloat 3s ease-in-out infinite;" 
                     alt="Socialite Logo">
                <h1 style="font-family:'Playfair Display',serif;font-size:2.8rem;font-weight:900;
                         background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         margin-top:1rem;letter-spacing:2px;">SOCIALITE</h1>
                <p style="color:#94a3b8;font-size:1.1rem;font-family:'Playfair Display',serif;">
                    {Config.APP_SLOGAN}
                </p>
            </div>
            
            <style>
            @keyframes logoFloat {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Auth tabs
            tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
            
            with tab1:
                with st.form("login_form"):
                    username = st.text_input(
                        "Username",
                        placeholder="Enter your username",
                        key="login_username"
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="login_password"
                    )
                    
                    if st.form_submit_button("🔓 Sign In", use_container_width=True):
                        if username and password:
                            success, result = self.user_manager.authenticate(
                                username, password
                            )
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
                    new_username = st.text_input(
                        "Choose Username",
                        placeholder=f"3-{Config.MAX_USERNAME_LENGTH} characters",
                        key="reg_username"
                    )
                    email = st.text_input(
                        "Email (optional)",
                        placeholder="your@email.com",
                        key="reg_email"
                    )
                    new_password = st.text_input(
                        "Choose Password",
                        type="password",
                        placeholder=f"Min {Config.MIN_PASSWORD_LENGTH} chars, include uppercase, number & symbol",
                        key="reg_password"
                    )
                    confirm = st.text_input(
                        "Confirm Password",
                        type="password",
                        placeholder="Re-enter password",
                        key="reg_confirm"
                    )
                    
                    if st.form_submit_button("✨ Create Account", use_container_width=True):
                        if not new_username or not new_password:
                            st.error("Username and password are required")
                        elif new_password != confirm:
                            st.error("Passwords don't match")
                        else:
                            success, message = self.user_manager.create_user(
                                new_username, new_password, email
                            )
                            if success:
                                st.success(message)
                                st.info("Please sign in with your new account!")
                                st.balloons()
                            else:
                                st.error(message)
    
    def render_feed(self):
        """Render feed page with all post features"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Quick post creator
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button("✨ What's on your mind? Create a post...", 
                        use_container_width=True, key="quick_post"):
                st.session_state.show_create_modal = True
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Load posts
        posts = self.post_manager.get_feed_posts(
            st.session_state.user_id, 
            page=st.session_state.feed_page
        )
        
        if not posts:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">
                <div style="font-size:5rem;animation:logoFloat 3s ease-in-out infinite;">👑</div>
                <h3 style="color:#FFD700;margin-top:1rem;">Welcome to Socialite!</h3>
                <p style="font-size:1rem;">Follow interesting people and create your first post!</p>
                <p style="font-size:0.8rem;">Share photos, videos, create polls, and more!</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for post in posts:
                self.render_post_card(post)
            
            # Pagination
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Load More", use_container_width=True):
                    st.session_state.feed_page += 1
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_post_card(self, post: Dict):
        """Render enhanced post card with all features"""
        with st.container():
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            
            # Header with user info
            st.markdown(f"""
            <div class="card-header">
                {self.render_avatar_html(post, 40)}
                <div style="flex:1;">
                    <div class="username-text">
                        @{html.escape(post['username'])}
                        {'<span style="color:#FFD700;"> ✓</span>' if post.get('is_verified') else ''}
                        {'<span style="color:#FFD700;"> 👑</span>' if post.get('is_premium') else ''}
                    </div>
                    <div class="timestamp">
                        {Utils.format_timestamp(post['timestamp'])}
                        {' · 📍 ' + html.escape(post['location']) if post.get('location') else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Post text with hashtags and mentions highlighted
            if post.get('text'):
                text = html.escape(post['text'])
                # Highlight hashtags
                text = re.sub(r'#(\w+)', r'<span style="color:#FFD700;">#\1</span>', text)
                # Highlight mentions
                text = re.sub(r'@(\w+)', r'<span style="color:#64ffda;">@\1</span>', text)
                st.markdown(f'<div class="post-text">{text}</div>', unsafe_allow_html=True)
            
            # Media - Image
            if post.get('media_data') and post.get('media_type') == 'image':
                try:
                    image_bytes = base64.b64decode(post['media_data'])
                    st.image(image_bytes, use_column_width=True)
                except:
                    pass
            
            # Media - Video
            if post.get('video_data'):
                try:
                    video_bytes = base64.b64decode(post['video_data'])
                    st.video(video_bytes)
                except:
                    pass
            
            # Media - Audio
            if post.get('audio_data'):
                try:
                    audio_bytes = base64.b64decode(post['audio_data'])
                    st.audio(audio_bytes)
                except:
                    pass
            
            # Stats row
            like_count = post.get('like_count', 0)
            comment_count = post.get('comment_count', 0)
            
            st.markdown(f"""
            <div style="padding:8px 16px;color:#94a3b8;font-size:0.8rem;border-top:1px solid rgba(255,215,0,0.1);">
                ❤️ {Utils.format_number(like_count)} likes · 💬 {Utils.format_number(comment_count)} comments
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("❤️", key=f"like_{post['id']}", 
                           help="Like", use_container_width=True):
                    success, result = self.post_manager.like_post(post['id'], st.session_state.user_id)
                    if success:
                        st.toast(f"Post {result}!")
                        st.rerun()
            
            with col2:
                if st.button("💬", key=f"comment_{post['id']}", 
                           help="Comment", use_container_width=True):
                    st.session_state.show_comments_for = post['id']
                    st.rerun()
            
            with col3:
                if st.button("🔖", key=f"save_{post['id']}", 
                           help="Save", use_container_width=True):
                    st.toast("Saved! 🔖")
            
            with col4:
                if post['username'] == st.session_state.username:
                    if st.button("🗑️", key=f"delete_{post['id']}", 
                               help="Delete", use_container_width=True):
                        st.toast("Post deleted")
                else:
                    if st.button("🚩", key=f"report_{post['id']}", 
                               help="Report", use_container_width=True):
                        st.toast("Reported")
            
            # Comments section
            if st.session_state.get('show_comments_for') == post['id']:
                self.render_comments_section(post['id'])
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_comments_section(self, post_id: str):
        """Render comments for a post"""
        st.markdown("""
        <div style="padding:12px 16px;border-top:1px solid rgba(255,215,0,0.1);
                 background:rgba(255,255,255,0.02);">
        """, unsafe_allow_html=True)
        
        # Add comment form
        with st.form(f"comment_form_{post_id}", clear_on_submit=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                comment_text = st.text_input(
                    "Write a comment...",
                    key=f"comment_input_{post_id}",
                    label_visibility="collapsed",
                    placeholder="Write a comment..."
                )
            with col2:
                submit_btn = st.form_submit_button("Post", use_container_width=True)
            
            if submit_btn and comment_text.strip():
                success, result = self.post_manager.add_comment(
                    post_id, st.session_state.user_id, comment_text
                )
                if success:
                    st.toast("Comment posted!")
                    st.rerun()
                else:
                    st.error("Failed to post comment")
        
        # Show existing comments
        comments = self.post_manager.get_comments(post_id)
        
        if comments:
            for comment in comments:
                st.markdown(f"""
                <div style="display:flex;gap:8px;margin-top:8px;padding:8px;">
                    {self.render_avatar_html(comment, 28)}
                    <div style="flex:1;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                            <span style="color:#FFD700;font-weight:600;font-size:0.8rem;">
                                @{html.escape(comment['username'])}
                            </span>
                            <span style="color:#64748b;font-size:0.7rem;">
                                {Utils.format_timestamp(comment['timestamp'])}
                            </span>
                        </div>
                        <p style="color:#e2e8f0;font-size:0.85rem;margin:0;">
                            {html.escape(comment['text'])}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="margin-top:8px;color:#94a3b8;font-size:0.8rem;text-align:center;padding:16px;">
                No comments yet. Be the first to comment!
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_create_modal(self):
        """Enhanced create post modal with all media types"""
        st.markdown("""
        <div class="modal-overlay">
        <div class="modal-box">
        <h3 style="color:#FFD700;text-align:center;margin-bottom:20px;">✨ Create Post</h3>
        """, unsafe_allow_html=True)
        
        with st.form("create_post_form", clear_on_submit=True):
            text = st.text_area(
                "What's on your mind?",
                max_chars=Config.MAX_POST_LENGTH,
                height=120,
                placeholder="Share your thoughts... Use #hashtags and @mentions!"
            )
            
            # Media upload options
            image_file = st.file_uploader(
                "📷 Image",
                type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                key="post_image"
            )
            video_file = st.file_uploader(
                "🎥 Video",
                type=['mp4', 'webm', 'mov'],
                key="post_video"
            )
            audio_file = st.file_uploader(
                "🎵 Audio",
                type=['mp3', 'wav', 'ogg'],
                key="post_audio"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                location = st.text_input(
                    "📍 Location",
                    placeholder="Add location"
                )
            with col2:
                price = st.number_input(
                    "💰 Price ($)",
                    min_value=0.0,
                    step=0.01,
                    help="Set price to list in marketplace"
                )
            
            is_for_sale = st.checkbox("List in Marketplace")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("📤 Post", use_container_width=True):
                    if text or image_file or video_file or audio_file:
                        success, result = self.post_manager.create_post(
                            st.session_state.user_id,
                            text=text,
                            media_file=image_file if image_file else None,
                            video_file=video_file if video_file else None,
                            audio_file=audio_file if audio_file else None,
                            location=location,
                            price=price,
                            is_for_sale=is_for_sale
                        )
                        if success:
                            st.session_state.show_create_modal = False
                            st.toast("Post created successfully! ✨")
                            st.rerun()
                        else:
                            st.error(f"Failed to create post: {result}")
                    else:
                        st.error("Post cannot be empty")
            with col2:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state.show_create_modal = False
                    st.rerun()
        
        if st.button("✕ Close", use_container_width=True, key="close_modal"):
            st.session_state.show_create_modal = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_explore(self):
        """Render explore page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">🔍 Explore</h3>', unsafe_allow_html=True)
        
        query = st.text_input(
            "Search users, hashtags, or topics...",
            placeholder="Search...",
            label_visibility="collapsed"
        )
        
        if query:
            users = self.user_manager.search_users(query, exclude_user_id=st.session_state.user_id)
            if users:
                for user in users:
                    col1, col2, col3 = st.columns([4, 2, 2])
                    with col1:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;">
                            {self.render_avatar_html(user, 44)}
                            <div>
                                <div style="color:#f1f5f9;font-weight:600;">
                                    @{html.escape(user['username'])}
                                    {'<span style="color:#FFD700;"> ✓</span>' if user.get('is_verified') else ''}
                                </div>
                                <div style="color:#94a3b8;font-size:0.75rem;">
                                    {Utils.format_number(user.get('follower_count', 0))} followers
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("Follow", key=f"explore_follow_{user['username']}", 
                                   use_container_width=True):
                            success, msg = self.user_manager.follow_user(
                                st.session_state.user_id, user['username']
                            )
                            st.toast(msg)
                            time.sleep(0.5)
                            st.rerun()
                    with col3:
                        if st.button("💬", key=f"explore_chat_{user['username']}", 
                                   use_container_width=True):
                            st.session_state.active_chat = user['username']
                            st.session_state.current_tab = 'chats'
                            st.rerun()
            else:
                st.info("No users found")
        else:
            # Show suggested users
            st.info("Search for users to connect with!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chats(self):
        """Render chats page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">💬 Messages</h3>', unsafe_allow_html=True)
        
        if st.session_state.active_chat:
            # Show chat view
            other_user = self.user_manager.get_user_by_username(st.session_state.active_chat)
            if other_user:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
                    {self.render_avatar_html(other_user, 40)}
                    <h4 style="color:#FFD700;margin:0;">@{other_user['username']}</h4>
                    <button onclick="document.getElementById('back_to_chats').click()" 
                            style="margin-left:auto;">← Back</button>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("← Back", key="back_to_chats"):
                    st.session_state.active_chat = None
                    st.rerun()
                
                # Get messages
                messages = self.chat_manager.get_messages(
                    st.session_state.user_id,
                    other_user['user_id']
                )
                
                # Display messages
                for msg in messages:
                    is_me = msg['from_id'] == st.session_state.user_id
                    align = "flex-end" if is_me else "flex-start"
                    bg = "rgba(255,215,0,0.2)" if is_me else "rgba(255,255,255,0.05)"
                    st.markdown(f"""
                    <div style="display:flex;justify-content:{align};margin-bottom:8px;">
                        <div style="max-width:70%;background:{bg};border-radius:12px;padding:8px 12px;">
                            <p style="margin:0;color:#e2e8f0;font-size:0.85rem;">{html.escape(msg['text'])}</p>
                            <p style="margin:4px 0 0 0;color:#64748b;font-size:0.7rem;text-align:right;">
                                {Utils.format_timestamp(msg['timestamp'])}
                            </p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Message input
                with st.form("send_message_form", clear_on_submit=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        msg_text = st.text_input(
                            "Type a message...",
                            key="msg_input",
                            label_visibility="collapsed"
                        )
                    with col2:
                        if st.form_submit_button("Send", use_container_width=True):
                            if msg_text.strip():
                                self.chat_manager.send_message(
                                    st.session_state.user_id,
                                    other_user['user_id'],
                                    msg_text
                                )
                                st.rerun()
        else:
            # Show conversation list
            conversations = self.chat_manager.get_conversations(st.session_state.user_id)
            
            if not conversations:
                st.info("No conversations yet. Start by following and messaging users!")
            else:
                for conv in conversations:
                    with st.container():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"""
                            <div style="display:flex;align-items:center;gap:10px;padding:8px;">
                                {self.render_avatar_html(conv, 40)}
                                <div>
                                    <div style="color:#f1f5f9;font-weight:600;">
                                        @{html.escape(conv['username'])}
                                        {'<span style="color:#FFD700;"> ✓</span>' if conv.get('is_verified') else ''}
                                    </div>
                                    <div style="color:#94a3b8;font-size:0.75rem;">
                                        {html.escape(conv.get('last_message', 'No messages')[:50])}
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col2:
                            if st.button("💬", key=f"chat_{conv['username']}", 
                                       use_container_width=True):
                                st.session_state.active_chat = conv['username']
                                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_marketplace(self):
        """Render marketplace page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;">🛒 Marketplace</h3>', unsafe_allow_html=True)
        
        # Get marketplace listings
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT m.*, u.username, u.is_verified, pr.avatar_path
                    FROM marketplace m
                    JOIN users u ON m.seller_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE m.status = 'active' AND m.is_sold = 0
                    ORDER BY m.created_at DESC
                    LIMIT 20
                """)
                listings = [dict(row) for row in cursor.fetchall()]
                
                if not listings:
                    st.info("No active listings found. Create a post with a price to list items!")
                else:
                    for listing in listings:
                        with st.container():
                            st.markdown(f"""
                            <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;margin-bottom:12px;">
                                <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                                    {self.render_avatar_html(listing, 36)}
                                    <div>
                                        <div style="color:#f1f5f9;font-weight:600;">@{listing['username']}</div>
                                        <div style="color:#94a3b8;font-size:0.7rem;">{Utils.format_timestamp(listing['created_at'])}</div>
                                    </div>
                                </div>
                                <h4 style="color:#FFD700;margin:8px 0;">{html.escape(listing['title'])}</h4>
                                <p style="color:#e2e8f0;font-size:0.85rem;">{html.escape(listing['description'][:200])}</p>
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;">
                                    <span style="background:rgba(255,215,0,0.2);color:#FFD700;padding:4px 12px;border-radius:20px;font-weight:700;">
                                        💰 ${listing['price']:.2f}
                                    </span>
                                    <button style="background:linear-gradient(135deg,#FFD700,#FFA500);color:#1a0033;border:none;padding:6px 12px;border-radius:8px;cursor:pointer;">
                                        Buy Now
                                    </button>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        except Exception as e:
            st.info("Marketplace feature coming soon! Create listings from posts.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_notifications(self):
        """Render notifications page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html.html)
        st.markdown('<h3 style="color:#FFD700;">🔔 Notifications</h3>', unsafe_allow_html=True)
        
        # Mark all as read
        self.user_manager.mark_notifications_read(st.session_state.user_id)
        
        # Get notifications
        notifications = self.user_manager.get_notifications(st.session_state.user_id)
        
        if not notifications:
            st.info("No notifications yet. Start interacting with others!")
        else:
            for notif in notifications:
                with st.container():
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;margin-bottom:8px;">
                        <div style="display:flex;align-items:center;gap:10px;">
                            {self.render_avatar_html(notif, 36) if notif.get('from_user_id') else '<div style="width:36px;"></div>'}
                            <div style="flex:1;">
                                <p style="color:#e2e8f0;margin:0;">{html.escape(notif['message'])}</p>
                                <p style="color:#64748b;font-size:0.7rem;margin:4px 0 0 0;">
                                    {Utils.format_timestamp(notif['timestamp'])}
                                </p>
                            </div>
                            {'<span style="color:#FFD700;">●</span>' if not notif['is_read'] else ''}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_profile(self):
        """Render enhanced profile page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            st.error("User not found")
            st.markdown('</div>', unsafe_allow_html=True)
            return
        
        # Profile header
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
            {self.render_avatar_html(user, 100)}
            <h2 style="color:#FFD700;margin-top:12px;">
                @{html.escape(user['username'])}
                {'<span style="color:#FFD700;"> ✓</span>' if user.get('is_verified') else ''}
                {'<span style="color:#FFD700;"> 👑</span>' if user.get('is_premium') else ''}
            </h2>
            <p style="color:#94a3b8;font-size:1rem;">
                {html.escape(user.get('display_name', user['username']))}
            </p>
            <p style="color:#94a3b8;font-size:0.9rem;">
                {html.escape(user.get('bio', 'No bio yet. Edit your profile to add one!'))}
            </p>
            {'<p style="color:#94a3b8;font-size:0.8rem;">🌐 ' + html.escape(user.get('website', '')) + '</p>' if user.get('website') else ''}
            {'<p style="color:#94a3b8;font-size:0.8rem;">📍 ' + html.escape(user.get('location', '')) + '</p>' if user.get('location') else ''}
        </div>
        """, unsafe_allow_html=True)
        
        # Stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Posts", user.get('total_posts', 0))
        with col2:
            follower_count = self._get_follower_count(user['user_id'])
            st.metric("Followers", follower_count)
        with col3:
            following_count = self._get_following_count(user['user_id'])
            st.metric("Following", following_count)
        
        # Edit Profile
        with st.expander("✏️ Edit Profile", expanded=False):
            with st.form("edit_profile_form"):
                display_name = st.text_input(
                    "Display Name",
                    value=user.get('display_name', '') or '',
                    max_chars=50
                )
                bio = st.text_area(
                    "Bio",
                    value=user.get('bio', '') or '',
                    max_chars=Config.MAX_BIO_LENGTH,
                    height=80
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    website = st.text_input(
                        "Website",
                        value=user.get('website', '') or '',
                        placeholder="https://..."
                    )
                with col2:
                    location = st.text_input(
                        "Location",
                        value=user.get('location', '') or '',
                        placeholder="City, Country"
                    )
                
                gender = st.selectbox(
                    "Gender",
                    ['prefer_not_to_say', 'male', 'female', 'non_binary'],
                    index=['prefer_not_to_say', 'male', 'female', 'non_binary'].index(user.get('gender', 'prefer_not_to_say'))
                )
                
                avatar = st.file_uploader(
                    "Profile Picture",
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    key="profile_avatar"
                )
                
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    updates = {
                        'display_name': SecurityUtils.sanitize_input(display_name, 50),
                        'bio': SecurityUtils.sanitize_input(bio, Config.MAX_BIO_LENGTH),
                        'website': SecurityUtils.sanitize_input(website, 200),
                        'location': SecurityUtils.sanitize_input(location, 100),
                        'gender': gender
                    }
                    
                    if avatar and avatar.size <= Config.MAX_AVATAR_SIZE:
                        try:
                            img_data = avatar.read()
                            if Utils.validate_image(img_data):
                                optimized = Utils.optimize_image(img_data, (400, 400))
                                path = Config.UPLOADS_DIR / f"avatar_{user['user_id']}.jpg"
                                with open(path, 'wb') as f:
                                    f.write(optimized)
                                updates['avatar_path'] = str(path)
                        except Exception as e:
                            st.error(f"Image error: {e}")
                    
                    if self.user_manager.update_profile(user['user_id'], updates):
                        st.success("Profile updated! ✨")
                        st.rerun()
        
        # Themes
        with st.expander("🎨 Themes", expanded=False):
            cols = st.columns(4)
            themes = {
                "midnight": "🌌 Midnight",
                "ocean": "🌊 Ocean",
                "sunset": "🌅 Sunset",
                "forest": "🌲 Forest",
                "royal": "👑 Royal",
                "crimson": "❤️ Crimson",
                "arctic": "❄️ Arctic",
                "neon": "💜 Neon"
            }
            for i, (tk, tn) in enumerate(themes.items()):
                with cols[i % 4]:
                    if st.button(tn, key=f"theme_{tk}", use_container_width=True):
                        self.user_manager.update_profile(user['user_id'], {'theme': tk})
                        st.rerun()
        
        # Sign Out
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_avatar_html(self, user_data: Dict, size: int = 36) -> str:
        """Generate avatar HTML with fallback"""
        if isinstance(user_data, dict):
            username = user_data.get('username', '')
            avatar_path = user_data.get('avatar_path')
            gender = user_data.get('gender', 'prefer_not_to_say')
            is_premium = user_data.get('is_premium', False)
        else:
            username = str(user_data)
            avatar_path = None
            gender = 'prefer_not_to_say'
            is_premium = False
        
        # If custom avatar exists
        if avatar_path and os.path.exists(avatar_path):
            try:
                with open(avatar_path, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                border = "3px solid #FFD700" if is_premium else "2px solid rgba(255,215,0,0.5)"
                glow = "box-shadow:0 0 15px rgba(255,215,0,0.5);" if is_premium else ""
                return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border};flex-shrink:0;{glow}" alt="{username}">'
            except:
                pass
        
        # Generate avatar placeholder
        color = Utils.get_avatar_color(username)
        initials = Utils.get_initials(username)
        
        # Gender-based emoji
        gender_emoji = {'male': '👨', 'female': '👩', 'non_binary': '🧑', 'prefer_not_to_say': '👤'}.get(gender, '👤')
        
        return f'''<div style="width:{size}px;height:{size}px;border-radius:50%;
                background:linear-gradient(135deg, {color}, {color}dd);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:700;font-size:{size*0.35}px;
                flex-shrink:0;border:2px solid rgba(255,215,0,0.5);
                position:relative;overflow:hidden;">
            <span style="position:absolute;font-size:{size*0.5}px;opacity:0.3;">{gender_emoji}</span>
            <span style="position:relative;z-index:1;">{initials}</span>
        </div>'''
    
    def _get_current_theme(self) -> Dict:
        """Get current user theme"""
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                theme_key = user.get('theme', 'midnight')
                themes = {
                    "midnight": {"name": "Midnight", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"},
                    "ocean": {"name": "Ocean", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)"},
                    "sunset": {"name": "Sunset", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)"},
                    "forest": {"name": "Forest", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50", "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)"},
                    "royal": {"name": "Royal", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)"},
                    "crimson": {"name": "Crimson", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336", "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)"},
                    "arctic": {"name": "Arctic", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)"},
                    "neon": {"name": "Neon", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)"},
                }
                return themes.get(theme_key, themes['midnight'])
        return {"name": "Midnight", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"}
    
    def _get_current_wallpaper(self) -> str:
        """Get current user wallpaper"""
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                wp_key = user.get('wallpaper', '🌈 Gradient')
                wallpapers = {
                    "🌈 Gradient": "gradient",
                    "✨ Purple": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=800&q=60",
                    "🌌 Galaxy": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=800&q=60",
                }
                return wallpapers.get(wp_key, "gradient")
        return "gradient"
    
    def _get_follower_count(self, user_id: int) -> int:
        """Get follower count"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count FROM follows 
                    WHERE following_id = ? AND is_accepted = 1
                """, (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0
    
    def _get_following_count(self, user_id: int) -> int:
        """Get following count"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count FROM follows 
                    WHERE follower_id = ? AND is_accepted = 1
                """, (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0

# ========== MAIN APPLICATION ENTRY POINT ==========
def main():
    """Main application entry point with error handling"""
    try:
        # Initialize database
        db = DatabaseManager()
        
        # Create backup on startup
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Config.BACKUP_DIR / f"socialite_backup_{timestamp}.db"
            if Config.DB_PATH.exists():
                shutil.copy2(Config.DB_PATH, backup_path)
            
            # Keep only last 10 backups
            backups = sorted(Config.BACKUP_DIR.glob("socialite_backup_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")
        
        # Initialize and render UI
        app = SocialiteUI()
        app.render()
        
    except Exception as e:
        logger.error(f"Critical application error: {e}", exc_info=True)
        st.error("""
        ## ⚠️ Application Error
        
        An unexpected error occurred. Please try the following:
        
        1. **Refresh the page** - This often resolves temporary issues
        2. **Clear your browser cache** - Old cached data can cause problems
        3. **Check your connection** - Ensure you have a stable internet connection
        4. **Contact support** - If the problem persists
        
        The development team has been notified of this error.
        """)

if __name__ == "__main__":
    main()
