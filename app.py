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
import hashlib
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
        'About': "Socialite - The Premium Social Experience v4.0"
    }
)

# ========== CONFIGURATION ==========
class Config:
    """Application configuration constants"""
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "4.0.0"
    APP_BUILD = "2024.1"
    
    # Directory paths
    DATA_DIR = pathlib.Path("data")
    DB_PATH = DATA_DIR / "socialite.db"
    UPLOADS_DIR = DATA_DIR / "uploads"
    BACKUP_DIR = DATA_DIR / "backups"
    CACHE_DIR = DATA_DIR / "cache"
    LOGS_DIR = DATA_DIR / "logs"
    TEMP_DIR = DATA_DIR / "temp"
    
    # Content limits
    MAX_POST_LENGTH = 5000
    MAX_COMMENT_LENGTH = 1000
    MAX_BIO_LENGTH = 500
    MAX_MESSAGE_LENGTH = 10000
    MAX_USERNAME_LENGTH = 30
    MIN_PASSWORD_LENGTH = 8
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_AVATAR_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_MEDIA_PER_POST = 10
    
    # Time limits
    STORY_EXPIRY_HOURS = 24
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    SESSION_TIMEOUT_HOURS = 24
    ONLINE_THRESHOLD_SECONDS = 300
    CACHE_TTL_SECONDS = 60
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Database limits
    MAX_FEED_ITEMS = 1000
    MAX_CHAT_MESSAGES = 5000
    MAX_NOTIFICATIONS = 200
    MAX_FOLLOWING = 5000
    MAX_BLOCKED = 1000
    MAX_SAVED_POSTS = 5000
    MAX_GROUPS = 50
    MAX_CHANNELS = 30

# Create all necessary directories
for dir_path in [Config.DATA_DIR, Config.UPLOADS_DIR, Config.BACKUP_DIR, 
                 Config.CACHE_DIR, Config.LOGS_DIR, Config.TEMP_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ========== LOGGING SETUP ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOGS_DIR / 'socialite.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== UTILITY FUNCTIONS ==========
class Utils:
    """Utility functions for the application"""
    
    @staticmethod
    def generate_id() -> str:
        """Generate a unique identifier using UUID4"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 12) -> str:
        """Generate a short unique identifier"""
        return str(uuid.uuid4())[:length]
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password using PBKDF2 with SHA-256 and 300,000 iterations"""
        if salt is None:
            salt = secrets.token_hex(32)
        h = hashlib.pbkdf2_hmac(
            'sha256', 
            password.encode('utf-8'), 
            salt.encode('utf-8'), 
            300000
        )
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        try:
            h, _ = Utils.hash_password(password, salt)
            return h == stored_hash
        except Exception:
            return False
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 5000) -> str:
        """Sanitize and truncate text input"""
        if not text:
            return ""
        # Remove control characters except newlines
        text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
        # Escape HTML
        text = html.escape(str(text).strip())
        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        return text
    
    @staticmethod
    def format_timestamp(ts) -> str:
        """Format timestamp to human-readable relative time"""
        if not ts:
            return ""
        try:
            if isinstance(ts, str):
                t = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                t = ts
            
            # Ensure t is timezone-naive for comparison
            if t.tzinfo is not None:
                from datetime import timezone
                t = t.replace(tzinfo=None)
            
            now = datetime.now()
            diff = (now - t).total_seconds()
            
            if diff < 5:
                return "just now"
            elif diff < 60:
                return f"{int(diff)}s"
            elif diff < 3600:
                return f"{int(diff//60)}m"
            elif diff < 86400:
                return f"{int(diff//3600)}h"
            elif diff < 604800:
                return f"{int(diff//86400)}d"
            elif diff < 2592000:
                return f"{int(diff//604800)}w"
            elif diff < 31536000:
                return f"{int(diff//2592000)}mo"
            else:
                return f"{int(diff//31536000)}y"
        except Exception as e:
            logger.error(f"Timestamp formatting error: {e}")
            return "unknown"
    
    @staticmethod
    def format_full_date(ts) -> str:
        """Format timestamp to full date string"""
        if not ts:
            return ""
        try:
            if isinstance(ts, str):
                t = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                t = ts
            return t.strftime("%B %d, %Y at %I:%M %p")
        except:
            return ""
    
    @staticmethod
    def format_number(num: int) -> str:
        """Format large numbers with K, M, B suffixes"""
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
    def validate_image(data: bytes) -> bool:
        """Validate that binary data is a valid image file"""
        try:
            img = Image.open(io.BytesIO(data))
            img.verify()
            return img.format.lower() in ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
        except:
            return False
    
    @staticmethod
    def validate_video(data: bytes) -> bool:
        """Validate that binary data is a valid video file"""
        try:
            header = data[:12]
            return any([
                header.startswith(b'\x00\x00\x00\x18ftypmp42'),
                header.startswith(b'\x00\x00\x00\x20ftypmp42'),
                header.startswith(b'RIFF'),
                header.startswith(b'\x1aE\xdf\xa3'),
            ])
        except:
            return False
    
    @staticmethod
    def optimize_image(data: bytes, max_size: Tuple[int, int] = (1200, 1200), 
                      quality: int = 85) -> bytes:
        """Optimize image for storage"""
        try:
            img = Image.open(io.BytesIO(data))
            
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
            
            # Resize if too large
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Save optimized
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Image optimization error: {e}")
            return data
    
    @staticmethod
    def get_avatar_color(username: str) -> str:
        """Get a consistent color for a user's avatar placeholder"""
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
        """Get initials from username for avatar placeholder"""
        if not username:
            return "?"
        parts = username.replace('_', ' ').replace('.', ' ').split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if len(username) >= 2 else username[0].upper()
    
    @staticmethod
    def slugify(text: str) -> str:
        """Convert text to URL-friendly slug"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_-]+', '-', text)
        text = re.sub(r'^-+|-+$', '', text)
        return text

# ========== CACHE SYSTEM ==========
class CacheSystem:
    """Advanced caching system with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000):
        self._cache = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache with LRU update"""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry > time.time():
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return value
                else:
                    del self._cache[key]
            self._misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = Config.CACHE_TTL_SECONDS):
        """Set item in cache with TTL"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                # Remove oldest (LRU)
                self._cache.popitem(last=False)
            
            self._cache[key] = (value, time.time() + ttl)
    
    def delete(self, key: str):
        """Delete item from cache"""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total = len(self._cache)
            expired = sum(1 for _, (_, exp) in self._cache.items() if exp <= time.time())
            return {
                'total_items': total,
                'expired_items': expired,
                'active_items': total - expired,
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{(self._hits / (self._hits + self._misses) * 100):.1f}%" if (self._hits + self._misses) > 0 else "0%"
            }

# ========== RATE LIMITER ==========
class RateLimiter:
    """Advanced rate limiter with sliding window algorithm"""
    
    def __init__(self):
        self._limits = defaultdict(lambda: defaultdict(list))
        self._lock = threading.Lock()
    
    def can_act(self, user_id: Any, action: str, limit: int = 5, 
                window: float = Config.RATE_LIMIT_WINDOW) -> bool:
        """Check if user can perform action within rate limit"""
        now = time.time()
        with self._lock:
            # Clean old entries
            self._limits[user_id][action] = [
                t for t in self._limits[user_id][action] 
                if now - t < window
            ]
            
            if len(self._limits[user_id][action]) >= limit:
                return False
            
            self._limits[user_id][action].append(now)
            return True
    
    def time_until_next(self, user_id: Any, action: str, 
                       window: float = Config.RATE_LIMIT_WINDOW) -> float:
        """Get seconds until next action is allowed"""
        with self._lock:
            if user_id not in self._limits or action not in self._limits[user_id]:
                return 0
            
            now = time.time()
            self._limits[user_id][action] = [
                t for t in self._limits[user_id][action]
                if now - t < window
            ]
            
            if self._limits[user_id][action]:
                return max(0, window - (now - min(self._limits[user_id][action])))
        return 0
    
    def reset(self, user_id: Any = None):
        """Reset rate limits for user or all users"""
        with self._lock:
            if user_id:
                self._limits.pop(user_id, None)
            else:
                self._limits.clear()
    
    def get_stats(self, user_id: Any = None) -> Dict:
        """Get rate limit statistics"""
        with self._lock:
            if user_id:
                return {
                    action: len(times) 
                    for action, times in self._limits.get(user_id, {}).items()
                }
            return {
                str(uid): {
                    action: len(times) 
                    for action, times in actions.items()
                }
                for uid, actions in self._limits.items()
            }

