import streamlit as st
import json
import os
import html
import hashlib
import pathlib
from datetime import datetime, timedelta
import uuid
import base64
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageColor, ImageEnhance
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

# Must be first Streamlit command
st.set_page_config(
    page_title="Socialite - Premium Social Network",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Socialite - The Premium Social Experience"
    }
)

# ========== BRAND EMOJI GENERATOR ==========
def generate_socialite_emoji() -> str:
    """
    Generate the Socialite brand emoji as an SVG:
    - A luxurious golden world globe in the background
    - A male socialite figure on the left
    - A female socialite figure on the right
    - Both figures are elegant and luxurious
    """
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
  <defs>
    <!-- Globe Gradient -->
    <radialGradient id="globeGrad" cx="50%" cy="40%" r="50%">
      <stop offset="0%" style="stop-color:#4A90D9;stop-opacity:1"/>
      <stop offset="40%" style="stop-color:#2E6DB4;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#1A3A5C;stop-opacity:1"/>
    </radialGradient>
    <!-- Gold Gradient -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1"/>
      <stop offset="25%" style="stop-color:#FFC107;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#FFD700;stop-opacity:1"/>
      <stop offset="75%" style="stop-color:#FFB300;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#FFD700;stop-opacity:1"/>
    </linearGradient>
    <!-- Male Figure Gradient -->
    <linearGradient id="maleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2C3E50;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#34495E;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#1A252F;stop-opacity:1"/>
    </linearGradient>
    <!-- Female Figure Gradient -->
    <linearGradient id="femaleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#C2185B;stop-opacity:1"/>
      <stop offset="50%" style="stop-color:#E91E63;stop-opacity:1"/>
      <stop offset="100%" style="stop-color:#880E4F;stop-opacity:1"/>
    </linearGradient>
    <!-- Glow Filter -->
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge>
        <feMergeNode in="coloredBlur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <!-- Inner Shadow -->
    <filter id="innerShadow">
      <feGaussianBlur in="SourceAlpha" stdDeviation="2" result="blur"/>
      <feOffset dx="0" dy="1"/>
      <feComposite in2="SourceAlpha" operator="arithmetic" k2="-1" k3="1"/>
      <feFlood flood-color="rgba(0,0,0,0.3)"/>
      <feComposite operator="in" in2="SourceGraphic"/>
      <feMerge>
        <feMergeNode in="SourceGraphic"/>
        <feMergeNode/>
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
  <!-- Globe Continents (simplified) -->
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
    <!-- Mouth -->
    <path d="M-3,9 Q0,11 3,9" fill="none" stroke="#1A1A1A" stroke-width="0.8"/>
    <!-- Crown -->
    <polygon points="-8,-16 -10,-22 -5,-20 0,-25 5,-20 10,-22 8,-16" fill="url(#goldGrad)" stroke="#B8860B" stroke-width="0.5"/>
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
    <polygon points="-6,-16 -8,-20 -4,-18 0,-23 4,-18 8,-20 6,-16" fill="url(#goldGrad)" stroke="#B8860B" stroke-width="0.5"/>
    <!-- Diamond -->
    <polygon points="0,-20 -1,-18 0,-16 1,-18" fill="#B9F2FF"/>
    <!-- Necklace -->
    <path d="M-8,15 Q0,20 8,15" fill="none" stroke="#FFD700" stroke-width="1"/>
    <circle cx="0" cy="17" r="1.5" fill="#B9F2FF"/>
    <!-- Earrings -->
    <circle cx="-12" cy="8" r="1.5" fill="#FFD700"/>
    <circle cx="12" cy="8" r="1.5" fill="#FFD700"/>
  </g>
  
  <!-- Sparkles -->
  <g fill="#FFD700" filter="url(#glow)">
    <polygon points="30,30 32,35 37,37 32,39 30,44 28,39 23,37 28,35" transform="scale(0.5)"/>
    <polygon points="170,30 172,35 177,37 172,39 170,44 168,39 163,37 168,35" transform="scale(0.5)"/>
    <polygon points="30,160 32,165 37,167 32,169 30,174 28,169 23,167 28,165" transform="scale(0.5)"/>
    <polygon points="170,160 172,165 177,167 172,169 170,174 168,169 163,167 168,165" transform="scale(0.5)"/>
  </g>
  
  <!-- Crown on top of globe -->
  <g transform="translate(100, 12)">
    <polygon points="0,-10 -15,-20 -10,-15 -5,-25 0,-15 5,-25 10,-15 15,-20" fill="url(#goldGrad)" stroke="#B8860B" stroke-width="1" filter="url(#glow)"/>
  </g>
</svg>"""
    return svg

def get_socialite_emoji_base64() -> str:
    """Get the Socialite emoji as base64 encoded SVG"""
    svg = generate_socialite_emoji()
    return base64.b64encode(svg.encode()).decode()

def get_socialite_emoji_html(size: int = 120) -> str:
    """Get the Socialite emoji as HTML img tag"""
    b64 = get_socialite_emoji_base64()
    return f'<img src="data:image/svg+xml;base64,{b64}" width="{size}" height="{size}" alt="Socialite" style="filter:drop-shadow(0 0 20px rgba(255,215,0,0.5));">'

# ========== CONSTANTS ==========
APP_NAME = "Socialite"
APP_FULL_NAME = "Socialite - Premium Social Network"
APP_SLOGAN = "Where Luxury Meets Connection"
APP_VERSION = "3.0.0"
APP_EMOJI_B64 = get_socialite_emoji_base64()

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
WALLPAPERS_DIR = DATA_DIR / "wallpapers"
WALLPAPERS_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

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
FOLLOW_REQUESTS_FILE = DATA_DIR / "follow_requests.json"
BLOCKED_USERS_FILE = DATA_DIR / "blocked_users.json"
REPORTED_POSTS_FILE = DATA_DIR / "reported_posts.json"
VERIFIED_USERS_FILE = DATA_DIR / "verified_users.json"
PREMIUM_USERS_FILE = DATA_DIR / "premium_users.json"
HASHTAGS_FILE = DATA_DIR / "hashtags.json"
TRENDING_FILE = DATA_DIR / "trending.json"
ANALYTICS_FILE = DATA_DIR / "analytics.json"

MAX_POST_LENGTH = 5000
MAX_COMMENT_LENGTH = 1000
MAX_BIO_LENGTH = 500
MAX_MESSAGE_LENGTH = 5000
MAX_USERNAME_LENGTH = 30
MIN_PASSWORD_LENGTH = 8
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_AVATAR_SIZE = 10 * 1024 * 1024  # 10MB
MAX_MEDIA_PER_POST = 10
STORY_EXPIRY_HOURS = 24
MAX_FEED_POSTS = 10000
MAX_CHAT_MESSAGES = 10000
MAX_NOTIFICATIONS = 200
ONLINE_THRESHOLD_SECONDS = 300
ACTIVE_THRESHOLD_SECONDS = 60
CACHE_TTL_SECONDS = 60
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15
SESSION_TIMEOUT_HOURS = 24
MAX_GROUPS_PER_USER = 50
MAX_CHANNELS_PER_USER = 30
MAX_MEMBERS_PER_GROUP = 5000
MAX_SUBSCRIBERS_PER_CHANNEL = 100000
MAX_FOLLOWING = 10000
MAX_BLOCKED = 1000
MAX_SAVED_POSTS = 5000
MAX_REACTIONS_PER_POST = 100

# ========== AVATAR COLORS ==========
AVATAR_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD',
    '#98D8C8', '#F7B787', '#FF8A80', '#B388FF', '#FF5722', '#9C27B0',
    '#3F51B5', '#009688', '#FF9800', '#795548', '#607D8B', '#E91E63',
    '#00BCD4', '#8BC34A', '#FF4081', '#536DFE', '#00BFA5', '#FF6E40',
    '#7C4DFF', '#64FFDA', '#FFD740', '#40C4FF', '#B2FF59', '#FF80AB',
    '#82B1FF', '#EA80FC', '#69F0AE', '#FF8A80', '#B9F6CA', '#FFE57F',
    '#80D8FF', '#CCFF90', '#F48FB1', '#84FFFF', '#FFD180', '#A7FFEB',
    '#FF80AB', '#B388FF', '#8C9EFF', '#80CBC4', '#FFCC80', '#EA80FC'
]

# ========== LUXURY EMOJI REACTIONS ==========
LUXURY_REACTIONS = {
    "crown": {"emoji": "👑", "label": "Royal Approval", "color": "#FFD700", "glow": "#FFD700", "tier": "legendary"},
    "diamond": {"emoji": "💎", "label": "Priceless", "color": "#B9F2FF", "glow": "#00FFFF", "tier": "legendary"},
    "cheers": {"emoji": "🥂", "label": "Celebration", "color": "#FFE4B5", "glow": "#FFD700", "tier": "premium"},
    "tophat": {"emoji": "🎩", "label": "Distinguished", "color": "#1A1A1A", "glow": "#C0C0C0", "tier": "premium"},
    "sparkle": {"emoji": "✨", "label": "Magnificent", "color": "#FFF8DC", "glow": "#FFD700", "tier": "premium"},
    "fleur": {"emoji": "⚜️", "label": "Noble", "color": "#FFD700", "glow": "#FFA500", "tier": "legendary"},
    "fire": {"emoji": "🔥", "label": "Trending", "color": "#FF4500", "glow": "#FF6347", "tier": "standard"},
    "star": {"emoji": "🌟", "label": "Rising Star", "color": "#FFD700", "glow": "#FFFF00", "tier": "standard"},
    "love": {"emoji": "💖", "label": "Adored", "color": "#FF69B4", "glow": "#FF1493", "tier": "premium"},
    "trophy": {"emoji": "🏆", "label": "Champion", "color": "#FFD700", "glow": "#DAA520", "tier": "legendary"},
    "pearl": {"emoji": "🦪", "label": "Rare Find", "color": "#F5F5DC", "glow": "#FFE4E1", "tier": "premium"},
    "ruby": {"emoji": "💠", "label": "Gem Quality", "color": "#E0115F", "glow": "#FF1493", "tier": "legendary"},
}

# ========== STANDARD REACTIONS ==========
STANDARD_REACTIONS = {
    "like": {"emoji": "👍", "label": "Like"},
    "love": {"emoji": "❤️", "label": "Love"},
    "laugh": {"emoji": "😂", "label": "Laugh"},
    "wow": {"emoji": "😮", "label": "Wow"},
    "sad": {"emoji": "😢", "label": "Sad"},
    "angry": {"emoji": "😡", "label": "Angry"},
}

# ========== SVG AVATARS ==========
MALE_AVATAR_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
  <defs>
    <linearGradient id='mg' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#667eea'/>
      <stop offset='100%' style='stop-color:#764ba2'/>
    </linearGradient>
  </defs>
  <circle cx='50' cy='50' r='48' fill='url(#mg)' stroke='#FFD700' stroke-width='2.5'/>
  <circle cx='50' cy='36' r='15' fill='#F5DEB3'/>
  <ellipse cx='50' cy='75' rx='22' ry='16' fill='#F5DEB3'/>
  <circle cx='44' cy='34' r='2' fill='#1A1A1A'/>
  <circle cx='56' cy='34' r='2' fill='#1A1A1A'/>
  <path d='M46 40 Q50 44 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/>
  <path d='M35 30 Q50 15 65 30' fill='#2C1810'/>
  <polygon points='38,22 40,16 44,19 50,14 56,19 60,16 62,22' fill='#FFD700'/>
</svg>"""

FEMALE_AVATAR_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
  <defs>
    <linearGradient id='fg' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#f093fb'/>
      <stop offset='100%' style='stop-color:#f5576c'/>
    </linearGradient>
  </defs>
  <circle cx='50' cy='50' r='48' fill='url(#fg)' stroke='#FFD700' stroke-width='2.5'/>
  <circle cx='50' cy='36' r='14' fill='#FFE0BD'/>
  <ellipse cx='50' cy='72' rx='18' ry='15' fill='#FFE0BD'/>
  <circle cx='45' cy='34' r='2' fill='#1A1A1A'/>
  <circle cx='55' cy='34' r='2' fill='#1A1A1A'/>
  <path d='M46 40 Q50 43 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/>
  <path d='M47 41 Q50 44 53 41' fill='#E91E63'/>
  <path d='M32 25 Q25 15 28 8 Q35 18 40 22' fill='#8B4513'/>
  <path d='M68 25 Q75 15 72 8 Q65 18 60 22' fill='#8B4513'/>
  <path d='M28 8 Q25 0 30 -5 Q32 2 35 8' fill='#8B4513'/>
  <path d='M72 8 Q75 0 70 -5 Q68 2 65 8' fill='#8B4513'/>
  <polygon points='40,22 42,16 46,20 50,15 54,20 58,16 60,22' fill='#FFD700'/>
  <circle cx='50' cy='15' r='2' fill='#B9F2FF'/>
