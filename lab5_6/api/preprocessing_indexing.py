import re
import html
from bs4 import BeautifulSoup
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="./chroma_db", embedding_function=embedding_function)

def clean_email_text(text: str) -> str:
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator=" ")
    clean = html.unescape(clean)
    return re.sub(r'\s+', ' ', clean).strip()

def index_email(email_data: dict, file_id: int) -> bool:
    try:
        sender = email_data.get("from", "")
        subject = email_data.get("subject", "")
        date_obj = email_data.get("date")
        date_str = date_obj.isoformat() if date_obj else ""
        message_id = email_data.get("id", "")

        raw_text = (
            f"От: {sender}\n"
            f"Тема: {subject}\n"
            f"Дата: {date_str}\n\n"
            f"Сообщение: {email_data.get('body', '')}"
        )
        clean_text = clean_email_text(raw_text)

        chunks = text_splitter.split_text(clean_text)
        documents = []
        for idx, chunk in enumerate(chunks):
            metadata = {
                "file_id": file_id,
                "sender": sender,
                "subject": subject,
                "date": date_str,
                "message_id": message_id,
                "chunk_index": idx
            }
            documents.append(Document(page_content=chunk, metadata=metadata))

        vectorstore.add_documents(documents)
        return True

    except Exception as e:
        print(f"Ошибка индексирования (file_id={file_id}): {e}")
        return False

def keyword_search(query: str) -> list:
    return vectorstore.similarity_search(query, k=5)
