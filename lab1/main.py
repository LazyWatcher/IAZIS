import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import PyPDF2
from nltk.tokenize import word_tokenize
from collections import Counter
import json
import os


class LexicalAnalyzerApp:

    def __init__(self, master):

        self.master = master
        master.title("Лексический анализатор текста")
        master.geometry("800x700")

        self.pdf_path = None
        self.raw_text = ""
        self.word_data = {}
        self.filtered_word_list = []

        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("TLabel", padding=5)
        style.configure("TEntry", padding=5)
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        style.configure("TLabelframe.Label", font=('Helvetica', 10, 'bold'))

        control_frame = ttk.Frame(master, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)

        input_text_frame = ttk.LabelFrame(master, text="Или введите текст для анализа здесь", padding="10")
        input_text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, padx=10, pady=5)

        list_frame = ttk.Frame(master, padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        detail_frame = ttk.Frame(master, padding="10")
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


        self.load_pdf_button = ttk.Button(control_frame, text="Загрузить PDF", command=self.load_pdf)
        self.load_pdf_button.pack(side=tk.LEFT, padx=5)

        self.save_dict_button = ttk.Button(control_frame, text="Сохранить словарь", command=self.save_dictionary, state=tk.DISABLED)
        self.save_dict_button.pack(side=tk.LEFT, padx=5)

        self.load_dict_button = ttk.Button(control_frame, text="Загрузить словарь", command=self.load_dictionary)
        self.load_dict_button.pack(side=tk.LEFT, padx=5)

        self.help_button = ttk.Button(control_frame, text="Помощь", command=self.show_help)
        self.help_button.pack(side=tk.RIGHT, padx=5)

        self.input_text_widget = scrolledtext.ScrolledText(input_text_frame, wrap=tk.WORD, height=8, relief=tk.SOLID, borderwidth=1)
        self.input_text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.input_text_widget.insert("1.0", "Введите или вставьте сюда текст на английском языке")
        self.input_text_widget.config(fg="grey")
        self.input_text_widget.bind("<FocusIn>", self.clear_placeholder)
        self.input_text_widget.bind("<FocusOut>", self.add_placeholder)

        self.process_input_button = ttk.Button(input_text_frame, text="Обработать введенный текст", command=self.process_input_text)
        self.process_input_button.pack(pady=(5,0))

        list_controls_frame = ttk.Frame(list_frame)
        list_controls_frame.pack(fill=tk.X, pady=(0, 5))

        self.filter_label = ttk.Label(list_controls_frame, text="Фильтр/Поиск:")
        self.filter_label.pack(side=tk.LEFT, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(list_controls_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.filter_var.trace_add("write", self.filter_list)

        self.word_tree = ttk.Treeview(list_frame)
        self.word_tree.heading('#0', text='Слово (Частота)')
        self.word_tree.column("#0", anchor=tk.W)

        tree_scroll_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.word_tree.yview)
        tree_scroll_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.word_tree.xview)
        self.word_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.word_tree.pack(fill=tk.BOTH, expand=True)
        self.word_tree.bind('<<TreeviewSelect>>', self.on_word_select)

        self.detail_label = ttk.Label(detail_frame, text="Морфологическая информация:", font=('Helvetica', 12, 'bold'))
        self.detail_label.pack(pady=(0, 5), anchor=tk.W)
        self.morphology_text = scrolledtext.ScrolledText(detail_frame, wrap=tk.WORD, height=10, state=tk.DISABLED, relief=tk.SOLID, borderwidth=1)
        self.morphology_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.save_morphology_button = ttk.Button(detail_frame, text="Сохранить информацию", command=self.save_morphology, state=tk.DISABLED)
        self.save_morphology_button.pack(anchor=tk.E)
        self.selected_word_label = ttk.Label(detail_frame, text="Выбранное слово: -", font=('Helvetica', 10, 'italic'))
        self.selected_word_label.pack(anchor=tk.W, pady=(5, 0))


    def clear_placeholder(self, event):
        if self.input_text_widget.get("1.0", tk.END).strip() == "Введите или вставьте сюда текст на английском языке":
            self.input_text_widget.delete("1.0", tk.END)
            self.input_text_widget.config(fg="black")

    def add_placeholder(self, event):
        if not self.input_text_widget.get("1.0", tk.END).strip():
            self.input_text_widget.insert("1.0", "Введите или вставьте сюда текст на английском языке")
            self.input_text_widget.config(fg="grey")

    def load_pdf(self):

        filepath = filedialog.askopenfilename(
            title="Выберите PDF файл",
            filetypes=[("PDF Files", "*.pdf")],
            parent=self.master
        )
        if not filepath:
            return

        self.pdf_path = filepath
        extracted_text = ""



        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                if num_pages == 0:
                    messagebox.showwarning("Пустой PDF", "Выбранный PDF файл не содержит страниц.", parent=self.master)
                    return

                for page_num in range(num_pages):
                    page = reader.pages[page_num]
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += page_text + "\n"
                    except Exception as page_error:
                        print(f"Предупреждение: Не удалось извлечь текст со страницы {page_num + 1}: {page_error}")



            if extracted_text:
                self.input_text_widget.delete("1.0", tk.END)
                self.add_placeholder(None)
                self.raw_text = extracted_text
                self.word_data = {}
                self.update_word_list()
                self.clear_details()
                self.process_text()
                messagebox.showinfo("Успех",
                                    f"Текст из PDF '{os.path.basename(self.pdf_path)}' успешно загружен и обработан.",
                                    parent=self.master)
            else:
                messagebox.showwarning("Предупреждение",
                                       "Не удалось извлечь текст из PDF файла. Возможно, он содержит только изображения или защищен.",
                                       parent=self.master)

        except PyPDF2.errors.PdfReadError as pdf_err:
            messagebox.showerror("Ошибка чтения PDF",
                                 f"Не удалось прочитать файл (возможно, он поврежден или зашифрован):\n{pdf_err}",
                                 parent=self.master)
        except Exception as e:
            messagebox.showerror("Ошибка чтения PDF", f"Не удалось прочитать файл:\n{e}", parent=self.master)


    def process_input_text(self):

        input_text = self.input_text_widget.get("1.0", tk.END).strip()

        if not input_text or input_text == "Введите или вставьте сюда текст на английском языке":
            messagebox.showwarning("Нет текста", "Пожалуйста, введите или вставьте текст в поле для анализа.", parent=self.master)
            return

        self.pdf_path = None
        self.raw_text = input_text
        self.word_data = {}
        self.update_word_list()
        self.clear_details()
        self.process_text()

    def process_text(self):

        try:
            tokens = [word.lower() for word in word_tokenize(self.raw_text) if word.isalpha()]

            if not tokens:
                source = f"PDF файла '{os.path.basename(self.pdf_path)}'" if self.pdf_path else "введенного текста"
                messagebox.showinfo("Нет слов", f"В тексте из {source} не найдено слов для анализа (после фильтрации).", parent=self.master)
                self.save_dict_button.config(state=tk.DISABLED)
                return

            word_counts = Counter(tokens)
            self.word_data = {}
            for word, freq in word_counts.items():
                self.word_data[word] = {'frequency': freq, 'morphology': ''}

            self.update_word_list()
            self.save_dict_button.config(state=tk.NORMAL)

            source_msg = f"PDF файла '{os.path.basename(self.pdf_path)}'" if self.pdf_path else "введенного текста"
            messagebox.showinfo("Обработка завершена", f"Анализ {source_msg} завершен.\nНайдено {len(self.word_data)} уникальных словоформ.", parent=self.master)


        except Exception as e:
            messagebox.showerror("Ошибка обработки", f"Произошла ошибка при обработке текста:\n{e}", parent=self.master)
            self.save_dict_button.config(state=tk.DISABLED)

    def update_word_list(self):

        for item in self.word_tree.get_children():
            self.word_tree.delete(item)

        word_filter_term = self.filter_var.get().lower().strip()
        sorted_words = sorted(self.word_data.keys())
        self.filtered_word_list = []

        for word in sorted_words:
            if not word_filter_term or word_filter_term in word:
                self.filtered_word_list.append(word)
                frequency = self.word_data[word]['frequency']
                display_text = f"{word} ({frequency})"
                self.word_tree.insert('', tk.END, iid=word, text=display_text)

        if not self.filtered_word_list:
            self.clear_details()
        else:
            selected = self.word_tree.selection()
            if selected and selected[0] not in self.filtered_word_list:
                 self.clear_details()
            elif not selected:
                 self.clear_details()

    def filter_list(self, *args):
        self.update_word_list()

    def on_word_select(self, event):

        selected_items = self.word_tree.selection()
        if selected_items:
            selected_word = selected_items[0]
            if selected_word in self.word_data:
                morphology = self.word_data[selected_word].get('morphology', '')
                self.morphology_text.config(state=tk.NORMAL)
                self.morphology_text.delete('1.0', tk.END)
                self.morphology_text.insert('1.0', morphology)
                self.save_morphology_button.config(state=tk.NORMAL)
                self.selected_word_label.config(text=f"Выбранное слово: {selected_word}")
            else:
                print(f"Предупреждение: Выбранное слово '{selected_word}' не найдено.")
                self.clear_details()
        else:
             self.clear_details()

    def clear_details(self):
        self.morphology_text.config(state=tk.NORMAL)
        self.morphology_text.delete('1.0', tk.END)
        self.morphology_text.config(state=tk.DISABLED)
        self.save_morphology_button.config(state=tk.DISABLED)
        self.selected_word_label.config(text="Выбранное слово: -")

    def save_morphology(self):

        selected_items = self.word_tree.selection()
        if not selected_items:
            messagebox.showwarning("Нет выбора", "Сначала выберите слово в списке.", parent=self.master)
            return

        selected_word = selected_items[0]
        if selected_word in self.word_data:
            new_morphology = self.morphology_text.get('1.0', tk.END).strip()
            if self.word_data[selected_word]['morphology'] != new_morphology:
                self.word_data[selected_word]['morphology'] = new_morphology
                messagebox.showinfo("Сохранено", f"Морфологическая информация для слова '{selected_word}' обновлена.", parent=self.master)
            else:
                messagebox.showinfo("Нет изменений", "Информация не была изменена.", parent=self.master)
        else:
            messagebox.showerror("Ошибка", "Выбранное слово не найдено в данных.", parent=self.master)

    def save_dictionary(self):

        if not self.word_data:
            messagebox.showwarning("Нет данных", "Словарь пуст. Нечего сохранять.", parent=self.master)
            return

        filepath = filedialog.asksaveasfilename(
            title="Сохранить словарь как",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self.master
        )
        if not filepath:
            return

        try:
            sorted_word_data = dict(sorted(self.word_data.items()))
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(sorted_word_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успех", f"Словарь успешно сохранен в файл:\n{filepath}", parent=self.master)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить словарь:\n{e}", parent=self.master)

    def load_dictionary(self):

        filepath = filedialog.askopenfilename(
            title="Загрузить словарь из файла",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            parent=self.master
        )
        if not filepath:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            if not isinstance(loaded_data, dict): raise ValueError("Формат файла не dict.")
            for word, data in loaded_data.items():
                 if not isinstance(data, dict) or 'frequency' not in data or 'morphology' not in data: raise ValueError(f"Структура для '{word}' некорректна.")
                 if not isinstance(data['frequency'], int): raise ValueError(f"Частота для '{word}' не int.")
                 if not isinstance(data['morphology'], str): raise ValueError(f"Морфология для '{word}' не str.")

            self.word_data = loaded_data
            self.filter_var.set("")
            self.update_word_list()
            self.save_dict_button.config(state=tk.NORMAL)
            self.pdf_path = None
            self.raw_text = ""
            self.input_text_widget.delete("1.0", tk.END)
            self.add_placeholder(None)
            messagebox.showinfo("Успех", f"Словарь успешно загружен из файла:\n{filepath}", parent=self.master)

        except FileNotFoundError:
             messagebox.showerror("Ошибка загрузки", f"Файл не найден:\n{filepath}", parent=self.master)
        except json.JSONDecodeError:
             messagebox.showerror("Ошибка загрузки", "Ошибка чтения JSON файла.", parent=self.master)
        except ValueError as ve:
             messagebox.showerror("Ошибка загрузки", f"Ошибка формата данных:\n{ve}", parent=self.master)
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить словарь:\n{e}", parent=self.master)

    def show_help(self):

        help_text = """
                                        Лексический анализатор текста

        Эта программа позволяет анализировать текст из PDF-файлов на английском языке.

                                                Основные шаги

        1. Нажмите кнопку "Загрузить PDF" и выберите файл. Текст будет извлечен автоматически.
        2. После загрузки PDF нажмите "Обработать текст". Программа разобьет текст на слова, подсчитает их частоту и отобразит в списке слева в формате "слово (частота)".
        3. Просмотр и редактирование:
            Список слов слева показывает словоформы и их частоту, отсортированные по алфавиту.
            Используйте поле "Фильтр/Поиск" для быстрого поиска нужных слов.
            Выберите строку в списке, чтобы увидеть/изменить морфологическую информацию для соответствующего слова справа.
            Введите или отредактируйте текст в поле "Морфологическая информация". 
            Нажмите "Сохранить информацию", чтобы сохранить изменения для выбранного слова.
        4. Нажмите "Сохранить словарь", чтобы сохранить текущий список слов, их частоты и введенную морфологическую информацию в файл формата JSON. Словарь будет сохранен в отсортированном виде.
        5. Нажмите "Загрузить словарь", чтобы загрузить ранее сохраненный словарь из файла JSON. Это заменит текущие данные.

                                                          Примечания
                                                           
        Извлечение текста из некоторых PDF (особенно сканированных изображений или защищенных) может быть невозможным или неполным.
        """
        help_window = tk.Toplevel(self.master)
        help_window.title("Справка")
        help_window.geometry("550x500")
        help_window.transient(self.master)
        help_window.grab_set()

        help_text_widget = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 10), relief=tk.FLAT, background=help_window.cget('bg'))
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        close_button = ttk.Button(help_window, text="Закрыть", command=help_window.destroy)
        close_button.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = LexicalAnalyzerApp(root)
    root.mainloop()
