import tkinter as tk
from tkinter import ttk, messagebox

class LadderingTab(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager
        self.create_ui()
        self.load_laddering_cards()

    def create_ui(self):
        # Explain the concept briefly
        desc = "【規則】強制斷開母語 (L1)！只能使用已熟練的第二外語 (L2) 來學習第三外語 (L3)。"
        ttk.Label(self, text=desc, foreground="red", font=("Helvetica", 10, "bold")).pack(pady=10)

        # Add Card Section
        add_frame = ttk.LabelFrame(self, text="新增階梯卡片 (Add Laddering Card)")
        add_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(add_frame, text="L2 提示/解釋 (Prompt/Explanation in L2):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.l2_prompt_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.l2_prompt_var, width=50).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="L3 目標詞彙/語法 (Target in L3):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.l3_target_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.l3_target_var, width=50).grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(add_frame, text="新增卡片 (Add Card)", command=self.add_laddering_card).grid(row=2, column=0, columnspan=2, pady=10)

        # View Cards Section
        view_frame = ttk.LabelFrame(self, text="卡片列表 (Card List - L2 Only)")
        view_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.ladder_listbox = tk.Listbox(view_frame, height=15)
        self.ladder_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.ladder_listbox.bind("<<ListboxSelect>>", self.on_ladder_select)

    def add_laddering_card(self):
        l2_prompt = self.l2_prompt_var.get().strip()
        l3_target = self.l3_target_var.get().strip()

        if not l2_prompt or not l3_target:
            messagebox.showwarning("警告", "L2 提示與 L3 目標都不能為空")
            return

        self.db.add_laddering_card(l2_prompt, l3_target)
        messagebox.showinfo("成功", "已新增卡片 (Card Added)")
        self.l2_prompt_var.set("")
        self.l3_target_var.set("")
        self.load_laddering_cards()

    def load_laddering_cards(self):
        self.ladder_listbox.delete(0, tk.END)
        self.ladder_cards = self.db.get_all_laddering_cards()

        for card in self.ladder_cards:
            # Show L2 prompt ONLY in the list to enforce L2 thinking
            display_text = f"[L2 Prompt]: {card[1]}"
            self.ladder_listbox.insert(tk.END, display_text)

    def on_ladder_select(self, event):
        selection = self.ladder_listbox.curselection()
        if not selection: return

        idx = selection[0]
        card = self.ladder_cards[idx]
        # card is (id, l2_prompt, l3_target, notes)

        msg = f"【L2 提示 Prompt】\n{card[1]}\n\n【L3 解答 Target】\n{card[2]}"
        messagebox.showinfo("語言階梯卡片 (Laddering Card)", msg)
