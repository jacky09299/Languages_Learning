import tkinter as tk
from tkinter import ttk, messagebox
import threading
from sheet_fetcher import fetch_and_sync_answers
from email_sender import send_translation_emails

class TranslationTab(ttk.Frame):
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db = db_manager
        self.app = app
        self.create_ui()
        self.load_translations()

    def refresh_data(self):
        self.load_translations()

    def create_ui(self):
        # Split into left (input) and right (review)
        left_frame = ttk.Frame(self)
        left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_frame = ttk.Frame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Left side: Input Translation
        ttk.Label(left_frame, text="外語 (L2 Text):").pack(anchor="w")
        self.l2_text_input = tk.Text(left_frame, height=10, width=40)
        self.l2_text_input.pack(fill="both", expand=True, pady=5)

        ttk.Label(left_frame, text="母語翻譯 (L1 Translation):").pack(anchor="w")
        self.l1_text_input = tk.Text(left_frame, height=10, width=40)
        self.l1_text_input.pack(fill="both", expand=True, pady=5)

        lock_frame = ttk.Frame(left_frame)
        lock_frame.pack(fill="x", pady=5)
        ttk.Label(lock_frame, text="時間鎖定天數 (Lock Days):").pack(side="left")
        self.lock_days_var = tk.IntVar(value=3)
        ttk.Entry(lock_frame, textvariable=self.lock_days_var, width=5).pack(side="left", padx=5)

        ttk.Button(left_frame, text="儲存並鎖定 (Save & Lock)", command=self.add_translation).pack(pady=10)

        # Right side: Review Unlocked Translations
        top_right_frame = ttk.Frame(right_frame)
        top_right_frame.pack(fill="x")
        ttk.Label(top_right_frame, text="解鎖可翻譯項目 (Ready to Translate):").pack(side="left", anchor="w")

        ttk.Button(top_right_frame, text="同步 Gmail 回答 (Sync Answers)", command=self.sync_answers).pack(side="right")
        ttk.Button(top_right_frame, text="手動寄送信件 (Send Emails)", command=self.send_emails).pack(side="right", padx=5)

        self.trans_listbox = tk.Listbox(right_frame, height=10)
        self.trans_listbox.pack(fill="both", expand=True, pady=5)
        self.trans_listbox.bind("<<ListboxSelect>>", self.on_trans_select)

        ttk.Label(right_frame, text="母語提示 (L1 Prompt) - 請翻回外語:").pack(anchor="w", pady=(5, 0))
        self.l1_prompt_display = tk.Text(right_frame, height=4, width=40)
        self.l1_prompt_display.pack(fill="both", expand=True, pady=(2, 5))
        self.l1_prompt_display.config(state="disabled")

        ttk.Label(right_frame, text="已收取信箱回答 / 手動填寫翻譯 (Fetched or Manual Translation):").pack(anchor="w", pady=(5, 0))
        self.trans_back_input = tk.Text(right_frame, height=8, width=40)
        self.trans_back_input.pack(fill="both", expand=True, pady=5)

        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="對比原文 (Compare)", command=self.compare_translation).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="標記完成 (Mark Completed)", command=self.complete_translation).pack(side="left", padx=5)

    def add_translation(self):
        l2_text = self.l2_text_input.get("1.0", tk.END).strip()
        l1_text = self.l1_text_input.get("1.0", tk.END).strip()
        lock_days = self.lock_days_var.get()

        if not l2_text or not l1_text:
            messagebox.showwarning("警告", "外語與母語都不能為空 (Texts cannot be empty)")
            return

        current_lang = self.app.get_current_language()
        self.db.add_translation(l2_text, l1_text, lock_days, target_language=current_lang)
        self.l2_text_input.delete("1.0", tk.END)
        self.l1_text_input.delete("1.0", tk.END)
        self.load_translations()

    def load_translations(self):
        self.trans_listbox.delete(0, tk.END)
        current_lang = self.app.get_current_language()
        self.ready_trans = self.db.get_ready_translations(target_language=current_lang)

        for trans in self.ready_trans:
            # trans is (id, l1_text, l2_text, l1_user_translation)
            is_synced = "✔️" if trans[3] else "❌"
            display_text = f"[{trans[0]}] [{is_synced}] {trans[1][:25]}..." if len(trans[1]) > 25 else f"[{trans[0]}] [{is_synced}] {trans[1]}"
            self.trans_listbox.insert(tk.END, display_text)

    def sync_answers(self):
        def _sync():
            current_lang = self.app.get_current_language()
            success = fetch_and_sync_answers(self.db, current_lang)
            self.after(0, self.load_translations)
            if success:
                pass
            else:
                self.after(0, lambda: messagebox.showwarning("同步失敗", "同步過程中發生錯誤或沒有新回答。"))

        threading.Thread(target=_sync, daemon=True).start()

    def send_emails(self):
        def _send():
            try:
                send_translation_emails(self.db)
            except Exception as e:
                self.after(0, lambda: messagebox.showwarning("發送失敗", f"發送過程中發生錯誤: {str(e)}"))

        threading.Thread(target=_send, daemon=True).start()

    def on_trans_select(self, event):
        selection = self.trans_listbox.curselection()
        if not selection: return

        idx = selection[0]
        l1_text = self.ready_trans[idx][1]
        user_trans = self.ready_trans[idx][3]

        # Display the L1 Prompt in the new text box
        self.l1_prompt_display.config(state="normal")
        self.l1_prompt_display.delete("1.0", tk.END)
        self.l1_prompt_display.insert("1.0", l1_text)
        self.l1_prompt_display.config(state="disabled")

        # Put user translation in text box if synced, otherwise empty so they can type manually
        self.trans_back_input.delete("1.0", tk.END)
        if user_trans:
            self.trans_back_input.insert("1.0", user_trans)

    def compare_translation(self):
        selection = self.trans_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇項目 (Select an item)")
            return

        idx = selection[0]
        l1_text_intermediate = self.ready_trans[idx][1]
        l2_text_original = self.ready_trans[idx][2]
        l2_text_user = self.trans_back_input.get("1.0", tk.END).strip()

        msg = (
            "這是一個「雙向翻譯」練習：我先把原文翻譯成母語，幾天後再翻回原文。\n\n"
            "目的是找出我「能理解但無法正確表達」的地方，以及語言能力的落差。\n\n"
            "請幫我分析我的翻譯過程：\n\n"
            "1. 比較原文與我翻回來的句子\n"
            "2. 指出錯誤與不自然之處\n"
            "3. 分析這些錯誤是否來自「中間翻譯」\n"
            "4. 告訴我哪些是母語干擾造成的\n"
            "5. 提供最接近原文的正確版本\n"
            "6. 教我應該怎麼避免這類錯誤\n"
            "7. 請幫我分類這些錯誤（例如：搭配錯誤 / 文法錯誤 / 語氣問題 / 母語直譯）\n\n\n"
            "【原文】\n"
            f"{l2_text_original}\n\n"
            "【我的翻譯（中間語言）】\n"
            f"{l1_text_intermediate}\n\n"
            "【我翻回來的句子】\n"
            f"{l2_text_user}"
        )

        # We can use a Toplevel window for better reading
        top = tk.Toplevel(self)
        top.title("對比結果 (Comparison)")
        text = tk.Text(top, height=30, width=90)
        text.pack(padx=10, pady=(10, 5))
        text.insert("1.0", msg)
        text.config(state="disabled")

        def copy_to_clipboard():
            top.clipboard_clear()
            top.clipboard_append(msg)
            top.destroy()

        ttk.Button(top, text="複製全部 (Copy All)", command=copy_to_clipboard).pack(pady=(0, 10))

    def complete_translation(self):
        selection = self.trans_listbox.curselection()
        if not selection: return

        idx = selection[0]
        trans_id = self.ready_trans[idx][0]

        self.db.complete_translation(trans_id)
        self.trans_back_input.delete("1.0", tk.END)
        self.load_translations()
