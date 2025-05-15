import streamlit as st
from api_utils import list_sessions
import requests


def display_email_loader():

    st.sidebar.header("Сессии")
    sessions = list_sessions()
    session_options = ["Новая беседа"] + sessions
    if st.session_state.session_id in sessions:
        default_index = sessions.index(st.session_state.session_id) + 1
    else:
        default_index = 0
    selected = st.sidebar.selectbox(
        "Выберите сессию",
        options = session_options,
        index = default_index,
        key = "session_selector"
    )

    if selected == "Новая беседа":
        st.session_state.session_id = None
        st.session_state.messages = []
        st.session_state.history_loaded = False
    else:
        if selected != st.session_state.session_id:
            st.session_state.session_id = selected
            st.session_state.messages = []
            st.session_state.history_loaded = False

    st.sidebar.header("Загрузить письма")
    email_input = st.sidebar.text_input("Введите ваш email", key="loader_email")
    password_input = st.sidebar.text_input("Введите пароль приложения", key="loader_password", type="password")

    if st.sidebar.button("Загрузить письма"):
        if not email_input or not password_input:
            st.sidebar.error("Укажите email и пароль")
            return
        with st.spinner("Загрузка писем..."):
            data = {"email": email_input, "password": password_input}
            try:
                response = requests.post("http://localhost:8000/load-emails", json=data)
                if response.status_code == 200:
                    result = response.json()
                    st.sidebar.success(f"Загружено и проиндексировано писем: {result.get('emails_indexed')}")
                else:
                    st.sidebar.error(f"Ошибка: {response.text}")
            except Exception as e:
                st.sidebar.error(f"Ошибка подключения: {e}")