</svg>"""

PREMIUM_MALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
  <defs>
    <linearGradient id='pmg' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FFD700'/>
      <stop offset='50%' style='stop-color:#FFA500'/>
      <stop offset='100%' style='stop-color:#FFD700'/>
    </linearGradient>
    <filter id='glow'>
      <feGaussianBlur stdDeviation='2'/>
      <feMerge><feMergeNode/><feMergeNode in='SourceGraphic'/></feMerge>
    </filter>
  </defs>
  <circle cx='50' cy='50' r='48' fill='url(#pmg)' stroke='#FFFFFF' stroke-width='3' filter='url(#glow)'/>
  <circle cx='50' cy='36' r='15' fill='#F5DEB3'/>
  <ellipse cx='50' cy='75' rx='22' ry='16' fill='#F5DEB3'/>
  <circle cx='44' cy='34' r='2' fill='#1A1A1A'/>
  <circle cx='56' cy='34' r='2' fill='#1A1A1A'/>
  <path d='M46 40 Q50 44 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/>
  <polygon points='40,22 42,16 46,19 50,14 54,19 58,16 60,22' fill='#FF4500'/>
  <text x='50' y='92' text-anchor='middle' fill='#FFFFFF' font-size='10' font-weight='bold'>PREMIUM</text>
</svg>"""

PREMIUM_FEMALE_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>
  <defs>
    <linearGradient id='pfg' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#FFD700'/>
      <stop offset='50%' style='stop-color:#FF69B4'/>
      <stop offset='100%' style='stop-color:#FFD700'/>
    </linearGradient>
    <filter id='glow'>
      <feGaussianBlur stdDeviation='2'/>
      <feMerge><feMergeNode/><feMergeNode in='SourceGraphic'/></feMerge>
    </filter>
  </defs>
  <circle cx='50' cy='50' r='48' fill='url(#pfg)' stroke='#FFFFFF' stroke-width='3' filter='url(#glow)'/>
  <circle cx='50' cy='36' r='14' fill='#FFE0BD'/>
  <ellipse cx='50' cy='72' rx='18' ry='15' fill='#FFE0BD'/>
  <circle cx='45' cy='34' r='2' fill='#1A1A1A'/>
  <circle cx='55' cy='34' r='2' fill='#1A1A1A'/>
  <path d='M46 40 Q50 43 54 40' fill='none' stroke='#1A1A1A' stroke-width='1.5'/>
  <path d='M47 41 Q50 44 53 41' fill='#E91E63'/>
  <polygon points='40,22 42,16 46,20 50,15 54,20 58,16 60,22' fill='#FF4500'/>
  <text x='50' y='92' text-anchor='middle' fill='#FFFFFF' font-size='10' font-weight='bold'>PREMIUM</text>
</svg>"""

# ========== 24 THEMES ==========
THEMES = {
    "midnight": {"name": "Midnight Galaxy", "icon": "🌌", "bg": "#0a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f1f5f9", "secondary": "#94a3b8", "accent": "#818cf8", "gradient": "linear-gradient(135deg, #0a0a1a 0%, #1a1030 50%, #0d0d2b 100%)", "category": "dark"},
    "ocean": {"name": "Deep Ocean", "icon": "🌊", "bg": "#0a192f", "card": "rgba(255,255,255,0.05)", "text": "#e2e8f0", "secondary": "#8892b0", "accent": "#64ffda", "gradient": "linear-gradient(135deg, #0a192f 0%, #112240 50%, #1a365d 100%)", "category": "dark"},
    "sunset": {"name": "Golden Sunset", "icon": "🌅", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#ce93d8", "accent": "#ff4081", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2d1b4e 50%, #4a1942 100%)", "category": "warm"},
    "forest": {"name": "Enchanted Forest", "icon": "🌲", "bg": "#0a1a0a", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#81c784", "accent": "#4caf50", "gradient": "linear-gradient(135deg, #0a1a0a 0%, #1a2f1a 50%, #2d4e2d 100%)", "category": "nature"},
    "neon": {"name": "Neon Nights", "icon": "💜", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#ede7f6", "secondary": "#b39ddb", "accent": "#7c4dff", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)", "category": "dark"},
    "coffee": {"name": "Coffee Aroma", "icon": "☕", "bg": "#1a0f0a", "card": "rgba(255,255,255,0.04)", "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#8d6e63", "gradient": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)", "category": "warm"},
    "cherry": {"name": "Cherry Blossom", "icon": "🌸", "bg": "#1a0a1a", "card": "rgba(255,255,255,0.05)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#e91e63", "gradient": "linear-gradient(135deg, #1a0a1a 0%, #2e1a2e 50%, #4e2d4e 100%)", "category": "warm"},
    "mint": {"name": "Fresh Mint", "icon": "🌿", "bg": "#0a1a1a", "card": "rgba(255,255,255,0.04)", "text": "#e0f2f1", "secondary": "#80cbc4", "accent": "#00bfa5", "gradient": "linear-gradient(135deg, #0a1a1a 0%, #1a2e2e 50%, #2d4e4e 100%)", "category": "nature"},
    "royal": {"name": "Royal Purple", "icon": "👑", "bg": "#1a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#9c27b0", "gradient": "linear-gradient(135deg, #1a0a2e 0%, #2e1a4e 50%, #4e2d7a 100%)", "category": "dark"},
    "crimson": {"name": "Crimson Red", "icon": "❤️", "bg": "#1a0a0a", "card": "rgba(255,255,255,0.04)", "text": "#ffebee", "secondary": "#ef9a9a", "accent": "#f44336", "gradient": "linear-gradient(135deg, #1a0a0a 0%, #2e0f0f 50%, #4e1a1a 100%)", "category": "warm"},
    "arctic": {"name": "Arctic Frost", "icon": "❄️", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e3f2fd", "secondary": "#90caf9", "accent": "#2196f3", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)", "category": "cool"},
    "ember": {"name": "Burning Ember", "icon": "🔥", "bg": "#1a0f00", "card": "rgba(255,255,255,0.04)", "text": "#fff3e0", "secondary": "#ffcc80", "accent": "#ff9800", "gradient": "linear-gradient(135deg, #1a0f00 0%, #2e1a00 50%, #4e2d00 100%)", "category": "warm"},
    "plum": {"name": "Plum Garden", "icon": "🫐", "bg": "#1a0a1a", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#ce93d8", "accent": "#7b1fa2", "gradient": "linear-gradient(135deg, #1a0a1a 0%, #2e1a2e 50%, #4e2d4e 100%)", "category": "dark"},
    "teal": {"name": "Teal Paradise", "icon": "🦋", "bg": "#0a1a1a", "card": "rgba(255,255,255,0.04)", "text": "#e0f2f1", "secondary": "#80cbc4", "accent": "#009688", "gradient": "linear-gradient(135deg, #0a1a1a 0%, #1a2e2e 50%, #2d4e4e 100%)", "category": "cool"},
    "slate": {"name": "Dark Slate", "icon": "🪨", "bg": "#1a1a2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#9fa8da", "accent": "#5c6bc0", "gradient": "linear-gradient(135deg, #1a1a2e 0%, #2e2e4e 50%, #4e4e7a 100%)", "category": "dark"},
    "rosegold": {"name": "Rose Gold", "icon": "🌹", "bg": "#1a0f1a", "card": "rgba(255,255,255,0.05)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#c2185b", "gradient": "linear-gradient(135deg, #1a0f1a 0%, #2e1a2e 50%, #4e2d4e 100%)", "category": "warm"},
    "midnightblue": {"name": "Midnight Blue", "icon": "🌃", "bg": "#0f0f2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#7986cb", "accent": "#3f51b5", "gradient": "linear-gradient(135deg, #0f0f2e 0%, #1a1a4e 50%, #2d2d7a 100%)", "category": "dark"},
    "chocolate": {"name": "Dark Chocolate", "icon": "🍫", "bg": "#1a1005", "card": "rgba(255,255,255,0.04)", "text": "#efebe9", "secondary": "#bcaaa4", "accent": "#795548", "gradient": "linear-gradient(135deg, #1a1005 0%, #2e1a0a 50%, #4e2d15 100%)", "category": "warm"},
    "lavender": {"name": "Lavender Fields", "icon": "💐", "bg": "#1a0f2e", "card": "rgba(255,255,255,0.04)", "text": "#f3e5f5", "secondary": "#b39ddb", "accent": "#673ab7", "gradient": "linear-gradient(135deg, #1a0f2e 0%, #2e1a4e 50%, #4e2d7a 100%)", "category": "dark"},
    "aqua": {"name": "Aqua Marine", "icon": "🐠", "bg": "#0a1a2e", "card": "rgba(255,255,255,0.05)", "text": "#e0f7fa", "secondary": "#80deea", "accent": "#00bcd4", "gradient": "linear-gradient(135deg, #0a1a2e 0%, #1a2e4e 50%, #2d4e7a 100%)", "category": "cool"},
    "coral": {"name": "Coral Reef", "icon": "🐚", "bg": "#1a0a0f", "card": "rgba(255,255,255,0.04)", "text": "#fce4ec", "secondary": "#f48fb1", "accent": "#ff6f61", "gradient": "linear-gradient(135deg, #1a0a0f 0%, #2e1a1a 50%, #4e2d2d 100%)", "category": "warm"},
    "sage": {"name": "Sage Green", "icon": "🌱", "bg": "#0f1a0f", "card": "rgba(255,255,255,0.04)", "text": "#e8f5e9", "secondary": "#a5d6a7", "accent": "#66bb6a", "gradient": "linear-gradient(135deg, #0f1a0f 0%, #1a2e1a 50%, #2d4e2d 100%)", "category": "nature"},
    "indigo": {"name": "Indigo Night", "icon": "💙", "bg": "#0a0a2e", "card": "rgba(255,255,255,0.04)", "text": "#e8eaf6", "secondary": "#9fa8da", "accent": "#3949ab", "gradient": "linear-gradient(135deg, #0a0a2e 0%, #1a1a4e 50%, #2d2d7a 100%)", "category": "dark"},
    "peach": {"name": "Peach Dream", "icon": "🍑", "bg": "#1a0f0a", "card": "rgba(255,255,255,0.04)", "text": "#fff3e0", "secondary": "#ffcc80", "accent": "#ff7043", "gradient": "linear-gradient(135deg, #1a0f0a 0%, #2e1a0f 50%, #4e2d1a 100%)", "category": "warm"},
}

# ========== 30 WALLPAPERS ==========
WALLPAPERS = {
    "wp_socialite": {"name": "Socialite Luxury", "icon": "👑", "url": None, "gradient": "linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #2d0050 50%, #1a0033 75%, #0a0015 100%)", "category": "luxury"},
    "wp_gold": {"name": "Pure Gold", "icon": "✨", "url": None, "gradient": "linear-gradient(135deg, #1a0f00 0%, #3d2200 25%, #5a3500 50%, #3d2200 75%, #1a0f00 100%)", "category": "luxury"},
    "wp_purple": {"name": "Purple Haze", "icon": "💜", "url": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1200&q=80"},
    "wp_nebula": {"name": "Cosmic Nebula", "icon": "🌌", "url": "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=1200&q=80"},
    "wp_ocean": {"name": "Ocean Waves", "icon": "🌊", "url": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=1200&q=80"},
    "wp_stars": {"name": "Starry Mountains", "icon": "🏔️", "url": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&q=80"},
    "wp_cherry": {"name": "Cherry Blossoms", "icon": "🌸", "url": "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1200&q=80"},
    "wp_sunset": {"name": "Sunset Beach", "icon": "🌅", "url": "https://images.unsplash.com/photo-1534274988757-a28bf1a57c17?w=1200&q=80"},
    "wp_forest": {"name": "Forest Path", "icon": "🌿", "url": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&q=80"},
    "wp_city": {"name": "City Lights", "icon": "🏙️", "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=1200&q=80"},
    "wp_lava": {"name": "Lava Flow", "icon": "🔥", "url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1200&q=80"},
    "wp_cyber": {"name": "Cyber Punk", "icon": "🎨", "url": "https://images.unsplash.com/photo-1515634928625-85bc09c9cbba?w=1200&q=80"},
    "wp_beach": {"name": "Tropical Beach", "icon": "🏝️", "url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&q=80"},
    "wp_aurora": {"name": "Aurora Borealis", "icon": "❄️", "url": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=1200&q=80"},
    "wp_autumn": {"name": "Autumn Leaves", "icon": "🍁", "url": "https://images.unsplash.com/photo-1504208434309-cb69f4fe52b0?w=1200&q=80"},
    "wp_lavender": {"name": "Lavender Fields", "icon": "💜", "url": "https://images.unsplash.com/photo-1505409859467-3a796fd5798e?w=1200&q=80"},
    "wp_alpine": {"name": "Alpine Peak", "icon": "🏔️", "url": "https://images.unsplash.com/photo-1454496522488-7a8e488e8606?w=1200&q=80"},
    "wp_desert": {"name": "Desert Dunes", "icon": "🌄", "url": "https://images.unsplash.com/photo-1509316785289-025f5b846b35?w=1200&q=80"},
    "wp_sunflower": {"name": "Sunflower Field", "icon": "🌻", "url": "https://images.unsplash.com/photo-1470506028280-a011fb34b6f7?w=1200&q=80"},
    "wp_northern": {"name": "Northern Lights", "icon": "🏰", "url": "https://images.unsplash.com/photo-1483347756197-71ef80e95f73?w=1200&q=80"},
    "wp_fireworks": {"name": "Fireworks", "icon": "🎆", "url": "https://images.unsplash.com/photo-1498931299472-f7a63a5a1cfa?w=1200&q=80"},
    "wp_storm": {"name": "Stormy Sea", "icon": "🌊", "url": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=1200&q=80"},
    "wp_crystal": {"name": "Crystal Waters", "icon": "🏖️", "url": "https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=1200&q=80"},
    "wp_canyon": {"name": "Grand Canyon", "icon": "🏜️", "url": "https://images.unsplash.com/photo-1474044159687-1ee9f3a51722?w=1200&q=80"},
    "wp_turquoise": {"name": "Turquoise Bay", "icon": "🌊", "url": "https://images.unsplash.com/photo-1505144808419-1957a94ca61e?w=1200&q=80"},
    "wp_meadow": {"name": "Mountain Meadow", "icon": "🌸", "url": "https://images.unsplash.com/photo-1444021465936-c6ca6d1cb1e6?w=1200&q=80"},
    "wp_abstract": {"name": "Abstract Art", "icon": "🎭", "url": "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=1200&q=80"},
    "wp_temple": {"name": "Japanese Temple", "icon": "🏯", "url": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1200&q=80"},
    "wp_greece": {"name": "Santorini", "icon": "🏛️", "url": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=1200&q=80"},
    "wp_volcano": {"name": "Volcano", "icon": "🌋", "url": "https://images.unsplash.com/photo-1468657988500-aca2e8a96ac1?w=1200&q=80"},
}

# ========== UTILITY FUNCTIONS ==========
def validate_image(data: bytes) -> bool:
    """Validate that binary data is a valid image file"""
    try:
        img = Image.open(io.BytesIO(data))
        img.verify()
        return img.format.lower() in ['jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
    except:
        return False

def validate_video(data: bytes) -> bool:
    """Validate that binary data is a valid video file"""
    try:
        header = data[:12]
        return any([
            header.startswith(b'\x00\x00\x00\x18ftypmp42'),
            header.startswith(b'\x00\x00\x00\x20ftypmp42'),
            header.startswith(b'\x00\x00\x00\x1cftypmp42'),
            header.startswith(b'RIFF'),
            header.startswith(b'\x1aE\xdf\xa3'),
            header.startswith(b'\x00\x00\x00\x1cftypisom'),
        ])
    except:
        return False

def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Sanitize and truncate text input"""
    if not text:
        return ""
    text = ''.join(c for c in text if ord(c) >= 32 or c == '\n')
    text = html.escape(str(text).strip())
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
        if diff < 5: return "just now"
        elif diff < 60: return f"{int(diff)}s ago"
        elif diff < 3600: return f"{int(diff//60)}m ago"
        elif diff < 86400: return f"{int(diff//3600)}h ago"
        elif diff < 604800: return f"{int(diff//86400)}d ago"
        elif diff < 2592000: return f"{int(diff//604800)}w ago"
        elif diff < 31536000: return f"{int(diff//2592000)}mo ago"
        else: return f"{int(diff//31536000)}y ago"
    except (ValueError, TypeError):
        return "unknown"

def format_full_date(ts: str) -> str:
    """Format timestamp to full date string"""
    if not ts:
        return ""
    try:
        t = datetime.fromisoformat(ts)
        return t.strftime("%B %d, %Y at %I:%M %p")
    except:
        return ""

def format_number(num: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if num < 1000: return str(num)
    elif num < 1000000: return f"{num/1000:.1f}K"
    elif num < 1000000000: return f"{num/1000000:.1f}M"
    else: return f"{num/1000000000:.1f}B"

def generate_id() -> str:
    """Generate a unique identifier"""
    return str(uuid.uuid4())

def generate_short_id() -> str:
    """Generate a short unique identifier"""
    return str(uuid.uuid4())[:12]

def get_avatar_color(username: str) -> str:
    """Get a consistent color for a user's avatar placeholder"""
    if not username: return AVATAR_COLORS[0]
    return AVATAR_COLORS[hash(username) % len(AVATAR_COLORS)]

def get_initials(username: str) -> str:
    """Get initials from username for avatar placeholder"""
    if not username: return "?"
    parts = username.replace('_', ' ').replace('.', ' ').split()
    if len(parts) >= 2: return (parts[0][0] + parts[1][0]).upper()
    return username[0].upper() if username else "?"

def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    if not text: return []
    return re.findall(r'#(\w+)', text)

def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text"""
    if not text: return []
    return re.findall(r'@(\w+)', text)

def atomic_save(filepath: pathlib.Path, data: Any) -> bool:
    """Save data atomically using a temporary file"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_path = filepath.with_suffix(f'.tmp_{generate_short_id()}')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_path.replace(filepath)
        return True
    except Exception as e:
        logger.error(f"Save failed for {filepath}: {e}")
        return False

def create_backup(filepath: pathlib.Path) -> bool:
    """Create a backup of a file"""
    try:
        if filepath.exists():
            timestamp = int(time.time())
            backup_path = BACKUP_DIR / f"{filepath.stem}_{timestamp}.bak"
            shutil.copy2(filepath, backup_path)
            backups = sorted(BACKUP_DIR.glob(f"{filepath.stem}_*.bak"))
            if len(backups) > 10:
                for old in backups[:-10]:
                    old.unlink()
            return True
    except Exception as e:
        logger.error(f"Backup failed: {e}")
    return False

def get_gender_avatar(username: str, size: int = 36, is_female: bool = False, is_premium: bool = False) -> str:
    """Generate pure-code SVG avatar based on gender and premium status"""
    if is_premium:
        svg = PREMIUM_FEMALE_SVG if is_female else PREMIUM_MALE_SVG
    else:
        svg = FEMALE_AVATAR_SVG if is_female else MALE_AVATAR_SVG
    b64 = base64.b64encode(svg.encode()).decode()
    return f'<img src="data:image/svg+xml;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #FFD700;flex-shrink:0;box-shadow:0 0 10px rgba(255,215,0,0.3);" alt="{username}">'

# ========== LOGGING ==========
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('socialite.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ========== RATE LIMITER ==========
class RateLimiter:
    """Rate limiter for user actions"""
    def __init__(self):
        self._actions: Dict[str, Dict[str, float]] = {}
    
    def can_act(self, user: str, action: str, limit: float = 2.0, cooldown: float = None) -> bool:
        """Check if user can perform action"""
        if cooldown is None: cooldown = limit
        now = time.time()
        if user not in self._actions: self._actions[user] = {}
        if action in self._actions[user]:
            if now - self._actions[user][action] < cooldown: return False
        self._actions[user][action] = now
        return True
    
    def time_until_next(self, user: str, action: str, cooldown: float = 2.0) -> float:
        """Get seconds until next action is allowed"""
        if user not in self._actions or action not in self._actions[user]: return 0
        return max(0, cooldown - (time.time() - self._actions[user][action]))
    
    def reset(self, user: str = None):
        """Reset rate limits"""
        if user: self._actions.pop(user, None)
        else: self._actions.clear()

# ========== CACHE ==========
class Cache:
    """Simple in-memory cache"""
    def __init__(self, ttl: int = CACHE_TTL_SECONDS):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._ttl: return data
            del self._cache[key]
        return None
    
    def set(self, key: str, data: Any):
        self._cache[key] = (data, time.time())
    
    def clear(self):
        self._cache.clear()

# Global cache instance
cache = Cache()

# ========== DATA MANAGER ==========
class DataManager:
    """Centralized data management with caching, backups, and error handling"""
    
    @staticmethod
    def load(filepath: pathlib.Path, default: Any = None) -> Any:
        """Load JSON data from file with caching and error recovery"""
        if default is None: default = {}
        cache_key = f"load_{filepath.name}"
        cached = cache.get(cache_key)
        if cached is not None: return cached
        
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cache.set(cache_key, data)
                return data
        except json.JSONDecodeError:
            logger.error(f"Corrupt JSON in {filepath}")
            backups = sorted(BACKUP_DIR.glob(f"{filepath.stem}_*.bak"), reverse=True)
            for backup in backups:
                try:
                    with open(backup, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.info(f"Restored from backup: {backup.name}")
                    cache.set(cache_key, data)
                    return data
                except: continue
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
        return default
    
    @staticmethod
    def save(filepath: pathlib.Path, data: Any) -> bool:
        """Save JSON data with atomic write and backup"""
        create_backup(filepath)
        if atomic_save(filepath, data):
            cache_key = f"load_{filepath.name}"
            cache.set(cache_key, data)
            return True
        return False
    
    @staticmethod
    def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password using PBKDF2 with SHA-256 and 200,000 iterations"""
        if salt is None: salt = secrets.token_hex(32)
        h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 200000)
        return h.hex(), salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: str) -> bool:
        """Verify password against stored hash"""
        h, _ = DataManager.hash_password(password, salt)
        return h == stored_hash
    
    # ========== USER MANAGEMENT ==========
    @staticmethod
    def get_users() -> Dict: return DataManager.load(USERS_FILE, {})
    @staticmethod
    def save_users(data: Dict): DataManager.save(USERS_FILE, data)
    @staticmethod
    def user_exists(username: str) -> bool: return username.lower() in [u.lower() for u in DataManager.get_users()]
    
    @staticmethod
    def create_user(username: str, password: str, email: str = "") -> Tuple[bool, str]:
        if DataManager.user_exists(username): return False, "Username already exists"
        if len(username) < 3 or len(username) > MAX_USERNAME_LENGTH: return False, f"Username must be 3-{MAX_USERNAME_LENGTH} characters"
        if not re.match(r'^[a-zA-Z0-9_]+$', username): return False, "Username can only contain letters, numbers, and underscores"
        users = DataManager.get_users()
        h, s = DataManager.hash_password(password)
        users[username] = {
            "password": h, "salt": s, "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None, "login_attempts": 0,
            "locked_until": None, "is_premium": False,
            "is_verified": False, "role": "user"
        }
        DataManager.save_users(users)
        profiles = DataManager.get_profiles()
        profiles[username] = DataManager._default_profile(username)
        DataManager.save_profiles(profiles)
        logger.info(f"User created: {username}")
        return True, "Account created successfully!"
    
    @staticmethod
    def authenticate(username: str, password: str) -> Tuple[bool, str]:
        users = DataManager.get_users()
        for un, data in users.items():
            if un.lower() == username.lower():
                if isinstance(data, dict):
                    # Check lockout
                    if data.get("locked_until"):
                        try:
                            lock_time = datetime.fromisoformat(data["locked_until"])
                            if datetime.now() < lock_time:
                                remaining = (lock_time - datetime.now()).seconds // 60
                                return False, f"Account locked for {remaining} more minutes"
                            else:
                                data["locked_until"] = None
                                data["login_attempts"] = 0
                                DataManager.save_users(users)
                        except: pass
                    
                    if "salt" in data:
                        if DataManager.verify_password(password, data["password"], data["salt"]):
                            data["last_login"] = datetime.now().isoformat()
                            data["login_attempts"] = 0
                            users[un] = data
                            DataManager.save_users(users)
                            return True, un
                        else:
                            data["login_attempts"] = data.get("login_attempts", 0) + 1
                            if data["login_attempts"] >= MAX_LOGIN_ATTEMPTS:
                                data["locked_until"] = (datetime.now() + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)).isoformat()
                            users[un] = data
                            DataManager.save_users(users)
                            return False, "Incorrect password"
                elif isinstance(data, str):
                    if data == hashlib.sha256(password.encode()).hexdigest():
                        h, s = DataManager.hash_password(password)
                        users[un] = {"password": h, "salt": s, "email": "", "created_at": datetime.now().isoformat(), "last_login": datetime.now().isoformat(), "login_attempts": 0, "locked_until": None, "is_premium": False, "is_verified": False, "role": "user"}
                        DataManager.save_users(users)
                        return True, un
                    return False, "Incorrect password"
        return False, "User not found"
    
    @staticmethod
    def _default_profile(username: str) -> Dict:
        return {
            "display_name": username, "bio": "", "avatar": None, "cover_photo": None,
            "website": "", "location": "", "birthday": "", "gender": "male",
            "is_private": False, "is_verified": False, "is_premium": False,
            "last_seen": "", "status": "", "followers": [], "following": [],
            "follow_requests": [], "blocked": [], "muted": [], "saved_posts": [],
            "highlights": [], "post_count": 0, "story_count": 0, "comment_count": 0,
            "like_count": 0, "share_count": 0, "total_views": 0,
            "theme": "midnight", "wallpaper": "wp_socialite", "language": "en",
            "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_profiles() -> Dict: return DataManager.load(PROFILES_FILE, {})
    @staticmethod
    def save_profiles(data: Dict): DataManager.save(PROFILES_FILE, data)
    
    @staticmethod
    def get_profile(username: str) -> Dict:
        profiles = DataManager.get_profiles()
        if username not in profiles:
            profiles[username] = DataManager._default_profile(username)
            DataManager.save_profiles(profiles)
        p = profiles[username]
        defaults = DataManager._default_profile(username)
        for k, v in defaults.items():
            if k not in p: p[k] = v
        return p
    
    @staticmethod
    def update_profile(username: str, updates: Dict):
        profiles = DataManager.get_profiles()
        if username in profiles:
            updates["updated_at"] = datetime.now().isoformat()
            profiles[username].update(updates)
            DataManager.save_profiles(profiles)
    
    @staticmethod
    def update_last_seen(username: str):
        profiles = DataManager.get_profiles()
        if username in profiles:
            profiles[username]["last_seen"] = datetime.now().isoformat()
            DataManager.save_profiles(profiles)
    
    @staticmethod
    def get_online_users() -> List[str]:
        profiles = DataManager.get_profiles()
        now = datetime.now()
        online = []
        for u, p in profiles.items():
            if p.get("last_seen"):
                try:
                    if (now - datetime.fromisoformat(p["last_seen"])).total_seconds() < ONLINE_THRESHOLD_SECONDS:
                        online.append(u)
                except: pass
        return online
    
    @staticmethod
    def search_users(query: str, limit: int = 50) -> List[Dict]:
        users = DataManager.get_users()
        profiles = DataManager.get_profiles()
        results = []
        q = query.lower()
        for u in users:
            if q in u.lower():
                p = profiles.get(u, {})
                results.append({"username": u, "display_name": p.get("display_name", u), "bio": p.get("bio", ""), "avatar": p.get("avatar"), "followers": len(p.get("followers", [])), "is_verified": p.get("is_verified", False), "is_premium": p.get("is_premium", False)})
            if len(results) >= limit: break
        return results
    
    # ========== FEED POSTS ==========
    @staticmethod
    def get_feed_posts() -> List[Dict]: return DataManager.load(FEED_POSTS_FILE, [])
    @staticmethod
    def save_feed_posts(data: List[Dict]):
        if len(data) > MAX_FEED_POSTS: data = data[-MAX_FEED_POSTS:]
        DataManager.save(FEED_POSTS_FILE, data)
    @staticmethod
    def get_user_posts(username: str) -> List[Dict]: return [p for p in DataManager.get_feed_posts() if p.get("username") == username]
    
    # ========== STORIES ==========
    @staticmethod
    def get_stories() -> Dict: return DataManager.load(STORIES_FILE, {})
    @staticmethod
    def save_stories(data: Dict): DataManager.save(STORIES_FILE, data)
    @staticmethod
    def get_active_stories() -> Dict:
        stories = DataManager.get_stories()
        active = {}
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        for u, ss in stories.items():
            a = [s for s in ss if s.get("timestamp", "") > cutoff]
            if a: active[u] = a
        return active
    
    # ========== MESSAGES ==========
    @staticmethod
    def get_direct_messages() -> Dict: return DataManager.load(DIRECT_MESSAGES_FILE, {})
    @staticmethod
    def save_direct_messages(data: Dict): DataManager.save(DIRECT_MESSAGES_FILE, data)
    @staticmethod
    def get_chat_id(u1: str, u2: str) -> str: return f"dm_{'_'.join(sorted([u1.lower(), u2.lower()]))}"
    
    # ========== GROUPS & CHANNELS ==========
    @staticmethod
    def get_group_chats() -> Dict: return DataManager.load(GROUP_CHATS_FILE, {})
    @staticmethod
    def save_group_chats(data: Dict): DataManager.save(GROUP_CHATS_FILE, data)
    @staticmethod
    def get_channels() -> Dict: return DataManager.load(CHANNELS_FILE, {})
    @staticmethod
    def save_channels(data: Dict): DataManager.save(CHANNELS_FILE, data)
    
    # ========== COMMENTS ==========
    @staticmethod
    def get_comments() -> Dict: return DataManager.load(COMMENTS_FILE, {})
    @staticmethod
    def save_comments(data: Dict): DataManager.save(COMMENTS_FILE, data)
    @staticmethod
    def get_post_comments(post_id: str) -> List[Dict]: return DataManager.get_comments().get(post_id, [])
    
    # ========== NOTIFICATIONS ==========
    @staticmethod
    def get_notifications() -> Dict: return DataManager.load(NOTIFICATIONS_FILE, {})
    @staticmethod
    def save_notifications(data: Dict): DataManager.save(NOTIFICATIONS_FILE, data)
    
    @staticmethod
    def add_notification(username: str, ntype: str, message: str, from_user: str = "", link: str = ""):
        notifs = DataManager.get_notifications()
        if username not in notifs: notifs[username] = []
        notifs[username].insert(0, {
            "id": generate_id(), "type": ntype, "message": message,
            "from_user": from_user, "link": link,
            "timestamp": datetime.now().isoformat(), "read": False
        })
        if len(notifs[username]) > MAX_NOTIFICATIONS: notifs[username] = notifs[username][:MAX_NOTIFICATIONS]
        DataManager.save_notifications(notifs)
    
    @staticmethod
    def get_unread_notification_count(username: str) -> int:
        return sum(1 for n in DataManager.get_notifications().get(username, []) if not n.get("read"))
    
    @staticmethod
    def mark_notifications_read(username: str):
        notifs = DataManager.get_notifications()
        if username in notifs:
            for n in notifs[username]: n["read"] = True
            DataManager.save_notifications(notifs)
    
    # ========== SAVED POSTS ==========
    @staticmethod
    def get_saved_posts() -> Dict: return DataManager.load(SAVED_POSTS_FILE, {})
    @staticmethod
    def save_saved_posts(data: Dict): DataManager.save(SAVED_POSTS_FILE, data)
    @staticmethod
    def is_post_saved(username: str, post_id: str) -> bool: return post_id in DataManager.get_saved_posts().get(username, [])

# ========== HANDLERS ==========
class PostHandler:
    """Handle all feed post operations"""
    
    @staticmethod
    def create(text: str, media_data: str = None, media_name: str = None, post_type: str = "post", location: str = "", tags: List[str] = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_POST_LENGTH) if text else ""
        if not text and not media_data: return False, "Post cannot be empty"
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "create_post", 5.0): return False, "Please wait before posting again"
        
        posts = DataManager.get_feed_posts()
        post = {
            "id": generate_id(), "username": st.session_state.user, "text": text,
            "timestamp": datetime.now().isoformat(), "type": post_type,
            "reactions": {}, "comments_count": 0, "shares_count": 0,
            "views_count": 0, "is_edited": False, "edited_at": None,
            "location": sanitize_text(location, 100) if location else "",
            "tags": tags or [], "hashtags": extract_hashtags(text),
            "mentions": extract_mentions(text), "is_pinned": False
        }
        if media_data:
            post["media"] = media_data
            post["media_name"] = sanitize_text(media_name, 200) if media_name else "media"
            post["media_type"] = "image"
        posts.append(post)
        DataManager.save_feed_posts(posts)
        st.session_state.feed_posts = posts
        
        p = DataManager.get_profile(st.session_state.user)
        p["post_count"] = p.get("post_count", 0) + 1
        DataManager.save_profiles(DataManager.get_profiles())
        
        # Process mentions for notifications
        for mention in post["mentions"]:
            if DataManager.user_exists(mention) and mention != st.session_state.user:
                DataManager.add_notification(mention, "mention", f"@{st.session_state.user} mentioned you in a post", st.session_state.user)
        
        return True, "Posted successfully!"
    
    @staticmethod
    def edit(post_id: str, new_text: str) -> Tuple[bool, str]:
        new_text = sanitize_text(new_text, MAX_POST_LENGTH)
        if not new_text: return False, "Post cannot be empty"
        posts = DataManager.get_feed_posts()
        for post in posts:
            if post["id"] == post_id and post["username"] == st.session_state.user:
                post["text"] = new_text
                post["is_edited"] = True
                post["edited_at"] = datetime.now().isoformat()
                post["hashtags"] = extract_hashtags(new_text)
                post["mentions"] = extract_mentions(new_text)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Post updated!"
        return False, "Post not found"
    
    @staticmethod
    def delete(post_id: str) -> Tuple[bool, str]:
        posts = DataManager.get_feed_posts()
        for i, post in enumerate(posts):
            if post["id"] == post_id and post["username"] == st.session_state.user:
                posts.pop(i)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return True, "Post deleted!"
        return False, "Post not found"
    
    @staticmethod
    def add_reaction(post_id: str, reaction_key: str):
        posts = DataManager.get_feed_posts()
        u = st.session_state.user
        for post in posts:
            if post["id"] == post_id:
                if "reactions" not in post: post["reactions"] = {}
                # Remove from other reactions first (one reaction per user per post)
                for rk in list(post["reactions"].keys()):
                    if u in post["reactions"][rk]:
                        post["reactions"][rk].remove(u)
                        if not post["reactions"][rk]: del post["reactions"][rk]
                if reaction_key not in post["reactions"]: post["reactions"][reaction_key] = []
                post["reactions"][reaction_key].append(u)
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                if post["username"] != u:
                    rdata = LUXURY_REACTIONS.get(reaction_key, STANDARD_REACTIONS.get(reaction_key, {}))
                    DataManager.add_notification(post["username"], "reaction", f"@{u} reacted with {rdata.get('emoji','')} to your post", u)
                return
    
    @staticmethod
    def save_post(post_id: str) -> Tuple[bool, str]:
        u = st.session_state.user
        saved = DataManager.get_saved_posts()
        if u not in saved: saved[u] = []
        if post_id in saved[u]:
            saved[u].remove(post_id); DataManager.save_saved_posts(saved); return True, "Post unsaved"
        else:
            saved[u].append(post_id)
            if len(saved[u]) > MAX_SAVED_POSTS: saved[u] = saved[u][-MAX_SAVED_POSTS:]
            DataManager.save_saved_posts(saved); return True, "Post saved!"
    
    @staticmethod
    def create_poll(question: str, options: List[str], duration_hours: int = 168) -> Tuple[bool, str]:
        question = sanitize_text(question, 500)
        options = [sanitize_text(o, 200) for o in options if o.strip()]
        if len(options) < 2: return False, "Need at least 2 options"
        if len(options) > 20: return False, "Maximum 20 options"
        posts = DataManager.get_feed_posts()
        posts.append({
            "id": generate_id(), "username": st.session_state.user, "text": question,
            "timestamp": datetime.now().isoformat(), "type": "poll",
            "poll_data": {"options": {o: [] for o in options}, "total_votes": 0,
            "ends_at": (datetime.now() + timedelta(hours=duration_hours)).isoformat()}
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
                # Remove previous vote
                for o, v in pd["options"].items():
                    if u in v: v.remove(u); pd["total_votes"] -= 1
                if option in pd["options"]:
                    pd["options"][option].append(u); pd["total_votes"] += 1
                DataManager.save_feed_posts(posts)
                st.session_state.feed_posts = posts
                return
    
    @staticmethod
    def get_feed_for_user(username: str, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], bool]:
        """Get personalized feed for a user"""
        profile = DataManager.get_profile(username)
        following = profile.get("following", [])
        posts = DataManager.get_feed_posts()
        # Show posts from following users + own posts
        feed_posts = [p for p in posts if p["username"] in following or p["username"] == username]
        feed_posts.reverse()
        total = len(feed_posts)
        start = (page - 1) * per_page
        end = start + per_page
        return feed_posts[start:end], end < total

class StoryHandler:
    """Handle story operations"""
    
    @staticmethod
    def create(media_data: str, media_name: str, caption: str = "") -> Tuple[bool, str]:
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "create_story", 10.0): return False, "Please wait before posting another story"
        stories = DataManager.get_stories()
        u = st.session_state.user
        if u not in stories: stories[u] = []
        cutoff = (datetime.now() - timedelta(hours=STORY_EXPIRY_HOURS)).isoformat()
        stories[u] = [s for s in stories[u] if s["timestamp"] > cutoff]
        if len(stories[u]) >= 20: return False, "Maximum 20 active stories"
        stories[u].append({
            "id": generate_id(), "username": u, "media": media_data,
            "media_name": sanitize_text(media_name, 200),
            "caption": sanitize_text(caption, 200) if caption else "",
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=STORY_EXPIRY_HOURS)).isoformat(),
            "views": [], "reactions": []
        })
        DataManager.save_stories(stories)
        st.session_state.stories = stories
        return True, "Story posted!"
    
    @staticmethod
    def view(username: str, story_id: str):
        stories = DataManager.get_stories()
        if username in stories:
            for s in stories[username]:
                if s["id"] == story_id and st.session_state.user not in s["views"]:
                    s["views"].append(st.session_state.user)
            DataManager.save_stories(stories)
            st.session_state.stories = stories
    
    @staticmethod
    def delete(story_id: str) -> Tuple[bool, str]:
        stories = DataManager.get_stories()
        u = st.session_state.user
        if u in stories:
            for i, s in enumerate(stories[u]):
                if s["id"] == story_id:
                    stories[u].pop(i); DataManager.save_stories(stories); st.session_state.stories = stories
                    return True, "Story deleted!"
        return False, "Story not found"

class ChatHandler:
    """Handle direct messaging"""
    
    @staticmethod
    def send(to_user: str, text: str, media_data: str = None, media_name: str = None, reply_to: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH) if text else ""
        if not text and not media_data: return False, "Message cannot be empty"
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "send_message", 1.0): return False, "Sending too fast"
        from_user = st.session_state.user
        # Check if blocked
        tp = DataManager.get_profile(to_user)
        if from_user in tp.get("blocked", []): return False, "You are blocked by this user"
        chat_id = DataManager.get_chat_id(from_user, to_user)
        dms = DataManager.get_direct_messages()
        if chat_id not in dms: dms[chat_id] = {"participants": [from_user, to_user], "messages": [], "created_at": datetime.now().isoformat(), "is_encrypted": True}
        msg = {"id": generate_id(), "from": from_user, "to": to_user, "text": text, "timestamp": datetime.now().isoformat(), "read": False, "delivered": True, "reply_to": reply_to}
        if media_data:
            msg["media"] = media_data; msg["media_name"] = sanitize_text(media_name, 200) if media_name else "file"
        dms[chat_id]["messages"].append(msg)
        if len(dms[chat_id]["messages"]) > MAX_CHAT_MESSAGES: dms[chat_id]["messages"] = dms[chat_id]["messages"][-MAX_CHAT_MESSAGES:]
        DataManager.save_direct_messages(dms)
        DataManager.add_notification(to_user, "message", f"New message from @{from_user}", from_user)
        return True, "Message sent!"
    
    @staticmethod
    def get_messages(with_user: str) -> List[Dict]:
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
                unread = sum(1 for m in msgs if m.get("to") == u and not m.get("read", False))
                chats.append({
                    "with_user": other,
                    "last_message": last["text"][:100] if last and last.get("text") else "📷 Media" if last and last.get("media") else "No messages",
                    "last_time": last["timestamp"] if last else cd["created_at"],
                    "unread": unread, "is_online": other in online,
                    "message_count": len(msgs)
                })
        chats.sort(key=lambda x: x["last_time"], reverse=True)
        return chats
    
    @staticmethod
    def delete_message(chat_id: str, msg_id: str) -> Tuple[bool, str]:
        dms = DataManager.get_direct_messages()
        if chat_id in dms:
            for i, m in enumerate(dms[chat_id]["messages"]):
                if m["id"] == msg_id and m["from"] == st.session_state.user:
                    dms[chat_id]["messages"].pop(i)
                    DataManager.save_direct_messages(dms)
                    return True, "Message deleted"
        return False, "Message not found"

class GroupHandler:
    """Handle group chats and channels"""
    
    @staticmethod
    def create(name: str, members: List[str], is_channel: bool = False, description: str = "") -> Tuple[bool, str]:
        name = sanitize_text(name, 100)
        if not name: return False, "Name required"
        all_members = list(set(members + [st.session_state.user]))
        if len(all_members) < 2 and not is_channel: return False, "Need at least 2 members"
        gid = f"{'channel' if is_channel else 'group'}_{generate_short_id()}"
        data = {
            "name": name, "owner": st.session_state.user,
            "admins": [st.session_state.user], "messages": [],
            "created_at": datetime.now().isoformat(),
            "description": sanitize_text(description, 500) if description else "",
            "icon": None, "is_public": False
        }
        if is_channel:
            data["subscribers"] = all_members
            channels = DataManager.get_channels(); channels[gid] = data; DataManager.save_channels(channels)
        else:
            data["members"] = all_members
            groups = DataManager.get_group_chats(); groups[gid] = data; DataManager.save_group_chats(groups)
            for m in members:
                if m != st.session_state.user:
                    DataManager.add_notification(m, "group_invite", f"You were added to '{name}'", st.session_state.user)
        return True, f"{'Channel' if is_channel else 'Group'} '{name}' created!"
    
    @staticmethod
    def send_message(group_id: str, text: str, media_data: str = None, is_channel: bool = False) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_MESSAGE_LENGTH)
        if not text and not media_data: return False, "Message cannot be empty"
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "send_group_message", 1.0): return False, "Sending too fast"
        data = DataManager.get_channels() if is_channel else DataManager.get_group_chats()
        if group_id not in data: return False, "Not found"
        if is_channel and st.session_state.user not in data[group_id].get("admins", []): return False, "Only admins can post"
        if not is_channel and st.session_state.user not in data[group_id].get("members", []): return False, "Not a member"
        msg = {"id": generate_id(), "from": st.session_state.user, "text": text, "timestamp": datetime.now().isoformat()}
        if media_data: msg["media"] = media_data
        data[group_id]["messages"].append(msg)
        if is_channel: DataManager.save_channels(data)
        else: DataManager.save_group_chats(data)
        return True, "Message sent!"
    
    @staticmethod
    def get_user_groups() -> List[Dict]:
        u = st.session_state.user
        groups = DataManager.get_group_chats()
        result = []
        for gid, gd in groups.items():
            if u in gd.get("members", []):
                msgs = gd["messages"]; last = msgs[-1] if msgs else None
                result.append({"id": gid, "name": gd["name"], "members": len(gd.get("members", [])), "description": gd.get("description", ""), "last_message": last["text"][:50] if last and last.get("text") else "No messages", "last_time": last["timestamp"] if last else gd["created_at"], "is_admin": u in gd.get("admins", [])})
        return sorted(result, key=lambda x: x["last_time"], reverse=True)
    
    @staticmethod
    def get_user_channels() -> List[Dict]:
        u = st.session_state.user
        channels = DataManager.get_channels()
        result = []
        for cid, cd in channels.items():
            if u in cd.get("subscribers", []):
                msgs = cd["messages"]; last = msgs[-1] if msgs else None
                result.append({"id": cid, "name": cd["name"], "subscribers": len(cd.get("subscribers", [])), "description": cd.get("description", ""), "last_message": last["text"][:50] if last and last.get("text") else "No posts", "last_time": last["timestamp"] if last else cd["created_at"], "is_admin": u in cd.get("admins", [])})
        return sorted(result, key=lambda x: x["last_time"], reverse=True)
    
    @staticmethod
    def get_group_messages(group_id: str) -> List: return DataManager.get_group_chats().get(group_id, {}).get("messages", [])
    @staticmethod
    def get_channel_messages(channel_id: str) -> List: return DataManager.get_channels().get(channel_id, {}).get("messages", [])

class CommentHandler:
    """Handle post comments"""
    
    @staticmethod
    def add(post_id: str, text: str, parent_id: str = None) -> Tuple[bool, str]:
        text = sanitize_text(text, MAX_COMMENT_LENGTH)
        if not text: return False, "Comment cannot be empty"
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "add_comment", 2.0): return False, "Please wait"
        comments = DataManager.get_comments()
        if post_id not in comments: comments[post_id] = []
        comment = {"id": generate_id(), "username": st.session_state.user, "text": text, "timestamp": datetime.now().isoformat(), "likes": [], "parent_id": parent_id, "replies": []}
        if parent_id:
            for c in comments[post_id]:
                if c["id"] == parent_id: c["replies"].append(comment); break
        else:
            comments[post_id].append(comment)
        DataManager.save_comments(comments)
        # Update comment count on post
        posts = DataManager.get_feed_posts()
        for p in posts:
            if p["id"] == post_id: p["comments_count"] = len(comments[post_id]); break
        DataManager.save_feed_posts(posts)
        return True, "Comment added!"
    
    @staticmethod
    def get(post_id: str) -> List: return DataManager.get_comments().get(post_id, [])
    
    @staticmethod
    def delete(post_id: str, comment_id: str) -> Tuple[bool, str]:
        comments = DataManager.get_comments()
        if post_id in comments:
            for i, c in enumerate(comments[post_id]):
                if c["id"] == comment_id and c["username"] == st.session_state.user:
                    comments[post_id].pop(i); DataManager.save_comments(comments); return True, "Comment deleted!"
        return False, "Comment not found"

class FollowHandler:
    """Handle follow/unfollow system"""
    
    @staticmethod
    def follow(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user: return False, "Cannot follow yourself"
        if not st.session_state.rate_limiter.can_act(st.session_state.user, "follow", 1.0): return False, "Please wait"
        profiles = DataManager.get_profiles()
        up = DataManager.get_profile(st.session_state.user)
        tp = DataManager.get_profile(target)
        for p in [up, tp]:
            for k in ["following", "followers", "blocked", "follow_requests"]:
                if k not in p: p[k] = []
        if st.session_state.user in tp.get("blocked", []): return False, "You are blocked"
        if target in up.get("blocked", []): return False, "Unblock first"
        
        if tp.get("is_private") and target not in up.get("following", []):
            if target in up.get("follow_requests", []): return False, "Request already sent"
            up["follow_requests"].append(target)
            DataManager.add_notification(target, "follow_request", f"@{st.session_state.user} requested to follow you", st.session_state.user)
            profiles[st.session_state.user] = up; profiles[target] = tp; DataManager.save_profiles(profiles)
            return True, "Follow request sent!"
        
        if target in up["following"]:
            up["following"].remove(target); tp["followers"].remove(st.session_state.user); action = "Unfollowed"
        else:
            up["following"].append(target); tp["followers"].append(st.session_state.user); action = "Following"
            DataManager.add_notification(target, "follow", f"@{st.session_state.user} started following you", st.session_state.user)
        profiles[st.session_state.user] = up; profiles[target] = tp; DataManager.save_profiles(profiles)
        return True, f"{action}!"
    
    @staticmethod
    def is_following(target: str) -> bool: return target in DataManager.get_profile(st.session_state.user).get("following", [])
    
    @staticmethod
    def block(target: str) -> Tuple[bool, str]:
        if target == st.session_state.user: return False, "Cannot block yourself"
        profiles = DataManager.get_profiles(); up = DataManager.get_profile(st.session_state.user)
        for k in ["following", "followers", "blocked"]:
            if k not in up: up[k] = []
        if target in up["blocked"]: up["blocked"].remove(target); action = "Unblocked"
        else:
            up["blocked"].append(target)
            if target in up.get("following", []): up["following"].remove(target)
            tp = DataManager.get_profile(target)
            if st.session_state.user in tp.get("followers", []): tp["followers"].remove(st.session_state.user)
            profiles[target] = tp; action = "Blocked"
        profiles[st.session_state.user] = up; DataManager.save_profiles(profiles)
        return True, f"{action}!"
    
    @staticmethod
    def accept_follow_request(from_user: str) -> Tuple[bool, str]:
        profiles = DataManager.get_profiles()
        up = DataManager.get_profile(st.session_state.user)
        fp = DataManager.get_profile(from_user)
        if from_user not in up.get("follow_requests", []): return False, "No request found"
        up["follow_requests"].remove(from_user)
        fp["following"].append(st.session_state.user)
        up["followers"].append(from_user)
        profiles[st.session_state.user] = up; profiles[from_user] = fp; DataManager.save_profiles(profiles)
        DataManager.add_notification(from_user, "follow_accepted", f"@{st.session_state.user} accepted your follow request", st.session_state.user)
        return True, "Request accepted!"

# ========== SESSION STATE ==========
def init_session():
    """Initialize all session state variables"""
    defaults = {
        'feed_posts': [], 'stories': {}, 'auth': False, 'user': "",
        'current_tab': "feed", 'active_chat': None, 'active_group': None,
        'active_channel': None, 'chat_type': None,
        'rate_limiter': RateLimiter(),
        'show_create_modal': False, 'show_notifications': False,
        'show_new_chat': False, 'show_new_group': False, 'show_new_channel': False,
        'show_comments_for': None, 'editing_post': None,
        'viewing_profile': None, 'feed_page': 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v
    if not st.session_state.feed_posts: st.session_state.feed_posts = DataManager.get_feed_posts()
    if not st.session_state.stories: st.session_state.stories = DataManager.get_stories()

init_session()
if st.session_state.get('auth'):
    st.session_state.feed_posts = DataManager.get_feed_posts()
    st.session_state.stories = DataManager.get_stories()
    DataManager.update_last_seen(st.session_state.user)

def get_theme() -> Dict:
    if st.session_state.get('auth'):
        t = DataManager.get_profile(st.session_state.user).get('theme', 'midnight')
        return THEMES.get(t, THEMES['midnight'])
    return THEMES['midnight']

def get_wallpaper() -> Dict:
    if st.session_state.get('auth'):
        w = DataManager.get_profile(st.session_state.user).get('wallpaper', 'wp_socialite')
        return WALLPAPERS.get(w, WALLPAPERS['wp_socialite'])
    return WALLPAPERS['wp_socialite']

# ========== CSS STYLES ==========
def inject_styles():
    theme = get_theme()
    wp = get_wallpaper()
    bg = f"url('{wp['url']}') center/cover no-repeat fixed" if wp.get("url") else wp.get("gradient", theme["gradient"])
    emoji_html = get_socialite_emoji_html(80)

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&display=swap');
    
    * {{ font-family: 'Inter', sans-serif; }}
    
    #MainMenu, footer, header {{ visibility: hidden !important; display: none !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    .stDeployButton, [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"], [data-testid="stToolbar"], .stApp > header, div[data-testid="stVerticalBlock"] > div:first-child {{ display: none !important; }}
    
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
    
    .app-logo {{
        font-size: 1.1rem !important; font-weight: 800 !important;
        background: linear-gradient(135deg, #FFD700, #FFA500, #FFD700) !important;
        -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
        display: flex !important; align-items: center !important; gap: 8px !important;
    }}
    
    .badge {{
        background: #FFD700 !important; color: #1a0033 !important; border-radius: 50% !important;
        padding: 1px 6px !important; font-size: 0.6rem !important; font-weight: 700 !important;
        position: absolute !important; top: -8px !important; right: -10px !important;
        box-shadow: 0 0 10px rgba(255,215,0,0.5) !important;
    }}
    
    /* Main content area */
    .main-content {{
        position: fixed !important; top: 48px !important; bottom: 56px !important;
        left: 0 !important; right: 0 !important; overflow-y: auto !important;
        overflow-x: hidden !important; padding: 8px 12px !important;
        -webkit-overflow-scrolling: touch !important;
    }}
    
    .content-wrapper {{ max-width: 650px !important; margin: 0 auto !important; padding-bottom: 8px !important; }}
    
    /* Bottom Nav - TASKBAR STYLE */
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
    .post-media {{ width: 100% !important; max-height: 400px !important; object-fit: cover !important; }}
    
    /* Luxury Reactions */
    .luxury-bar {{ display: flex !important; gap: 3px !important; padding: 6px 8px !important; border-top: 1px solid rgba(255,215,0,0.1) !important; flex-wrap: wrap !important; }}
    .luxury-btn {{
        padding: 4px 7px !important; border-radius: 16px !important; cursor: pointer !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        background: rgba(255,255,255,0.03) !important; border: 1px solid rgba(255,255,255,0.06) !important;
        font-size: 0.85rem !important; color: {theme['secondary']} !important;
    }}
    .luxury-btn:hover {{
        transform: scale(1.2) !important; background: rgba(255,215,0,0.15) !important;
        border-color: rgba(255,215,0,0.4) !important;
        box-shadow: 0 0 20px rgba(255,215,0,0.5), 0 0 40px rgba(255,215,0,0.2) !important; z-index: 10 !important;
    }}
    .luxury-btn.active {{ background: rgba(255,215,0,0.2) !important; border-color: rgba(255,215,0,0.5) !important; box-shadow: 0 0 15px rgba(255,215,0,0.3) !important; }}
    
    /* Chat */
    .chat-bubble {{ max-width: 80% !important; padding: 8px 12px !important; border-radius: 14px !important; font-size: 0.82rem !important; line-height: 1.4 !important; margin: 2px 0 !important; }}
    .chat-bubble.sent {{ background: linear-gradient(135deg, #667eea, #764ba2) !important; color: white !important; align-self: flex-end !important; border-bottom-right-radius: 4px !important; }}
    .chat-bubble.received {{ background: rgba(255,255,255,0.07) !important; color: #e2e8f0 !important; align-self: flex-start !important; border-bottom-left-radius: 4px !important; }}
    
    /* Stories */
    .stories-row {{ display: flex !important; gap: 12px !important; padding: 8px 0 !important; overflow-x: auto !important; margin-bottom: 8px !important; }}
    .stories-row::-webkit-scrollbar {{ height: 0 !important; }}
    .story-item {{ display: flex !important; flex-direction: column !important; align-items: center !important; gap: 3px !important; min-width: 60px !important; cursor: pointer !important; }}
    .story-ring {{ width: 56px !important; height: 56px !important; border-radius: 50% !important; padding: 2.5px !important; background: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) !important; box-shadow: 0 0 12px rgba(255,215,0,0.3) !important; }}
    .story-ring.viewed {{ background: rgba(255,255,255,0.2) !important; box-shadow: none !important; }}
    .story-ring-inner {{ width: 100% !important; height: 100% !important; border-radius: 50% !important; object-fit: cover !important; border: 2px solid {theme['bg']} !important; }}
    .story-ring-inner-placeholder {{ width: 100% !important; height: 100% !important; border-radius: 50% !important; display: flex !important; align-items: center !important; justify-content: center !important; font-weight: 700 !important; color: white !important; font-size: 1rem !important; border: 2px solid {theme['bg']} !important; }}
    .story-name {{ color: {theme['secondary']} !important; font-size: 0.58rem !important; max-width: 58px !important; overflow: hidden !important; text-overflow: ellipsis !important; white-space: nowrap !important; }}
    
    /* Modal */
    .modal-overlay {{ position: fixed !important; top: 0 !important; left: 0 !important; right: 0 !important; bottom: 0 !important; background: rgba(0,0,0,0.85) !important; backdrop-filter: blur(8px) !important; display: flex !important; align-items: center !important; justify-content: center !important; z-index: 10000 !important; }}
    .modal-box {{ background: {theme['bg']}fa !important; border: 1px solid rgba(255,215,0,0.2) !important; border-radius: 18px !important; width: 92% !important; max-width: 480px !important; max-height: 80vh !important; overflow-y: auto !important; padding: 16px !important; }}
    
    /* Theme & Wallpaper grids */
    .theme-grid {{ display: grid !important; grid-template-columns: repeat(3, 1fr) !important; gap: 6px !important; padding: 6px 0 !important; }}
    .wallpaper-grid {{ display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 5px !important; padding: 6px 0 !important; }}
    .theme-card {{ border-radius: 10px !important; padding: 14px 4px !important; text-align: center !important; cursor: pointer !important; border: 2px solid transparent !important; transition: all 0.3s !important; }}
    .theme-card:hover {{ transform: scale(1.05) !important; box-shadow: 0 0 20px rgba(255,215,0,0.3) !important; }}
    .theme-card.selected {{ border-color: #FFD700 !important; box-shadow: 0 0 20px rgba(255,215,0,0.4) !important; }}
    .wallpaper-card {{ border-radius: 8px !important; height: 50px !important; cursor: pointer !important; border: 2px solid transparent !important; background-size: cover !important; background-position: center !important; transition: all 0.3s !important; }}
    .wallpaper-card:hover {{ transform: scale(1.08) !important; box-shadow: 0 0 15px rgba(255,215,0,0.3) !important; }}
    .wallpaper-card.selected {{ border-color: #FFD700 !important; box-shadow: 0 0 20px rgba(255,215,0,0.5) !important; }}
    
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
    
    .stTabs [data-baseweb="tab-list"] {{ gap: 3px !important; background: transparent !important; }}
    .stTabs [data-baseweb="tab"] {{ color: {theme['secondary']} !important; border-radius: 6px !important; padding: 5px 12px !important; font-size: 0.78rem !important; }}
    .stTabs [aria-selected="true"] {{ color: #FFD700 !important; background: rgba(255,215,0,0.1) !important; }}
    
    .stExpander {{ background: {theme['card']} !important; border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 12px !important; }}
    .streamlit-expanderHeader {{ color: {theme['text']} !important; font-size: 0.85rem !important; }}
    
    ::-webkit-scrollbar {{ width: 4px !important; }}
    ::-webkit-scrollbar-track {{ background: transparent !important; }}
    ::-webkit-scrollbar-thumb {{ background: #FFD70044 !important; border-radius: 2px !important; }}
    
    /* Socialite Brand Emoji */
    .socialite-emoji {{
        filter: drop-shadow(0 0 30px rgba(255,215,0,0.6)) !important;
        animation: float 3s ease-in-out infinite !important;
    }}
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

# ========== RENDERERS ==========
def render_avatar(username: str, size: int = 36) -> str:
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    is_female = profile.get("gender", "male") == "female"
    is_premium = profile.get("is_premium", False)
    if path and os.path.exists(path):
        try:
            with open(path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
            border = "3px solid #FFD700" if is_premium else "2px solid #FFD700"
            glow = "box-shadow:0 0 15px rgba(255,215,0,0.5);" if is_premium else "box-shadow:0 0 8px rgba(255,215,0,0.2);"
            return f'<img src="data:image/jpeg;base64,{b64}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:{border};flex-shrink:0;{glow}" alt="{username}">'
        except: pass
    return get_gender_avatar(username, size, is_female, is_premium)

def render_story_ring(username: str, size: int = 56, has_new: bool = False) -> str:
    ring_class = "story-ring" if has_new else "story-ring viewed"
    profile = DataManager.get_profile(username)
    path = profile.get("avatar")
    is_female = profile.get("gender", "male") == "female"
    is_premium = profile.get("is_premium", False)
    if path and os.path.exists(path):
        with open(path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
        return f'<div class="{ring_class}"><img src="data:image/jpeg;base64,{b64}" class="story-ring-inner" alt="{username}"></div>'
    color = get_avatar_color(username)
    return f'<div class="{ring_class}"><div class="story-ring-inner-placeholder" style="font-size:{size*0.3}px;background:{color};">{get_initials(username)}</div></div>'

def render_header():
    user = st.session_state.user
    unread = DataManager.get_unread_notification_count(user)
    badge = f'<span class="badge">{unread}</span>' if unread > 0 else ''
    st.markdown(f'<div class="app-header"><div class="app-logo">{get_socialite_emoji_html(24)} Socialite</div><div style="display:flex;align-items:center;gap:12px;color:{get_theme()["text"]};"><span style="position:relative;cursor:pointer;">🔔{badge}</span>{render_avatar(user, 28)}</div></div>', unsafe_allow_html=True)

def render_stories_bar():
    user = st.session_state.user; active = DataManager.get_active_stories()
    html = '<div class="stories-row">'
    html += f'<div class="story-item">{render_story_ring(user, 56, user not in active)}<div class="story-name">You</div></div>'
    for u, ss in active.items():
        if u != user:
            has_new = any(st.session_state.user not in s.get("views", []) for s in ss)
            html += f'<div class="story-item">{render_story_ring(u, 56, has_new)}<div class="story-name">@{u[:8]}</div></div>'
    if len(active) <= 1: html += '<div style="color:#94a3b8;display:flex;align-items:center;font-size:0.7rem;padding-left:8px;">No stories yet</div>'
    html += '</div>'; st.markdown(html, unsafe_allow_html=True)

def render_luxury_bar(post_id: str, reactions: Dict):
    st.markdown('<div class="luxury-bar">', unsafe_allow_html=True)
    cols = st.columns(len(LUXURY_REACTIONS))
    for i, (rkey, rdata) in enumerate(LUXURY_REACTIONS.items()):
        count = len(reactions.get(rkey, [])); active = "active" if st.session_state.user in reactions.get(rkey, []) else ""
        with cols[i]:
            if st.button(f"{rdata['emoji']} {count}", key=f"lux_{rkey}_{post_id}", help=rdata['label']):
                PostHandler.add_reaction(post_id, rkey); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_post_card(post: Dict):
    username = post.get("username", ""); pid = post.get("id", ""); is_owner = username == st.session_state.user
    profile = DataManager.get_profile(username)
    st.markdown(f'<div class="card"><div class="card-header">{render_avatar(username)}<div style="flex:1;"><div class="username-text">@{html.escape(username)}{" <span style=\\"color:#FFD700;font-size:0.65rem;\\">✓✓</span>" if profile.get("is_verified") else ""}{" <span style=\\"color:#FFD700;font-size:0.6rem;\\">👑</span>" if profile.get("is_premium") else ""}</div><div class="timestamp">{format_timestamp(post.get("timestamp", ""))}{" · Edited" if post.get("is_edited") else ""}</div></div></div>', unsafe_allow_html=True)
    if post.get("text"): st.markdown(f'<div class="post-text">{html.escape(post["text"])}</div>', unsafe_allow_html=True)
    if post.get("media") and post.get("media_type") == "image": st.markdown(f'<img src="{post["media"]}" class="post-media" alt="Post">', unsafe_allow_html=True)
    render_luxury_bar(pid, post.get("reactions", {}))
    st.markdown('<div style="display:flex;align-items:center;padding:4px 10px 8px 10px;gap:8px;">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([1, 1, 1, 3])
    with c1:
        if st.button("💬", key=f"cm_{pid}"): st.session_state.show_comments_for = None if st.session_state.show_comments_for == pid else pid; st.rerun()
    with c2:
        if st.button("🔄", key=f"rp_{pid}"): st.toast("Reposted!")
    with c3:
        is_saved = DataManager.is_post_saved(st.session_state.user, pid)
        if st.button("📌" if is_saved else "🔖", key=f"sv_{pid}"): PostHandler.save_post(pid); st.rerun()
    if is_owner:
        with c4:
            if st.button("🗑️ Delete", key=f"dl_{pid}"): PostHandler.delete(pid); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.show_comments_for == pid: render_comments(pid)
    st.markdown('</div>', unsafe_allow_html=True)

def render_poll_card(post: Dict):
    username = post.get("username", ""); pid = post.get("id", ""); pd = post.get("poll_data", {})
    total = pd.get("total_votes", 0); options = pd.get("options", {}); profile = DataManager.get_profile(username)
    st.markdown(f'<div class="card"><div class="card-header">{render_avatar(username)}<div style="flex:1;"><div class="username-text">@{html.escape(username)}{" <span style=\\"color:#FFD700;\\">✓✓</span>" if profile.get("is_verified") else ""}</div><div class="timestamp">📊 Poll · {format_timestamp(post.get("timestamp", ""))}{" · Ends " + format_timestamp(pd.get("ends_at","")) if pd.get("ends_at") else ""}</div></div></div><div class="post-text" style="font-weight:600;">{html.escape(post.get("text", ""))}</div><div style="padding:0 10px 8px 10px;">', unsafe_allow_html=True)
    for opt, voters in options.items():
        pct = (len(voters) / total * 100) if total > 0 else 0; voted = st.session_state.user in voters
        st.markdown(f'<div style="background:rgba(255,255,255,0.03);border-radius:8px;padding:5px 8px;margin:3px 0;{"border:1px solid #FFD700;" if voted else ""}"><div style="display:flex;justify-content:space-between;color:#e2e8f0;font-size:0.8rem;"><span>{"✓ " if voted else ""}{html.escape(opt)}</span><span>{pct:.0f}%</span></div><div style="height:3px;background:rgba(255,255,255,0.05);border-radius:2px;margin-top:3px;"><div style="width:{pct}%;height:100%;background:linear-gradient(90deg,#FFD700,#FFA500);border-radius:2px;"></div></div></div>', unsafe_allow_html=True)
        if st.button(f"Vote", key=f"pv_{pid}_{opt[:8]}"): PostHandler.vote_poll(pid, opt); st.rerun()
    st.markdown(f'<div style="color:#94a3b8;font-size:0.6rem;margin-top:4px;">{total} votes</div></div></div>', unsafe_allow_html=True)

def render_comments(post_id: str):
    comments = CommentHandler.get(post_id)
    st.markdown('<div style="padding:4px 10px;border-top:1px solid rgba(255,215,0,0.1);">', unsafe_allow_html=True)
    for c in comments[-20:]:
        st.markdown(f'<div style="margin:3px 0;display:flex;gap:5px;align-items:flex-start;">{render_avatar(c["username"], 20)}<div><span style="color:#f1f5f9;font-weight:600;font-size:0.7rem;">@{html.escape(c["username"])}</span> <span style="color:#e2e8f0;font-size:0.73rem;">{html.escape(c["text"])}</span><div style="color:#64748b;font-size:0.6rem;">{format_timestamp(c["timestamp"])}</div></div></div>', unsafe_allow_html=True)
        for reply in c.get("replies", [])[-5:]:
            st.markdown(f'<div style="margin:2px 0 2px 25px;display:flex;gap:4px;align-items:flex-start;">{render_avatar(reply["username"], 16)}<div><span style="color:#f1f5f9;font-weight:600;font-size:0.65rem;">@{html.escape(reply["username"])}</span> <span style="color:#e2e8f0;font-size:0.68rem;">{html.escape(reply["text"])}</span></div></div>', unsafe_allow_html=True)
    with st.form(f"cmf_{post_id}", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1: txt = st.text_input("Comment", placeholder="Write a comment...", key=f"ci_{post_id}")
        with c2:
            if st.form_submit_button("Post"):
                if txt.strip(): CommentHandler.add(post_id, txt); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_chat_interface():
    ac = st.session_state.get('active_chat'); ag = st.session_state.get('active_group'); ach = st.session_state.get('active_channel')
    if st.button("← Back", use_container_width=True, key="back"): st.session_state.active_chat = None; st.session_state.active_group = None; st.session_state.active_channel = None; st.rerun()
    if ac:
        msgs = ChatHandler.get_messages(ac)
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);">{render_avatar(ac, 32)}<div class="username-text">@{html.escape(ac)}</div></div>', unsafe_allow_html=True)
        for m in msgs:
            sent = m.get("from") == st.session_state.user; cls = "sent" if sent else "received"
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:{"flex-end" if sent else "flex-start"};padding:0 4px;"><div class="chat-bubble {cls}">{html.escape(m.get("text",""))}{"<br>" + f"<img src=\\"{m.get(\\"media\\",\\"\\")}\\" style=\\"max-width:200px;border-radius:8px;margin-top:4px;\\">" if m.get("media") else ""}<div style="font-size:0.55rem;opacity:0.7;text-align:right;">{format_timestamp(m["timestamp"])}{" ✓✓" if sent and m.get("read") else " ✓" if sent else ""}</div></div></div>', unsafe_allow_html=True)
        with st.form(f"dmf_{ac}", clear_on_submit=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            with c1: txt = st.text_input("Message", placeholder="Type a message...", key=f"dmt_{ac}")
            with c2:
                media = st.file_uploader("📎", type=['png','jpg','jpeg','gif'], key=f"dmm_{ac}", label_visibility="collapsed")
            with c3:
                if st.form_submit_button("➤"):
                    md = None
                    if media: md = base64.b64encode(media.read()).decode()
                    if txt.strip() or md: ChatHandler.send(ac, txt, md, media.name if media else None); st.rerun()
    elif ag:
        msgs = GroupHandler.get_group_messages(ag); gd = DataManager.get_group_chats().get(ag, {})
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);"><div style="width:32px;height:32px;border-radius:50%;background:#667eea;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div><div><div class="username-text">{html.escape(gd.get("name","Group"))}</div><div style="color:#94a3b8;font-size:0.6rem;">{len(gd.get("members",[]))} members</div></div></div>', unsafe_allow_html=True)
        for m in msgs:
            sent = m.get("from") == st.session_state.user; cls = "sent" if sent else "received"; align = "flex-end" if sent else "flex-start"
            sender = "" if sent else f'<div style="color:#FFD700;font-size:0.6rem;">@{html.escape(m.get("from",""))}</div>'
            st.markdown(f'<div style="display:flex;flex-direction:column;align-items:{align};padding:0 4px;"><div class="chat-bubble {cls}">{sender}{html.escape(m.get("text",""))}<div style="font-size:0.55rem;opacity:0.7;text-align:right;">{format_timestamp(m["timestamp"])}</div></div></div>', unsafe_allow_html=True)
        with st.form(f"grpf_{ag}", clear_on_submit=True):
            c1, c2 = st.columns([5, 1])
            with c1: txt = st.text_input("Message", placeholder="Type...", key=f"grpt_{ag}")
            with c2:
                if st.form_submit_button("➤"):
                    if txt.strip(): GroupHandler.send_message(ag, txt); st.rerun()
    elif ach:
        msgs = GroupHandler.get_channel_messages(ach); cd = DataManager.get_channels().get(ach, {})
        is_admin = st.session_state.user in cd.get("admins", [])
        st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:6px 0;margin-bottom:6px;border-bottom:1px solid rgba(255,215,0,0.1);"><div style="width:32px;height:32px;border-radius:50%;background:#f093fb;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div><div><div class="username-text">{html.escape(cd.get("name","Channel"))}</div><div style="color:#94a3b8;font-size:0.6rem;">{len(cd.get("subscribers",[]))} subscribers</div></div></div>', unsafe_allow_html=True)
        for m in msgs:
            st.markdown(f'<div class="card" style="margin:4px 0;padding:6px 8px;"><div style="display:flex;align-items:center;gap:5px;">{render_avatar(m.get("from",""), 24)}<div><div class="username-text">@{html.escape(m.get("from",""))}</div><div class="timestamp">{format_timestamp(m["timestamp"])}</div></div></div><div style="color:#e2e8f0;font-size:0.8rem;margin-top:3px;">{html.escape(m.get("text",""))}</div></div>', unsafe_allow_html=True)
        if is_admin:
            with st.form(f"chnf_{ach}", clear_on_submit=True):
                c1, c2 = st.columns([5, 1])
                with c1: txt = st.text_input("Broadcast", placeholder="Post to channel...", key=f"chnt_{ach}")
                with c2:
                    if st.form_submit_button("📢"):
                        if txt.strip(): GroupHandler.send_message(ach, txt, is_channel=True); st.rerun()

def render_create_modal():
    if not st.session_state.get('show_create_modal'): return
    st.markdown(f'<div class="modal-overlay"><div class="modal-box"><h3 style="color:#FFD700;text-align:center;margin-bottom:10px;">✨ Create Post</h3>', unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📝 Post", "📊 Poll", "📷 Story"])
    with t1:
        with st.form("cpf", clear_on_submit=True):
            text = st.text_area("What's on your mind?", max_chars=MAX_POST_LENGTH, height=100, placeholder="Share your thoughts with the world...")
            media = st.file_uploader("Add media", type=['png','jpg','jpeg','gif','webp'], key="mup")
            location = st.text_input("Location", placeholder="Add location (optional)", key="cpl")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📤 Post", use_container_width=True):
                    md, mn = None, None
                    if media and media.size <= MAX_FILE_SIZE:
                        fb = media.read()
                        if validate_image(fb): md = base64.b64encode(fb).decode(); mn = media.name
                    if text.strip() or md: PostHandler.create(text, md, mn, location=location); st.session_state.show_create_modal = False; st.rerun()
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    with t2:
        with st.form("cplf", clear_on_submit=True):
            q = st.text_input("Poll question", max_chars=500, placeholder="What do you want to ask?")
            opts = st.text_area("Options (one per line, max 20)", height=100, placeholder="Option 1\nOption 2\nOption 3")
            duration = st.slider("Duration (hours)", 1, 168, 24)
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📊 Create Poll", use_container_width=True):
                    if q and opts:
                        olist = [o.strip() for o in opts.split('\n') if o.strip()]
                        if len(olist) >= 2: PostHandler.create_poll(q, olist, duration); st.session_state.show_create_modal = False; st.rerun()
                        else: st.error("Need at least 2 options")
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    with t3:
        with st.form("csf", clear_on_submit=True):
            sm = st.file_uploader("Story image", type=['png','jpg','jpeg','gif','webp'], key="sup")
            caption = st.text_input("Caption", placeholder="Add caption (optional)", key="scap")
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("📷 Post Story", use_container_width=True):
                    if sm and sm.size <= MAX_FILE_SIZE:
                        fb = sm.read()
                        if validate_image(fb): StoryHandler.create(base64.b64encode(fb).decode(), sm.name, caption); st.session_state.show_create_modal = False; st.rerun()
                    else: st.error("Please select an image")
            with c2:
                if st.form_submit_button("Cancel", use_container_width=True): st.session_state.show_create_modal = False; st.rerun()
    if st.button("✕ Close", use_container_width=True, key="close_modal"): st.session_state.show_create_modal = False; st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)

def render_bottom_nav():
    current = st.session_state.get('current_tab', 'feed')
    theme = get_theme()
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    tabs = [("feed", "🏠", "Feed"), ("explore", "🔍", "Explore"), ("create", "➕", "Create"), ("chats", "💬", "Chats"), ("profile", "👤", "Profile")]
    cols = st.columns(5)
    for i, (tab, icon, label) in enumerate(tabs):
        with cols[i]:
            if current == tab:
                st.markdown(f'<div style="text-align:center;padding:2px;"><div style="font-size:1.2rem;color:#FFD700;">{icon}</div><div style="font-size:0.5rem;color:#FFD700;font-weight:600;">{label}</div></div>', unsafe_allow_html=True)
            else:
                if st.button(icon, key=f"nav_{tab}", use_container_width=True, help=label):
                    if tab == "create": st.session_state.show_create_modal = True
                    else: st.session_state.current_tab = tab; st.session_state.show_create_modal = False; st.session_state.active_chat = None; st.session_state.active_group = None; st.session_state.active_channel = None
                    st.rerun()
                st.markdown(f'<div style="text-align:center;font-size:0.48rem;color:{theme["secondary"]};margin-top:-6px;">{label}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== PAGES ==========
def render_feed_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    render_stories_bar()
    if st.button("✨ What's on your mind? Tap to post...", use_container_width=True, key="qp"): st.session_state.show_create_modal = True; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    posts = st.session_state.feed_posts
    if not posts:
        emoji_html = get_socialite_emoji_html(100)
        st.markdown(f'<div style="text-align:center;padding:3rem 1rem;color:#94a3b8;"><div class="socialite-emoji">{emoji_html}</div><h3 style="color:#FFD700;margin-top:1rem;">Welcome to {APP_NAME}</h3><p style="font-size:0.9rem;">{APP_SLOGAN}</p><p style="font-size:0.8rem;">Follow users or create your first post to get started!</p></div>', unsafe_allow_html=True)
    else:
        for post in reversed(posts[-50:]):
            if post.get("type") == "poll": render_poll_card(post)
            else: render_post_card(post)
    st.markdown('</div>', unsafe_allow_html=True)

def render_explore_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">🔍 Explore Users</h3>', unsafe_allow_html=True)
    search = st.text_input("Search", placeholder="Search by username...", key="es")
    users = list(DataManager.get_users().keys())
    filtered = [u for u in users if u != st.session_state.user and (not search or search.lower() in u.lower())]
    if search and not filtered: st.info("No users found")
    for u in filtered[:50]:
        profile = DataManager.get_profile(u); is_following = FollowHandler.is_following(u)
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            bio_preview = (profile.get("bio","") or "No bio")[:60]
            st.markdown(f'<div style="display:flex;align-items:center;gap:6px;padding:4px 0;">{render_avatar(u, 34)}<div><div class="username-text">@{html.escape(u)}{" ✓✓" if profile.get("is_verified") else ""}{" 👑" if profile.get("is_premium") else ""}</div><div style="color:#94a3b8;font-size:0.65rem;">{len(profile.get("followers",[]))} followers · {html.escape(bio_preview)}</div></div></div>', unsafe_allow_html=True)
        with c2:
            if st.button("✓ Following" if is_following else "+ Follow", key=f"ef_{u}", use_container_width=True): FollowHandler.follow(u); st.rerun()
        with c3:
            if st.button("💬", key=f"em_{u}", use_container_width=True): st.session_state.active_chat = u; st.session_state.current_tab = "chats"; st.rerun()
        st.markdown("<hr style='border-color:rgba(255,215,0,0.04);margin:0;'>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_chats_page():
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    if st.session_state.get('active_chat') or st.session_state.get('active_group') or st.session_state.get('active_channel'): render_chat_interface(); st.markdown('</div>', unsafe_allow_html=True); return
    st.markdown('<h3 style="color:#FFD700;margin-bottom:6px;">💬 Messages</h3>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("💬 New Chat", use_container_width=True, key="nc"): st.session_state.show_new_chat = True
    with c2:
        if st.button("👥 New Group", use_container_width=True, key="ng"): st.session_state.show_new_group = True
    with c3:
        if st.button("📢 New Channel", use_container_width=True, key="nch"): st.session_state.show_new_channel = True
    t1, t2, t3 = st.tabs(["📱 Direct Messages", "👥 Groups", "📢 Channels"])
    with t1:
        chats = ChatHandler.get_chat_list()
        if chats:
            for ch in chats:
                dot = '<span class="online-dot"></span>' if ch['is_online'] else ''
                unread = f'<span class="unread-count">{ch["unread"]}</span>' if ch['unread'] > 0 else ''
                st.markdown(f'<div class="user-row" style="justify-content:space-between;"><div style="display:flex;align-items:center;gap:6px;flex:1;">{render_avatar(ch["with_user"], 36)}<div style="flex:1;min-width:0;"><div style="display:flex;align-items:center;gap:3px;"><span class="username-text">@{html.escape(ch["with_user"])}</span>{dot}</div><div style="color:#94a3b8;font-size:0.65rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{html.escape(ch["last_message"])}</div></div></div><div style="text-align:right;flex-shrink:0;"><div class="timestamp">{format_timestamp(ch["last_time"])}</div>{unread}</div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"oc_{ch['with_user']}"): st.session_state.active_chat = ch['with_user']; st.rerun()
                st.markdown("<hr style='border-color:rgba(255,215,0,0.03);margin:0;'>", unsafe_allow_html=True)
        else: st.info("No conversations yet. Start a new chat!")
        if st.session_state.get('show_new_chat'):
            with st.expander("New Chat", expanded=True):
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                if avail:
                    sel = st.selectbox("Select user", avail, key="ncs")
                    if st.button("Start Chat", use_container_width=True): st.session_state.active_chat = sel; st.session_state.show_new_chat = False; st.rerun()
                else: st.info("No other users available")
    with t2:
        groups = GroupHandler.get_user_groups()
        if groups:
            for gr in groups:
                st.markdown(f'<div class="user-row"><div style="width:36px;height:36px;border-radius:50%;background:#667eea;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">G</div><div><div class="username-text">{html.escape(gr["name"])}</div><div style="color:#94a3b8;font-size:0.65rem;">{gr["members"]} members · {html.escape(gr.get("description","")[:30])}</div></div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"og_{gr['id']}"): st.session_state.active_group = gr['id']; st.rerun()
        else: st.info("No groups yet. Create one!")
        if st.session_state.get('show_new_group'):
            with st.expander("New Group", expanded=True):
                gn = st.text_input("Group name", max_chars=100, key="ngn", placeholder="Enter group name")
                gd = st.text_area("Description", max_chars=500, key="ngd", placeholder="Group description (optional)")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                mems = st.multiselect("Add members", avail, key="ngm")
                if st.button("Create Group", use_container_width=True) and gn: GroupHandler.create(gn, mems, description=gd); st.session_state.show_new_group = False; st.rerun()
    with t3:
        channels = GroupHandler.get_user_channels()
        if channels:
            for ch in channels:
                st.markdown(f'<div class="user-row"><div style="width:36px;height:36px;border-radius:50%;background:#f093fb;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;">C</div><div><div class="username-text">{html.escape(ch["name"])}</div><div style="color:#94a3b8;font-size:0.65rem;">{ch["subscribers"]} subscribers · {html.escape(ch.get("description","")[:30])}</div></div></div>', unsafe_allow_html=True)
                if st.button("Open", key=f"och_{ch['id']}"): st.session_state.active_channel = ch['id']; st.rerun()
        else: st.info("No channels yet. Create one!")
        if st.session_state.get('show_new_channel'):
            with st.expander("New Channel", expanded=True):
                cn = st.text_input("Channel name", max_chars=100, key="nchn", placeholder="Enter channel name")
                cd = st.text_area("Description", max_chars=500, key="nchd", placeholder="Channel description (optional)")
                avail = [u for u in list(DataManager.get_users().keys()) if u != st.session_state.user]
                subs = st.multiselect("Add subscribers", avail, key="nchs")
                if st.button("Create Channel", use_container_width=True) and cn: GroupHandler.create(cn, subs or [], is_channel=True, description=cd); st.session_state.show_new_channel = False; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

def render_profile_page():
    user = st.session_state.user; profile = DataManager.get_profile(user); theme = get_theme()
    st.markdown('<div class="content-wrapper">', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center;padding:12px 0;">{render_avatar(user, 72)}<h2 style="color:#FFD700;margin-top:6px;">@{html.escape(user)}{" <span style=\\"color:#FFD700;font-size:1rem;\\">✓✓</span>" if profile.get("is_verified") else ""}{" <span style=\\"color:#FFD700;font-size:0.9rem;\\">👑</span>" if profile.get("is_premium") else ""}</h2><p style="color:{theme["secondary"]};font-size:0.8rem;">{html.escape(profile.get("bio","No bio yet"))}</p>{f"<p style=\\"color:{theme[\\"secondary\\"]};font-size:0.7rem;\\">🌐 {html.escape(profile.get(\\"website\\",\\"\\"))}</p>" if profile.get("website") else ""}{f"<p style=\\"color:{theme[\\"secondary\\"]};font-size:0.7rem;\\">📍 {html.escape(profile.get(\\"location\\",\\"\\"))}</p>" if profile.get("location") else ""}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="display:flex;justify-content:space-around;text-align:center;padding:10px;border-top:1px solid rgba(255,215,0,0.1);border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:10px;"><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{profile.get("post_count",0)}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Posts</div></div><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("followers",[]))}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Followers</div></div><div><div style="color:#FFD700;font-size:1.1rem;font-weight:700;">{len(profile.get("following",[]))}</div><div style="color:{theme["secondary"]};font-size:0.55rem;">Following</div></div></div>', unsafe_allow_html=True)
    
    with st.expander("✏️ Edit Profile"):
        with st.form("epf"):
            display_name = st.text_input("Display Name", value=profile.get("display_name", user))
            bio = st.text_area("Bio", value=profile.get("bio",""), max_chars=MAX_BIO_LENGTH, placeholder="Tell people about yourself...")
            website = st.text_input("Website", value=profile.get("website",""), placeholder="https://...")
            location = st.text_input("Location", value=profile.get("location",""), placeholder="City, Country")
            gender = st.selectbox("Gender", ["male","female"], index=0 if profile.get("gender","male")=="male" else 1)
            is_private = st.checkbox("Private Account", value=profile.get("is_private", False))
            avatar_file = st.file_uploader("Profile Picture", type=['png','jpg','jpeg','webp'], key="pau")
            cover_file = st.file_uploader("Cover Photo", type=['png','jpg','jpeg','webp'], key="pcu")
            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                updates = {"display_name": sanitize_text(display_name, 50), "bio": sanitize_text(bio, MAX_BIO_LENGTH), "website": sanitize_text(website, 200), "location": sanitize_text(location, 100), "gender": gender, "is_private": is_private}
                if avatar_file and avatar_file.size <= MAX_AVATAR_SIZE:
                    try:
                        img = Image.open(avatar_file)
                        if img.mode in ('RGBA','LA','P'): bg = Image.new('RGB', img.size, (255,255,255)); bg.paste(img.convert('RGBA'), mask=img.split()[-1] if img.mode=='RGBA' else None); img = bg
                        else: img = img.convert("RGB")
                        img.thumbnail((400,400)); path = UPLOADS_DIR / f"{user}_avatar.jpg"; img.save(path, "JPEG", quality=85); updates["avatar"] = str(path)
                    except: st.error("Failed to process avatar")
                if cover_file and cover_file.size <= MAX_FILE_SIZE:
                    try:
                        img = Image.open(cover_file); img = img.convert("RGB")
                        img.thumbnail((1200,400)); path = UPLOADS_DIR / f"{user}_cover.jpg"; img.save(path, "JPEG", quality=85); updates["cover_photo"] = str(path)
                    except: st.error("Failed to process cover")
                DataManager.update_profile(user, updates); st.success("Profile updated!"); st.rerun()
    
    with st.expander("🎨 Themes (24)"):
        st.markdown('<div class="theme-grid">', unsafe_allow_html=True)
        ct = profile.get('theme','midnight')
        for tk, td in THEMES.items():
            sel = "selected" if ct == tk else ""
            st.markdown(f'<div class="theme-card {sel}" style="background:{td["gradient"]};"><div style="font-size:1.3rem;">{td["icon"]}</div><div style="color:white;font-size:0.6rem;margin-top:3px;">{td["name"]}</div></div>', unsafe_allow_html=True)
            if st.button("Apply", key=f"th_{tk}"): DataManager.update_profile(user, {"theme": tk}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("🖼️ Wallpapers (30)"):
        st.markdown('<div class="wallpaper-grid">', unsafe_allow_html=True)
        cw = profile.get('wallpaper','wp_socialite')
        for wk, wd in WALLPAPERS.items():
            sel = "selected" if cw == wk else ""
            bg_style = f"background-image:url('{wd['url']}');" if wd.get("url") else f"background:{wd.get('gradient','')};"
            st.markdown(f'<div class="wallpaper-card {sel}" style="{bg_style}" title="{wd["name"]}"></div>', unsafe_allow_html=True)
            if st.button("Apply", key=f"wp_{wk}"): DataManager.update_profile(user, {"wallpaper": wk}); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    
    posts = [p for p in st.session_state.feed_posts if p.get("username")==user]
    if posts:
        st.markdown(f'<h4 style="color:#FFD700;margin-top:10px;">Your Posts ({len(posts)})</h4>', unsafe_allow_html=True)
        for post in reversed(posts[-30:]):
            if post.get("type")=="poll": render_poll_card(post)
            else: render_post_card(post)
    
    if st.button("🚪 Sign Out", use_container_width=True, key="so"):
        for k in list(st.session_state.keys()): del st.session_state[k]; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ========== AUTH ==========
def render_auth():
    st.markdown("<style>html,body{overflow:auto!important;height:auto!important;position:relative!important;}.stApp{position:relative!important;overflow:auto!important;}</style>", unsafe_allow_html=True)
    _, c, _ = st.columns([1, 2, 1])
    with c:
        emoji_html = get_socialite_emoji_html(120)
        st.markdown(f"""
        <div style="text-align:center;padding:2rem 0;">
            <div class="socialite-emoji">{emoji_html}</div>
            <h1 style="font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:900;background:linear-gradient(135deg,#FFD700,#FFA500,#FFD700);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:1rem;">Socialite</h1>
            <p style="color:#94a3b8;font-size:1rem;font-family:'Playfair Display',serif;">{APP_SLOGAN}</p>
            <p style="color:#64748b;font-size:0.75rem;">Feed · Stories · Chat · Groups · Channels</p>
        </div>
        """, unsafe_allow_html=True)
        t1, t2 = st.tabs(["🔑 Sign In", "✨ Create Account"])
        with t1:
            with st.form("li"):
                u = st.text_input("Username", placeholder="Enter your username", key="li_u")
                p = st.text_input("Password", type="password", placeholder="Enter your password", key="li_p")
                if st.form_submit_button("🔓 Sign In", use_container_width=True):
                    if u and p:
                        ok, res = DataManager.authenticate(u, p)
                        if ok: st.session_state.auth = True; st.session_state.user = res; st.session_state.feed_posts = DataManager.get_feed_posts(); st.session_state.stories = DataManager.get_stories(); st.rerun()
                        else: st.error(res)
                    else: st.error("Please fill all fields")
        with t2:
            with st.form("su"):
                u = st.text_input("Choose Username", placeholder=f"3-{MAX_USERNAME_LENGTH} characters", key="su_u")
                e = st.text_input("Email (optional)", placeholder="your@email.com", key="su_e")
                p = st.text_input("Choose Password", type="password", placeholder=f"Min {MIN_PASSWORD_LENGTH} characters", key="su_p")
                cp = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="su_cp")
                if st.form_submit_button("✨ Create Account", use_container_width=True):
                    if not u or not p: st.error("Please fill all required fields")
                    elif p != cp: st.error("Passwords don't match")
                    elif len(p) < MIN_PASSWORD_LENGTH: st.error(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
                    elif len(u) < 3 or len(u) > MAX_USERNAME_LENGTH: st.error(f"Username must be 3-{MAX_USERNAME_LENGTH} characters")
                    elif not re.match(r'^[a-zA-Z0-9_]+$', u): st.error("Only letters, numbers, and underscores")
                    else:
                        ok, msg = DataManager.create_user(u, p, e)
                        if ok: st.success(msg); st.info("You can now sign in!"); st.balloons()
                        else: st.error(msg)

# ========== MAIN ==========
def main():
    init_session()
    inject_styles()
    if not st.session_state.get('auth'): render_auth(); return
    render_header()
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    tab = st.session_state.get('current_tab', 'feed')
    if tab == "feed": render_feed_page()
    elif tab == "explore": render_explore_page()
    elif tab == "chats": render_chats_page()
    elif tab == "profile": render_profile_page()
    st.markdown('</div>', unsafe_allow_html=True)
    if st.session_state.get('show_create_modal'): render_create_modal()
    render_bottom_nav()

if __name__ == "__main__":
    main()
