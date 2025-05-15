import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import nltk
import spacy
import os



try:
    from docx import Document
except ImportError:
    print("python-docx library not found. DOCX support will be disabled. Install with: pip install python-docx")
    Document = None

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 library not found. PDF support will be disabled. Install with: pip install PyPDF2")
    PyPDF2 = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup4 library not found. HTML support will be disabled. Install with: pip install beautifulsoup4")
    BeautifulSoup = None

try:
    from striprtf.striprtf import rtf_to_text
except ImportError:
    print("striprtf library not found. RTF support will be disabled. Install with: pip install striprtf")
    rtf_to_text = None

try:
    import spacy
    from spacy import displacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        messagebox.showwarning("spaCy Model Missing",
                               "spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm.")
        nlp = None
except ImportError:
    nlp = None
    print("spaCy not found. Dependency Parsing support will be disabled. Install with: pip install spacy en-core-web-sm")



class NLPLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №4 - Семантико-синтаксический анализ")
        self.root.geometry("900x700")

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", padding=5, font=('Arial', 10))
        self.style.configure("TButton", padding=5, font=('Arial', 10, 'bold'))
        self.style.configure("TFrame", padding=10)
        self.style.configure("TMenubutton", font=('Arial', 10))

        self.analysis_type_var = tk.StringVar(value="Tokenization & POS Tagging")
        self.current_file_path = None

        self.main_paned_window = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Input
        self.input_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.input_frame, weight=1)
        ttk.Label(self.input_frame, text="Входной текст:").pack(anchor="w")
        self.input_text_area = scrolledtext.ScrolledText(self.input_frame, wrap=tk.WORD, height=15, font=('Arial', 11))
        self.input_text_area.pack(fill=tk.BOTH, expand=True, pady=(0,5))

        # Controls
        self.controls_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.controls_frame, weight=0)
        ttk.Label(self.controls_frame, text="Тип анализа:").pack(side=tk.LEFT)
        choices = ["Tokenization & POS Tagging", "Sentiment Analysis", "Lemmatization", "Dependency Parsing"]
        ttk.OptionMenu(self.controls_frame, self.analysis_type_var, self.analysis_type_var.get(), *choices).pack(side=tk.LEFT)
        ttk.Button(self.controls_frame, text="Анализировать", command=self.perform_analysis).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.controls_frame, text="Очистить все", command=self.clear_all_text_areas).pack(side=tk.RIGHT)

        # Output
        self.output_frame = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.output_frame, weight=1)
        ttk.Label(self.output_frame, text="Результат анализа:").pack(anchor="w")
        self.output_text_area = scrolledtext.ScrolledText(self.output_frame, wrap=tk.WORD, height=15, font=('Arial',11), state=tk.DISABLED)
        self.output_text_area.pack(fill=tk.BOTH, expand=True)

        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Открыть...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить результат как...", command=self.save_results, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.exit_app)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Очистить входной текст", command=lambda: self.input_text_area.delete(1.0,tk.END))
        edit_menu.add_command(label="Очистить результат", command=lambda: self.set_output_text(""))
        edit_menu.add_command(label="Копировать результат", command=self.copy_results)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

        self.root.bind_all("<Control-o>", lambda e: self.open_file())
        self.root.bind_all("<Control-s>", lambda e: self.save_results())

    def set_output_text(self, text):
        self.output_text_area.config(state=tk.NORMAL)
        self.output_text_area.delete(1.0, tk.END)
        self.output_text_area.insert(tk.END, text)
        self.output_text_area.config(state=tk.DISABLED)

    def copy_results(self):
        try:
            content = self.output_text_area.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            messagebox.showinfo("Скопировано", "Результат скопирован в буфер обмена.")
        except Exception as e:
            messagebox.showwarning("Ошибка копирования", f"Не удалось скопировать результат: {e}")

    def clear_all_text_areas(self):
        self.input_text_area.delete(1.0, tk.END)
        self.set_output_text("")
        self.current_file_path = None
        self.root.title("Лабораторная работа №4 - Семантико-синтаксический анализ")

    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Открыть текстовый файл",
            filetypes=(
                ("Текстовые файлы", "*.txt"),
                ("Документы Word", "*.docx"),
                ("PDF файлы", "*.pdf"),
                ("HTML файлы", "*.html *.htm"),
                ("RTF файлы", "*.rtf"),
                ("Все файлы", "*.*")
            )
        )
        if not filepath:
            return

        self.current_file_path = filepath
        filename = os.path.basename(filepath)
        self.root.title(f"Лабораторная работа №4 - {filename}")

        try:
            content = ""
            file_extension = os.path.splitext(filepath)[1].lower()

            if file_extension == ".txt":
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            elif file_extension == ".docx":
                if Document:
                    doc = Document(filepath)
                    content = "\n".join([para.text for para in doc.paragraphs])
                else:
                    messagebox.showerror("Ошибка",
                                         "Библиотека python-docx не установлена. Невозможно открыть DOCX файлы.")
                    return
            elif file_extension == ".pdf":
                if PyPDF2:
                    try:
                        with open(filepath, "rb") as f:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                content += page.extract_text() + "\n"
                    except Exception as e:
                        messagebox.showerror("Ошибка чтения PDF",
                                             f"Не удалось прочитать PDF файл: {e}\nВозможно, файл зашифрован или поврежден.")
                        return
                else:
                    messagebox.showerror("Ошибка", "Библиотека PyPDF2 не установлена. Невозможно открыть PDF файлы.")
                    return
            elif file_extension in [".html", ".htm"]:
                if BeautifulSoup:
                    with open(filepath, "r", encoding="utf-8") as f:
                        soup = BeautifulSoup(f, "html.parser")
                        content = soup.get_text(separator="\n", strip=True)
                else:
                    messagebox.showerror("Ошибка",
                                         "Библиотека BeautifulSoup4 не установлена. Невозможно открыть HTML файлы.")
                    return
            elif file_extension == ".rtf":
                if rtf_to_text:
                    try:
                        with open(filepath, "r",
                                  encoding="utf-8") as f:
                            rtf_content = f.read()
                        content = rtf_to_text(rtf_content)
                    except Exception as e:
                        try:
                            with open(filepath, "rb") as f_bin:
                                rtf_content_bin = f_bin.read().decode('latin-1', errors='ignore')  # Common RTF encoding
                            content = rtf_to_text(rtf_content_bin)
                        except Exception as e_bin:
                            messagebox.showerror("Ошибка чтения RTF", f"Не удалось прочитать RTF файл: {e_bin}")
                            return
                else:
                    messagebox.showerror("Ошибка", "Библиотека striprtf не установлена. Невозможно открыть RTF файлы.")
                    return
            else:
                messagebox.showwarning("Неподдерживаемый формат",
                                       f"Файлы с расширением '{file_extension}' не поддерживаются для автоматического чтения в этой версии.")
                return

            self.input_text_area.delete(1.0, tk.END)
            self.input_text_area.insert(tk.END, content)
            self.set_output_text("")

        except Exception as e:
            messagebox.showerror("Ошибка открытия файла", f"Не удалось прочитать файл: {filepath}\n{str(e)}")
            self.current_file_path = None
            self.root.title("Лабораторная работа №4 - Семантико-синтаксический анализ")

    def save_results(self):
        content_to_save = self.output_text_area.get(1.0, tk.END).strip()
        if not content_to_save:
            messagebox.showwarning("Нечего сохранять", "Область результатов пуста.")
            return

        filepath = filedialog.asksaveasfilename(
            title="Сохранить результат анализа",
            defaultextension=".txt",
            filetypes=(("Текстовые файлы", "*.txt"), ("Все файлы", "*.*"))
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content_to_save)
            messagebox.showinfo("Сохранено", f"Результат успешно сохранен в: {filepath}")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл: {filepath}\n{str(e)}")

    def perform_analysis(self):
        input_text = self.input_text_area.get(1.0, tk.END).strip()
        if not input_text:
            messagebox.showwarning("Нет текста", "Пожалуйста, введите или откройте текст для анализа.")
            return

        analysis_choice = self.analysis_type_var.get()
        results = ""
        self.output_text_area.config(state=tk.NORMAL)
        self.output_text_area.delete(1.0, tk.END)

        try:
            sentences = nltk.sent_tokenize(input_text)
            if not sentences:
                results = "Не удалось сегментировать текст на предложения."
                self.set_output_text(results)
                return

            if analysis_choice == "Tokenization & POS Tagging":
                results += "--- Токенизация и Частеречная разметка (POS Tagging) ---\n\n"
                for i, sentence in enumerate(sentences):
                    words = nltk.word_tokenize(sentence)
                    tagged_words = nltk.pos_tag(words)
                    results += f"Предложение {i + 1}: {sentence}\n"
                    results += "Токены и теги: " + str(tagged_words) + "\n\n"

            elif analysis_choice == "Sentiment Analysis":

                try:
                    from nltk.sentiment import SentimentIntensityAnalyzer
                except ImportError:
                    self.set_output_text("Анализ тональности недоступен: не найден модуль SentimentIntensityAnalyzer.")
                    return

                analyzer = SentimentIntensityAnalyzer()
                results += "--- Анализ тональности (Sentiment Analysis) ---\n\n"
                for i, sentence in enumerate(sentences):
                    scores = analyzer.polarity_scores(sentence)
                    results += f"Предложение {i + 1}: {sentence}\n"
                    results += (f"Положительный: {scores['pos']:.3f}, "
                                f"Нейтральный: {scores['neu']:.3f}, "
                                f"Отрицательный: {scores['neg']:.3f}, "
                                f"Сводный балл: {scores['compound']:.3f}\n\n")
                self.set_output_text(results.strip())
                return

            elif analysis_choice == "Lemmatization":
                results += "--- Лемматизация (WordNetLemmatizer) ---\n\n"
                lemmatizer = nltk.stem.WordNetLemmatizer()

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

                for i, sentence in enumerate(sentences):
                    words = nltk.word_tokenize(sentence)
                    pos_tags = nltk.pos_tag(words)
                    results += f"Предложение {i + 1}: {sentence}\n"
                    results += "Слово -> Лемма (с учетом части речи):\n"
                    for word, tag in pos_tags:
                        wn_tag = get_wordnet_pos(tag)
                        lemma = lemmatizer.lemmatize(word, wn_tag)
                        results += f"  '{word}' ({tag} -> {wn_tag}) -> '{lemma}'\n"
                    results += "\n"
            elif analysis_choice == "Dependency Parsing":
                if not nlp:
                    self.set_output_text("Dependency Parsing недоступен: spaCy не установлен или модель не загружена.")
                    return
                results = "--- Деревья зависимостей (spaCy) ---\n\n"
                for i, sent in enumerate(sentences):
                    doc = nlp(sent)
                    results += f"Предложение {i+1}: {sent}\n"
                    for token in doc:
                        results += f"{token.text:<12} ---> {token.dep_:<10} ---> {token.head.text}\n"
                    results += "\n"
                self.set_output_text(results)
                return

            else:
                results = "Выбран неизвестный тип анализа."

            self.set_output_text(results.strip())

        except Exception as e:
            messagebox.showerror("Ошибка анализа",
                                 f"Произошла ошибка во время анализа:\n{str(e)}\n\nУбедитесь, что необходимые ресурсы NLTK загружены (см. меню Помощь).")
            self.set_output_text(f"Ошибка: {str(e)}")

    def show_about(self):
        about_text = """
Лабораторная работа №4: Семантико-синтаксический анализ текстов



Дерево зависмостей:

| Метка        | Полное название          | Описание                                                                                              |
| ------------ | ------------------------ | ----------------------------------------------------------------------------------------------------- |
| **ROOT**     | root                     | Корень предложения– обычно главный глагол или сказуемое, к которому “привязаны” все остальные слова. |
| **nsubj**    | nominal subject          | Именная подлежащее– существительное или местоимение, выполняющее действие (кто? что?).               |
| **dobj**     | direct object            | Прямое дополнение– дополнение, принимаемое непосредственно глаголом (что? кого?).                    |
| **iobj**     | indirect object          | Косвенное дополнение– обычно получает что‑либо от действия (кому? чему?).                            |
| **amod**     | adjectival modifier      | Атрибутивный (прилагательный) модификатор– прилагательное, описывающее существительное.              |
| **advmod**   | adverbial modifier       | Обстоятельственный (наречный) модификатор– наречие, описывающее глагол (или прилагательное).         |
| **aux**      | auxiliary                | Вспомогательный глагол– «be», «do», «have» в сложных формах (was running, has eaten).                |
| **det**      | determiner               | Артикль или указательное слово (the, a, this, that, мой, твой и т.д.).                               |
| **prep**     | prepositional modifier   | Предлог, вводящий придаточное обстоятельство (in, on, at, с, на и т.д.).                             |
| **pobj**     | object of preposition    | Объект предлога – существительное после предлога (in **the** house: “house” = pobj).                  |
| **conj**     | conjunct                 | Член координационного союза (and, or) или сам союзный элемент в связке (cats **and** dogs).           |
| **cc**       | coordinating conjunction | Координирующий союз (and, but, or).                                                                   |
| **nummod**   | numeric modifier         | Числительное, модифицирующее существительное (three **dogs** → “three” = nummod).                     |
| **neg**      | negation modifier        | Частица отрицания (not, never).                                                                       |
| **compound** | compound                 | Композитное слово или составной термин (ice-cream, tea-time).                                         |


Тональность:

| Поле         | Обозначение   | Описание                                                                                                                                                                      |
| ------------ | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **pos**      | Положительный | Суммарная “веса” положительных выражений в предложении, нормированная в диапазоне.                                                                                |
| **neu**      | Нейтральный   | Суммарная “веса” нейтральных выражений, нормированная в диапазоне.                                                                                                |
| **neg**      | Отрицательный | Суммарная “веса” отрицательных выражений, нормированная в диапазоне.                                                                                              |
| **compound** | Сводный балл  | Итоговый нормированный балл тональности в диапазоне ≥ +0.05 — положительная тональность; ≤ –0.05 — отрицательная; (–0.05, +0.05) — нейтральная. 


Токенизация:

| Тег   | Обозначение                                                                            |
| ----- | -------------------------------------------------------------------------------------- |
| CD    | Cardinal number—количественное числительное (one, 2, 100)                            |
| DT    | Determiner—артикль/указательное слово (the, this, каждый)                            |
| EX    | Existential there—«there» в конструкции “there is”                                   |
| FW    | Foreign word—иностранное слово                                                       |
| IN    | Preposition/Subordinating conjunction—предлог/подчинительный союз (in, of, although) |
| JJ    | Adjective—прилагательное (beautiful, красный)                                        |
| LS    | List item marker—маркер элементов списка (1., a., i.)                                |
| MD    | Modal—модальный глагол (can, should, must)                                           |
| NN    | Noun, singular or mass—имя существительное, ед.число (dog, information)             |
| PDT   | Predeterminer—пре-детерминатив (all, both)                                           |
| POS   | Possessive ending—притяжательное окончание (‘s, s’)                                  |
| PRP   | Personal pronoun—личное местоимение (I, you, he)                                     |
| RB    | Adverb—наречие (quickly, очень)                                                      |
| RBR   | Adverb, comparative—наречие в сравнительной степени (faster)                         |
| RBS   | Adverb, superlative—наречие в превосходной степени (fastest)                         |
| RP    | Particle—частица (up, off в “pick up”, “break off”)                                  |
| SYM   | Symbol—символ (%, )                                                                |
| TO    | “to” as preposition or infinitive marker—«to»                                        |
| UH    | Interjection—междометие (oh, wow)                                                    |
| VB    | Verb, base form—глагол в начальной форме (look)                                      |
| WDT   | Wh‑determiner—вопросно-относительное слово (which, that)                             |
| WP    | Wh‑pronoun—вопросное местоимение (who, what)                                         |
| WRB   | Wh‑adverb—вопросное наречие (where, when, why)                                       |

        """
        messagebox.showinfo("О программе", about_text)



    def exit_app(self):
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = NLPLabApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()