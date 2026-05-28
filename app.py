import streamlit as st
import datetime
import uuid
import hashlib
import json
import os

st.set_page_config(page_title="ChatVerse", page_icon="💬", layout="wide")

# File storage
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_messages(messages):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(messages, f)

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "messages" not in st.session_state:
    st.session_state.messages = load_messages()

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
    }
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #a855f7);
        color: white;
        border: none;
    }
    .stButton > button:hover {
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# Authentication
if not st.session_state.logged_in:
    st.title("💬 ChatVerse")
    st.markdown("### Welcome to the Community Forum")
    
    tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Sign Up"])
    
    with tab1:
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                users = load_users()
                if username in users and users[username] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("signup"):
            new_user = st.text_input("Choose Username")
            new_pass = st.text_input("Choose Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up")
            
            if submitted:
                if not new_user or not new_pass:
                    st.error("Fill all fields")
                elif new_pass != confirm:
                    st.error("Passwords don't match")
                else:
                    users = load_users()
                    if new_user in users:
                        st.error("Username already exists")
                    else:
                        users[new_user] = hash_password(new_pass)
                        save_users(users)
                        st.success("Account created! Please sign in.")
else:
    # Main chat
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("💬 ChatVerse")
    with col2:
        st.markdown(f"**👤 {st.session_state.username}**")
    with col3:
        if st.button("🚪 Sign Out"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Chat Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        unique_users = len(set(m["username"] for m in st.session_state.messages))
        st.metric("Community Members", unique_users)
        
        st.markdown("---")
        if st.button("🗑️ Clear All Messages"):
            st.session_state.messages = []
            save_messages(st.session_state.messages)
            st.success("Chat cleared!")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎨 About")
        st.info("Welcome to ChatVerse! A friendly community forum where everyone can connect and share ideas. Be respectful and have fun!")
    
    # Display messages
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            if msg["username"] == st.session_state.username:
                with st.chat_message("user"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
    
    # Message input
    prompt = st.chat_input("Type your message here...")
    
    if prompt:
        new_msg = {
            "id": str(uuid.uuid4()),
            "username": st.session_state.username,
            "text": prompt,
            "time": datetime.datetime.now().strftime("%I:%M %p")
        }
        st.session_state.messages.append(new_msg)
        save_messages(st.session_state.messages)
        st.rerun()
    
    st.markdown("---")
    st.caption("✨ Be kind • Stay curious • Connect with others ✨")
