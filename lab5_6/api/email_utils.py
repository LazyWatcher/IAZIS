import imapclient
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from bs4 import BeautifulSoup
import re

IMAP_SERVERS = {
    "gmail.com": "imap.gmail.com",
    "outlook.com": "imap-mail.outlook.com",
    "yahoo.com": "imap.mail.yahoo.com",
    "yandex.ru": "imap.yandex.ru",
    "mail.ru": "imap.mail.ru"
}

def get_imap_server(email_address):
    domain = email_address.split("@")[-1]
    return IMAP_SERVERS.get(domain, None)

def authenticate_email(email_address, password):
    imap_server = get_imap_server(email_address)
    if not imap_server:
        print("Неизвестный почтовый сервер для", email_address)
        return None

    try:
        client = imapclient.IMAPClient(imap_server, ssl=True)
        client.login(email_address, password)
        print(f"Успешный вход в {email_address}")
        return client
    except Exception as e:
        print("Ошибка аутентификации:", e)
        return None

def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)
    clean_text = re.sub(r'\s+', ' ', text)

    return clean_text.strip()

def fetch_emails(client, folder="INBOX", search_criteria="ALL", num_emails=100):
    client.select_folder(folder)
    message_ids = client.search([search_criteria])
    email_data = []

    for msg_id in message_ids[:num_emails]:
        raw = client.fetch([msg_id], ["RFC822"])[msg_id][b"RFC822"]
        msg = email.message_from_bytes(raw)

        subject, enc = decode_header(msg.get("Subject", ""))[0]
        if isinstance(subject, bytes):
            subject = subject.decode(enc or "utf-8", errors="ignore")
        else:
            subject = str(subject)

        sender = parseaddr(msg.get("From", ""))[1]

        date = None
        date_str = msg.get("Date")
        if date_str:
            try:
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = None

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"

                if ctype == "text/plain":
                    try:
                        body = payload.decode(charset, errors="ignore")
                        break
                    except:
                        continue
                if ctype == "text/html" and not body:
                    try:
                        html_body = payload.decode(charset, errors="ignore")
                        body = html_to_text(html_body)
                    except:
                        continue
        else:
            payload = msg.get_payload(decode=True) or b""
            ctype = msg.get_content_type()
            charset = msg.get_content_charset() or "utf-8"
            try:
                raw_text = payload.decode(charset, errors="ignore")
                if ctype == "text/html":
                    body = html_to_text(raw_text)
                else:
                    body = raw_text
            except:
                body = ""

        email_data.append({
            "id": msg_id,
            "from": sender,
            "subject": subject,
            "date": date,
            "body": body.strip()
        })

    return email_data

if __name__ == "__main__":
    email_address = input("Введите ваш email: ")
    password = input("Введите пароль приложения: ")

    client = authenticate_email(email_address, password)
    if client:
        emails = fetch_emails(client, num_emails=100)
        for e in emails:
            print(f"ID: {e['id']} | От: {e['from']} | Дата: {e['date']} | Тема: {e['subject']}")
            print(e['body'][:200] + '...')
            print('-'*50)
        client.logout()
