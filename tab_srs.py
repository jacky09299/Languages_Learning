import tkinter as tk
from tkinter import ttk, messagebox

class SRSTab(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.create_ui()
        self.load_due_srs_items()

    def create_ui(self):
        # Upper area: Add new items
        add_frame = ttk.LabelFrame(self, text="新增單字/句子 (Add New Item)")
        add_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(add_frame, text="單字 (Word):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.srs_word_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.srs_word_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="句子 (Sentences):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.srs_sentence_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.srs_sentence_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(add_frame, text="新增 (Add)", command=self.add_srs_item).grid(row=2, column=0, columnspan=2, pady=10)

        # Lower area: Review Due Items
        review_frame = ttk.LabelFrame(self, text="待複習項目 (Due for Review)")
        review_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox for due items
        self.srs_listbox = tk.Listbox(review_frame, height=10)
        self.srs_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons for Review Outcome
        btn_frame = ttk.Frame(review_frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="記得 (Remembered)", command=lambda: self.review_srs_item(True)).pack(side="left", padx=10, expand=True)
        ttk.Button(btn_frame, text="忘記 (Forgot)", command=lambda: self.review_srs_item(False)).pack(side="right", padx=10, expand=True)

    def add_srs_item(self):
        word = self.srs_word_var.get().strip()
        sentences = self.srs_sentence_var.get().strip()

        if not word:
            messagebox.showwarning("警告", "單字不能為空 (Word cannot be empty)")
            return

        self.db.add_srs_item(word, sentences)
        messagebox.showinfo("成功", "新增成功 (Successfully added)")
        self.srs_word_var.set("")
        self.srs_sentence_var.set("")
        self.load_due_srs_items()

    def load_due_srs_items(self):
        self.srs_listbox.delete(0, tk.END)
        self.due_srs_items = self.db.get_due_srs_items()

        for item in self.due_srs_items:
            # item is (id, word, sentences, step)
            display_text = f"[{item[3]}] {item[1]} - {item[2]}"
            self.srs_listbox.insert(tk.END, display_text)

    def review_srs_item(self, success):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要複習的項目 (Select an item to review)")
            return

        idx = selection[0]
        item_id = self.due_srs_items[idx][0]

        self.db.update_srs_item(item_id, success)
        self.load_due_srs_items()