# ========== DATABASE MANAGER ==========
class DatabaseManager:
    """SQLite database manager with connection pooling and thread safety"""
    
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
        self._migrate_db()
        logger.info("Database manager initialized")
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(Config.DB_PATH), 
                check_same_thread=False,
                timeout=30,
                isolation_level=None  # Autocommit mode
            )
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA journal_mode=WAL")
            self._local.connection.execute("PRAGMA foreign_keys=ON")
            self._local.connection.execute("PRAGMA cache_size=-20000")
            self._local.connection.execute("PRAGMA synchronous=NORMAL")
            self._local.connection.execute("PRAGMA temp_store=MEMORY")
            self._local.connection.execute("PRAGMA mmap_size=268435456")
        
        try:
            yield self._local.connection
        except Exception as e:
            try:
                self._local.connection.rollback()
            except:
                pass
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            pass  # Keep connection open for reuse
    
    def _init_db(self):
        """Initialize database schema with all tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # ========== USERS TABLE ==========
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
                    total_shares INTEGER DEFAULT 0,
                    total_views INTEGER DEFAULT 0,
                    reputation_score REAL DEFAULT 0.0,
                    account_status TEXT DEFAULT 'active'
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
                    gender TEXT DEFAULT 'male',
                    is_private BOOLEAN DEFAULT 0,
                    theme TEXT DEFAULT 'midnight',
                    wallpaper TEXT DEFAULT 'wp_socialite',
                    language TEXT DEFAULT 'en',
                    custom_css TEXT DEFAULT '',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                    post_type TEXT DEFAULT 'post',
                    location TEXT DEFAULT '',
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
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            # ========== POLL OPTIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poll_options (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    option_text TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
                )
            """)
            
            # ========== POLL VOTES TABLE ==========
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
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_edited BOOLEAN DEFAULT 0,
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
                    caption TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    view_count INTEGER DEFAULT 0,
                    is_highlighted BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== STORY VIEWS TABLE ==========
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
            
            # ========== DIRECT MESSAGES TABLE ==========
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
                    is_edited BOOLEAN DEFAULT 0,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (to_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== GROUPS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
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
                    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== GROUP MEMBERS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notifications_enabled BOOLEAN DEFAULT 1,
                    PRIMARY KEY (group_id, user_id),
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== GROUP MESSAGES TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS group_messages (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    from_id INTEGER NOT NULL,
                    text TEXT DEFAULT '',
                    media_data TEXT,
                    media_name TEXT,
                    reply_to TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_pinned BOOLEAN DEFAULT 0,
                    FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                    FOREIGN KEY (from_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # ========== HASHTAGS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hashtags (
                    tag TEXT PRIMARY KEY,
                    post_count INTEGER DEFAULT 1,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_trending BOOLEAN DEFAULT 0
                )
            """)
            
            # ========== POST HASHTAGS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS post_hashtags (
                    post_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (post_id, tag),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag) REFERENCES hashtags(tag) ON DELETE CASCADE
                )
            """)
            
            # ========== MENTIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    post_id TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    PRIMARY KEY (post_id, user_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
                    FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # ========== SESSIONS TABLE ==========
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Create all indexes for performance
            self._create_indexes(cursor)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def _create_indexes(self, cursor):
        """Create all database indexes"""
        indexes = [
            # Users
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(account_status)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            
            # Posts
            "CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_visibility ON posts(visibility)",
            "CREATE INDEX IF NOT EXISTS idx_posts_deleted ON posts(is_deleted)",
            
            # Comments
            "CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)",
            
            # Messages
            "CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_from_id ON messages(from_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_to_id ON messages(to_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            
            # Notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_timestamp ON notifications(timestamp)",
            
            # Stories
            "CREATE INDEX IF NOT EXISTS idx_stories_user_id ON stories(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at)",
            
            # Follows
            "CREATE INDEX IF NOT EXISTS idx_follows_follower ON follows(follower_id)",
            "CREATE INDEX IF NOT EXISTS idx_follows_following ON follows(following_id)",
            
            # Blocks
            "CREATE INDEX IF NOT EXISTS idx_blocks_blocker ON blocks(blocker_id)",
            "CREATE INDEX IF NOT EXISTS idx_blocks_blocked ON blocks(blocked_id)",
            
            # Reactions
            "CREATE INDEX IF NOT EXISTS idx_reactions_post ON reactions(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_reactions_user ON reactions(user_id)",
            
            # Hashtags
            "CREATE INDEX IF NOT EXISTS idx_hashtags_trending ON hashtags(is_trending)",
            
            # Groups
            "CREATE INDEX IF NOT EXISTS idx_groups_owner ON groups(owner_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_group ON group_members(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id)",
            
            # Analytics
            "CREATE INDEX IF NOT EXISTS idx_analytics_event ON analytics(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_timestamp ON analytics(timestamp)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")
    
    def _migrate_db(self):
        """Handle database migrations"""
        # Add any future migrations here
        pass
    
    def close(self):
        """Close all connections"""
        if hasattr(self._local, 'connection') and self._local.connection:
            try:
                self._local.connection.close()
            except:
                pass
            finally:
                self._local.connection = None
    
    def backup(self) -> bool:
        """Create database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = Config.BACKUP_DIR / f"socialite_backup_{timestamp}.db"
            shutil.copy2(Config.DB_PATH, backup_path)
            
            # Clean old backups (keep last 10)
            backups = sorted(Config.BACKUP_DIR.glob("socialite_backup_*.db"))
            if len(backups) > 10:
                for old_backup in backups[:-10]:
                    old_backup.unlink()
            
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

# ========== USER MANAGER ==========
class UserManager:
    """Handle all user-related operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = CacheSystem(max_size=500)
    
    def create_user(self, username: str, password: str, email: str = "") -> Tuple[bool, str]:
        """Create a new user account"""
        username = username.strip().lower()
        email = email.strip().lower()
        
        # Validate username
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > Config.MAX_USERNAME_LENGTH:
            return False, f"Username must be {Config.MAX_USERNAME_LENGTH} characters or less"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        if username in ['admin', 'moderator', 'system', 'socialite', 'root', 'owner']:
            return False, "This username is reserved"
        
        # Validate password
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
        
        # Check password strength
        if not re.search(r'[A-Z]', password) and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        
        # Validate email
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Please enter a valid email address"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if username exists
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                if cursor.fetchone():
                    return False, "Username already exists"
                
                # Check if email exists
                if email:
                    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                    if cursor.fetchone():
                        return False, "Email already registered"
                
                # Hash password
                password_hash, salt = Utils.hash_password(password)
                
                # Create user
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt)
                    VALUES (?, ?, ?, ?)
                """, (username, email, password_hash, salt))
                
                user_id = cursor.lastrowid
                
                # Create profile
                cursor.execute("""
                    INSERT INTO profiles (user_id, display_name)
                    VALUES (?, ?)
                """, (user_id, username))
                
                # Log analytics
                self._log_event(cursor, 'user_registered', user_id)
                
                conn.commit()
                
                logger.info(f"User created: {username} (ID: {user_id})")
                return True, "Account created successfully!"
                
        except Exception as e:
            logger.error(f"Error creating user: {e}", exc_info=True)
            return False, "An error occurred. Please try again."
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Union[str, int]]:
        """Authenticate user and return username or error message"""
        username = username.strip()
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, password_hash, salt, login_attempts, 
                           locked_until, is_banned, is_deleted, account_status
                    FROM users 
                    WHERE username = ? OR LOWER(username) = LOWER(?)
                """, (username, username))
                
                user = cursor.fetchone()
                if not user:
                    return False, "User not found"
                
                user_id = user['id']
                actual_username = user['username']
                
                # Check account status
                if user['is_deleted']:
                    return False, "Account has been deleted"
                if user['is_banned']:
                    return False, "Account has been banned"
                if user['account_status'] == 'suspended':
                    return False, "Account has been suspended"
                
                # Check lockout
                if user['locked_until']:
                    try:
                        lock_time = datetime.fromisoformat(user['locked_until'])
                        if datetime.now() < lock_time:
                            remaining = (lock_time - datetime.now()).seconds // 60
                            return False, f"Account locked for {remaining} more minutes"
                        else:
                            # Reset lockout
                            cursor.execute("""
                                UPDATE users 
                                SET locked_until = NULL, login_attempts = 0 
                                WHERE id = ?
                            """, (user_id,))
                            conn.commit()
                    except:
                        pass
                
                # Verify password
                if Utils.verify_password(password, user['password_hash'], user['salt']):
                    # Successful login
                    cursor.execute("""
                        UPDATE users 
                        SET last_login = CURRENT_TIMESTAMP, login_attempts = 0 
                        WHERE id = ?
                    """, (user_id,))
                    
                    # Log analytics
                    self._log_event(cursor, 'user_logged_in', user_id)
                    
                    conn.commit()
                    
                    # Clear cache for this user
                    self.cache.delete(f"user_{actual_username}")
                    self.cache.delete(f"user_id_{user_id}")
                    
                    logger.info(f"User authenticated: {actual_username}")
                    return True, actual_username
                else:
                    # Failed login
                    attempts = user['login_attempts'] + 1
                    if attempts >= Config.MAX_LOGIN_ATTEMPTS:
                        lock_until = datetime.now() + timedelta(minutes=Config.LOGIN_LOCKOUT_MINUTES)
                        cursor.execute("""
                            UPDATE users 
                            SET login_attempts = ?, locked_until = ? 
                            WHERE id = ?
                        """, (attempts, lock_until.isoformat(), user_id))
                        
                        # Log security event
                        self._log_event(cursor, 'account_locked', user_id, 
                                      data=json.dumps({'attempts': attempts}))
                    else:
                        cursor.execute("""
                            UPDATE users 
                            SET login_attempts = ? 
                            WHERE id = ?
                        """, (attempts, user_id))
                    
                    conn.commit()
                    
                    # Log failed attempt
                    self._log_event(cursor, 'login_failed', user_id,
                                  data=json.dumps({'attempt': attempts}))
                    
                    remaining = Config.MAX_LOGIN_ATTEMPTS - attempts
                    return False, f"Incorrect password. {remaining} attempts remaining"
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            return False, "An error occurred. Please try again."
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user data by username with caching"""
        cache_key = f"user_{username}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.*
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.username = ? AND u.is_deleted = 0
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    self.cache.set(cache_key, user_data, ttl=300)  # 5 minutes
                    return user_data
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
        
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user data by ID with caching"""
        cache_key = f"user_id_{user_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.*
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.id = ? AND u.is_deleted = 0
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    user_data = dict(row)
                    self.cache.set(cache_key, user_data, ttl=300)
                    return user_data
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
        
        return None
    
    def update_profile(self, user_id: int, updates: Dict) -> bool:
        """Update user profile fields"""
        try:
            # Filter only valid profile fields
            valid_fields = [
                'display_name', 'bio', 'avatar_path', 'cover_path',
                'website', 'location', 'birthday', 'gender',
                'is_private', 'theme', 'wallpaper', 'language',
                'custom_css'
            ]
            
            filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
            if not filtered_updates:
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build update query
                set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
                values = list(filtered_updates.values()) + [user_id]
                
                cursor.execute(f"""
                    UPDATE profiles 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, values)
                
                conn.commit()
                
                # Clear cache
                user = self.get_user_by_id(user_id)
                if user:
                    self.cache.delete(f"user_{user['username']}")
                    self.cache.delete(f"user_id_{user_id}")
                
                # Log event
                self._log_event(cursor, 'profile_updated', user_id,
                              data=json.dumps(filtered_updates))
                
                return True
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False
    
    def update_last_seen(self, user_id: int):
        """Update user's last seen timestamp"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating last seen: {e}")
    
    def get_online_users(self) -> List[str]:
        """Get list of currently online users"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cutoff = datetime.now() - timedelta(seconds=Config.ONLINE_THRESHOLD_SECONDS)
                cursor.execute("""
                    SELECT username 
                    FROM users 
                    WHERE last_login >= ? 
                    AND is_banned = 0 
                    AND is_deleted = 0
                    AND account_status = 'active'
                    ORDER BY username
                """, (cutoff.isoformat(),))
                
                return [row['username'] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting online users: {e}")
            return []
    
    def search_users(self, query: str, limit: int = 50, 
                    exclude_user_id: int = None) -> List[Dict]:
        """Search users by username or display name"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                query_params = []
                sql = """
                    SELECT DISTINCT u.username, u.is_verified, u.is_premium, u.id,
                           p.display_name, p.bio, p.avatar_path, p.gender,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id AND is_accepted = 1) as follower_count
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.is_banned = 0 
                    AND u.is_deleted = 0
                    AND u.account_status = 'active'
                    AND (u.username LIKE ? OR p.display_name LIKE ?)
                """
                query_params.extend([f"%{query}%", f"%{query}%"])
                
                if exclude_user_id:
                    sql += " AND u.id != ?"
                    query_params.append(exclude_user_id)
                
                sql += " ORDER BY follower_count DESC LIMIT ?"
                query_params.append(limit)
                
                cursor.execute(sql, query_params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    def get_trending_users(self, limit: int = 10) -> List[Dict]:
        """Get trending users based on recent activity"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.username, u.is_verified, u.is_premium, u.id,
                           p.display_name, p.avatar_path, p.gender,
                           u.total_posts, u.total_likes_received,
                           (SELECT COUNT(*) FROM follows WHERE following_id = u.id) as follower_count
                    FROM users u
                    LEFT JOIN profiles p ON u.id = p.user_id
                    WHERE u.is_banned = 0 
                    AND u.is_deleted = 0
                    AND u.account_status = 'active'
                    ORDER BY u.reputation_score DESC
                    LIMIT ?
                """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting trending users: {e}")
            return []
    
    def follow_user(self, follower_id: int, following_username: str) -> Tuple[bool, str]:
        """Follow or unfollow a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get target user
                cursor.execute("""
                    SELECT id, username, is_private 
                    FROM users 
                    WHERE username = ? AND is_deleted = 0
                """, (following_username,))
                target = cursor.fetchone()
                
                if not target:
                    return False, "User not found"
                
                following_id = target['id']
                
                if follower_id == following_id:
                    return False, "Cannot follow yourself"
                
                # Check if blocked
                cursor.execute("""
                    SELECT 1 FROM blocks 
                    WHERE blocker_id = ? AND blocked_id = ?
                """, (following_id, follower_id))
                if cursor.fetchone():
                    return False, "You are blocked by this user"
                
                # Check if already following
                cursor.execute("""
                    SELECT is_accepted FROM follows 
                    WHERE follower_id = ? AND following_id = ?
                """, (follower_id, following_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    if existing['is_accepted']:
                        # Unfollow
                        cursor.execute("""
                            DELETE FROM follows 
                            WHERE follower_id = ? AND following_id = ?
                        """, (follower_id, following_id))
                        conn.commit()
                        
                        # Log event
                        self._log_event(cursor, 'user_unfollowed', follower_id,
                                      data=json.dumps({'target': following_username}))
                        
                        return True, f"Unfollowed @{following_username}"
                    else:
                        return False, "Follow request already sent"
                else:
                    # Follow or request
                    is_accepted = not target['is_private']
                    
                    cursor.execute("""
                        INSERT INTO follows (follower_id, following_id, is_accepted)
                        VALUES (?, ?, ?)
                    """, (follower_id, following_id, 1 if is_accepted else 0))
                    
                    if is_accepted:
                        # Create notification
                        self._create_notification(
                            cursor, following_id, 'follow',
                            f"started following you",
                            follower_id, f"/profile/{following_username}"
                        )
                        
                        conn.commit()
                        
                        # Log event
                        self._log_event(cursor, 'user_followed', follower_id,
                                      data=json.dumps({'target': following_username}))
                        
                        return True, f"Now following @{following_username}"
                    else:
                        # Create follow request notification
                        self._create_notification(
                            cursor, following_id, 'follow_request',
                            f"requested to follow you",
                            follower_id, f"/profile/{following_username}"
                        )
                        
                        conn.commit()
                        
                        # Log event
                        self._log_event(cursor, 'follow_requested', follower_id,
                                      data=json.dumps({'target': following_username}))
                        
                        return True, "Follow request sent"
                        
        except Exception as e:
            logger.error(f"Error in follow_user: {e}")
            return False, "An error occurred"
    
    def block_user(self, blocker_id: int, blocked_username: str) -> Tuple[bool, str]:
        """Block or unblock a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get target user
                cursor.execute("""
                    SELECT id FROM users 
                    WHERE username = ? AND is_deleted = 0
                """, (blocked_username,))
                target = cursor.fetchone()
                
                if not target:
                    return False, "User not found"
                
                blocked_id = target['id']
                
                if blocker_id == blocked_id:
                    return False, "Cannot block yourself"
                
                # Check if already blocked
                cursor.execute("""
                    SELECT 1 FROM blocks 
                    WHERE blocker_id = ? AND blocked_id = ?
                """, (blocker_id, blocked_id))
                
                if cursor.fetchone():
                    # Unblock
                    cursor.execute("""
                        DELETE FROM blocks 
                        WHERE blocker_id = ? AND blocked_id = ?
                    """, (blocker_id, blocked_id))
                    conn.commit()
                    
                    self._log_event(cursor, 'user_unblocked', blocker_id,
                                  data=json.dumps({'target': blocked_username}))
                    
                    return True, f"Unblocked @{blocked_username}"
                else:
                    # Block
                    cursor.execute("""
                        INSERT INTO blocks (blocker_id, blocked_id)
                        VALUES (?, ?)
                    """, (blocker_id, blocked_id))
                    
                    # Remove any follow relationship
                    cursor.execute("""
                        DELETE FROM follows 
                        WHERE (follower_id = ? AND following_id = ?)
                        OR (follower_id = ? AND following_id = ?)
                    """, (blocker_id, blocked_id, blocked_id, blocker_id))
                    
                    conn.commit()
                    
                    self._log_event(cursor, 'user_blocked', blocker_id,
                                  data=json.dumps({'target': blocked_username}))
                    
                    return True, f"Blocked @{blocked_username}"
                    
        except Exception as e:
            logger.error(f"Error in block_user: {e}")
            return False, "An error occurred"
    
    def is_following(self, follower_id: int, following_id: int) -> bool:
        """Check if user is following another user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 1 FROM follows 
                    WHERE follower_id = ? AND following_id = ? AND is_accepted = 1
                """, (follower_id, following_id))
                return cursor.fetchone() is not None
        except:
            return False
    
    def _create_notification(self, cursor, user_id: int, ntype: str, 
                            message: str, from_user_id: int = None, 
                            link: str = "", metadata: Dict = None):
        """Create a notification for a user"""
        try:
            notification_id = Utils.generate_id()
            cursor.execute("""
                INSERT INTO notifications (id, user_id, type, message, from_user_id, link, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                notification_id, user_id, ntype, message, 
                from_user_id, link, 
                json.dumps(metadata or {})
            ))
            
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
            logger.error(f"Error creating notification: {e}")
    
    def _log_event(self, cursor, event_type: str, user_id: int = None,
                  target_type: str = None, target_id: str = None,
                  data: str = '{}'):
        """Log an analytics event"""
        try:
            cursor.execute("""
                INSERT INTO analytics (event_type, user_id, target_type, target_id, data)
                VALUES (?, ?, ?, ?, ?)
            """, (event_type, user_id, target_type, target_id, data))
        except Exception as e:
            logger.error(f"Error logging event: {e}")

# ========== POST MANAGER ==========
class PostManager:
    """Handle all post-related operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = CacheSystem(max_size=300)
    
    def create_post(self, user_id: int, text: str = "", media_data: str = None,
                   media_name: str = None, media_type: str = "image",
                   post_type: str = "post", location: str = "",
                   visibility: str = "public", poll_data: Dict = None) -> Tuple[bool, str]:
        """Create a new post"""
        text = Utils.sanitize_text(text, Config.MAX_POST_LENGTH) if text else ""
        
        if not text and not media_data and not poll_data:
            return False, "Post cannot be empty"
        
        try:
            post_id = Utils.generate_id()
            hashtags = Utils.extract_hashtags(text)
            mentions = Utils.extract_mentions(text)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create post
                cursor.execute("""
                    INSERT INTO posts (id, user_id, text, media_data, media_name, 
                                      media_type, post_type, location, visibility)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (post_id, user_id, text, media_data, media_name,
                      media_type, post_type, location, visibility))
                
                # Handle hashtags
                for tag in hashtags:
                    tag_lower = tag.lower()
                    cursor.execute("""
                        INSERT INTO hashtags (tag, post_count, last_used)
                        VALUES (?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(tag) DO UPDATE SET 
                            post_count = post_count + 1,
                            last_used = CURRENT_TIMESTAMP
                    """, (tag_lower,))
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO post_hashtags (post_id, tag)
                        VALUES (?, ?)
                    """, (post_id, tag_lower))
                
                # Handle mentions
                for mentioned_username in mentions:
                    cursor.execute("""
                        SELECT id FROM users WHERE username = ? AND is_deleted = 0
                    """, (mentioned_username,))
                    mentioned_user = cursor.fetchone()
                    
                    if mentioned_user and mentioned_user['id'] != user_id:
                        cursor.execute("""
                            INSERT OR IGNORE INTO mentions (post_id, user_id)
                            VALUES (?, ?)
                        """, (post_id, mentioned_user['id']))
                        
                        # Create notification
                        self._create_notification(
                            cursor, mentioned_user['id'], 
                            'mention', 
                            f"mentioned you in a post",
                            user_id, f"/post/{post_id}"
                        )
                
                # Handle poll
                if poll_data and post_type == 'poll':
                    cursor.execute("""
                        INSERT INTO polls (post_id, question, ends_at, is_multiple_choice)
                        VALUES (?, ?, ?, ?)
                    """, (post_id, poll_data['question'],
                          poll_data.get('ends_at'),
                          poll_data.get('is_multiple_choice', False)))
                    
                    for option_text in poll_data.get('options', []):
                        cursor.execute("""
                            INSERT INTO poll_options (post_id, option_text)
                            VALUES (?, ?)
                        """, (post_id, option_text))
                
                # Update user post count
                cursor.execute("""
                    UPDATE users 
                    SET total_posts = total_posts + 1 
                    WHERE id = ?
                """, (user_id,))
                
                conn.commit()
                
                # Clear cache
                self.cache.delete(f"post_{post_id}")
                
                logger.info(f"Post created: {post_id} by user {user_id}")
                return True, post_id
                
        except Exception as e:
            logger.error(f"Error creating post: {e}", exc_info=True)
            return False, "Failed to create post"
    
    def get_post(self, post_id: str, user_id: int = None) -> Optional[Dict]:
        """Get a single post with all related data"""
        cache_key = f"post_{post_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.*, u.username, u.is_verified, u.is_premium,
                           pr.display_name, pr.avatar_path, pr.gender
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE p.id = ? AND p.is_deleted = 0
                """, (post_id,))
                
                post = cursor.fetchone()
                if post:
                    post_dict = dict(post)
                    
                    # Get poll data
                    if post_dict['post_type'] == 'poll':
                        cursor.execute("""
                            SELECT po.*, 
                                   (SELECT COUNT(*) FROM poll_votes WHERE option_id = po.id) as vote_count
                            FROM poll_options po
                            WHERE po.post_id = ?
                            ORDER BY po.sort_order, po.id
                        """, (post_id,))
                        post_dict['poll_options'] = [dict(row) for row in cursor.fetchall()]
                    
                    # Get reactions summary
                    cursor.execute("""
                        SELECT reaction_type, COUNT(*) as count
                        FROM reactions
                        WHERE post_id = ?
                        GROUP BY reaction_type
                    """, (post_id,))
                    post_dict['reactions'] = {row['reaction_type']: row['count'] 
                                             for row in cursor.fetchall()}
                    
                    # Get user's reaction if logged in
                    if user_id:
                        cursor.execute("""
                            SELECT reaction_type FROM reactions
                            WHERE post_id = ? AND user_id = ?
                        """, (post_id, user_id))
                        user_reaction = cursor.fetchone()
                        post_dict['user_reaction'] = user_reaction['reaction_type'] if user_reaction else None
                    
                    # Get comment count
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM comments
                        WHERE post_id = ? AND is_deleted = 0
                    """, (post_id,))
                    post_dict['comment_count'] = cursor.fetchone()['count']
                    
                    # Get share count
                    post_dict['share_count'] = post_dict.get('share_count', 0)
                    
                    # Cache the post
                    self.cache.set(cache_key, post_dict, ttl=120)
                    
                    return post_dict
        except Exception as e:
            logger.error(f"Error getting post: {e}")
        return None
    
    def get_feed(self, user_id: int, page: int = 1, per_page: int = 20,
                feed_type: str = 'home') -> Tuple[List[Dict], bool]:
        """Get personalized feed for user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                offset = (page - 1) * per_page
                
                if feed_type == 'home':
                    # Home feed: posts from followed users and own posts
                    cursor.execute("""
                        SELECT p.id
                        FROM posts p
                        WHERE p.is_deleted = 0
                        AND p.visibility = 'public'
                        AND (p.user_id = ? OR p.user_id IN (
                            SELECT following_id FROM follows 
                            WHERE follower_id = ? AND is_accepted = 1
                        ))
                        AND p.user_id NOT IN (
                            SELECT blocked_id FROM blocks WHERE blocker_id = ?
                        )
                        ORDER BY 
                            CASE WHEN p.is_pinned THEN 0 ELSE 1 END,
                            p.timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, user_id, user_id, per_page + 1, offset))
                
                elif feed_type == 'explore':
                    # Explore feed: popular posts from all users
                    cursor.execute("""
                        SELECT p.id
                        FROM posts p
                        WHERE p.is_deleted = 0
                        AND p.visibility = 'public'
                        AND p.user_id NOT IN (
                            SELECT blocked_id FROM blocks WHERE blocker_id = ?
                        )
                        ORDER BY p.view_count DESC, p.timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, per_page + 1, offset))
                
                elif feed_type == 'trending':
                    # Trending feed: posts with most recent engagement
                    cursor.execute("""
                        SELECT p.id
                        FROM posts p
                        LEFT JOIN (
                            SELECT post_id, COUNT(*) as reaction_count
                            FROM reactions
                            GROUP BY post_id
                        ) r ON p.id = r.post_id
                        WHERE p.is_deleted = 0
                        AND p.visibility = 'public'
                        AND p.timestamp >= datetime('now', '-24 hours')
                        AND p.user_id NOT IN (
                            SELECT blocked_id FROM blocks WHERE blocker_id = ?
                        )
                        ORDER BY COALESCE(r.reaction_count, 0) DESC, p.timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, per_page + 1, offset))
                
                else:
                    # Default to home feed
                    cursor.execute("""
                        SELECT p.id
                        FROM posts p
                        WHERE p.is_deleted = 0
                        AND p.visibility = 'public'
                        AND (p.user_id = ? OR p.user_id IN (
                            SELECT following_id FROM follows 
                            WHERE follower_id = ? AND is_accepted = 1
                        ))
                        ORDER BY p.timestamp DESC
                        LIMIT ? OFFSET ?
                    """, (user_id, user_id, per_page + 1, offset))
                
                post_ids = [row['id'] for row in cursor.fetchall()]
                
                has_more = len(post_ids) > per_page
                if has_more:
                    post_ids = post_ids[:per_page]
                
                # Get full post data
                posts = []
                for pid in post_ids:
                    post = self.get_post(pid, user_id)
                    if post:
                        posts.append(post)
                
                return posts, has_more
        except Exception as e:
            logger.error(f"Error getting feed: {e}")
            return [], False
    
    def add_reaction(self, post_id: str, user_id: int, reaction_type: str) -> Tuple[bool, str]:
        """Add or remove reaction to post"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if user already reacted
                cursor.execute("""
                    SELECT reaction_type FROM reactions 
                    WHERE post_id = ? AND user_id = ?
                """, (post_id, user_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    if existing['reaction_type'] == reaction_type:
                        # Remove same reaction
                        cursor.execute("""
                            DELETE FROM reactions 
                            WHERE post_id = ? AND user_id = ?
                        """, (post_id, user_id))
                        
                        conn.commit()
                        self.cache.delete(f"post_{post_id}")
                        return True, "Reaction removed"
                    else:
                        # Change reaction
                        cursor.execute("""
                            UPDATE reactions 
                            SET reaction_type = ?, created_at = CURRENT_TIMESTAMP
                            WHERE post_id = ? AND user_id = ?
                        """, (reaction_type, post_id, user_id))
                        
                        conn.commit()
                        self.cache.delete(f"post_{post_id}")
                        return True, "Reaction updated"
                else:
                    # Add new reaction
                    cursor.execute("""
                        INSERT INTO reactions (post_id, user_id, reaction_type)
                        VALUES (?, ?, ?)
                    """, (post_id, user_id, reaction_type))
                    
                    # Get post owner for notification
                    cursor.execute("""
                        SELECT user_id FROM posts WHERE id = ?
                    """, (post_id,))
                    post = cursor.fetchone()
                    
                    if post and post['user_id'] != user_id:
                        self._create_notification(
                            cursor, post['user_id'], 'reaction',
                            f"reacted to your post",
                            user_id, f"/post/{post_id}"
                        )
                    
                    # Update user's total likes received
                    cursor.execute("""
                        UPDATE users 
                        SET total_likes_received = total_likes_received + 1 
                        WHERE id = (SELECT user_id FROM posts WHERE id = ?)
                    """, (post_id,))
                    
                    conn.commit()
                    self.cache.delete(f"post_{post_id}")
                    return True, "Reaction added"
                
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return False, "Failed to update reaction"
    
    def get_comments(self, post_id: str, limit: int = 50, 
                   parent_id: str = None) -> List[Dict]:
        """Get comments for a post"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if parent_id:
                    cursor.execute("""
                        SELECT c.*, u.username, u.is_verified, u.is_premium,
                               pr.display_name, pr.avatar_path, pr.gender
                        FROM comments c
                        JOIN users u ON c.user_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE c.post_id = ? AND c.parent_id = ? AND c.is_deleted = 0
                        ORDER BY c.timestamp ASC
                        LIMIT ?
                    """, (post_id, parent_id, limit))
                else:
                    cursor.execute("""
                        SELECT c.*, u.username, u.is_verified, u.is_premium,
                               pr.display_name, pr.avatar_path, pr.gender
                        FROM comments c
                        JOIN users u ON c.user_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE c.post_id = ? AND c.parent_id IS NULL AND c.is_deleted = 0
                        ORDER BY c.timestamp DESC
                        LIMIT ?
                    """, (post_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting comments: {e}")
            return []
    
    def add_comment(self, post_id: str, user_id: int, text: str, 
                   parent_id: str = None) -> Tuple[bool, str]:
        """Add a comment to a post"""
        text = Utils.sanitize_text(text, Config.MAX_COMMENT_LENGTH)
        if not text:
            return False, "Comment cannot be empty"
        
        try:
            comment_id = Utils.generate_id()
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO comments (id, post_id, user_id, parent_id, text)
                    VALUES (?, ?, ?, ?, ?)
                """, (comment_id, post_id, user_id, parent_id, text))
                
                # Update user comment count
                cursor.execute("""
                    UPDATE users 
                    SET total_comments = total_comments + 1 
                    WHERE id = ?
                """, (user_id,))
                
                # Notify post owner
                cursor.execute("""
                    SELECT user_id FROM posts WHERE id = ?
                """, (post_id,))
                post = cursor.fetchone()
                
                if post and post['user_id'] != user_id:
                    self._create_notification(
                        cursor, post['user_id'], 'comment',
                        f"commented on your post",
                        user_id, f"/post/{post_id}"
                    )
                
                # Notify parent comment author if reply
                if parent_id:
                    cursor.execute("""
                        SELECT user_id FROM comments WHERE id = ?
                    """, (parent_id,))
                    parent_comment = cursor.fetchone()
                    
                    if parent_comment and parent_comment['user_id'] != user_id:
                        self._create_notification(
                            cursor, parent_comment['user_id'], 'comment_reply',
                            f"replied to your comment",
                            user_id, f"/post/{post_id}"
                        )
                
                conn.commit()
                
                # Clear post cache
                self.cache.delete(f"post_{post_id}")
                
                return True, comment_id
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return False, "Failed to add comment"
    
    def delete_post(self, post_id: str, user_id: int) -> Tuple[bool, str]:
        """Soft delete a post"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check ownership
                cursor.execute("""
                    SELECT user_id FROM posts WHERE id = ? AND is_deleted = 0
                """, (post_id,))
                post = cursor.fetchone()
                
                if not post:
                    return False, "Post not found"
                
                if post['user_id'] != user_id:
                    return False, "You can only delete your own posts"
                
                # Soft delete
                cursor.execute("""
                    UPDATE posts 
                    SET is_deleted = 1 
                    WHERE id = ?
                """, (post_id,))
                
                # Update user post count
                cursor.execute("""
                    UPDATE users 
                    SET total_posts = MAX(0, total_posts - 1) 
                    WHERE id = ?
                """, (user_id,))
                
                conn.commit()
                
                # Clear cache
                self.cache.delete(f"post_{post_id}")
                
                return True, "Post deleted"
        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            return False, "Failed to delete post"
    
    def vote_poll(self, post_id: str, user_id: int, option_id: int) -> Tuple[bool, str]:
        """Vote in a poll"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if poll exists and is active
                cursor.execute("""
                    SELECT p.id, po.id as option_id
                    FROM polls p
                    JOIN poll_options po ON p.post_id = po.post_id
                    WHERE p.post_id = ? AND po.id = ?
                """, (post_id, option_id))
                
                if not cursor.fetchone():
                    return False, "Invalid poll option"
                
                # Check if already voted
                cursor.execute("""
                    SELECT option_id FROM poll_votes
                    WHERE option_id IN (SELECT id FROM poll_options WHERE post_id = ?)
                    AND user_id = ?
                """, (post_id, user_id))
                
                existing_vote = cursor.fetchone()
                
                if existing_vote:
                    if existing_vote['option_id'] == option_id:
                        # Remove vote
                        cursor.execute("""
                            DELETE FROM poll_votes 
                            WHERE option_id = ? AND user_id = ?
                        """, (option_id, user_id))
                        
                        conn.commit()
                        self.cache.delete(f"post_{post_id}")
                        return True, "Vote removed"
                    else:
                        # Change vote
                        cursor.execute("""
                            DELETE FROM poll_votes 
                            WHERE option_id = ? AND user_id = ?
                        """, (existing_vote['option_id'], user_id))
                        
                        cursor.execute("""
                            INSERT INTO poll_votes (option_id, user_id)
                            VALUES (?, ?)
                        """, (option_id, user_id))
                        
                        conn.commit()
                        self.cache.delete(f"post_{post_id}")
                        return True, "Vote changed"
                else:
                    # New vote
                    cursor.execute("""
                        INSERT INTO poll_votes (option_id, user_id)
                        VALUES (?, ?)
                    """, (option_id, user_id))
                    
                    # Update total votes
                    cursor.execute("""
                        UPDATE polls 
                        SET total_votes = (
                            SELECT COUNT(DISTINCT user_id) 
                            FROM poll_votes pv
                            JOIN poll_options po ON pv.option_id = po.id
                            WHERE po.post_id = ?
                        )
                        WHERE post_id = ?
                    """, (post_id, post_id))
                    
                    conn.commit()
                    self.cache.delete(f"post_{post_id}")
                    return True, "Vote recorded"
                
        except Exception as e:
            logger.error(f"Error voting in poll: {e}")
            return False, "Failed to vote"
    
    def _create_notification(self, cursor, user_id: int, ntype: str, 
                            message: str, from_user_id: int = None, 
                            link: str = ""):
        """Create a notification"""
        try:
            notification_id = Utils.generate_id()
            cursor.execute("""
                INSERT INTO notifications (id, user_id, type, message, from_user_id, link)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notification_id, user_id, ntype, message, from_user_id, link))
        except Exception as e:
            logger.error(f"Error creating notification: {e}")

# ========== CHAT MANAGER ==========
class ChatManager:
    """Handle all messaging operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache = CacheSystem(max_size=300)
    
    def send_message(self, from_id: int, to_username: str, text: str = "",
                    media_data: str = None, media_name: str = None,
                    reply_to: str = None) -> Tuple[bool, str]:
        """Send a direct message"""
        text = Utils.sanitize_text(text, Config.MAX_MESSAGE_LENGTH) if text else ""
        
        if not text and not media_data:
            return False, "Message cannot be empty"
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get recipient
                cursor.execute("""
                    SELECT id, username FROM users 
                    WHERE username = ? AND is_deleted = 0
                """, (to_username,))
                to_user = cursor.fetchone()
                
                if not to_user:
                    return False, "User not found"
                
                to_id = to_user['id']
                
                # Check if blocked
                cursor.execute("""
                    SELECT 1 FROM blocks 
                    WHERE blocker_id = ? AND blocked_id = ?
                """, (to_id, from_id))
                
                if cursor.fetchone():
                    return False, "You are blocked by this user"
                
                # Generate chat ID
                chat_id = self._get_chat_id(from_id, to_id)
                message_id = Utils.generate_id()
                
                cursor.execute("""
                    INSERT INTO messages (id, chat_id, from_id, to_id, text, 
                                         media_data, media_name, reply_to)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (message_id, chat_id, from_id, to_id, text, 
                      media_data, media_name, reply_to))
                
                # Create notification
                notification_id = Utils.generate_id()
                cursor.execute("""
                    INSERT INTO notifications (id, user_id, type, message, 
                                              from_user_id, link)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (notification_id, to_id, 'message', 
                      "sent you a message", from_id, f"/chat/{from_id}"))
                
                conn.commit()
                
                # Clear cache
                self.cache.delete(f"messages_{chat_id}")
                
                return True, message_id
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False, "Failed to send message"
    
    def get_messages(self, user_id: int, with_user_id: int, 
                    limit: int = 50, before_id: str = None) -> List[Dict]:
        """Get messages between two users"""
        try:
            chat_id = self._get_chat_id(user_id, with_user_id)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Mark messages as read
                cursor.execute("""
                    UPDATE messages 
                    SET is_read = 1 
                    WHERE chat_id = ? AND to_id = ? AND is_read = 0
                """, (chat_id, user_id))
                
                # Get messages
                if before_id:
                    cursor.execute("""
                        SELECT m.*, u.username as from_username,
                               pr.avatar_path, pr.gender
                        FROM messages m
                        JOIN users u ON m.from_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE m.chat_id = ? AND m.id < ? AND m.is_deleted = 0
                        ORDER BY m.timestamp DESC
                        LIMIT ?
                    """, (chat_id, before_id, limit))
                else:
                    cursor.execute("""
                        SELECT m.*, u.username as from_username,
                               pr.avatar_path, pr.gender
                        FROM messages m
                        JOIN users u ON m.from_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE m.chat_id = ? AND m.is_deleted = 0
                        ORDER BY m.timestamp DESC
                        LIMIT ?
                    """, (chat_id, limit))
                
                messages = [dict(row) for row in cursor.fetchall()]
                messages.reverse()  # Oldest first
                
                conn.commit()
                return messages
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def get_chat_list(self, user_id: int) -> List[Dict]:
        """Get list of chats for user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        CASE WHEN m.from_id = ? THEN m.to_id ELSE m.from_id END as other_user_id,
                        u.username as other_username,
                        u.is_verified,
                        u.is_premium,
                        pr.display_name,
                        pr.avatar_path,
                        pr.gender,
                        MAX(m.timestamp) as last_message_time,
                        COUNT(CASE WHEN m.to_id = ? AND m.is_read = 0 THEN 1 END) as unread_count,
                        SUBSTRING_INDEX(
                            GROUP_CONCAT(m.text ORDER BY m.timestamp DESC), ',', 1
                        ) as last_message_text
                    FROM messages m
                    JOIN users u ON (
                        CASE WHEN m.from_id = ? THEN m.to_id = u.id 
                             ELSE m.from_id = u.id END
                    )
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE (m.from_id = ? OR m.to_id = ?) AND m.is_deleted = 0
                    GROUP BY other_user_id
                    ORDER BY last_message_time DESC
                """, (user_id, user_id, user_id, user_id, user_id))
                
                chats = []
                online_users = set(UserManager(self.db).get_online_users())
                
                for row in cursor.fetchall():
                    chat = dict(row)
                    chat['is_online'] = chat['other_username'] in online_users
                    chats.append(chat)
                
                return chats
        except Exception as e:
            logger.error(f"Error getting chat list: {e}")
            # Fallback query without SUBSTRING_INDEX
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            CASE WHEN m.from_id = ? THEN m.to_id ELSE m.from_id END as other_user_id,
                            u.username as other_username,
                            u.is_verified,
                            u.is_premium,
                            MAX(m.timestamp) as last_message_time,
                            COUNT(CASE WHEN m.to_id = ? AND m.is_read = 0 THEN 1 END) as unread_count
                        FROM messages m
                        JOIN users u ON (
                            CASE WHEN m.from_id = ? THEN m.to_id = u.id 
                                 ELSE m.from_id = u.id END
                        )
                        WHERE (m.from_id = ? OR m.to_id = ?) AND m.is_deleted = 0
                        GROUP BY other_user_id
                        ORDER BY last_message_time DESC
                    """, (user_id, user_id, user_id, user_id, user_id))
                    
                    chats = []
                    online_users = set(UserManager(self.db).get_online_users())
                    
                    for row in cursor.fetchall():
                        chat = dict(row)
                        chat['is_online'] = chat['other_username'] in online_users
                        chats.append(chat)
                    
                    return chats
            except:
                return []
    
    def _get_chat_id(self, user1_id: int, user2_id: int) -> str:
        """Generate consistent chat ID for two users"""
        ids = sorted([user1_id, user2_id])
        return f"chat_{ids[0]}_{ids[1]}"

