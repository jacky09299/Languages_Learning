import tkinter as tk
from tkinter import ttk, messagebox

class DashboardTab(ttk.Frame):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.db = db_manager

        # Timer state initialization
        self.current_phase = 0
        self.phases = [
            (15 * 60, "階段: 15分鐘 高強度複習 (Review)"),
            (30 * 60, "階段: 30分鐘 吸收新輸入 (New Input)\n(手動將感興趣的素材貼給 AI 降階為 i+1)"),
            (15 * 60, "階段: 15分鐘 預覽 (Preview)")
        ]
        self.time_left = self.phases[self.current_phase][0]
        self.timer_running = False

        self.create_ui()
        self.load_rotations()

    def create_ui(self):
        # Upper: Rotation System
        rotation_frame = ttk.LabelFrame(self, text="語言輪替系統 (Language Rotation - 3 Months)")
        rotation_frame.pack(fill="x", padx=10, pady=10)

        input_frame = ttk.Frame(rotation_frame)
        input_frame.pack(fill="x", pady=5)

        ttk.Label(input_frame, text="語言:").pack(side="left", padx=5)
        self.lang_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.lang_var, width=15).pack(side="left", padx=5)

        ttk.Label(input_frame, text="狀態:").pack(side="left", padx=5)
        self.status_var = tk.StringVar(value="核心突破區 (Core)")
        ttk.Combobox(input_frame, textvariable=self.status_var, values=["核心突破區 (Core)", "背景維護區 (Background)"], width=20, state="readonly").pack(side="left", padx=5)

        ttk.Button(input_frame, text="新增輪替 (Add)", command=self.add_rotation).pack(side="left", padx=10)

        self.rotation_listbox = tk.Listbox(rotation_frame, height=5)
        self.rotation_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Lower: Pomodoro 15/30/15 Timer
        timer_frame = ttk.LabelFrame(self, text="15/30/15 分鐘法則 (Timer)")
        timer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.timer_label = ttk.Label(timer_frame, text="15:00", font=("Helvetica", 48, "bold"))
        self.timer_label.pack(pady=20)

        self.phase_label = ttk.Label(timer_frame, text=self.phases[0][1], font=("Helvetica", 14))
        self.phase_label.pack(pady=5)

        btn_frame = ttk.Frame(timer_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="開始/暫停 (Start/Pause)", command=self.toggle_timer).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="跳至下一階段 (Next Phase)", command=self.next_phase).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="重置 (Reset)", command=self.reset_timer).pack(side="left", padx=5)

    def add_rotation(self):
        lang = self.lang_var.get().strip()
        status = self.status_var.get()
        if not lang:
            messagebox.showwarning("警告", "請輸入語言名稱")
            return

        self.db.add_language_rotation(lang, status)
        self.lang_var.set("")
        self.load_rotations()

    def load_rotations(self):
        self.rotation_listbox.delete(0, tk.END)
        active = self.db.get_active_rotations()
        for item in active:
            # item: id, language, status, end_date
            display_text = f"[{item[2]}] {item[1]} (直至/Until {item[3]})"
            self.rotation_listbox.insert(tk.END, display_text)

    def update_timer_display(self):
        mins, secs = divmod(self.time_left, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

    def toggle_timer(self):
        self.timer_running = not self.timer_running
        if self.timer_running:
            self.timer_id = self.after(1000, self.tick)
        else:
            if hasattr(self, 'timer_id'):
                self.after_cancel(self.timer_id)

    def tick(self):
        if self.timer_running and self.time_left > 0:
            self.time_left -= 1
            self.update_timer_display()
            self.timer_id = self.after(1000, self.tick)
        elif self.time_left == 0:
            self.timer_running = False
            messagebox.showinfo("時間到 (Time's up)", "目前階段結束！(Phase completed!)")

    def next_phase(self):
        self.timer_running = False
        if hasattr(self, 'timer_id'):
            self.after_cancel(self.timer_id)
        self.current_phase = (self.current_phase + 1) % 3
        self.time_left = self.phases[self.current_phase][0]
        self.phase_label.config(text=self.phases[self.current_phase][1])
        self.update_timer_display()

    def reset_timer(self):
        self.timer_running = False
        if hasattr(self, 'timer_id'):
            self.after_cancel(self.timer_id)
        self.time_left = self.phases[self.current_phase][0]
        self.update_timer_display()
