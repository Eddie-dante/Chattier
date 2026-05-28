import streamlit as st
import datetime
import uuid

st.set_page_config(page_title="ChatVerse", page_icon="💬")

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []
if "username" not in st.session_state:
    st.session_state.username = ""

st.title("💬 ChatVerse")

# Sidebar
with st.sidebar:
    st.session_state.username = st.text_input("Your name", st.session_state.username)
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()
    st.caption(f"Messages: {len(st.session_state.messages)}")

# Show messages
for msg in st.session_state.messages:
    with st.chat_message("user" if msg["name"] == st.session_state.username else "assistant"):
        st.markdown(f"**{msg['name']}** *{msg['time']}*")
        st.write(msg["text"])

# Input
if st.session_state.username:
    if prompt := st.chat_input("Type message..."):
        st.session_state.messages.append({
            "name": st.session_state.username,
            "text": prompt,
            "time": datetime.datetime.now().strftime("%H:%M")
        })
        st.rerun()
else:
    st.info("👈 Enter your name in sidebar to start")
