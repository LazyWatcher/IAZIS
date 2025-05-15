import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, simpledialog, Toplevel, Text, Label, Entry, Button
import os
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
import pickle


corpus = []
lemmatizer = WordNetLemmatizer()

def get_wordnet_pos(treebank_tag):
    if treebank_tag.startswith('J'):
        return nltk.corpus.wordnet.ADJ
    elif treebank_tag.startswith('V'):
        return nltk.corpus.wordnet.VERB
    elif treebank_tag.startswith('N'):
        return nltk.corpus.wordnet.NOUN
    elif treebank_tag.startswith('R'):
        return nltk.corpus.wordnet.ADV
    else:
        return nltk.corpus.wordnet.NOUN

def process_text(text, doc_name):
    processed_tokens = []
    raw_sentences = sent_tokenize(text)

    for sent_idx, sentence_text in enumerate(raw_sentences):
        raw_tokens = word_tokenize(sentence_text)
        if not raw_tokens:
            continue

        tagged_tokens = nltk.pos_tag(raw_tokens)

        for token_idx, (token, tag) in enumerate(tagged_tokens):
            token_lower = token.lower()
            wn_tag = get_wordnet_pos(tag)
            lemma = lemmatizer.lemmatize(token_lower, pos=wn_tag)

            token_info = {
                'token': token,
                'token_lower': token_lower,
                'tag': tag,
                'lemma': lemma,
                'doc_name': doc_name,
                'sent_num': sent_idx + 1,
                'token_num': token_idx + 1
            }
            processed_tokens.append(token_info)

    return processed_tokens

