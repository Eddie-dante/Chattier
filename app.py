import streamlit as st
import datetime
import uuid
import hashlib
import json
import os
from PIL import Image
import io

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
if "profile_pics" not in st.session_state:
    st.session_state.profile_pics = {}
    users = load_users()
    for user in users:
        if "profile_pic" in users[user]:
            st.session_state.profile_pics[user] = users[user]["profile_pic"]

# Custom CSS - Bright wallpaper
st.markdown("""
<style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1600');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Glass effect for containers */
    .stApp > header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    /* Chat message styling */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 10px;
        margin: 10px 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    h1, h2, h3 {
        color: #1a1a2e !important;
    }
    
    .stMarkdown {
        color: #1a1a2e;
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
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            
            if submitted:
                users = load_users()
                if username in users and users[username]["password"] == hash_password(password):
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
            submitted = st.form_submit_button("Sign Up", use_container_width=True)
            
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
                        users[new_user] = {
                            "password": hash_password(new_pass),
                            "profile_pic": None,
                            "bio": "",
                            "joined": datetime.datetime.now().isoformat()
                        }
                        save_users(users)
                        st.success("Account created! Please sign in.")

else:
    # Main chat
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("💬 ChatVerse")
    with col2:
        st.markdown(f"**Welcome, {st.session_state.username}** 👋")
    with col3:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
    
    st.markdown("---")
    
    # Sidebar with profile
    with st.sidebar:
        st.markdown("## 👤 My Profile")
        
        # Profile picture
        users_data = load_users()
        current_user_data = users_data.get(st.session_state.username, {})
        
        col1, col2 = st.columns([1, 2])
        with col1:
            if current_user_data.get("profile_pic"):
                st.image(current_user_data["profile_pic"], width=80, caption="Profile")
            else:
                st.markdown(f"### 🧑\n\n**{st.session_state.username[0].upper()}**")
        
        with col2:
            st.markdown(f"**@{st.session_state.username}**")
            if current_user_data.get("bio"):
                st.caption(current_user_data["bio"])
        
        # Edit profile button
        with st.expander("✏️ Edit Profile"):
            # Profile picture upload
            uploaded_file = st.file_uploader("Upload Profile Picture", type=['jpg', 'png', 'jpeg'])
            if uploaded_file:
                # Save the image
                img = Image.open(uploaded_file)
                # Resize to small size
                img = img.resize((150, 150))
                # Save to user data
                users_data[st.session_state.username]["profile_pic"] = uploaded_file.getvalue()
                save_users(users_data)
                st.success("Profile picture updated!")
                st.rerun()
            
            # Bio
            new_bio = st.text_area("Bio", value=current_user_data.get("bio", ""), 
                                   placeholder="Tell us about yourself...")
            if st.button("Save Bio"):
                users_data[st.session_state.username]["bio"] = new_bio
                save_users(users_data)
                st.success("Bio updated!")
                st.rerun()
        
        st.markdown("---")
        
        # Chat stats
        st.markdown("## 📊 Chat Stats")
        st.metric("Total Messages", len(st.session_state.messages))
        if st.session_state.messages:
            unique_users = len(set(msg.get("username", "") for msg in st.session_state.messages if msg.get("username")))
            st.metric("Community Members", unique_users)
        
        st.markdown("---")
        
        # Clear chat button
        if st.button("🗑️ Clear All Messages", use_container_width=True):
            if st.checkbox("Confirm delete all messages?"):
                st.session_state.messages = []
                save_messages(st.session_state.messages)
                st.success("Chat cleared!")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🎨 About")
        st.info("✨ Welcome to ChatVerse! A bright, friendly community forum where everyone can connect, share ideas, and make friends. Be respectful and have fun!")
    
    # Display messages
    st.markdown("### 💬 Live Chat")
    
    if not st.session_state.messages:
        st.info("✨ No messages yet. Start the conversation!")
    else:
        for msg in st.session_state.messages:
            # Get profile picture if exists
            users_data = load_users()
            user_info = users_data.get(msg["username"], {})
            
            if msg["username"] == st.session_state.username:
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    st.write(msg["text"])
            else:
                # Use profile pic if available
                avatar = "💬"
                if user_info.get("profile_pic"):
                    # Would need to convert bytes to image, using emoji for simplicity
                    avatar = "👤"
                with st.chat_message("assistant", avatar=avatar):
                    st.markdown(f"**{msg['username']}**  `{msg['time']}`")
                    if user_info.get("bio"):
                        st.caption(f"📝 {user_info['bio'][:50]}")
                    st.write(msg["text"])
    
    # Message input
    st.markdown("---")
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
    
    # Footer
    st.markdown("---")
    st.caption("✨ Be kind • Stay curious • Connect with others ✨")
