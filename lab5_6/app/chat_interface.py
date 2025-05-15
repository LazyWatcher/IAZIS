import streamlit as st
from api_utils import get_api_response, get_chat_history

def display_chat_interface():
    if st.session_state.session_id and not st.session_state.get("history_loaded", False):
        hist = get_chat_history(st.session_state.session_id)
        if hist:
            st.session_state.messages = hist.copy()
        st.session_state.history_loaded = True

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Query:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            response = get_api_response(
                question=prompt,
                session_id=st.session_state.session_id,
                model=st.session_state.model
            )

            if response:
                st.session_state.session_id = response["session_id"]
                st.session_state.messages.append({"role": "assistant", "content": response["answer"]})

                with st.chat_message("assistant"):
                    st.markdown(response["answer"])

                    with st.expander("Details"):
                        st.subheader("Generated Answer")
                        st.code(response["answer"])
                        st.subheader("Model Used")
                        st.code(response["model"])
                        st.subheader("Session ID")
                        st.code(response["session_id"])
            else:
                st.error("Failed to get a response from the API. Please try again.")