# ========== STORY MANAGER ==========
class StoryManager:
    """Handle all story operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def create_story(self, user_id: int, media_data: str, media_name: str = "",
                    caption: str = "", media_type: str = "image") -> Tuple[bool, str]:
        """Create a new story"""
        try:
            story_id = Utils.generate_id()
            expires_at = datetime.now() + timedelta(hours=Config.STORY_EXPIRY_HOURS)
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check story count
                cursor.execute("""
                    SELECT COUNT(*) as count FROM stories
                    WHERE user_id = ? AND expires_at > CURRENT_TIMESTAMP
                """, (user_id,))
                
                if cursor.fetchone()['count'] >= 20:
                    return False, "Maximum 20 active stories reached"
                
                cursor.execute("""
                    INSERT INTO stories (id, user_id, media_data, media_name, 
                                        media_type, caption, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (story_id, user_id, media_data, media_name, 
                      media_type, caption, expires_at.isoformat()))
                
                conn.commit()
                
                return True, story_id
        except Exception as e:
            logger.error(f"Error creating story: {e}")
            return False, "Failed to create story"
    
    def get_active_stories(self) -> List[Dict]:
        """Get all active stories"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, u.username, u.is_verified, u.is_premium,
                           pr.avatar_path, pr.gender,
                           (SELECT COUNT(*) FROM story_views WHERE story_id = s.id) as view_count
                    FROM stories s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE s.expires_at > CURRENT_TIMESTAMP
                    ORDER BY s.timestamp DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting active stories: {e}")
            return []
    
    def get_user_stories(self, username: str) -> List[Dict]:
        """Get stories for a specific user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT s.*, u.username, u.is_verified,
                           pr.avatar_path, pr.gender
                    FROM stories s
                    JOIN users u ON s.user_id = u.id
                    LEFT JOIN profiles pr ON u.id = pr.user_id
                    WHERE u.username = ? AND s.expires_at > CURRENT_TIMESTAMP
                    ORDER BY s.timestamp ASC
                """, (username,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting user stories: {e}")
            return []
    
    def view_story(self, story_id: str, user_id: int):
        """Record a story view"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO story_views (story_id, user_id)
                    VALUES (?, ?)
                """, (story_id, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error viewing story: {e}")

# ========== NOTIFICATION MANAGER ==========
class NotificationManager:
    """Handle all notification operations"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def get_notifications(self, user_id: int, limit: int = 50, 
                         unread_only: bool = False) -> List[Dict]:
        """Get notifications for a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                if unread_only:
                    cursor.execute("""
                        SELECT n.*, u.username as from_username,
                               pr.avatar_path as from_avatar
                        FROM notifications n
                        LEFT JOIN users u ON n.from_user_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE n.user_id = ? AND n.is_read = 0
                        ORDER BY n.timestamp DESC
                        LIMIT ?
                    """, (user_id, limit))
                else:
                    cursor.execute("""
                        SELECT n.*, u.username as from_username,
                               pr.avatar_path as from_avatar
                        FROM notifications n
                        LEFT JOIN users u ON n.from_user_id = u.id
                        LEFT JOIN profiles pr ON u.id = pr.user_id
                        WHERE n.user_id = ?
                        ORDER BY n.timestamp DESC
                        LIMIT ?
                    """, (user_id, limit))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM notifications 
                    WHERE user_id = ? AND is_read = 0
                """, (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0
    
    def mark_all_read(self, user_id: int):
        """Mark all notifications as read"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE notifications 
                    SET is_read = 1 
                    WHERE user_id = ? AND is_read = 0
                """, (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error marking notifications read: {e}")
    
    def mark_read(self, notification_id: str, user_id: int):
        """Mark a single notification as read"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE notifications 
                    SET is_read = 1 
                    WHERE id = ? AND user_id = ?
                """, (notification_id, user_id))
                conn.commit()
        except Exception as e:
            logger.error(f"Error marking notification read: {e}")

# ========== BRAND EMOJI GENERATOR ==========
def generate_socialite_emoji(size: int = 200) -> str:
    """Generate the Socialite brand emoji as an SVG"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="{size}" height="{size}">
  <defs>
    <radialGradient id="globeGrad" cx="50%" cy="40%" r="50%">
      <stop offset="0%" style="stop-color:#4A90D9;stop-opacity:1"/>
      <stop offset="40%" style="stop-color:#2E6DB4;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#1A3A5C;stop-opacity:1"/>
    </radialGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1"/>
      <stop offset="25%" style="stop-color:#FFC107;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#FFD700;stop-opacity:1"/>
      <stop offset="75%" style="stop-color:#FFB300;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#FFD700;stop-opacity:1"/>
    </linearGradient>
    <linearGradient id="maleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2C3E50;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#34495E;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#1A252F;stop-opacity:1"/>
    </linearGradient>
    <linearGradient id="femaleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#C2185B;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#E91E63;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#880E4F;stop-opacity:1"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="strongGlow">
      <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <!-- Background Globe -->
  <circle cx="100" cy="100" r="85" fill="url(#globeGrad)" stroke="url(#goldGrad)" stroke-width="3" filter="url(#glow)"/>
  
  <!-- Globe Grid Lines -->
  <ellipse cx="100" cy="100" rx="85" ry="30" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  <ellipse cx="100" cy="100" rx="30" ry="85" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  <line x1="15" y1="100" x2="185" y2="100" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  <line x1="100" y1="15" x2="100" y2="185" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>
  
  <!-- Simplified Continents -->
  <ellipse cx="85" cy="70" rx="20" ry="12" fill="rgba(255,255,255,0.2)"/>
  <ellipse cx="120" cy="80" rx="15" ry="10" fill="rgba(255,255,255,0.2)"/>
  <ellipse cx="75" cy="120" rx="18" ry="8" fill="rgba(255,255,255,0.2)"/>
  <ellipse cx="130" cy="115" rx="12" ry="14" fill="rgba(255,255,255,0.2)"/>
  
  <!-- Male Socialite (Left) -->
  <g transform="translate(55, 55)">
    <!-- Body - Suit -->
    <rect x="-12" y="15" width="24" height="30" rx="5" fill="url(#maleGrad)" stroke="url(#goldGrad)" stroke-width="1.5"/>
    <!-- Tie -->
    <polygon points="0,15 -3,30 3,30" fill="#FFD700"/>
    <!-- Head -->
    <circle cx="0" cy="5" r="12" fill="#F5DEB3" stroke="url(#goldGrad)" stroke-width="1.5"/>
    <!-- Hair -->
    <path d="M-10,0 Q-12,-10 -5,-14 Q0,-16 5,-14 Q12,-10 10,0" fill="#1A1A1A"/>
    <!-- Eyes -->
    <circle cx="-5" cy="4" r="1.5" fill="#1A1A1A"/>
    <circle cx="5" cy="4" r="1.5" fill="#1A1A1A"/>
    <!-- Smile -->
    <path d="M-3,9 Q0,11 3,9" fill="none" stroke="#1A1A1A" stroke-width="0.8"/>
    <!-- Crown -->
    <polygon points="-8,-16 -10,-22 -5,-20 0,-25 5,-20 10,-22 8,-16" fill="url(#goldGrad)" stroke="#B8860B" stroke-width="0.5" filter="url(#glow)"/>
    <!-- Lapel Pin -->
    <circle cx="0" cy="22" r="2" fill="#FFD700"/>
  </g>
  
  <!-- Female Socialite (Right) -->
  <g transform="translate(145, 55)">
    <!-- Body - Dress -->
    <path d="M-10,15 L-14,45 L14,45 L10,15 Z" fill="url(#femaleGrad)" stroke="url(#goldGrad)" stroke-width="1.5"/>
    <path d="M-14,45 L-18,55 L18,55 L14,45 Z" fill="url(#femaleGrad)" stroke="url(#goldGrad)" stroke-width="1.5" opacity="0.8"/>
    <!-- Head -->
    <circle cx="0" cy="5" r="12" fill="#FFE0BD" stroke="url(#goldGrad)" stroke-width="1.5"/>
    <!-- Hair -->
    <path d="M-10,0 Q-12,-8 -8,-13 Q-3,-16 3,-15 Q8,-14 10,-10 Q12,-5 10,0" fill="#8B4513"/>
    <path d="M-10,0 Q-14,10 -12,20" fill="none" stroke="#8B4513" stroke-width="3"/>
    <path d="M10,0 Q14,10 12,20" fill="none" stroke="#8B4513" stroke-width="3"/>
    <!-- Eyes -->
    <circle cx="-5" cy="4" r="1.5" fill="#1A1A1A"/>
    <circle cx="5" cy="4" r="1.5" fill="#1A1A1A"/>
    <!-- Eyelashes -->
    <line x1="-6" y1="2.5" x2="-7" y2="1.5" stroke="#1A1A1A" stroke-width="0.5"/>
    <line x1="6" y1="2.5" x2="7" y2="1.5" stroke="#1A1A1A" stroke-width="0.5"/>
    <!-- Lips -->
    <path d="M-3,9 Q0,12 3,9" fill="#E91E63" stroke="#C2185B" stroke-width="0.5"/>
    <!-- Tiara -->
    <polygon points="-6,-16 -8,-20 -4,-18 0,-23 4,-18 8,-20 6,-16" fill="url(#goldGrad)" stroke="#B8860B" stroke-width="0.5" filter="url(#glow)"/>
    <!-- Diamond on Tiara -->
    <polygon points="0,-20 -1,-18 0,-16 1,-18" fill="#B9F2FF" filter="url(#glow)"/>
    <!-- Necklace -->
    <path d="M-8,15 Q0,20 8,15" fill="none" stroke="#FFD700" stroke-width="1"/>
    <circle cx="0" cy="17" r="1.5" fill="#B9F2FF"/>
    <!-- Earrings -->
    <circle cx="-12" cy="8" r="1.5" fill="#FFD700" filter="url(#glow)"/>
    <circle cx="12" cy="8" r="1.5" fill="#FFD700" filter="url(#glow)"/>
  </g>
  
  <!-- Sparkles around the globe -->
  <g fill="#FFD700" filter="url(#strongGlow)">
    <circle cx="25" cy="25" r="2"/>
    <circle cx="175" cy="25" r="2"/>
    <circle cx="25" cy="175" r="2"/>
    <circle cx="175" cy="175" r="2"/>
    <circle cx="100" cy="10" r="1.5"/>
    <circle cx="10" cy="100" r="1.5"/>
    <circle cx="190" cy="100" r="1.5"/>
  </g>
  
  <!-- Main Crown on top -->
  <g transform="translate(100, 8)">
    <polygon points="0,-12 -18,-24 -12,-18 -6,-30 0,-18 6,-30 12,-18 18,-24" 
             fill="url(#goldGrad)" stroke="#B8860B" stroke-width="1.5" filter="url(#strongGlow)"/>
    <!-- Crown jewels -->
    <circle cx="0" cy="-20" r="2" fill="#FF0000"/>
    <circle cx="-8" cy="-22" r="1.5" fill="#00FF00"/>
    <circle cx="8" cy="-22" r="1.5" fill="#0000FF"/>
  </g>
  
  <!-- Brand Name -->
  <text x="100" y="185" text-anchor="middle" fill="url(#goldGrad)" 
        font-family="Arial, sans-serif" font-size="12" font-weight="bold" 
        filter="url(#glow)">SOCIALITE</text>
</svg>"""

def get_socialite_emoji_html(size: int = 120) -> str:
    """Get the Socialite emoji as HTML img tag"""
    b64 = base64.b64encode(generate_socialite_emoji(size).encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" alt="Socialite" style="filter:drop-shadow(0 0 20px rgba(255,215,0,0.5));animation:float 3s ease-in-out infinite;">'

# ========== THEMES & WALLPAPERS ==========
THEMES = {
    "midnight": {
        "name": "Midnight Galaxy", "icon": "🌌",
        "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)",
        "text": "#f1f5f9", "secondary": "#94a3b8",
        "accent": "#818cf8", 
        "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)",
        "category": "dark"
    },
    "ocean": {
        "name": "Deep Ocean", "icon": "🌊",
        "bg": "#0a192f", "card": "rgba(255,255,255,0.05)",
        "text": "#e2e8f0", "secondary": "#8892b0",
        "accent": "#64ffda",
        "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)",
        "category": "dark"
    },
    "sunset": {
        "name": "Golden Sunset", "icon": "🌅",
        "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)",
        "text": "#fce4ec", "secondary": "#ce93d8",
        "accent": "#ff4081",
        "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)",
        "category": "warm"
    },
    "forest": {
        "name": "Enchanted Forest", "icon": "🌲",
        "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)",
        "text": "#e8f5e9", "secondary": "#81c784",
        "accent": "#4caf50",
        "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)",
        "category": "nature"
    },
    "neon": {
        "name": "Neon Nights", "icon": "💜",
        "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)",
        "text": "#ede7f6", "secondary": "#b39ddb",
        "accent": "#7c4dff",
        "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)",
        "category": "dark"
    },
    "royal": {
        "name": "Royal Purple", "icon": "👑",
        "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)",
        "text": "#f3e5f5", "secondary": "#ce93d8",
        "accent": "#9c27b0",
        "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)",
        "category": "dark"
    },
    "crimson": {
        "name": "Crimson Red", "icon": "❤️",
        "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)",
        "text": "#ffebee", "secondary": "#ef9a9a",
        "accent": "#f44336",
        "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)",
        "category": "warm"
    },
    "arctic": {
        "name": "Arctic Frost", "icon": "❄️",
        "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)",
        "text": "#e3f2fd", "secondary": "#90caf9",
        "accent": "#2196f3",
        "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)",
        "category": "cool"
    }
}

WALLPAPERS = {
    "wp_socialite": {
        "name": "Socialite Luxury", "icon": "👑",
        "url": None, 
        "gradient": "linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%)",
        "category": "luxury"
    },
    "wp_gold": {
        "name": "Pure Gold", "icon": "✨",
        "url": None, 
        "gradient": "linear-gradient(135deg, #1a0f00 0%, #3d2200 25%, #5a3500 50%, #3d2200 75%, #1a0f00 100%)",
        "category": "luxury"
    },
    "wp_purple": {
        "name": "Purple Haze", "icon": "💜",
        "url": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1200&q=80",
        "gradient": None,
        "category": "abstract"
    },
    "wp_ocean": {
        "name": "Ocean Waves", "icon": "🌊",
        "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&q=80",
        "gradient": None,
        "category": "nature"
    },
    "wp_stars": {
        "name": "Starry Mountains", "icon": "🏔️",
        "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&q=80",
        "gradient": None,
        "category": "nature"
    }
}

# ========== STREAMLIT UI ==========
class SocialiteUI:
    """Handle all Streamlit UI rendering"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self.story_manager = StoryManager(self.db)
        self.notification_manager = NotificationManager(self.db)
        self.rate_limiter = RateLimiter()
        self._init_session()
    
    def _init_session(self):
        """Initialize session state variables"""
        defaults = {
            'auth': False,
            'user_id': None,
            'username': None,
            'current_tab': 'feed',
            'active_chat': None,
            'active_group': None,
            'show_create_modal': False,
            'show_notifications': False,
            'feed_page': 1,
            'feed_type': 'home',
            'editing_post': None,
            'viewing_profile': None,
            'show_comments_for': None,
            'reply_to_comment': None,
            'viewing_story': None
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
    
    def render(self):
        """Main render method"""
        if not st.session_state.auth:
            self.render_auth()
            return
        
        # Update last seen
        if st.session_state.user_id:
            self.user_manager.update_last_seen(st.session_state.user_id)
        
        self.inject_styles()
        self.render_header()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        tab = st.session_state.current_tab
        if tab == 'feed':
            self.render_feed()
        elif tab == 'explore':
            self.render_explore()
        elif tab == 'chats':
            self.render_chats()
        elif tab == 'notifications':
            self.render_notifications()
        elif tab == 'profile':
            self.render_profile()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.show_create_modal:
            self.render_create_modal()
        
        self.render_bottom_nav()
    
    def render_auth(self):
        """Render the improved authentication page"""
        # Reset any restrictive styles for auth page
        st.markdown("""
        <style>
        /* Override container styles for auth page */
        .stApp {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: 100vh !important;
            background: linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%) !important;
            overflow: auto !important;
        }
        
        .main {
            height: auto !important;
            overflow: visible !important;
        }
        
        .block-container {
            height: auto !important;
            overflow: visible !important;
            padding: 2rem 1rem !important;
            max-width: 100% !important;
        }
        
        /* Auth container styling */
        .auth-wrapper {
            background: rgba(10, 10, 26, 0.8) !important;
            backdrop-filter: blur(30px) !important;
            -webkit-backdrop-filter: blur(30px) !important;
            border: 2px solid rgba(255, 215, 0, 0.2) !important;
            border-radius: 24px !important;
            padding: 2.5rem 2rem !important;
            box-shadow: 0 0 60px rgba(255, 215, 0, 0.1), 
                       0 0 120px rgba(255, 215, 0, 0.05),
                       inset 0 0 30px rgba(255, 215, 0, 0.02) !important;
            max-width: 450px !important;
            margin: 0 auto !important;
        }
        
        /* Logo animations */
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes pulse {
            0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.3; }
            50% { transform: translate(-50%, -50%) scale(1.3); opacity: 0.6; }
        }
        
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
        
        .logo-container {
            position: relative;
            display: inline-block;
            margin-bottom: 1.5rem;
        }
        
        .logo-glow {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(255,215,0,0.4) 0%, rgba(255,215,0,0.1) 30%, transparent 70%);
            border-radius: 50%;
            animation: pulse 2.5s ease-in-out infinite;
        }
        
        .logo-image {
            position: relative;
            z-index: 1;
            animation: float 3s ease-in-out infinite;
        }
        
        /* Brand title */
        .brand-title {
            font-family: 'Playfair Display', 'Georgia', serif !important;
            font-size: 2.8rem !important;
            font-weight: 900 !important;
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 25%, #FFD700 50%, #FFB300 75%, #FFD700 100%) !important;
            background-size: 200% auto !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            background-clip: text !important;
            animation: shimmer 3s linear infinite !important;
            text-shadow: 0 0 40px rgba(255, 215, 0, 0.4) !important;
            margin: 0.5rem 0 !important;
            letter-spacing: 2px !important;
        }
        
        /* Form elements */
        .stTextInput > div > div > input {
            background: rgba(255, 255, 255, 0.06) !important;
            border: 2px solid rgba(255, 215, 0, 0.15) !important;
            color: #f1f5f9 !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
            font-size: 0.95rem !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            height: auto !important;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #FFD700 !important;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.2), 0 0 40px rgba(255, 215, 0, 0.1) !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #64748b !important;
            font-size: 0.9rem !important;
        }
        
        /* Submit buttons */
        .stButton > button {
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%) !important;
            background-size: 200% auto !important;
            color: #1a0033 !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            padding: 14px 28px !important;
            border-radius: 12px !important;
            border: none !important;
            width: 100% !important;
            cursor: pointer !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            animation: shimmer 3s linear infinite !important;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3) !important;
            height: auto !important;
            min-height: 50px !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 30px rgba(255, 215, 0, 0.4), 0 0 60px rgba(255, 215, 0, 0.1) !important;
            border: none !important;
        }
        
        .stButton > button:active {
            transform: translateY(-1px) !important;
        }
        
        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0 !important;
            background: transparent !important;
            border-bottom: 2px solid rgba(255, 215, 0, 0.15) !important;
            margin-bottom: 1.5rem !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: #94a3b8 !important;
            font-weight: 500 !important;
            padding: 12px 20px !important;
            font-size: 0.95rem !important;
            transition: all 0.3s !important;
            border-bottom: 3px solid transparent !important;
            margin-bottom: -2px !important;
            border-radius: 0 !important;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #FFD700 !important;
        }
        
        .stTabs [aria-selected="true"] {
            color: #FFD700 !important;
            border-bottom-color: #FFD700 !important;
            background: transparent !important;
        }
        
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #FFD700 !important;
            height: 3px !important;
        }
        
        /* Feature grid */
        .feature-grid {
            display: grid !important;
            grid-template-columns: repeat(3, 1fr) !important;
            gap: 12px !important;
            margin-top: 2rem !important;
            padding-top: 1.5rem !important;
            border-top: 1px solid rgba(255, 215, 0, 0.1) !important;
        }
        
        .feature-item {
            text-align: center !important;
            padding: 12px 8px !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.03) !important;
            transition: all 0.3s !important;
            cursor: default !important;
        }
        
        .feature-item:hover {
            background: rgba(255, 215, 0, 0.08) !important;
            transform: translateY(-2px) !important;
        }
        
        .feature-icon {
            font-size: 1.8rem !important;
            margin-bottom: 6px !important;
        }
        
        .feature-text {
            color: #94a3b8 !important;
            font-size: 0.7rem !important;
            font-weight: 500 !important;
        }
        
        /* Error and success messages */
        .stAlert {
            border-radius: 10px !important;
            border: 1px solid !important;
        }
        
        /* Hide Streamlit elements */
        [data-testid="stDecoration"],
        [data-testid="stToolbar"],
        #MainMenu,
        footer,
        header {
            display: none !important;
        }
        
        @media (max-width: 640px) {
            .auth-wrapper {
                padding: 1.5rem !important;
                border-radius: 18px !important;
                margin: 0 10px !important;
            }
            
            .brand-title {
                font-size: 2rem !important;
            }
            
            .feature-grid {
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 8px !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Center the auth form
        st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)
        
        # Logo Section
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div class="logo-container">
                <div class="logo-glow"></div>
                <div class="logo-image">
                    {get_socialite_emoji_html(120)}
                </div>
            </div>
            <h1 class="brand-title">SOCIALITE</h1>
            <p style="color: #94a3b8; font-size: 1rem; margin: 0.5rem 0; font-family: 'Playfair Display', serif; font-style: italic;">
                Where Luxury Meets Connection
            </p>
            <div style="display: flex; justify-content: center; gap: 8px; margin-top: 0.5rem;">
                <span style="background: rgba(255, 215, 0, 0.1); color: #FFD700; padding: 4px 10px; border-radius: 15px; font-size: 0.7rem; border: 1px solid rgba(255, 215, 0, 0.2);">
                    ✨ Premium Network
                </span>
                <span style="background: rgba(255, 215, 0, 0.1); color: #FFD700; padding: 4px 10px; border-radius: 15px; font-size: 0.7rem; border: 1px solid rgba(255, 215, 0, 0.2);">
                    🔒 Secure & Private
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Auth Tabs
        tab1, tab2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
        
        with tab1:
            with st.form("login_form", clear_on_submit=False):
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
                
                submitted = st.form_submit_button(
                    "🔓 Sign In",
                    use_container_width=True
                )
                
                if submitted:
                    if not username or not password:
                        st.error("Please fill in all fields")
                    else:
                        if not self.rate_limiter.can_act('login', 'attempt', 5, 300):
                            st.error("Too many login attempts. Please wait.")
                        else:
                            success, result = self.user_manager.authenticate(
                                username, password
                            )
                            if success:
                                st.session_state.auth = True
                                st.session_state.username = result
                                user = self.user_manager.get_user_by_username(result)
                                if user:
                                    st.session_state.user_id = user['user_id']
                                st.rerun()
                            else:
                                st.error(result)
        
        with tab2:
            with st.form("register_form", clear_on_submit=False):
                new_username = st.text_input(
                    "Choose Username",
                    placeholder=f"3-{Config.MAX_USERNAME_LENGTH} characters, letters/numbers only",
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
                    placeholder=f"Minimum {Config.MIN_PASSWORD_LENGTH} characters",
                    key="reg_password"
                )
                
                confirm_password = st.text_input(
                    "Confirm Password",
                    type="password",
                    placeholder="Re-enter your password",
                    key="reg_confirm"
                )
                
                submitted = st.form_submit_button(
                    "✨ Create Account",
                    use_container_width=True
                )
                
                if submitted:
                    if not new_username or not new_password:
                        st.error("Username and password are required")
                    elif new_password != confirm_password:
                        st.error("Passwords don't match")
                    elif len(new_password) < Config.MIN_PASSWORD_LENGTH:
                        st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                    elif len(new_username) < 3 or len(new_username) > Config.MAX_USERNAME_LENGTH:
                        st.error(f"Username must be 3-{Config.MAX_USERNAME_LENGTH} characters")
                    elif not re.match(r'^[a-zA-Z0-9_]+$', new_username):
                        st.error("Username can only contain letters, numbers, and underscores")
                    else:
                        success, message = self.user_manager.create_user(
                            new_username, new_password, email
                        )
                        if success:
                            st.success("🎉 " + message)
                            st.info("Please sign in with your new account!")
                            st.balloons()
                        else:
                            st.error(message)
        
        # Features Showcase
        st.markdown("""
        <div class="feature-grid">
            <div class="feature-item">
                <div class="feature-icon">📝</div>
                <div class="feature-text">Rich Posts</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">💬</div>
                <div class="feature-text">Live Chat</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📊</div>
                <div class="feature-text">Polls</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📸</div>
                <div class="feature-text">Stories</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🎨</div>
                <div class="feature-text">8 Themes</div>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🔒</div>
                <div class="feature-text">Secure</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(255, 215, 0, 0.1);">
            <p style="color: #64748b; font-size: 0.7rem;">
                Version {Config.APP_VERSION} • Premium Social Experience
            </p>
            <p style="color: #64748b; font-size: 0.65rem; margin-top: 4px;">
                © 2024 Socialite. All rights reserved.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def inject_styles(self):
        """Inject CSS styles"""
        theme = self._get_current_theme()
        wallpaper = self._get_current_wallpaper()
        
        if wallpaper.get('url'):
            bg = f"url('{wallpaper['url']}') center/cover no-repeat fixed"
        else:
            bg = wallpaper.get('gradient', theme['gradient'])
        
        st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Playfair+Display:wght@400;700;900&display=swap');
        
        * {{ font-family: 'Inter', sans-serif; }}
        
        #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
        section[data-testid="stSidebar"] {{ display: none !important; }}
        .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="stToolbar"] {{ display: none !important; }}
        
        html, body {{ height: 100% !important; width: 100% !important; margin: 0 !important; padding: 0 !important; overflow: hidden !important; }}
        
        .stApp {{
            background: {bg} !important;
            height: 100vh !important; width: 100vw !important;
            overflow: hidden !important; position: relative !important;
        }}
        
        .main {{ height: 100vh !important; overflow: hidden !important; }}
        .block-container {{ height: 100vh !important; overflow: hidden !important; padding: 0 !important; margin: 0 !important; max-width: 100% !important; }}
        
        /* Header */
        .app-header {{
            position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important;
            height: 48px !important; background: {theme['bg']}f0 !important;
            backdrop-filter: blur(20px) !important; -webkit-backdrop-filter: blur(20px) !important;
            border-bottom: 1px solid rgba(255,215,0,0.15) !important;
            padding: 0 16px !important; z-index: 9999 !important;
            display: flex !important; align-items: center !important; justify-content: space-between !important;
        }}
        
        /* Main content area */
        .main-content {{
            position: fixed !important; top: 48px !important; bottom: 56px !important;
            left: 0 !important; right: 0 !important; overflow-y: auto !important;
            overflow-x: hidden !important; padding: 8px 12px !important;
            -webkit-overflow-scrolling: touch !important;
        }}
        
        .content-wrapper {{ max-width: 650px !important; margin: 0 auto !important; padding-bottom: 8px !important; }}
        
        /* Bottom Nav */
        .bottom-nav {{
            position: fixed !important; bottom: 0 !important; left: 0 !important; right: 0 !important;
            height: 56px !important; background: {theme['bg']}fa !important;
            backdrop-filter: blur(20px) !important; -webkit-backdrop-filter: blur(20px) !important;
            border-top: 2px solid rgba(255,215,0,0.25) !important;
            display: flex !important; align-items: center !important; justify-content: space-around !important;
            z-index: 9999 !important; box-shadow: 0 -4px 20px rgba(0,0,0,0.5) !important;
        }}
        
        /* Cards */
        .card {{
            background: {theme['card']} !important; border: 1px solid rgba(255,255,255,0.06) !important;
            border-radius: 14px !important; margin-bottom: 10px !important; overflow: hidden !important;
        }}
        .card-header {{ display: flex !important; align-items: center !important; padding: 8px 10px !important; gap: 8px !important; }}
        .username-text {{ color: {theme['text']} !important; font-weight: 600 !important; font-size: 0.82rem !important; }}
        .timestamp {{ color: {theme['secondary']} !important; font-size: 0.62rem !important; }}
        .post-text {{ color: #e2e8f0 !important; font-size: 0.85rem !important; line-height: 1.5 !important; padding: 0 10px 8px 10px !important; word-wrap: break-word !important; }}
        
        /* Buttons */
        .stButton > button {{
            background: rgba(255,215,0,0.08) !important; border: 1px solid rgba(255,215,0,0.2) !important;
            color: {theme['text']} !important; border-radius: 8px !important; padding: 6px 12px !important;
            font-size: 0.8rem !important; font-weight: 500 !important; min-height: auto !important; transition: all 0.2s !important;
        }}
        .stButton > button:hover {{ background: rgba(255,215,0,0.15) !important; border-color: #FFD700 !important; box-shadow: 0 0 12px rgba(255,215,0,0.25) !important; }}
        
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
            background: rgba(255,255,255,0.06) !important; border: 1px solid rgba(255,255,255,0.1) !important;
            color: {theme['text']} !important; border-radius: 8px !important; padding: 8px 12px !important; font-size: 0.85rem !important;
        }}
        .stTextInput > div > div > input::placeholder {{ color: {theme['secondary']} !important; }}
        
        ::-webkit-scrollbar {{ width: 4px !important; }}
        ::-webkit-scrollbar-track {{ background: transparent !important; }}
        ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        @media (max-width: 480px) {{
            .main-content {{ padding: 6px 8px !important; }}
            .card {{ border-radius: 10px !important; margin-bottom: 8px !important; }}
            .bottom-nav {{ height: 52px !important; }}
            .main-content {{ bottom: 52px !important; }}
            .app-header {{ height: 44px !important; }}
            .main-content {{ top: 44px !important; }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_header(self):
        """Render app header"""
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        unread_notifications = self.notification_manager.get_unread_count(user['user_id'])
        badge = f'<span style="background:#FFD700;color:#000;border-radius:50%;padding:1px 6px;font-size:0.6rem;position:absolute;top:-5px;right:-10px;">{unread_notifications}</span>' if unread_notifications > 0 else ''
        
        st.markdown(f"""
        <div class="app-header">
            <div style="display:flex;align-items:center;gap:8px;font-weight:800;font-size:1.1rem;
                 background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                {get_socialite_emoji_html(24)} Socialite
            </div>
            <div style="display:flex;align-items:center;gap:15px;color:#94a3b8;">
                <span style="cursor:pointer;position:relative;">
                    🔔{badge}
                </span>
                {self.render_avatar_html(user, 28)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Hidden button for notification click
        col1, col2 = st.columns([10, 1])
        with col2:
            if st.button("🔔", key="notif_btn_header", help="View notifications"):
                st.session_state.current_tab = 'notifications'
                st.rerun()
    
    def render_feed(self):
        """Render feed page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Stories bar
        self.render_stories_bar()
        
        # Quick post button
        if st.button("✨ What's on your mind? Tap to post...", use_container_width=True):
            st.session_state.show_create_modal = True
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Get user
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        # Feed type selector
        feed_type = st.selectbox(
            "Feed",
            ["Home", "Explore", "Trending"],
            key="feed_type_selector",
            label_visibility="collapsed"
        )
        st.session_state.feed_type = feed_type.lower()
        
        # Load feed
        posts, has_more = self.post_manager.get_feed(
            user['user_id'], 
            page=st.session_state.feed_page,
            feed_type=st.session_state.feed_type
        )
        
        if not posts:
            st.markdown(f"""
            <div style="text-align:center;padding:3rem 1rem;color:#94a3b8;">
                {get_socialite_emoji_html(100)}
                <h3 style="color:#FFD700;margin-top:1rem;">Welcome to Socialite</h3>
                <p style="font-size:0.9rem;">Follow users or create your first post to get started!</p>
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
                        {"<span style='color:#FFD700;'> 👑</span>" if post.get('is_premium') else ""}
                    </div>
                    <div class="timestamp">
                        {Utils.format_timestamp(post['timestamp'])}
                        {" · Edited" if post.get('is_edited') else ""}
                        {" · 📌" if post.get('is_pinned') else ""}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Text
            if post.get('text'):
                st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', 
                          unsafe_allow_html=True)
            
            # Media
            if post.get('media_data'):
                try:
                    image_bytes = base64.b64decode(post['media_data'])
                    st.image(image_bytes, use_column_width=True)
                except:
                    st.error("Failed to load image")
            
            # Poll
            if post.get('post_type') == 'poll' and post.get('poll_options'):
                self.render_poll(post)
            
            # Actions
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 3])
            
            with col1:
                reaction_emoji = "❤️"
                reaction_count = sum(post.get('reactions', {}).values())
                if post.get('user_reaction'):
                    reaction_emoji = "❤️‍🔥"
                
                if st.button(f"{reaction_emoji} {reaction_count}", 
                           key=f"react_{post['id']}", use_container_width=True):
                    self.post_manager.add_reaction(
                        post['id'],
                        st.session_state.user_id,
                        'like'
                    )
                    st.rerun()
            
            with col2:
                if st.button(f"💬 {post.get('comment_count', 0)}", 
                           key=f"comment_btn_{post['id']}", use_container_width=True):
                    st.session_state.show_comments_for = post['id'] if st.session_state.show_comments_for != post['id'] else None
                    st.rerun()
            
            with col3:
                if st.button("🔄", key=f"share_{post['id']}", use_container_width=True):
                    st.toast("Post shared!")
            
            with col4:
                if st.button("🔖", key=f"save_{post['id']}", use_container_width=True):
                    st.toast("Post saved!")
            
            with col5:
                if post['username'] == st.session_state.username:
                    if st.button("🗑️", key=f"delete_{post['id']}", use_container_width=True):
                        self.post_manager.delete_post(post['id'], st.session_state.user_id)
                        st.rerun()
                else:
                    if st.button("🚩", key=f"report_{post['id']}", use_container_width=True):
                        st.toast("Post reported")
            
            # Comments section
            if st.session_state.show_comments_for == post['id']:
                self.render_comments_section(post['id'])
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_poll(self, post: Dict):
        """Render poll options"""
        st.markdown('<div style="padding:0 10px 10px 10px;">', unsafe_allow_html=True)
        
        total_votes = sum(opt.get('vote_count', 0) for opt in post.get('poll_options', []))
        
        for option in post.get('poll_options', []):
            vote_count = option.get('vote_count', 0)
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div style="padding:8px;margin:4px 0;background:rgba(255,255,255,0.03);
                         border-radius:8px;position:relative;overflow:hidden;">
                    <div style="position:absolute;left:0;top:0;bottom:0;width:{percentage}%;
                             background:linear-gradient(90deg,rgba(255,215,0,0.2),rgba(255,165,0,0.1));
                             border-radius:8px;transition:width 0.3s;"></div>
                    <div style="position:relative;z-index:1;display:flex;justify-content:space-between;
                             color:#e2e8f0;font-size:0.85rem;">
                        <span>{html.escape(option['option_text'])}</span>
                        <span>{percentage:.0f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("Vote", key=f"poll_vote_{post['id']}_{option['id']}"):
                    self.post_manager.vote_poll(post['id'], st.session_state.user_id, option['id'])
                    st.rerun()
        
        st.markdown(f"""
        <div style="color:#94a3b8;font-size:0.65rem;text-align:center;margin-top:5px;">
            {total_votes} total votes
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_comments_section(self, post_id: str):
        """Render comments section for a post"""
        st.markdown('<div style="padding:8px 10px;border-top:1px solid rgba(255,215,0,0.1);">', 
                   unsafe_allow_html=True)
        
        comments = self.post_manager.get_comments(post_id)
        
        for comment in comments:
            st.markdown(f"""
            <div style="margin:6px 0;display:flex;gap:8px;align-items:flex-start;">
                {self.render_avatar_html(comment, 24)}
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:4px;">
                        <span style="color:#FFD700;font-weight:600;font-size:0.75rem;">
                            @{html.escape(comment['username'])}
                        </span>
                        <span style="color:#64748b;font-size:0.6rem;">
                            {Utils.format_timestamp(comment['timestamp'])}
                        </span>
                    </div>
                    <div style="color:#e2e8f0;font-size:0.8rem;margin-top:2px;">
                        {html.escape(comment['text'])}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if not comments:
            st.markdown('<div style="color:#64748b;font-size:0.75rem;text-align:center;padding:10px;">No comments yet</div>', 
                       unsafe_allow_html=True)
        
        # Add comment form
        with st.form(f"comment_form_{post_id}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                text = st.text_input(
                    "Add a comment...",
                    key=f"comment_input_{post_id}",
                    placeholder="Write a comment..."
                )
            with col2:
                if st.form_submit_button("Post", use_container_width=True):
                    if text.strip():
                        success, _ = self.post_manager.add_comment(
                            post_id,
                            st.session_state.user_id,
                            text
                        )
                        if success:
                            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_stories_bar(self):
        """Render stories bar"""
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        active_stories = self.story_manager.get_active_stories()
        
        st.markdown('<div style="display:flex;gap:12px;padding:8px 0;overflow-x:auto;margin-bottom:8px;">', 
                   unsafe_allow_html=True)
        
        # Current user's story
        st.markdown(f"""
        <div style="text-align:center;min-width:65px;cursor:pointer;">
            {self.render_avatar_html(user, 56)}
            <div style="color:#94a3b8;font-size:0.6rem;margin-top:4px;">Your Story</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Other users' stories
        seen_users = set()
        for story in active_stories[:15]:
            if story['username'] != st.session_state.username and story['username'] not in seen_users:
                seen_users.add(story['username'])
                st.markdown(f"""
                <div style="text-align:center;min-width:65px;cursor:pointer;">
                    {self.render_avatar_html(story, 56)}
                    <div style="color:#94a3b8;font-size:0.6rem;margin-top:4px;">
                        @{html.escape(story['username'][:8])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if not seen_users:
            st.markdown("""
            <div style="display:flex;align-items:center;color:#64748b;font-size:0.7rem;padding-left:12px;">
                No stories yet
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_explore(self):
        """Render explore page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        st.markdown('<h3 style="color:#FFD700;margin-bottom:10px;">🔍 Explore</h3>', 
                   unsafe_allow_html=True)
        
        # Search
        query = st.text_input("Search users", placeholder="Search by username or name...", 
                            key="explore_search")
        
        if query:
            users = self.user_manager.search_users(
                query, 
                exclude_user_id=st.session_state.user_id
            )
            
            if not users:
                st.info("No users found matching your search")
            else:
                for user in users:
                    col1, col2, col3 = st.columns([4, 2, 2])
                    
                    with col1:
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;">
                            {self.render_avatar_html(user, 40)}
                            <div>
                                <div style="color:#f1f5f9;font-weight:600;">
                                    @{html.escape(user['username'])}
                                    {"<span style='color:#FFD700;'> ✓</span>" if user.get('is_verified') else ""}
                                </div>
                                <div style="color:#94a3b8;font-size:0.7rem;">
                                    {Utils.format_number(user.get('follower_count', 0))} followers
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("Follow", key=f"explore_follow_{user['username']}", 
                                   use_container_width=True):
                            self.user_manager.follow_user(
                                st.session_state.user_id, 
                                user['username']
                            )
                            st.rerun()
                    
                    with col3:
                        if st.button("💬", key=f"explore_chat_{user['username']}", 
                                   use_container_width=True):
                            st.session_state.active_chat = user['username']
                            st.session_state.current_tab = 'chats'
                            st.rerun()
        
        # Trending users
        st.markdown('<h4 style="color:#FFD700;margin-top:20px;">📈 Trending Users</h4>', 
                   unsafe_allow_html=True)
        
        trending = self.user_manager.get_trending_users(10)
        for user in trending:
            if user['username'] != st.session_state.username:
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                         border-bottom:1px solid rgba(255,215,0,0.05);">
                    {self.render_avatar_html(user, 40)}
                    <div style="flex:1;">
                        <div style="color:#f1f5f9;font-weight:600;">
                            @{html.escape(user['username'])}
                            {"<span style='color:#FFD700;'> ✓</span>" if user.get('is_verified') else ""}
                        </div>
                        <div style="color:#94a3b8;font-size:0.7rem;">
                            {Utils.format_number(user.get('follower_count', 0))} followers · 
                            {user.get('total_posts', 0)} posts
                        </div>
                    </div>
                    <span style="color:#FFD700;font-size:0.8rem;">
                        #{trending.index(user) + 1}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chats(self):
        """Render chats page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        if st.session_state.active_chat:
            self.render_chat_interface()
        else:
            self.render_chat_list()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_chat_list(self):
        """Render list of chats"""
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        st.markdown('<h3 style="color:#FFD700;margin-bottom:10px;">💬 Messages</h3>', 
                   unsafe_allow_html=True)
        
        chats = self.chat_manager.get_chat_list(user['user_id'])
        
        if not chats:
            st.info("No conversations yet. Explore users to start chatting!")
        else:
            for chat in chats:
                online_dot = "🟢" if chat.get('is_online') else "⚫"
                unread_badge = f"<span style='background:#FFD700;color:#000;border-radius:50%;padding:1px 6px;font-size:0.6rem;'>{chat['unread_count']}</span>" if chat.get('unread_count', 0) > 0 else ""
                
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 0;
                         border-bottom:1px solid rgba(255,215,0,0.05);">
                    {self.render_avatar_html(chat, 44)}
                    <div style="flex:1;min-width:0;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#f1f5f9;font-weight:600;">
                                @{html.escape(chat.get('other_username', 'unknown'))}
                                {online_dot}
                            </span>
                            {unread_badge}
                        </div>
                        <div style="color:#94a3b8;font-size:0.7rem;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                            {Utils.format_timestamp(chat.get('last_message_time'))}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Open Chat", key=f"open_chat_{chat.get('other_username')}"):
                    st.session_state.active_chat = chat['other_username']
                    st.rerun()
        
        # New chat section
        with st.expander("💬 Start New Chat"):
            all_users = self.user_manager.search_users("", limit=100, 
                                                      exclude_user_id=user['user_id'])
            if all_users:
                selected = st.selectbox(
                    "Select user to chat with",
                    [u['username'] for u in all_users],
                    key="new_chat_select"
                )
                if st.button("Start Chat", use_container_width=True):
                    st.session_state.active_chat = selected
                    st.rerun()
    
    def render_chat_interface(self):
        """Render chat interface with specific user"""
        if st.button("← Back to Chats", key="back_to_chats", use_container_width=True):
            st.session_state.active_chat = None
            st.rerun()
        
        with_user = self.user_manager.get_user_by_username(st.session_state.active_chat)
        if not with_user:
            st.error("User not found")
            return
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        # Chat header
        is_online = with_user['username'] in self.user_manager.get_online_users()
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                 border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:10px;">
            {self.render_avatar_html(with_user, 36)}
            <div>
                <div style="color:#f1f5f9;font-weight:600;">@{html.escape(with_user['username'])}</div>
                <div style="color:{'#4ade80' if is_online else '#94a3b8'};font-size:0.7rem;">
                    {'🟢 Online' if is_online else '⚫ Offline'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Messages container
        st.markdown('<div style="max-height:50vh;overflow-y:auto;padding:10px 0;">', 
                   unsafe_allow_html=True)
        
        messages = self.chat_manager.get_messages(
            user['user_id'],
            with_user['user_id']
        )
        
        for msg in messages:
            is_sent = msg['from_id'] == user['user_id']
            align = 'flex-end' if is_sent else 'flex-start'
            bg = 'linear-gradient(135deg,#667eea,#764ba2)' if is_sent else 'rgba(255,255,255,0.07)'
            
            st.markdown(f"""
            <div style="display:flex;justify-content:{align};margin:4px 8px;">
                <div style="max-width:70%;padding:8px 14px;border-radius:16px;background:{bg};
                         color:white;font-size:0.85rem;line-height:1.4;">
                    {html.escape(msg.get('text', ''))}
                    <div style="font-size:0.55rem;opacity:0.7;margin-top:4px;text-align:right;">
                        {Utils.format_timestamp(msg['timestamp'])}
                        {' ✓✓' if is_sent and msg.get('is_read') else ' ✓' if is_sent else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Message input
        st.markdown('<div style="position:sticky;bottom:0;padding:10px 0;">', 
                   unsafe_allow_html=True)
        with st.form(f"send_message_{with_user['user_id']}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                text = st.text_input(
                    "Message",
                    placeholder="Type a message...",
                    key=f"msg_input_{with_user['user_id']}",
                    label_visibility="collapsed"
                )
            with col2:
                if st.form_submit_button("➤ Send", use_container_width=True):
                    if text.strip():
                        if self.rate_limiter.can_act(st.session_state.user_id, 'send_message', 10, 60):
                            self.chat_manager.send_message(
                                user['user_id'],
                                with_user['username'],
                                text
                            )
                            st.rerun()
                        else:
                            st.error("Sending too fast. Please wait.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_notifications(self):
        """Render notifications page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        st.markdown('<h3 style="color:#FFD700;margin-bottom:10px;">🔔 Notifications</h3>', 
                   unsafe_allow_html=True)
        
        notifications = self.notification_manager.get_notifications(user['user_id'])
        
        if notifications:
            if st.button("Mark All as Read", use_container_width=True):
                self.notification_manager.mark_all_read(user['user_id'])
                st.rerun()
        
        if not notifications:
            st.info("No notifications yet")
        else:
            for notif in notifications:
                icon = {
                    'like': '❤️',
                    'reaction': '❤️',
                    'comment': '💬',
                    'comment_reply': '💬',
                    'follow': '👤',
                    'follow_request': '👤',
                    'mention': '@️',
                    'message': '💬'
                }.get(notif['type'], '🔔')
                
                bg = 'rgba(255,215,0,0.05)' if not notif['is_read'] else 'transparent'
                
                st.markdown(f"""
                <div style="padding:10px;margin:4px 0;background:{bg};
                         border-radius:8px;display:flex;align-items:center;gap:10px;">
                    <span style="font-size:1.2rem;">{icon}</span>
                    <div style="flex:1;">
                        <div style="color:#e2e8f0;font-size:0.85rem;">
                            {html.escape(notif['message'])}
                            {'<span style="color:#FFD700;">@' + html.escape(notif['from_username']) + '</span>' if notif.get('from_username') else ''}
                        </div>
                        <div style="color:#64748b;font-size:0.65rem;margin-top:2px;">
                            {Utils.format_timestamp(notif['timestamp'])}
                        </div>
                    </div>
                    {'' if notif['is_read'] else '<span style="width:8px;height:8px;border-radius:50%;background:#FFD700;flex-shrink:0;"></span>'}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_profile(self):
        """Render profile page"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        # Profile header
        follower_count = self._get_follower_count(user['user_id'])
        following_count = self._get_following_count(user['user_id'])
        
        st.markdown(f"""
        <div style="text-align:center;padding:20px 0;">
            {self.render_avatar_html(user, 80)}
            <h2 style="color:#FFD700;margin-top:10px;">
                @{html.escape(user['username'])}
                {"<span style='color:#FFD700;'> ✓</span>" if user.get('is_verified') else ""}
                {"<span style='color:#FFD700;'> 👑</span>" if user.get('is_premium') else ""}
            </h2>
            <p style="color:#94a3b8;font-size:0.9rem;margin:5px 0;">
                {html.escape(user.get('display_name', user['username']))}
            </p>
            <p style="color:#94a3b8;font-size:0.85rem;margin:5px 0;">
                {html.escape(user.get('bio', 'No bio yet'))}
            </p>
            {"<p style='color:#94a3b8;font-size:0.75rem;'>🌐 " + html.escape(user.get('website', '')) + "</p>" if user.get('website') else ""}
            {"<p style='color:#94a3b8;font-size:0.75rem;'>📍 " + html.escape(user.get('location', '')) + "</p>" if user.get('location') else ""}
            
            <div style="display:flex;justify-content:space-around;margin-top:20px;padding:15px 0;
                     border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);">
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">
                        {Utils.format_number(user.get('total_posts', 0))}
                    </div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Posts</div>
                </div>
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">
                        {Utils.format_number(follower_count)}
                    </div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Followers</div>
                </div>
                <div>
                    <div style="color:#FFD700;font-weight:700;font-size:1.2rem;">
                        {Utils.format_number(following_count)}
                    </div>
                    <div style="color:#94a3b8;font-size:0.7rem;">Following</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Edit profile
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile_form"):
                display_name = st.text_input(
                    "Display Name",
                    value=user.get('display_name', ''),
                    max_chars=50
                )
                
                bio = st.text_area(
                    "Bio",
                    value=user.get('bio', ''),
                    max_chars=Config.MAX_BIO_LENGTH,
                    height=80
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    website = st.text_input(
                        "Website",
                        value=user.get('website', ''),
                        placeholder="https://..."
                    )
                with col2:
                    location = st.text_input(
                        "Location",
                        value=user.get('location', ''),
                        placeholder="City, Country"
                    )
                
                gender = st.selectbox(
                    "Gender",
                    ['male', 'female'],
                    index=0 if user.get('gender', 'male') == 'male' else 1
                )
                
                is_private = st.checkbox(
                    "Private Account",
                    value=user.get('is_private', False)
                )
                
                avatar_file = st.file_uploader(
                    "Profile Picture",
                    type=['png', 'jpg', 'jpeg', 'webp'],
                    key="profile_avatar"
                )
                
                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    updates = {
                        'display_name': Utils.sanitize_text(display_name, 50),
                        'bio': Utils.sanitize_text(bio, Config.MAX_BIO_LENGTH),
                        'website': Utils.sanitize_text(website, 200),
                        'location': Utils.sanitize_text(location, 100),
                        'gender': gender,
                        'is_private': is_private
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
                        except Exception as e:
                            st.error(f"Failed to process image: {e}")
                    
                    if self.user_manager.update_profile(user['user_id'], updates):
                        st.success("Profile updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update profile")
        
        # Themes
        with st.expander("🎨 Themes"):
            st.markdown('<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;">', 
                       unsafe_allow_html=True)
            
            current_theme = user.get('theme', 'midnight')
            for theme_key, theme_data in THEMES.items():
                is_active = current_theme == theme_key
                st.markdown(f"""
                <div style="background:{theme_data['gradient']};padding:15px 10px;border-radius:10px;
                         text-align:center;cursor:pointer;border:{'2px solid #FFD700' if is_active else '2px solid transparent'};">
                    <div style="font-size:1.5rem;">{theme_data['icon']}</div>
                    <div style="color:white;font-size:0.7rem;margin-top:4px;">{theme_data['name']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Apply", key=f"theme_apply_{theme_key}"):
                    self.user_manager.update_profile(user['user_id'], {'theme': theme_key})
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Wallpapers
        with st.expander("🖼️ Wallpapers"):
            st.markdown('<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;">', 
                       unsafe_allow_html=True)
            
            current_wp = user.get('wallpaper', 'wp_socialite')
            for wp_key, wp_data in WALLPAPERS.items():
                is_active = current_wp == wp_key
                bg_style = f"background-image:url('{wp_data['url']}');background-size:cover;" if wp_data.get('url') else f"background:{wp_data.get('gradient','')};"
                
                st.markdown(f"""
                <div style="{bg_style}height:50px;border-radius:8px;cursor:pointer;
                         border:{'2px solid #FFD700' if is_active else '2px solid transparent'};"
                     title="{wp_data['name']}">
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Set", key=f"wp_apply_{wp_key}"):
                    self.user_manager.update_profile(user['user_id'], {'wallpaper': wp_key})
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Sign out
        if st.button("🚪 Sign Out", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_create_modal(self):
        """Render create post modal"""
        st.markdown(f"""
        <div style="position:fixed;top:0;left:0;right:0;bottom:0;
                 background:rgba(0,0,0,0.85);backdrop-filter:blur(8px);
                 z-index:10000;display:flex;align-items:center;justify-content:center;">
            <div style="background:#1a1a2e;border:1px solid rgba(255,215,0,0.2);
                     border-radius:18px;width:90%;max-width:480px;max-height:80vh;
                     overflow-y:auto;padding:20px;">
                <h3 style="color:#FFD700;text-align:center;margin-bottom:15px;">✨ Create Post</h3>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📝 Post", "📊 Poll"])
        
        with tab1:
            with st.form("create_post_form", clear_on_submit=True):
                text = st.text_area(
                    "What's on your mind?",
                    max_chars=Config.MAX_POST_LENGTH,
                    height=120,
                    placeholder="Share your thoughts with the world..."
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    media = st.file_uploader(
                        "Add image",
                        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                        key="post_media"
                    )
                with col2:
                    location = st.text_input(
                        "Location",
                        placeholder="Add location",
                        key="post_location"
                    )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("📤 Post", use_container_width=True):
                        if text or media:
                            media_data = None
                            media_name = None
                            media_type = None
                            
                            if media and media.size <= Config.MAX_FILE_SIZE:
                                try:
                                    image_data = media.read()
                                    if Utils.validate_image(image_data):
                                        optimized = Utils.optimize_image(image_data)
                                        media_data = base64.b64encode(optimized).decode()
                                        media_name = media.name
                                        media_type = "image"
                                except:
                                    st.error("Invalid image file")
                                    st.stop()
                            
                            if text.strip() or media_data:
                                success, result = self.post_manager.create_post(
                                    st.session_state.user_id,
                                    text,
                                    media_data,
                                    media_name,
                                    media_type,
                                    location=location
                                )
                                
                                if success:
                                    st.session_state.show_create_modal = False
                                    st.rerun()
                                else:
                                    st.error(result)
                        else:
                            st.error("Post cannot be empty")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        with tab2:
            with st.form("create_poll_form", clear_on_submit=True):
                question = st.text_input(
                    "Poll question",
                    max_chars=500,
                    placeholder="What do you want to ask?"
                )
                
                options_text = st.text_area(
                    "Options (one per line, max 20)",
                    height=100,
                    placeholder="Option 1\nOption 2\nOption 3"
                )
                
                duration = st.slider(
                    "Duration (hours)",
                    1, 168, 24
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("📊 Create Poll", use_container_width=True):
                        if question and options_text:
                            options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
                            if len(options) >= 2 and len(options) <= 20:
                                ends_at = (datetime.now() + timedelta(hours=duration)).isoformat()
                                poll_data = {
                                    'question': question,
                                    'options': options,
                                    'ends_at': ends_at
                                }
                                
                                success, result = self.post_manager.create_post(
                                    st.session_state.user_id,
                                    question,
                                    post_type='poll',
                                    poll_data=poll_data
                                )
                                
                                if success:
                                    st.session_state.show_create_modal = False
                                    st.rerun()
                                else:
                                    st.error(result)
                            else:
                                st.error("Need 2-20 options")
                        else:
                            st.error("Please fill all fields")
                
                with col2:
                    if st.form_submit_button("Cancel", use_container_width=True):
                        st.session_state.show_create_modal = False
                        st.rerun()
        
        if st.button("✕ Close", key="modal_close", use_container_width=True):
            st.session_state.show_create_modal = False
            st.rerun()
        
        st.markdown('</div></div>', unsafe_allow_html=True)
    
    def render_bottom_nav(self):
        """Render bottom navigation bar"""
        current_tab = st.session_state.current_tab
        
        st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
        
        tabs = [
            ('feed', '🏠', 'Feed'),
            ('explore', '🔍', 'Explore'),
            ('create', '➕', 'Post'),
            ('chats', '💬', 'Chats'),
            ('profile', '👤', 'Profile')
        ]
        
        cols = st.columns(5)
        for i, (tab, icon, label) in enumerate(tabs):
            with cols[i]:
                if tab == 'create':
                    if st.button(icon, key=f"nav_{tab}", use_container_width=True):
                        st.session_state.show_create_modal = True
                        st.rerun()
                elif current_tab == tab:
                    st.markdown(f"""
                    <div style="text-align:center;color:#FFD700;font-weight:600;padding:4px 0;">
                        <div style="font-size:1.3rem;">{icon}</div>
                        <div style="font-size:0.55rem;">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    if st.button(icon, key=f"nav_{tab}", use_container_width=True):
                        st.session_state.current_tab = tab
                        st.session_state.show_create_modal = False
                        st.session_state.active_chat = None
                        st.rerun()
                    st.markdown(f"""
                    <div style="text-align:center;font-size:0.48rem;color:#94a3b8;margin-top:-6px;">
                        {label}
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
                glow = "box-shadow:0 0 15px rgba(255,215,0,0.5);" if is_premium else ""
                return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border};flex-shrink:0;{glow}" alt="{username}">'
            except:
                pass
        
        color = Utils.get_avatar_color(username)
        initials = Utils.get_initials(username)
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:{color};display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:{size*0.4}px;flex-shrink:0;border:2px solid #FFD700;">{initials}</div>'
    
    def _get_current_theme(self) -> Dict:
        """Get current user's theme"""
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                theme_key = user.get('theme', 'midnight')
                return THEMES.get(theme_key, THEMES['midnight'])
        return THEMES['midnight']
    
    def _get_current_wallpaper(self) -> Dict:
        """Get current user's wallpaper"""
        if st.session_state.auth and st.session_state.user_id:
            user = self.user_manager.get_user_by_username(st.session_state.username)
            if user:
                wp_key = user.get('wallpaper', 'wp_socialite')
                return WALLPAPERS.get(wp_key, WALLPAPERS['wp_socialite'])
        return WALLPAPERS['wp_socialite']
    
    def _get_follower_count(self, user_id: int) -> int:
        """Get follower count for a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM follows 
                    WHERE following_id = ? AND is_accepted = 1
                """, (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0
    
    def _get_following_count(self, user_id: int) -> int:
        """Get following count for a user"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM follows 
                    WHERE follower_id = ? AND is_accepted = 1
                """, (user_id,))
                return cursor.fetchone()['count']
        except:
            return 0

# ========== MAIN APPLICATION ==========
def main():
    """Main application entry point"""
    try:
        # Initialize database and create backup
        db = DatabaseManager()
        db.backup()
        
        # Initialize and render UI
        app = SocialiteUI()
        app.render()
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        st.error("""
        An error occurred. Please refresh the page.
        
        If the problem persists, try clearing your browser cache or contact support.
        """)

if __name__ == "__main__":
    main()