def add_file_to_corpus():
    global corpus
    filepath = filedialog.askopenfilename(
        title="Выберите текстовый файл (.txt)",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if not filepath:
        return

    doc_name = os.path.basename(filepath)

    if any(token_info['doc_name'] == doc_name for token_info in corpus):
        messagebox.showwarning("Предупреждение", f"Файл '{doc_name}' уже есть в корпусе.")
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_text = f.read()

        new_tokens = process_text(raw_text, doc_name)
        corpus.extend(new_tokens)

        update_status(f"Файл '{doc_name}' добавлен. Всего токенов в корпусе: {len(corpus)}")
        view_corpus_content()

    except Exception as e:
        messagebox.showerror("Ошибка чтения файла", f"Не удалось прочитать или обработать файл:\n{e}")


def add_text_directly():
    global corpus

    input_window = Toplevel(root)
    input_window.title("Добавить текст в корпус")
    input_window.geometry("500x400")
    input_window.transient(root)
    input_window.grab_set()

    Label(input_window, text="Идентификатор:").pack(pady=(10, 0))
    identifier_entry = Entry(input_window, width=50)
    identifier_entry.pack(pady=5)
    existing_ids = {token_info['doc_name'] for token_info in corpus if token_info['doc_name'].startswith('Введенный текст')}
    count = 1
    while f"Введенный текст {count}" in existing_ids:
        count += 1
    default_id = f"Введенный текст {count}"
    identifier_entry.insert(0, default_id)

    Label(input_window, text="Введите текст:").pack(pady=5)
    text_area = scrolledtext.ScrolledText(input_window, wrap=tk.WORD, width=60, height=15)
    text_area.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

    def on_ok():
        identifier = identifier_entry.get().strip()
        raw_text = text_area.get("1.0", tk.END).strip()

        if not identifier or not raw_text:
            messagebox.showwarning("Предупреждение", "Введите идентификатор и текст.", parent=input_window)
            return
        if any(token_info['doc_name'] == identifier for token_info in corpus):
             messagebox.showwarning("Предупреждение", f"Идентификатор '{identifier}' уже используется.", parent=input_window)
             return

        try:
            new_tokens = process_text(raw_text, identifier)
            corpus.extend(new_tokens)

            update_status(f"Текст '{identifier}' добавлен. Всего токенов в корпусе: {len(corpus)}")
            view_corpus_content()
            input_window.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка обработки текста", f"Не удалось обработать текст:\n{e}", parent=input_window)

    button_frame = tk.Frame(input_window)
    button_frame.pack(pady=10)
    ok_button = Button(button_frame, text="OK", width=10, command=on_ok)
    ok_button.pack(side=tk.LEFT, padx=5)
    cancel_button = Button(button_frame, text="Отмена", width=10, command=input_window.destroy)
    cancel_button.pack(side=tk.LEFT, padx=5)
    text_area.focus_set()
    input_window.wait_window()


def get_all_items(item_type='tokens'):
    if not corpus:
        return []

    key_map = {
        'tokens': 'token_lower',
        'lemmas': 'lemma',
        'tags': 'tag'
    }
    attribute_key = key_map.get(item_type)
    if not attribute_key:
        return []

    all_items = [
        token_info[attribute_key]
        for token_info in corpus
        if token_info['token'].isalpha()
    ]
    return all_items

def show_frequency_stats():
    if not corpus:
        messagebox.showinfo("Информация", "Корпус пуст. Добавьте файлы или текст.")
        return

    all_tokens = get_all_items('tokens')
    all_lemmas = get_all_items('lemmas')
    all_tags = get_all_items('tags')

    if not all_tokens:
         messagebox.showinfo("Информация", "В корпусе нет слов для статистики.")
         return

    token_counts = Counter(all_tokens)
    lemma_counts = Counter(all_lemmas)
    tag_counts = Counter(all_tags)

    unique_docs = {token_info['doc_name'] for token_info in corpus}

    report = "=== Частотная статистика ===\n\n"
    report += f"Всего документов/текстов: {len(unique_docs)}\n"
    report += f"Всего слов: {len(all_tokens)}\n"
    report += f"Уникальных слов: {len(token_counts)}\n"
    report += f"Всего лемм: {len(all_lemmas)}\n"
    report += f"Уникальных лемм: {len(lemma_counts)}\n"
    report += f"Всего тегов частей речи: {len(all_tags)}\n"
    report += f"Уникальных тегов: {len(tag_counts)}\n\n"

    report += "--- Частота Токенов ---\n"
    for token, count in token_counts.most_common():
        report += f"{token}: {count}\n"
    report += "\n"

    report += "--- Частота Лемм ---\n"
    for lemma, count in lemma_counts.most_common():
        report += f"{lemma}: {count}\n"
    report += "\n"

    report += "--- Частота Тегов Частей Речи ---\n"
    for tag, count in tag_counts.most_common():
        report += f"{tag}: {count}\n"

    display_results(report)

def find_concordance():
    if not corpus:
        messagebox.showinfo("Информация", "Корпус пуст. Добавьте файлы или текст.")
        return

    query = simpledialog.askstring("Конкорданс", "Введите слово или фразу для поиска:")
    if not query:
        return

    query_tokens_lower = [token.lower() for token in word_tokenize(query) if token.isalpha()]
    if not query_tokens_lower:
        messagebox.showwarning("Предупреждение", "Запрос не содержит слов для поиска.")
        return
    n_query = len(query_tokens_lower)

    results = []
    context_window_tokens = 7


    for i in range(len(corpus) - n_query + 1):
        potential_match = True
        phrase_tokens_info = []
        first_token_info = corpus[i]

        for j in range(n_query):
            current_token_info = corpus[i+j]
            phrase_tokens_info.append(current_token_info)
            if (current_token_info['token_lower'] != query_tokens_lower[j] or
                current_token_info['doc_name'] != first_token_info['doc_name'] or
                current_token_info['sent_num'] != first_token_info['sent_num']):
                potential_match = False
                break

        if potential_match:
            doc_name = first_token_info['doc_name']
            sent_num = first_token_info['sent_num']
            sent_start_idx = -1
            sent_end_idx = -1

            k = i
            while k >= 0 and corpus[k]['doc_name'] == doc_name and corpus[k]['sent_num'] == sent_num:
                sent_start_idx = k
                k -= 1

            k = i + n_query - 1
            while k < len(corpus) and corpus[k]['doc_name'] == doc_name and corpus[k]['sent_num'] == sent_num:
                sent_end_idx = k + 1
                k += 1

            if sent_start_idx != -1 and sent_end_idx != -1:
                sentence_tokens_info = corpus[sent_start_idx:sent_end_idx]
                sentence_original_tokens = [info['token'] for info in sentence_tokens_info]
                phrase_start_in_sentence = phrase_tokens_info[0]['token_num'] - 1

                context_start = max(0, phrase_start_in_sentence - context_window_tokens)
                context_end = min(len(sentence_original_tokens), phrase_start_in_sentence + n_query + context_window_tokens)

                left_context = " ".join(sentence_original_tokens[context_start:phrase_start_in_sentence])
                match_phrase = " ".join(sentence_original_tokens[phrase_start_in_sentence : phrase_start_in_sentence + n_query])
                right_context = " ".join(sentence_original_tokens[phrase_start_in_sentence + n_query : context_end])

                results.append(f"[{doc_name}, Предл. {sent_num}]: ...{left_context} **{match_phrase}** {right_context}...")

    if results:
        unique_results = sorted(list(set(results)))
        display_results(f"=== Конкорданс для '{query}' ({len(unique_results)} найдено) ===\n\n" + "\n".join(unique_results))
    else:
        display_results(f"Фраза '{query}' не найдена в корпусе.")


def get_word_info():

    if not corpus:
        messagebox.showinfo("Информация", "Корпус пуст. Добавьте файлы или текст.")
        return

    word = simpledialog.askstring("Информация о слове", "Введите слово:")
    if not word:
        return

    word_lower = word.lower()
    found_occurrences_info = []

    for token_info in corpus:
        if token_info['token_lower'] == word_lower:
            found_occurrences_info.append(token_info)

    if found_occurrences_info:
        report = f"=== Информация о слове '{word}' ===\n\n"
        report += f"Найдено вхождений: {len(found_occurrences_info)}\n\n"
        report += "--- Местоположения ---\n"

        for info in found_occurrences_info:
            report += (f"- Документ: {info['doc_name']}, "
                       f"Предложение: {info['sent_num']}, "
                       f"Слово: {info['token_num']}\n")

            report += f"  Токен: '{info['token']}', Тег: {info['tag']}, Лемма: {info['lemma']}\n\n"

        display_results(report)

    else:
        display_results(f"Слово '{word}' не найдено в корпусе. Введите одно слово для анализа.")






def save_corpus():
    global corpus
    if not corpus:
        messagebox.showinfo("Информация", "Корпус пуст. Нечего сохранять.")
        return
    filepath = filedialog.asksaveasfilename(
        title="Сохранить корпус как...",
        defaultextension=".corpus",
        filetypes=(("Corpus files", "*.corpus"), ("All files", "*.*"))
    )
    if not filepath: return
    try:
        with open(filepath, 'wb') as f:
            pickle.dump(corpus, f)
        update_status(f"Корпус сохранен в '{os.path.basename(filepath)}'")
    except Exception as e:
        messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить корпус:\n{e}")

def load_corpus():
    global corpus
    filepath = filedialog.askopenfilename(
        title="Загрузить корпус",
        filetypes=(("Corpus files", "*.corpus"), ("All files", "*.*"))
    )
    if not filepath: return
    try:
        with open(filepath, 'rb') as f:
            corpus = pickle.load(f)
            if not isinstance(corpus, list):
                raise TypeError("Загруженный файл не содержит список токенов.")
        update_status(f"Корпус загружен из '{os.path.basename(filepath)}'. Всего токенов: {len(corpus)}")
        view_corpus_content()
    except (pickle.UnpicklingError, TypeError, EOFError) as e:
         messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить корпус или формат файла некорректен:\n{e}")
         corpus = []
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить корпус:\n{e}")
        corpus = []

def view_corpus_content():
    if not corpus:
        display_results("Корпус пуст.")
        return

    unique_docs = sorted(list({token_info['doc_name'] for token_info in corpus}))
    total_tokens = len(corpus)
    total_words = len(get_all_items('tokens'))

    content_report = "=== Содержимое корпуса ===\n\n"
    content_report += f"Всего документов/текстов: {len(unique_docs)}\n"
    content_report += f"Всего токенов (вкл. пунктуацию): {total_tokens}\n"
    content_report += f"Всего токенов (только слова): {total_words}\n\n"
    content_report += "--- Документы/Тексты в корпусе ---\n"
    for i, doc_name in enumerate(unique_docs):
         content_report += f"{i+1}. {doc_name}\n"
    display_results(content_report)

def show_help():
    help_text = """
    === Справка по Корпусному Менеджеру ===

    **Структура данных:** Корпус хранится как единый список токенов. Каждый токен содержит информацию о себе, своей части речи, лемме, а также о документе, предложении и позиции, откуда он взят.

    **Файл:**
      - Добавить файл (.txt): Добавить текстовый файл в корпус. Текст будет разбит на токены, и они добавятся в общий список.
      - Добавить текст...: Открыть окно для ввода/вставки текста. Текст будет обработан и добавлен в общий список токенов.
      - Сохранить корпус: Сохранить текущий список токенов в файл .corpus.
      - Загрузить корпус: Загрузить ранее сохраненный список токенов из файла .corpus.
      - Выход: Закрыть приложение.

    **Корпус:**
      - Показать содержимое: Отобразить сводную информацию: список документов/текстов в корпусе и общее количество токенов.
      - Показать статистику: Рассчитать и показать частотную статистику по словам, леммам и частям речи для всего корпуса.

    **Анализ:**
      - Найти конкорданс: Поиск слова или фразы в корпусе. Отображает найденную фразу в контексте предложения, из которого она взята.
      - Информация о слове: Показать детальную информацию о каждом вхождении слова (документ, предложение, позиция, тег, лемма).

    **Помощь:**
      - Справка: Показать это окно.

    """
    messagebox.showinfo("Справка", help_text)


root = tk.Tk()
root.title("Корпусный Менеджер")
root.geometry("800x600")

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Файл", menu=file_menu)
file_menu.add_command(label="Добавить файл (.txt)", command=add_file_to_corpus)
file_menu.add_command(label="Добавить текст...", command=add_text_directly)
file_menu.add_separator()
file_menu.add_command(label="Сохранить корпус", command=save_corpus)
file_menu.add_command(label="Загрузить корпус", command=load_corpus)
file_menu.add_separator()
file_menu.add_command(label="Выход", command=root.quit)

corpus_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Корпус", menu=corpus_menu)
corpus_menu.add_command(label="Показать содержимое", command=view_corpus_content)
corpus_menu.add_command(label="Показать статистику", command=show_frequency_stats)

analysis_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Анализ", menu=analysis_menu)
analysis_menu.add_command(label="Найти конкорданс", command=find_concordance)
analysis_menu.add_command(label="Информация о слове", command=get_word_info)

help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Помощь", menu=help_menu)
help_menu.add_command(label="Справка", command=show_help)

results_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=30, font=("Arial", 10))
results_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
results_text.insert(tk.END, "Добро пожаловать в Корпусный Менеджер!\nДобавьте файлы или текст для начала работы.")
results_text.config(state=tk.DISABLED)

def display_results(text):
    results_text.config(state=tk.NORMAL)
    results_text.delete(1.0, tk.END)
    results_text.insert(tk.END, text)
    results_text.config(state=tk.DISABLED)

status_bar = tk.Label(root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
status_bar.pack(side=tk.BOTTOM, fill=tk.X)

def update_status(message):
    status_bar.config(text=message)

root.mainloop()
