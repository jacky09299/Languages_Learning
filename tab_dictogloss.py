import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class DictoglossTab(ttk.Frame):
    def __init__(self, parent, db_manager, root_window):
        super().__init__(parent)
        self.db = db_manager
        self.root_window = root_window
        self.app = root_window
        self.create_ui()
        self.init_audio()
        self.load_dictogloss_history()

    def refresh_data(self):
        self.load_dictogloss_history()

    def create_ui(self):
        # Audio Player Section
        player_frame = ttk.LabelFrame(self, text="音訊播放器 (Audio Player)")
        player_frame.pack(fill="x", padx=10, pady=10)

        self.audio_path_var = tk.StringVar()
        ttk.Entry(player_frame, textvariable=self.audio_path_var, width=50, state="readonly").grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(player_frame, text="選擇音檔 (Browse...)", command=self.load_audio).grid(row=0, column=1, padx=5, pady=5)

        controls_frame = ttk.Frame(player_frame)
        controls_frame.grid(row=1, column=0, columnspan=2, pady=5)

        ttk.Button(controls_frame, text="⏮ -5s (F2)", command=self.rewind_audio).pack(side="left", padx=5)
        ttk.Button(controls_frame, text="⏯ 播放/暫停 (F3)", command=self.toggle_play).pack(side="left", padx=5)
        ttk.Button(controls_frame, text="⏭ +5s (F4)", command=self.forward_audio).pack(side="left", padx=5)

        # Bind global hotkeys to the root window
        self.root_window.bind("<F2>", lambda e: self.rewind_audio())
        self.root_window.bind("<F3>", lambda e: self.toggle_play())
        self.root_window.bind("<F4>", lambda e: self.forward_audio())

        # Text Input & History Section
        text_frame = ttk.LabelFrame(self, text="重構文本 (Reconstructed Text)")
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.dicto_text_input = tk.Text(text_frame, wrap="word", height=10)
        self.dicto_text_input.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(text_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="新增儲存 (Save New)", command=self.save_dictogloss).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="更新當前 (Update Current)", command=self.update_dictogloss).pack(side="left", padx=5)

        history_frame = ttk.LabelFrame(self, text="歷史紀錄 (History)")
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.dicto_listbox = tk.Listbox(history_frame, height=5)
        self.dicto_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.dicto_listbox.bind("<<ListboxSelect>>", self.on_dicto_select)

    def init_audio(self):
        if PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
            except pygame.error:
                # Fallback for headless environments or machines without audio devices
                pass

        self.is_playing = False
        self.audio_loaded = False
        self.current_pos = 0.0

    def load_dictogloss_history(self):
        self.dicto_listbox.delete(0, tk.END)
        current_lang = self.app.get_current_language()
        self.dicto_history = self.db.get_all_dictogloss(target_language=current_lang)
        for item in self.dicto_history:
            # id, title, audio_path, text
            display_text = f"[{item[1]}] {item[2]}"
            self.dicto_listbox.insert(tk.END, display_text)

    def on_dicto_select(self, event):
        selection = self.dicto_listbox.curselection()
        if not selection: return
        idx = selection[0]
        item = self.dicto_history[idx]

        self.dicto_text_input.delete("1.0", tk.END)
        self.dicto_text_input.insert("1.0", item[3] if item[3] else "")

    def load_audio(self):
        if not PYGAME_AVAILABLE:
            messagebox.showerror("錯誤", "需要安裝 pygame 才能使用音訊功能 (Requires pygame module)")
            return
        filepath = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if filepath:
            self.audio_path_var.set(filepath)
            pygame.mixer.music.load(filepath)
            self.audio_loaded = True
            self.is_playing = False
            self.current_pos = 0.0

    def toggle_play(self):
        if not PYGAME_AVAILABLE or not self.audio_loaded: return

        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False
        else:
            if pygame.mixer.music.get_pos() == -1: # Never started or ended
                pygame.mixer.music.play()
            else:
                pygame.mixer.music.unpause()
            self.is_playing = True

    def rewind_audio(self):
        if not PYGAME_AVAILABLE or not self.audio_loaded: return
        try:
            new_pos = max(0.0, self.current_pos + (pygame.mixer.music.get_pos()/1000.0) - 5.0)
            pygame.mixer.music.set_pos(new_pos)
            self.current_pos = new_pos
        except:
            pass

    def forward_audio(self):
        if not PYGAME_AVAILABLE or not self.audio_loaded: return
        try:
            new_pos = self.current_pos + (pygame.mixer.music.get_pos()/1000.0) + 5.0
            pygame.mixer.music.set_pos(new_pos)
            self.current_pos = new_pos
        except:
            pass

    def save_dictogloss(self):
        audio_path = self.audio_path_var.get()
        text = self.dicto_text_input.get("1.0", tk.END).strip()

        if not audio_path:
            messagebox.showwarning("警告", "請先載入音檔 (Please load an audio file)")
            return

        current_lang = self.app.get_current_language()
        self.db.add_dictogloss("Audio Lesson", audio_path, text, target_language=current_lang)
        messagebox.showinfo("成功", "已儲存重構文本 (Saved)")
        self.load_dictogloss_history()

    def update_dictogloss(self):
        selection = self.dicto_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請先選擇歷史紀錄 (Select an item to update)")
            return

        idx = selection[0]
        item_id = self.dicto_history[idx][0]
        text = self.dicto_text_input.get("1.0", tk.END).strip()

        self.db.update_dictogloss_text(item_id, text)
        messagebox.showinfo("成功", "已更新重構文本 (Updated)")
        self.load_dictogloss_history()
