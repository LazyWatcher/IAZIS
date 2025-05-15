import streamlit as st
from sidebar import display_email_loader
from chat_interface import display_chat_interface

st.title("Интеллектуальный ассистент")

if "model" not in st.session_state:
    st.session_state.model = "llama3.2"
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "selected_session" not in st.session_state:
    st.session_state.selected_session = None

display_email_loader()
display_chat_interface()

