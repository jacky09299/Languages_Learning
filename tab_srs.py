import tkinter as tk
from tkinter import ttk, messagebox

class SRSTab(ttk.Frame):
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db = db_manager
        self.app = app
        self.create_ui()
        self.load_due_srs_items()

    def refresh_data(self):
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

        ttk.Label(add_frame, text="解釋 (Explanation):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.srs_explanation_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.srs_explanation_var, width=40).grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(add_frame, text="新增 (Add)", command=self.add_srs_item).grid(row=3, column=0, columnspan=2, pady=10)

        # Lower area: Review Due Items
        review_frame = ttk.LabelFrame(self, text="待複習項目 (Due for Review)")
        review_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox for due items
        self.srs_listbox = tk.Listbox(review_frame, height=10)
        self.srs_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Buttons for Review Outcome
        btn_frame = ttk.Frame(review_frame)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="記得 (Remembered)", command=lambda: self.review_srs_item(True)).pack(side="left", padx=5, expand=True)
        ttk.Button(btn_frame, text="👁️ 查看解釋與句子 (View Ext.)", command=self.show_explanation).pack(side="left", padx=5, expand=True)
        ttk.Button(btn_frame, text="忘記 (Forgot)", command=lambda: self.review_srs_item(False)).pack(side="right", padx=5, expand=True)

    def add_srs_item(self):
        word = self.srs_word_var.get().strip()
        sentences = self.srs_sentence_var.get().strip()
        explanation = self.srs_explanation_var.get().strip()

        if not word:
            messagebox.showwarning("警告", "單字不能為空 (Word cannot be empty)")
            return

        current_lang = self.app.get_current_language()
        self.db.add_srs_item(word, sentences, explanation, target_language=current_lang)
        messagebox.showinfo("成功", "新增成功 (Successfully added)")
        self.srs_word_var.set("")
        self.srs_sentence_var.set("")
        self.srs_explanation_var.set("")
        self.load_due_srs_items()

    def load_due_srs_items(self):
        self.srs_listbox.delete(0, tk.END)
        current_lang = self.app.get_current_language()
        self.due_srs_items = self.db.get_due_srs_items(target_language=current_lang)

        for item in self.due_srs_items:
            # item is (id, word, sentences, explanation, step)
            display_text = f"[{item[4]}] {item[1]}" 
            if item[2]: # Has sentences
                display_text += f" - {item[2][:20]}..." if len(item[2]) > 20 else f" - {item[2]}"
            self.srs_listbox.insert(tk.END, display_text)

    def show_explanation(self):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要查看的項目 (Select an item to view)")
            return

        idx = selection[0]
        item = self.due_srs_items[idx]
        msg = f"【單字 Word】\n{item[1]}\n\n【句子 Sentences】\n{item[2]}\n\n【解釋 Explanation】\n{item[3]}"
        messagebox.showinfo("項目詳細資訊 (Item Details)", msg)

    def review_srs_item(self, success):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要複習的項目 (Select an item to review)")
            return

        idx = selection[0]
        item_id = self.due_srs_items[idx][0]

        self.db.update_srs_item(item_id, success)
        self.load_due_srs_items()
