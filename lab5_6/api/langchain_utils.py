import re
from typing import List, Dict
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from preprocessing_indexing import vectorstore

qa_prompt = ChatPromptTemplate.from_messages([
    ("system", "Вы — помощник, отвечающий на вопросы пользователя на основе загруженных писем."),
    ("system", "Контекст для ответа: {context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}")
])


def get_rag_chain(model: str = "gpt-4o-mini"):
    llm = ChatOllama(model=model)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    qa_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(retriever, qa_chain)

def query_emails_by_sender(sender_email: str) -> List[Dict]:
    found = vectorstore._collection.get(where={"sender": sender_email})
    docs = []
    for content, meta in zip(found["documents"], found["metadatas"]):
        docs.append({
            "from": meta["sender"],
            "subject": meta["subject"],
            "date": meta["date"],
            "body": content
        })
    return docs

def handle_email_query(user_input: str, chat_history: List[Dict], model: str) -> str:
    if match := re.search(r"письма от\s+([\w\.-]+@[\w\.-]+)", user_input.lower()):
        sender = match.group(1)
        docs = query_emails_by_sender(sender)
        if not docs:
            return "Нет подходящих писем."
        return "\n\n".join(
            f"От: {d['from']}\nТема: {d['subject']}\nДата: {d['date']}\nСообщение: {d['body']}"
            for d in docs
        )

    rag_chain = get_rag_chain(model)
    response = rag_chain.invoke({
        "input": user_input,
        "chat_history": chat_history,
        "context": "Писем с запросом: уже проиндексированных."
    })
    if isinstance(response, dict) and response.get('answer'):
        return response['answer']
    return str(response)

