import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

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

        ttk.Label(add_frame, text="關聯字 (Associated Words):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        self.srs_associated_words_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.srs_associated_words_var, width=40).grid(row=3, column=1, padx=5, pady=5)

        btn_add_frame = ttk.Frame(add_frame)
        btn_add_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_add_frame, text="新增 (Add)", command=self.add_srs_item).pack(side="left", padx=5)
        ttk.Button(btn_add_frame, text="從 Google Sheet 同步 (Sync from Google Sheet)", command=self.sync_srs_from_sheet).pack(side="left", padx=5)

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
        ttk.Button(btn_frame, text="忘記 (Forgot)", command=lambda: self.review_srs_item(False)).pack(side="left", padx=5, expand=True)

        edit_frame = ttk.Frame(review_frame)
        edit_frame.pack(fill="x", pady=5)
        ttk.Button(edit_frame, text="修改內容 (Edit Item)", command=self.edit_item).pack(side="left", padx=5, expand=True)
        ttk.Button(edit_frame, text="🔍 從原文尋找 (Search Texts)", command=self.search_in_translations).pack(side="left", padx=5, expand=True)
        ttk.Button(edit_frame, text="刪除此項 (Delete Item)", command=self.delete_srs_item).pack(side="right", padx=5, expand=True)

    def add_srs_item(self):
        word = self.srs_word_var.get().strip()
        sentences = self.srs_sentence_var.get().strip()
        explanation = self.srs_explanation_var.get().strip()
        assoc_words = self.srs_associated_words_var.get().strip()

        if not word:
            messagebox.showwarning("警告", "單字不能為空 (Word cannot be empty)")
            return

        current_lang = self.app.get_current_language()
        self.db.add_srs_item(word, sentences, explanation, assoc_words, target_language=current_lang)
        messagebox.showinfo("成功", "新增成功 (Successfully added)")
        self.srs_word_var.set("")
        self.srs_sentence_var.set("")
        self.srs_explanation_var.set("")
        self.srs_associated_words_var.set("")
        self.load_due_srs_items()

    def sync_srs_from_sheet(self):
        from sheet_fetcher import fetch_and_sync_srs_items
        count = fetch_and_sync_srs_items(self.db)
        if count > 0:
            messagebox.showinfo("同步結果", f"成功匯入了 {count} 筆單字/句子！\n(Imported {count} items!)")
            self.load_due_srs_items()
        else:
            messagebox.showinfo("同步結果", "目前沒有新的項目需要同步\n(No new items to sync).")

    def load_due_srs_items(self):
        self.srs_listbox.delete(0, tk.END)
        current_lang = self.app.get_current_language()
        self.due_srs_items = self.db.get_due_srs_items(target_language=current_lang)

        for item in self.due_srs_items:
            # item is (id, word, sentences, explanation, step)
            display_text = f"[{item[4]}]"
            if item[1]:
                display_text += f" {item[1]}"
                if item[2]:
                    display_text += f" - {item[2][:20]}..." if len(item[2]) > 20 else f" - {item[2]}"
            else:
                if item[2]:
                    display_text += f" {item[2][:40]}..." if len(item[2]) > 40 else f" {item[2]}"
            self.srs_listbox.insert(tk.END, display_text)

    def delete_srs_item(self):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要刪除的項目 (Select an item to delete)")
            return
        
        idx = selection[0]
        item = self.due_srs_items[idx]
        item_id = item[0]
        
        if messagebox.askyesno("確認", "確定要刪除嗎？\n(Are you sure you want to delete?)"):
            self.db.delete_srs_item(item_id)
            self.load_due_srs_items()

    def search_in_translations(self):
        word = ""
        assoc_str = ""
        selection = self.srs_listbox.curselection()
        if selection:
            idx = selection[0]
            item = self.due_srs_items[idx]
            word = item[1].strip() if item[1] else ""
            assoc_str = item[5].strip() if len(item) > 5 and item[5] else ""
        
        if not word:
            word = self.srs_word_var.get().strip()
            if hasattr(self, 'srs_associated_words_var'):
                assoc_str = self.srs_associated_words_var.get().strip()

        if not word:
            messagebox.showwarning("警告", "請先選擇要查詢的待複習項目，或在「單字」欄位輸入文字\n(Select an item or enter a word in the add section)")
            return

        current_lang = self.app.get_current_language()
        
        search_terms = [word]
        if assoc_str:
            extra_terms = [t.strip() for t in assoc_str.replace("，", ",").split(',') if t.strip()]
            search_terms.extend(extra_terms)
            
        all_results = []
        seen = set()
        for term in search_terms:
            res = self.db.search_translations_l2(term, current_lang)
            for r in res:
                if r not in seen:
                    seen.add(r)
                    all_results.append(r)
        
        results = all_results
            
        top = tk.Toplevel(self)
        title_word = word
        if len(search_terms) > 1:
            title_word += " / " + " / ".join(search_terms[1:])
        top.title(f"搜尋結果 (Search Results) - {title_word}")
        top.geometry("700x550")
        
        # Add button frame at the top
        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        frame = ttk.Frame(top)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text_widget = tk.Text(frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)
        
        text_widget.tag_configure("highlight", background="yellow", foreground="black")
        
        def display_results(res_list, words_to_highlight):
            text_widget.config(state="normal")
            text_widget.delete("1.0", tk.END)
            if not res_list:
                text_widget.insert(tk.END, "找不到結果 (No results found)。\n")
            for i, res in enumerate(res_list, 1):
                text_widget.insert(tk.END, f"【{i}】\n{res}\n\n")
            
            # highlight all matched words by sorting descending by length to avoid sub-word overlap issues
            words_to_highlight = sorted(list(words_to_highlight), key=len, reverse=True)
            for w in words_to_highlight:
                if not w.strip(): continue
                start_pos = "1.0"
                while True:
                    start_pos = text_widget.search(w, start_pos, stopindex=tk.END, nocase=True)
                    if not start_pos:
                        break
                    end_pos = f"{start_pos}+{len(w)}c"
                    text_widget.tag_add("highlight", start_pos, end_pos)
                    start_pos = end_pos
                    
            text_widget.config(state="disabled")

        display_results(results, search_terms)
        
        def run_advanced_search():
            adv_btn.config(state="disabled", text="處理中... (Processing...)")
            top.config(cursor="wait")
            top.update()
            
            def _thread_task():
                try:
                    all_adv_results = []
                    all_matched_words = set(search_terms)
                    adv_seen = set()
                    
                    for term in search_terms:
                        adv_res, matched = self.db.search_translations_l2_advanced(term, current_lang)
                        for r in adv_res:
                            if r not in adv_seen:
                                adv_seen.add(r)
                                all_adv_results.append(r)
                        for m in matched:
                            all_matched_words.add(m)
                            
                    def update_ui():
                        display_results(all_adv_results, list(all_matched_words))
                        adv_btn.config(state="normal", text="進階搜尋 (Enhanced Search with Spacy)")
                        top.config(cursor="")
                        if not all_adv_results:
                            messagebox.showinfo("搜尋結果", "進階搜尋找不到更多結果。")
                    self.after(0, update_ui)
                except Exception as e:
                    def update_ui_err():
                        messagebox.showerror("錯誤", f"進階搜尋發生錯誤: {e}")
                        adv_btn.config(state="normal", text="進階搜尋 (Enhanced Search with Spacy)")
                        top.config(cursor="")
                    self.after(0, update_ui_err)
            
            import threading
            threading.Thread(target=_thread_task, daemon=True).start()
            
        adv_btn = ttk.Button(btn_frame, text="進階搜尋 (Enhanced Search with Spacy)", command=run_advanced_search)
        adv_btn.pack(side="left")

    def edit_item(self):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要修改的項目 (Select an item to edit)")
            return
            
        idx = selection[0]
        item = self.due_srs_items[idx]
        item_id = item[0]
        current_word = item[1]
        current_sent = item[2]
        current_exp = item[3]
        current_assoc = item[5] if len(item) > 5 else ""

        top = tk.Toplevel(self)
        top.title("修改內容 (Edit Item)")
        
        ttk.Label(top, text="單字 (Word):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        word_var = tk.StringVar(value=current_word)
        ttk.Entry(top, textvariable=word_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(top, text="句子 (Sentences):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        sent_var = tk.StringVar(value=current_sent)
        ttk.Entry(top, textvariable=sent_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(top, text="解釋 (Explanation):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        exp_var = tk.StringVar(value=current_exp)
        ttk.Entry(top, textvariable=exp_var, width=40).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(top, text="關聯字 (Associated Words):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        assoc_var = tk.StringVar(value=current_assoc)
        ttk.Entry(top, textvariable=assoc_var, width=40).grid(row=3, column=1, padx=5, pady=5)
        
        def save_changes():
            self.db.update_srs_item_content(item_id, word_var.get(), sent_var.get(), exp_var.get(), assoc_var.get())
            self.load_due_srs_items()
            top.destroy()
            
        ttk.Button(top, text="儲存 (Save)", command=save_changes).grid(row=4, column=0, columnspan=2, pady=10)

    def show_explanation(self):
        selection = self.srs_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇要查看的項目 (Select an item to view)")
            return

        idx = selection[0]
        item = self.due_srs_items[idx]
        assoc = item[5] if len(item) > 5 else ""
        msg = f"【單字 Word】\n{item[1]}\n\n【句子 Sentences】\n{item[2]}\n\n【解釋 Explanation】\n{item[3]}\n\n【關聯字 Associated Words】\n{assoc}"
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
