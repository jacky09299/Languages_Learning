import tkinter as tk
from tkinter import ttk, messagebox

class TranslationTab(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.create_ui()
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
        ttk.Label(right_frame, text="解鎖可翻譯項目 (Ready to Translate):").pack(anchor="w")

        self.trans_listbox = tk.Listbox(right_frame, height=10)
        self.trans_listbox.pack(fill="both", expand=True, pady=5)
        self.trans_listbox.bind("<<ListboxSelect>>", self.on_trans_select)

        ttk.Label(right_frame, text="翻譯回外語 (Translate back to L2):").pack(anchor="w", pady=(10, 0))
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

        self.db.add_translation(l2_text, l1_text, lock_days)
        messagebox.showinfo("成功", "已儲存並鎖定 (Saved and Locked)")
        self.l2_text_input.delete("1.0", tk.END)
        self.l1_text_input.delete("1.0", tk.END)
        self.load_translations()

    def load_translations(self):
        self.trans_listbox.delete(0, tk.END)
        self.ready_trans = self.db.get_ready_translations()

        for trans in self.ready_trans:
            # trans is (id, l1_text, l2_text)
            display_text = trans[1][:30] + "..." if len(trans[1]) > 30 else trans[1]
            self.trans_listbox.insert(tk.END, display_text)

    def on_trans_select(self, event):
        selection = self.trans_listbox.curselection()
        if not selection: return

        idx = selection[0]
        l1_text = self.ready_trans[idx][1]

        # Display the prompt (L1 text) somewhere, maybe via messagebox or just the listbox is enough,
        # Let's show it in a messagebox to focus the user
        messagebox.showinfo("母語提示 (L1 Prompt)", f"請將以下母語翻回外語：\n\n{l1_text}")

    def compare_translation(self):
        selection = self.trans_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請選擇項目 (Select an item)")
            return

        idx = selection[0]
        l2_text_original = self.ready_trans[idx][2]
        l2_text_user = self.trans_back_input.get("1.0", tk.END).strip()

        # For simplicity, we just show both in a message box to let the user manual-AI verify
        msg = f"【你的翻譯 Your Translation】\n{l2_text_user}\n\n【原始外語 Original L2】\n{l2_text_original}\n\n(將此對比貼給 AI 進行深度分析 / Paste this to AI for analysis)"

        # We can use a Toplevel window for better reading
        top = tk.Toplevel(self)
        top.title("對比結果 (Comparison)")
        text = tk.Text(top, height=20, width=60)
        text.pack(padx=10, pady=10)
        text.insert("1.0", msg)
        text.config(state="disabled")

    def complete_translation(self):
        selection = self.trans_listbox.curselection()
        if not selection: return

        idx = selection[0]
        trans_id = self.ready_trans[idx][0]

        self.db.complete_translation(trans_id)
        self.trans_back_input.delete("1.0", tk.END)
        self.load_translations()
        messagebox.showinfo("成功", "已完成 (Completed)")
