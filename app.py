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
from tenacity import retry, stop_after_attempt, wait_exponential

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
    """Ultimate configuration for Socialite"""
    APP_NAME = "Socialite"
    APP_SLOGAN = "Where Luxury Meets Connection"
    APP_VERSION = "7.0.0"
    APP_BUILD = "2024.4"
    
    # Brand Logo (from Google Drive)
    LOGO_URL = "https://drive.google.com/uc?export=view&id=1Rxb3t3yLEdrqS6hWZJw4DPg6T1PNSkKb"
    
    # Directory Structure
    DATA_DIR = pathlib.Path("data")
    DB_PATH = DATA_DIR / "socialite_v7.db"
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
    
    # NEW: Connection Pool Settings
    DB_POOL_SIZE = 10
    DB_POOL_TIMEOUT = 5

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
        logging.FileHandler(Config.LOGS_DIR / 'socialite_v7.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== CUSTOM EXCEPTIONS ==========
class SocialiteError(Exception):
    """Base exception for Socialite"""
    pass

class AuthenticationError(SocialiteError):
    """Authentication related errors"""
    pass

class ValidationError(SocialiteError):
    """Validation related errors"""
    pass

class DatabaseError(SocialiteError):
    """Database related errors"""
    pass

# ========== CONNECTION POOL ==========
class DatabasePool:
    """Enhanced connection pool for better database performance"""
    
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
        """Create a new database connection"""
        try:
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
            conn.execute("PRAGMA mmap_size=536870912")
            conn.execute("PRAGMA busy_timeout=5000")
            self._created_count += 1
            return conn
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            raise DatabaseError(f"Connection creation failed: {e}")
    
    def get_connection(self, timeout=None):
        """Get a connection from the pool with retry"""
        if timeout is None:
            timeout = Config.DB_POOL_TIMEOUT
        
        try:
            # Try to get from pool
            conn = self._pool.get_nowait()
            # Check if connection is still valid
            try:
                conn.execute("SELECT 1")
                return conn
            except:
                # Connection is dead, create new one
                try:
                    conn.close()
                except:
                    pass
                return self._create_connection()
        except queue.Empty:
            # Pool is empty, create new if under limit
            with self._pool_lock:
                if self._created_count < Config.DB_POOL_SIZE:
                    return self._create_connection()
                else:
                    # Wait for available connection
                    try:
                        return self._pool.get(timeout=timeout)
                    except queue.Empty:
                        raise DatabaseError("Connection pool exhausted")
    
    def return_connection(self, conn):
        """Return connection to the pool"""
        if conn is None:
            return
        try:
            # Check if connection is still valid
            conn.execute("SELECT 1")
            # Try to return to pool
            try:
                self._pool.put_nowait(conn)
            except queue.Full:
                # Pool is full, close connection
                conn.close()
                with self._pool_lock:
                    self._created_count -= 1
        except:
            # Connection is dead, close it
            try:
                conn.close()
            except:
                pass
            with self._pool_lock:
                self._created_count -= 1
    
    @contextmanager
    def connection_context(self):
        """Context manager for connection handling"""
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
        """Close all connections in pool"""
        while True:
            try:
                conn = self._pool.get_nowait()
                try:
                    conn.close()
                except:
                    pass
            except queue.Empty:
                break

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
        self.pool = DatabasePool()
        self._init_db()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager using pool"""
        with self.pool.connection_context() as conn:
            yield conn
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def execute_with_retry(self, operation, *args, **kwargs):
        """Execute database operation with retry logic"""
        with self.get_connection() as conn:
            return operation(conn, *args, **kwargs)
    
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
            
            # Create indexes and other tables (simplified for brevity - keep all your existing tables)
            self._create_indexes(cursor)
            
            # Create FTS table for better search
            try:
                cursor.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
                        text, location, content='posts', content_rowid='rowid'
                    )
                """)
            except:
                pass
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def _create_indexes(self, cursor):
        """Create all performance indexes"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_status ON users(account_status)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(post_type)",
            "CREATE INDEX IF NOT EXISTS idx_posts_visibility ON posts(visibility)",
            "CREATE INDEX IF NOT EXISTS idx_posts_deleted ON posts(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)",
            "CREATE INDEX IF NOT EXISTS idx_comments_user ON comments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_chat ON messages(chat_id)",
            "CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")

# ========== ENHANCED STREAMLIT UI WITH WORKING NAVIGATION ==========
class SocialiteUI:
    """Enhanced Streamlit UI with working navigation"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.user_manager = UserManager(self.db)
        self.post_manager = PostManager(self.db)
        self.chat_manager = ChatManager(self.db)
        self.pool = DatabasePool()
        self._init_session()
    
    def _init_session(self):
        """Initialize session state with navigation tracking"""
        defaults = {
            'auth': False,
            'user_id': None,
            'username': None,
            'session_token': None,
            'csrf_token': None,
            'current_tab': 'feed',
            'previous_tab': None,
            'active_chat': None,
            'active_group': None,
            'show_create_modal': False,
            'show_emoji_picker': False,
            'show_gif_picker': False,
            'show_sticker_picker': False,
            'feed_page': 1,
            'show_comments_for': None,
            'nav_history': [],
            'search_query': '',
            'notifications_unread': 0,
        }
        for k, v in defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v
        
        # Initialize navigation state
        if 'nav_state' not in st.session_state:
            st.session_state.nav_state = {
                'feed': False,
                'explore': False,
                'chats': False,
                'marketplace': False,
                'notifications': False,
                'profile': False
            }
    
    def render(self):
        """Main render method"""
        if not st.session_state.auth:
            self.render_auth()
            return
        
        # Update last active
        if st.session_state.user_id:
            self.user_manager.update_last_active(st.session_state.user_id)
        
        # Handle navigation
        self.handle_navigation()
        
        self.inject_styles()
        self.render_top_nav()
        
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Render current tab
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
        
        # Render modals
        if st.session_state.show_create_modal:
            self.render_create_modal()
    
    def handle_navigation(self):
        """Handle navigation with query parameters for better state management"""
        # Check URL query parameters
        query_params = st.query_params
        if 'tab' in query_params:
            tab = query_params['tab']
            if tab in ['feed', 'explore', 'chats', 'marketplace', 'notifications', 'profile']:
                st.session_state.current_tab = tab
        
        # Update unread notifications count
        if st.session_state.auth and st.session_state.user_id:
            notifications = self.user_manager.get_notifications(st.session_state.user_id, 1)
            st.session_state.notifications_unread = sum(1 for n in notifications if not n.get('is_read'))
    
    def navigate_to(self, tab: str):
        """Navigate to a specific tab with state tracking"""
        if tab != st.session_state.current_tab:
            st.session_state.previous_tab = st.session_state.current_tab
            st.session_state.nav_history.append(st.session_state.current_tab)
            st.session_state.current_tab = tab
            # Update URL
            st.query_params['tab'] = tab
            st.rerun()
    
    def go_back(self):
        """Navigate back to previous tab"""
        if st.session_state.nav_history:
            previous = st.session_state.nav_history.pop()
            st.session_state.current_tab = previous
            st.query_params['tab'] = previous
            st.rerun()
    
    def render_top_nav(self):
        """Render top navigation with working buttons"""
        current_tab = st.session_state.current_tab
        user = self.user_manager.get_user_by_username(st.session_state.username)
        if not user:
            return
        
        unread_count = st.session_state.notifications_unread
        
        # Create columns for layout
        nav_col1, nav_col2, nav_col3 = st.columns([1, 3, 1])
        
        with nav_col1:
            # Logo and brand
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; padding: 8px 0;">
                <img src="{Config.LOGO_URL}" style="width: 36px; height: 36px; border-radius: 50%; 
                     object-fit: cover; border: 2px solid #FFD700; box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);">
                <span style="font-weight: 800; font-size: 1.1rem; 
                           background: linear-gradient(135deg, #FFD700 0%, #FFA500 50%, #FFD700 100%);
                           -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Socialite
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with nav_col2:
            # Navigation buttons in a row
            cols = st.columns(6)
            
            # Define navigation items
            nav_items = [
                ('feed', '🏠', 'Feed'),
                ('explore', '🔍', 'Explore'),
                ('chats', '💬', 'Chats'),
                ('marketplace', '🛒', 'Shop'),
                ('profile', '👤', 'Profile'),
                ('notifications', '🔔', 'Alerts')
            ]
            
            for i, (tab, icon, label) in enumerate(nav_items):
                with cols[i]:
                    # Determine if this is the active tab
                    is_active = current_tab == tab
                    button_style = "primary" if is_active else "secondary"
                    
                    # Create button with badge for notifications
                    button_label = icon
                    if tab == 'notifications' and unread_count > 0:
                        button_label = f"{icon} ({unread_count})"
                    
                    if st.button(
                        button_label,
                        key=f"nav_btn_{tab}",
                        use_container_width=True,
                        type=button_style,
                        help=label
                    ):
                        self.navigate_to(tab)
        
        with nav_col3:
            # User avatar and quick actions
            avatar_html = self.render_avatar_html(user, 32)
            st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; justify-content: flex-end;">
                {avatar_html}
                <span style="color: #f1f5f9; font-weight: 600;">@{html.escape(user['username'])}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Divider
        st.markdown("""<hr style="margin: 5px 0; border-color: rgba(255,215,0,0.2);">""", unsafe_allow_html=True)
    
    def inject_styles(self):
        """Inject comprehensive styles with skeleton loading"""
        theme = self._get_current_theme()
        
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
            background: {theme['gradient']} !important;
            min-height: 100vh !important;
        }}
        
        .main {{ min-height: 100vh !important; }}
        .block-container {{ 
            padding: 0 !important; 
            margin: 0 !important; 
            max-width: 100% !important; 
        }}
        
        /* Main content */
        .main-content {{
            padding: 12px 16px !important;
            max-width: 800px !important;
            margin: 0 auto !important;
        }}
        
        /* Buttons */
        .stButton > button {{
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 500 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            min-height: auto !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}
        
        .stButton > button:active {{
            transform: translateY(0) !important;
        }}
        
        /* Primary button */
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
            color: #1a0033 !important;
            border: none !important;
            font-weight: 700 !important;
        }}
        
        /* Secondary button */
        .stButton > button[kind="secondary"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 215, 0, 0.3) !important;
            color: {theme['text']} !important;
        }}
        
        /* Input fields */
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
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3) !important;
            background: rgba(255, 255, 255, 0.15) !important;
        }}
        
        /* Cards */
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
        
        /* Skeleton loading */
        .skeleton {{
            background: linear-gradient(90deg, 
                rgba(255,255,255,0.05) 25%, 
                rgba(255,255,255,0.1) 50%, 
                rgba(255,255,255,0.05) 75%
            ) !important;
            background-size: 200% 100% !important;
            animation: skeleton-loading 1.5s infinite !important;
            border-radius: 8px !important;
        }}
        
        @keyframes skeleton-loading {{
            0% {{ background-position: 200% 0; }}
            100% {{ background-position: -200% 0; }}
        }}
        
        .skeleton-avatar {{
            width: 40px !important;
            height: 40px !important;
            border-radius: 50% !important;
        }}
        
        .skeleton-text {{
            height: 16px !important;
            margin: 8px 0 !important;
            width: 80% !important;
        }}
        
        .skeleton-text.short {{
            width: 60% !important;
        }}
        
        /* Scrollbar */
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
        
        /* Modal */
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
        
        /* Responsive */
        @media (max-width: 640px) {{
            .main-content {{
                padding: 8px 10px !important;
            }}
        }}
        </style>
        """, unsafe_allow_html=True)
    
    def render_skeleton_card(self):
        """Render skeleton loading card"""
        st.markdown("""
        <div class="card">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div class="skeleton skeleton-avatar"></div>
                <div style="flex: 1;">
                    <div class="skeleton skeleton-text" style="width: 120px;"></div>
                    <div class="skeleton skeleton-text short" style="width: 80px;"></div>
                </div>
            </div>
            <div class="skeleton skeleton-text" style="width: 90%;"></div>
            <div class="skeleton skeleton-text" style="width: 70%;"></div>
            <div class="skeleton skeleton-text short" style="width: 50%; margin-top: 16px;"></div>
        </div>
        """, unsafe_allow_html=True)
    
    def render_feed(self):
        """Render feed page with skeleton loading and improved UI"""
        st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
        
        # Header with back button if needed
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            if st.session_state.previous_tab:
                if st.button("← Back", key="feed_back", use_container_width=True):
                    self.go_back()
        with col2:
            st.markdown("""
            <h2 style="color: #FFD700; text-align: center; margin: 10px 0;">
                ✨ Your Feed
            </h2>
            """, unsafe_allow_html=True)
        with col3:
            if st.button("✚ Post", key="create_post_btn", use_container_width=True, type="primary"):
                st.session_state.show_create_modal = True
                st.rerun()
        
        # Quick post creator
        with st.expander("Create Quick Post", expanded=False):
            with st.form("quick_post_form", clear_on_submit=True):
                quick_text = st.text_area(
                    "What's on your mind?",
                    max_chars=Config.MAX_POST_LENGTH,
                    height=80,
                    placeholder="Share your thoughts..."
                )
                col1, col2 = st.columns(2)
                with col1:
                    quick_image = st.file_uploader("📷 Image", type=['png', 'jpg', 'jpeg', 'gif', 'webp'])
                with col2:
                    if st.form_submit_button("Post", use_container_width=True, type="primary"):
                        if quick_text or quick_image:
                            success, result = self.post_manager.create_post(
                                st.session_state.user_id,
                                text=quick_text,
                                media_file=quick_image
                            )
                            if success:
                                st.success("Posted successfully! ✨")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error(f"Failed: {result}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Load posts with loading state
        with st.spinner("Loading posts..."):
            # Show skeletons while loading
            loading_placeholder = st.empty()
            with loading_placeholder.container():
                for _ in range(3):
                    self.render_skeleton_card()
            
            posts = self.post_manager.get_feed_posts(
                st.session_state.user_id, 
                page=st.session_state.feed_page
            )
            
            # Clear skeletons
            loading_placeholder.empty()
        
        if not posts:
            # Empty state
            st.markdown(f"""
            <div style="text-align: center; padding: 3rem 1rem; color: #94a3b8;">
                <div style="font-size: 5rem; animation: float 3s ease-in-out infinite;">👑</div>
                <h3 style="color: #FFD700; margin-top: 1rem;">Welcome to Socialite!</h3>
                <p style="font-size: 1rem;">Follow interesting people and create your first post!</p>
                <p style="font-size: 0.8rem;">Share photos, videos, create polls, and more!</p>
                <button onclick="document.getElementById('explore_nav').click()" 
                        style="background: linear-gradient(135deg, #FFD700, #FFA500); 
                               color: #1a0033; border: none; padding: 10px 20px; 
                               border-radius: 8px; margin-top: 1rem; cursor: pointer;">
                    Explore Users 🔍
                </button>
            </div>
            
            <style>
            @keyframes float {{
                0%, 100% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
            }}
            </style>
            """, unsafe_allow_html=True)
        else:
            # Render posts
            for post in posts:
                self.render_post_card(post)
            
            # Load more button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("📜 Load More Posts", use_container_width=True, key="load_more"):
                    st.session_state.feed_page += 1
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def render_post_card(self, post: Dict):
        """Render enhanced post card with improved layout"""
        with st.container():
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            
            # Header with user info
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px;">
                    {self.render_avatar_html(post, 40)}
                    <div>
                        <div style="color: #f1f5f9; font-weight: 600;">
                            @{html.escape(post['username'])}
                            {'<span style="color: #FFD700;"> ✓</span>' if post.get('is_verified') else ''}
                            {'<span style="color: #FFD700;"> 👑</span>' if post.get('is_premium') else ''}
                        </div>
                        <div style="color: #94a3b8; font-size: 0.75rem;">
                            {Utils.format_timestamp(post['timestamp'])}
                            {' · 📍 ' + html.escape(post['location']) if post.get('location') else ''}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if post['username'] == st.session_state.username:
                    if st.button("⋯", key=f"more_{post['id']}", help="More options"):
                        st.session_state.show_comments_for = None
        
            # Post text with hashtags and mentions highlighted
            if post.get('text'):
                text = html.escape(post['text'])
                # Highlight hashtags
                text = re.sub(r'#(\w+)', r'<span style="color:#FFD700; font-weight:600;">#\1</span>', text)
                # Highlight mentions
                text = re.sub(r'@(\w+)', r'<span style="color:#64ffda; font-weight:600;">@\1</span>', text)
                st.markdown(f"""
                <div style="color: #e2e8f0; font-size: 0.95rem; line-height: 1.6; 
                            padding: 8px 0; word-wrap: break-word; white-space: pre-wrap;">
                    {text}
                </div>
                """, unsafe_allow_html=True)
            
            # Media - Image with lazy loading
            if post.get('media_data') and post.get('media_type') == 'image':
                try:
                    image_bytes = base64.b64decode(post['media_data'])
                    st.image(image_bytes, use_column_width=True)
                except:
                    st.warning("Unable to load image")
            
            # Media - Video
            if post.get('video_data'):
                try:
                    video_bytes = base64.b64decode(post['video_data'])
                    st.video(video_bytes)
                except:
                    st.warning("Unable to load video")
            
            # Media - Audio
            if post.get('audio_data'):
                try:
                    audio_bytes = base64.b64decode(post['audio_data'])
                    st.audio(audio_bytes)
                except:
                    st.warning("Unable to load audio")
            
            # Stats
            like_count = post.get('like_count', 0)
            comment_count = post.get('comment_count', 0)
            
            # Action buttons in a row
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
            
            with col1:
                if st.button(f"❤️ {Utils.format_number(like_count)}", 
                           key=f"like_{post['id']}", 
                           use_container_width=True,
                           help="Like"):
                    success, result = self.post_manager.like_post(post['id'], st.session_state.user_id)
                    if success:
                        st.toast(f"Post {result}!")
                        st.rerun()
            
            with col2:
                if st.button(f"💬 {Utils.format_number(comment_count)}", 
                           key=f"comment_{post['id']}", 
                           use_container_width=True,
                           help="Comment"):
                    st.session_state.show_comments_for = post['id'] if st.session_state.show_comments_for != post['id'] else None
                    st.rerun()
            
            with col3:
                if st.button("🔄", key=f"share_{post['id']}", 
                           use_container_width=True,
                           help="Share"):
                    st.toast("Post shared! 🔄")
            
            with col4:
                if st.button("🔖", key=f"save_{post['id']}", 
                           use_container_width=True,
                           help="Save"):
                    st.toast("Saved to collection! 🔖")
            
            with col5:
                if st.button("⚡", key=f"boost_{post['id']}", 
                           use_container_width=True,
                           help="Boost"):
                    st.toast("Post boosted! ⚡")
            
            # Comments section
            if st.session_state.get('show_comments_for') == post['id']:
                st.markdown("""<hr style="border-color: rgba(255,215,0,0.1);">""", unsafe_allow_html=True)
                self.render_comments_section(post['id'])
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    def render_comments_section(self, post_id: str):
        """Render comments section with improved UI"""
        st.markdown("<h4 style='color: #FFD700;'>💬 Comments</h4>", unsafe_allow_html=True)
        
        # Add comment form
        with st.form(f"comment_form_{post_id}", clear_on_submit=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                comment_text = st.text_input(
                    "Write a comment...",
                    key=f"comment_input_{post_id}",
                    label_visibility="collapsed",
                    placeholder="Write a comment..."
                )
            with col2:
                submit_btn = st.form_submit_button("Post 💬", use_container_width=True, type="primary")
            
            if submit_btn and comment_text.strip():
                success, result = self.post_manager.add_comment(
                    post_id, st.session_state.user_id, comment_text
                )
                if success:
                    st.toast("Comment posted!")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("Failed to post comment")
        
        # Show existing comments
        comments = self.post_manager.get_comments(post_id)
        
        if comments:
            for comment in comments[:10]:  # Show first 10 comments
                st.markdown(f"""
                <div style="display: flex; gap: 10px; padding: 8px; 
                            background: rgba(255,255,255,0.02); border-radius: 8px; margin: 4px 0;">
                    {self.render_avatar_html(comment, 28)}
                    <div style="flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                            <span style="color: #FFD700; font-weight: 600; font-size: 0.8rem;">
                                @{html.escape(comment['username'])}
                            </span>
                            <span style="color: #64748b; font-size: 0.7rem;">
                                {Utils.format_timestamp(comment['timestamp'])}
                            </span>
                        </div>
                        <p style="color: #e2e8f0; font-size: 0.85rem; margin: 0;">
                            {html.escape(comment['text'])}
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 16px; color: #94a3b8;">
                No comments yet. Be the first to comment!
            </div>
            """, unsafe_allow_html=True)
    
    # Keep all your other render methods (render_explore, render_chats, etc.)
    # They remain the same but work with the new navigation system
    
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
        
        return f'''<div style="width:{size}px;height:{size}px;border-radius:50%;
                background:linear-gradient(135deg, {color}, {color}dd);
                display:flex;align-items:center;justify-content:center;
                color:white;font-weight:700;font-size:{size*0.35}px;
                flex-shrink:0;border:2px solid rgba(255,215,0,0.5);">
            {initials}
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
                }
                return themes.get(theme_key, themes['midnight'])
        return {"name": "Midnight", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)"}

# Keep all your existing classes (Utils, SecurityUtils, PostManager, etc.) as they are
# Just add the navigation improvements shown above

# ========== MAIN APPLICATION ENTRY POINT ==========
def main():
    """Main application entry point with enhanced error handling"""
    try:
        # Initialize database with connection pool
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
        st.error(f"""
        ## ⚠️ Application Error
        
        An unexpected error occurred: {str(e)}
        
        Please try:
        1. **Refresh the page**
        2. **Clear your browser cache**
        3. **Contact support** if the problem persists
        """)
    finally:
        # Cleanup connection pool
        try:
            pool = DatabasePool()
            pool.close_all()
        except:
            pass

if __name__ == "__main__":
    main()
