from fastapi import FastAPI, HTTPException
from pydantic_models import QueryInput, QueryResponse, EmailAuth
from langchain_utils import handle_email_query
from db_utils import insert_application_logs, get_chat_history, get_all_sessions
from email_utils import authenticate_email, fetch_emails
from preprocessing_indexing import index_email
from uuid import uuid4
import logging


logging.basicConfig(filename='app.log', level=logging.INFO)

app = FastAPI()



@app.post("/chat", response_model=QueryResponse)
def chat(query_input: QueryInput):
    session_id = query_input.session_id or str(uuid4())

    insert_application_logs(
        session_id=session_id,
        user_query=query_input.question,
        gpt_response="",
        model=query_input.model.value
    )

    raw_history = get_chat_history(session_id)
    formatted_history = []
    for entry in raw_history:
        role = "user" if entry["role"] == "human" else "assistant"
        formatted_history.append({
            "role": role,
            "content": entry["content"]
        })

    answer = handle_email_query(
        user_input=query_input.question,
        chat_history=formatted_history,
        model=query_input.model.value
    )

    insert_application_logs(
        session_id=session_id,
        user_query=query_input.question,
        gpt_response=answer,
        model=query_input.model.value
    )

    return QueryResponse(
        answer=answer,
        session_id=session_id,
        model=query_input.model
    )


@app.post("/load-emails", response_model=dict)
def load_emails(auth: EmailAuth):
    client = authenticate_email(auth.email, auth.password)
    if not client:
        raise HTTPException(status_code=400,
                            detail="Ошибка аутентификации. Проверьте email и пароль приложения).")

    emails = fetch_emails(client, search_criteria="ALL", num_emails=20)
    client.logout()

    if not emails:
        raise HTTPException(status_code=404, detail="Письма не найдены.")

    indexed_count = 0
    for i, email_data in enumerate(emails, start=1):
        success = index_email(email_data, file_id=i)
        if success:
            indexed_count += 1

    return {"status": "success", "emails_indexed": indexed_count}


@app.get("/sessions/{session_id}", response_model=list[dict])
def get_session_history(session_id: str):
    raw = get_chat_history(session_id)
    formatted = []
    for entry in raw:
        role = "user" if entry["role"] == "human" else "assistant"
        formatted.append({"role": role, "content": entry["content"]})
    return formatted

@app.get("/sessions", response_model=list[str])
def list_sessions():
    return get_all_sessions()

