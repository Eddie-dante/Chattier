import streamlit as st
import json
import os
from datetime import datetime
import uuid

# Page config MUST be the first Streamlit command
st.set_page_config(
    page_title="ChatVerse • Community Forum",
    page_icon="💬",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        display: flex;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message.user {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(96, 165, 250, 0.1));
        border: 1px solid rgba(59, 130, 246, 0.3);
        margin-left: 20%;
    }
    
    .chat-message.other {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-right: 20%;
    }
    
    .chat-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.2rem;
        margin-right: 1rem;
        flex-shrink: 0;
    }
    
    .user-avatar {
        background: linear-gradient(135deg, #3b82f6, #60a5fa);
    }
    
    .other-avatar {
        background: linear-gradient(135deg, #7c3aed, #a78bfa);
    }
    
    .chat-content {
        flex: 1;
    }
    
    .chat-author {
        font-weight: 600;
        font-size: 0.9rem;
        color: #cbd5e1;
        margin-bottom: 0.3rem;
    }
    
    .chat-time {
        font-size: 0.7rem;
        color: #64748b;
        margin-left: 0.5rem;
    }
    
    .chat-text {
        color: #f1f5f9;
        line-height: 1.5;
    }
    
    /* Header */
    .header-container {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .online-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(255, 255, 255, 0.08);
        padding: 0.3rem 1rem;
        border-radius: 2rem;
        font-size: 0.8rem;
    }
    
    .online-dot {
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .chat-message.user {
            margin-left: 5%;
        }
        .chat-message.other {
            margin-right: 5%;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'username' not in st.session_state:
    st.session_state.username = "Guest_" + str(uuid.uuid4())[:6]

# File for storing messages
MESSAGES_FILE = "chat_messages.json"

def load_messages():
    """Load messages from file"""
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    # Default messages if file doesn't exist
    return [
        {
            "id": "1",
            "username": "Astra",
            "text": "Welcome to ChatVerse! 🌟 This is a live community forum. Feel free to chat!",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "2",
            "username": "Nebula",
            "text": "Hey everyone! Love the vibe here. What's everyone up to? ✨",
            "timestamp": datetime.now().isoformat()
        }
    ]

def save_messages():
    """Save messages to file"""
    try:
        with open(MESSAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
    except:
        pass

# Load messages on startup
if len(st.session_state.messages) == 0:
    st.session_state.messages = load_messages()

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
    <div class="header-container">
        <h1 style="background: linear-gradient(to right, #c084fc, #a78bfa); 
                   -webkit-background-clip: text; 
                   -webkit-text-fill-color: transparent;
                   font-size: 2.5rem;
                   margin-bottom: 0.5rem;">
            💬 ChatVerse
        </h1>
        <div class="online-badge">
            <span class="online-dot"></span>
            <span>Community Forum</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎨 Settings")
    
    # Username input
    new_username = st.text_input("Your Display Name", value=st.session_state.username, max_chars=20)
    if new_username:
        st.session_state.username = new_username
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🗑️ Clear All Messages", use_container_width=True):
        st.session_state.messages = []
        save_messages()
        st.success("Chat cleared!")
        st.rerun()
    
    st.markdown("---")
    
    # Stats
    st.markdown("### 📊 Stats")
    st.metric("Total Messages", len(st.session_state.messages))
    
    st.markdown("---")
    st.markdown("""
    ### ℹ️ About
    **ChatVerse** is a community forum where everyone can share ideas and connect.
    
    ✨ **Features:**
    - Persistent messages
    - Custom usernames
    - Beautiful design
    """)

# Main chat area
st.markdown("## 💬 Community Chat")

# Function to add message
def add_message():
    if st.session_state.message_input and st.session_state.message_input.strip():
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": st.session_state.message_input.strip(),
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.messages.append(new_msg)
        save_messages()
        st.session_state.message_input = ""  # Clear input
        st.rerun()

# Display messages
if not st.session_state.messages:
    st.info("💫 No messages yet. Start the conversation!")
else:
    # Display messages in reverse order (newest first)
    for msg in reversed(st.session_state.messages):
        is_user = msg['username'] == st.session_state.username
        avatar_letter = msg['username'][0].upper() if msg['username'] else "?"
        
        # Format time
        try:
            msg_time = datetime.fromisoformat(msg['timestamp'])
            time_str = msg_time.strftime("%I:%M %p")
        except:
            time_str = "Just now"
        
        # Create message HTML
        message_html = f"""
        <div class="chat-message {'user' if is_user else 'other'}">
            <div class="chat-avatar {'user-avatar' if is_user else 'other-avatar'}">
                {avatar_letter}
            </div>
            <div class="chat-content">
                <div class="chat-author">
                    {msg['username']}
                    <span class="chat-time">{time_str}</span>
                </div>
                <div class="chat-text">
                    {msg['text']}
                </div>
            </div>
        </div>
        """
        st.markdown(message_html, unsafe_allow_html=True)

# Message input
st.markdown("---")

# Use form for better handling
with st.form(key="message_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        message = st.text_input(
            "Message",
            placeholder="Type your message here...",
            key="message_input",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("📤 Send", use_container_width=True)
    
    if submitted and message and message.strip():
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": message.strip(),
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.messages.append(new_msg)
        save_messages()
        st.rerun()

# Footer
st.markdown("""
<div style="text-align: center; padding: 1rem; color: #64748b; font-size: 0.8rem;">
    ✨ Be kind • Stay curious • Connect with others ✨
</div>
""", unsafe_allow_html=True)
