import requests
import streamlit as st


def get_api_response(question, session_id, model):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model
    }
    if session_id:
        data["session_id"] = session_id

    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None


def get_chat_history(session_id):
    try:
        r = requests.get(f"http://localhost:8000/sessions/{session_id}")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.error(f"Failed to load history: {e}")
    return []

def list_sessions():
    try:
        r = requests.get("http://localhost:8000/sessions")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []