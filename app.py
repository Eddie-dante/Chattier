import streamlit as st
import datetime
import hashlib
import json
import os

st.set_page_config(page_title="ChatVerse", page_icon="💬", layout="wide")

# File paths
USERS_FILE = "users.json"
MESSAGES_FILE = "messages.json"

# Helper functions
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def load_msgs():
    if os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'r') as f:
            return json.load(f)
    return []

def save_msgs(msgs):
    with open(MESSAGES_FILE, 'w') as f:
        json.dump(msgs, f)

# Session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'msgs' not in st.session_state:
    st.session_state.msgs = load_msgs()

# CSS
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
}
[data-testid="stChatMessage"] {
    background: rgba(255, 255, 255, 0.08) !important;
    backdrop-filter: blur(18px) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 1rem !important;
}
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.8) !important;
    backdrop-filter: blur(18px) !important;
}
h1 {
    background: linear-gradient(135deg, #c084fc, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)

# Login/Signup
if not st.session_state.logged_in:
    st.title("💬 ChatVerse")
    
    choice = st.radio("", ["Sign In", "Sign Up"], horizontal=True)
    
    if choice == "Sign In":
        with st.form("login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            btn = st.form_submit_button("Sign In")
            if btn:
                users = load_users()
                if user in users and users[user] == hash_password(pwd):
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Wrong username or password")
    
    else:
        with st.form("signup"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm", type="password")
            btn = st.form_submit_button("Sign Up")
            if btn:
                if not user or not pwd:
                    st.error("Fill all fields")
                elif pwd != confirm:
                    st.error("Passwords don't match")
                else:
                    users = load_users()
                    if user in users:
                        st.error("Username taken")
                    else:
                        users[user] = hash_password(pwd)
                        save_users(users)
                        st.success("Account created! Sign in now.")

# Main chat
else:
    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("💬 ChatVerse")
    with col2:
        count = len(set(m['user'] for m in st.session_state.msgs)) + 1
        st.markdown(f"🟢 {count} online")
    with col3:
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.session_state.user = ""
            st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.write(f"### 👤 {st.session_state.user}")
        st.write("---")
        st.metric("Messages", len(st.session_state.msgs))
        if st.button("Clear Chat"):
            st.session_state.msgs = []
            save_msgs(st.session_state.msgs)
            st.rerun()
        st.write("---")
        st.info("✨ Glass morphism chat")
    
    # Chat area
    st.write("### 💬 Live Chat")
    
    # Load latest messages
    st.session_state.msgs = load_msgs()
    
    # Show messages
    if not st.session_state.msgs:
        st.info("No messages yet")
    else:
        for m in st.session_state.msgs:
            if m['user'] == st.session_state.user:
                with st.chat_message("user"):
                    st.write(f"**{m['user']}** `{m['time']}`")
                    st.write(m['text'])
            else:
                with st.chat_message("assistant"):
                    st.write(f"**{m['user']}** `{m['time']}`")
                    st.write(m['text'])
    
    # Input
    msg = st.chat_input("Type here...")
    if msg:
        new = {
            'user': st.session_state.user,
            'text': msg,
            'time': datetime.datetime.now().strftime("%I:%M %p")
        }
        st.session_state.msgs.append(new)
        save_msgs(st.session_state.msgs)
        st.rerun()
