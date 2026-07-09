import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class SettingsTab(ttk.Frame):
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db = db_manager
        self.app = app
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_ai = ttk.Frame(self.notebook)
        self.tab_srs = ttk.Frame(self.notebook)
        self.tab_config = ttk.Frame(self.notebook)
        self.tab_tutorial = ttk.Frame(self.notebook)
        self.tab_about = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_ai, text="AI 產生與匯入")
        self.notebook.add(self.tab_srs, text="學習與複習機制")
        self.notebook.add(self.tab_config, text="系統設定檔 (Config)")
        self.notebook.add(self.tab_tutorial, text="軟體教學")
        self.notebook.add(self.tab_about, text="關於系統")
        
        self.create_ai_ui(self.tab_ai)
        self.create_srs_ui(self.tab_srs)
        self.create_config_ui(self.tab_config)
        self.create_tutorial_ui(self.tab_tutorial)
        self.create_about_ui(self.tab_about)

    # -----------------------------
    # 1. AI 產生與匯入 (Original UI)
    # -----------------------------
    def create_ai_ui(self, parent_frame):
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Frame for Prompt Generation
        prompt_frame = ttk.LabelFrame(scrollable_frame, text="AI Prompt 生成器 (Prompt Generator)")
        prompt_frame.pack(fill="x", padx=10, pady=10)

        # Controls for generating prompt
        control_frame = ttk.Frame(prompt_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(control_frame, text="語言:").pack(side="left", padx=5)
        self.lang_var = tk.StringVar(value="繁體中文")
        ttk.Combobox(control_frame, textvariable=self.lang_var, values=["繁體中文", "英文"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Label(control_frame, text="類型:").pack(side="left", padx=5)
        self.type_var = tk.StringVar(value="鼓勵的話")
        ttk.Combobox(control_frame, textvariable=self.type_var, values=["鼓勵的話", "笑話", "小故事"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Label(control_frame, text="數量:").pack(side="left", padx=5)
        self.quantity_var = tk.IntVar(value=5)
        ttk.Entry(control_frame, textvariable=self.quantity_var, width=5).pack(side="left", padx=5)

        ttk.Label(control_frame, text="格式:").pack(side="left", padx=5)
        self.format_var = tk.StringVar(value="JSON")
        ttk.Combobox(control_frame, textvariable=self.format_var, values=["JSON", "SQLite DB"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Button(control_frame, text="生成 Prompt", command=self.generate_prompt).pack(side="left", padx=10)

        pref_frame = ttk.Frame(prompt_frame)
        pref_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(pref_frame, text="自訂偏好 (例如：要幽默、主角是貓):").pack(side="left", padx=5)
        self.pref_var = tk.StringVar()
        ttk.Entry(pref_frame, textvariable=self.pref_var, width=50).pack(side="left", padx=5)

        self.prompt_text = tk.Text(prompt_frame, height=8, width=60)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(prompt_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="複製 Prompt", command=self.copy_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="編輯目前範本", command=self.open_template_editor).pack(side="left", padx=5)

        # Import JSON
        import_frame = ttk.LabelFrame(scrollable_frame, text="匯入 AI 生成結果 (Import AI Output)")
        import_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ttk.Label(import_frame, text="請將 AI 輸出的 JSON 格式貼在下方：").pack(anchor="w", padx=5, pady=5)
        self.json_text = tk.Text(import_frame, height=10, width=60)
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(import_frame, text="儲存至資料庫", command=self.save_to_database).pack(pady=10)

        # Import DB
        db_import_frame = ttk.LabelFrame(scrollable_frame, text="匯入外部資料庫 (Import SQLite DB)")
        db_import_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(db_import_frame, text="支援匯入您的 jokes.db (笑話) 或 story.db (小故事) 格式").pack(anchor="w", padx=5, pady=5)
        ttk.Button(db_import_frame, text="選擇並匯入 DB 檔...", command=self.import_db_file).pack(padx=5, pady=5)

    def get_default_template(self, key):
        if key == "JSON":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "請嚴格使用以下 JSON 陣列格式輸出，不要包含任何其他文字或 markdown 標籤：\n"
                "[\n  {{\"content\": \"第一個內容\"}},\n  {{\"content\": \"第二個內容\"}}\n]\n{extra}"
            )
        elif key == "DB_story":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "我需要你將生成的內容存入 SQLite 資料庫中。\n"
                "請建立一個名為 story.db 的 SQLite 資料庫檔案。\n"
                "其中包含 stories 資料表，欄位：(storyid INTEGER PRIMARY KEY, storytitle TEXT, sentence1 TEXT, sentence2 TEXT, sentence3 TEXT, sentence4 TEXT, sentence5 TEXT)。\n"
                "請寫入資料庫並提供下載，或給我 Python 程式碼讓我自己產生。\n"
            )
        elif key == "DB_joke":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "請存入 SQLite 資料庫中。\n"
                "建立名為 jokes.db 檔案，包含 jokes 資料表，欄位：(id INTEGER PRIMARY KEY, setup TEXT, punchline TEXT)。如果不是笑話也可拆分兩段填入。\n"
                "請寫入資料庫並提供下載，或給我 Python 程式碼讓我自己產生。\n"
            )
        return ""

    def generate_prompt(self):
        lang, item_type, quantity, output_format, custom_pref = self.lang_var.get(), self.type_var.get(), self.quantity_var.get(), self.format_var.get(), self.pref_var.get().strip()
        
        prompt_key = "JSON" if output_format == "JSON" else ("DB_story" if item_type == "小故事" else "DB_joke")
        description = "鼓勵的話" if item_type == "鼓勵的話" else ("有分段的小故事" if item_type == "小故事" else "笑話")
        lang_desc = "繁體中文" if lang == "繁體中文" else "英文"
        
        pref_text = f"【內容偏好與限制】：{custom_pref}。\n" if custom_pref else ""
        extra = "請確保故事內容有適當的分段（可使用 \\n 換行）。\n" if output_format == "JSON" and item_type == "小故事" else ""
            
        template = self.db.get_prompt(prompt_key) or self.get_default_template(prompt_key)
            
        try:
            prompt = template.format(quantity=quantity, lang_desc=lang_desc, description=description, pref_text=pref_text, extra=extra)
            self.prompt_text.delete(1.0, tk.END)
            self.prompt_text.insert(tk.END, prompt)
        except Exception as e:
            messagebox.showerror("範本錯誤", f"自訂範本格式有誤：\n{str(e)}")

    def open_template_editor(self):
        prompt_key = "JSON" if self.format_var.get() == "JSON" else ("DB_story" if self.type_var.get() == "小故事" else "DB_joke")
        template = self.db.get_prompt(prompt_key) or self.get_default_template(prompt_key)
            
        editor = tk.Toplevel(self)
        editor.title(f"編輯範本 - {prompt_key}")
        editor.geometry("700x500")
        
        ttk.Label(editor, text="可用變數: {quantity}, {lang_desc}, {description}, {pref_text}, {extra}").pack(pady=5, padx=10, anchor="w")
        text_area = tk.Text(editor, wrap="word", height=20)
        text_area.pack(fill="both", expand=True, padx=10, pady=5)
        text_area.insert("1.0", template)
        
        btn_frame = ttk.Frame(editor)
        btn_frame.pack(pady=10)
        
        def save():
            self.db.save_prompt(prompt_key, text_area.get("1.0", tk.END).strip())
            messagebox.showinfo("成功", "已儲存！")
            editor.destroy()
            self.generate_prompt()
            
        def reset():
            if messagebox.askyesno("確認", "確定要還原成預設範本嗎？"):
                self.db.delete_prompt(prompt_key)
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", self.get_default_template(prompt_key))
                
        ttk.Button(btn_frame, text="儲存", command=save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="還原預設", command=reset).pack(side="left", padx=5)

    def copy_prompt(self):
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if prompt:
            self.clipboard_clear()
            self.clipboard_append(prompt)
            messagebox.showinfo("成功", "已複製到剪貼簿！")

    def save_to_database(self):
        json_str = self.json_text.get(1.0, tk.END).strip()
        if not json_str: return
        try:
            data = json.loads(json_str)
            lang = "Chinese" if self.lang_var.get() == "繁體中文" else "English"
            db_category = "encouragement" if self.type_var.get() == "鼓勵的話" else "joke"
            count = 0
            for item in data:
                if "content" in item and item["content"].strip():
                    self.db.add_daily_resource(category=db_category, content=item["content"].strip(), language=lang)
                    count += 1
            messagebox.showinfo("成功", f"成功匯入 {count} 筆資料！")
            self.json_text.delete(1.0, tk.END)
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入失敗：{str(e)}")

    def import_db_file(self):
        from tkinter import filedialog
        import sqlite3
        filepath = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")])
        if not filepath: return
        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            count = 0
            if "jokes" in tables:
                for j in cursor.execute("SELECT id, setup, punchline FROM jokes").fetchall():
                    self.db.add_daily_resource(category="joke", content=f"{j[1]}\n\n{j[2]}", language="English")
                    count += 1
            if "stories" in tables:
                for s in cursor.execute("SELECT storyid, storytitle, sentence1, sentence2, sentence3, sentence4, sentence5 FROM stories").fetchall():
                    self.db.add_daily_resource(category="joke", content=f"{s[1]}\n{s[2]}\n{s[3]}\n{s[4]}\n{s[5]}", language="English")
                    count += 1
            if count > 0: messagebox.showinfo("成功", f"成功匯入 {count} 筆資料！")
            else: messagebox.showwarning("警告", "找不到支援的資料表。")
            conn.close()
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入失敗：{str(e)}")

    # -----------------------------
    # 2. 學習與複習機制 (SRS)
    # -----------------------------
    def create_srs_ui(self, parent_frame):
        # Read current values from DB, or default
        prob = self.db.get_setting("srs_revert_probability", 0.14)
        count = self.db.get_setting("srs_revert_count", 3)
        minimum = self.db.get_setting("srs_min_unanswered", 2)
                
        self.srs_prob = tk.DoubleVar(value=prob) # 1/7 ~= 0.14
        self.srs_revert_count = tk.IntVar(value=count)
        self.srs_min_unanswered = tk.IntVar(value=minimum)

        ttk.Label(parent_frame, text="雙向翻譯複習 (間隔重複/SRS) 設定", font=("Helvetica", 14, "bold")).pack(pady=15, padx=10, anchor="w")
        ttk.Label(parent_frame, text="每天早上系統會根據以下規則，將已經標記為「完成 (Completed)」的翻譯，隨機降級回「準備好 (Ready)」讓您重新複習。").pack(padx=10, anchor="w")

        frame1 = ttk.LabelFrame(parent_frame, text="規則一：每日隨機抽考")
        frame1.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame1, text="觸發機率 (0 = 永遠不退回, 1 = 每天都退回):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        prob_entry = ttk.Entry(frame1, textvariable=self.srs_prob, width=10)
        prob_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame1, text="(預設: 0.14，約為每週 1 次)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        
        ttk.Label(frame1, text="每次隨機退回的題數:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        count_entry = ttk.Entry(frame1, textvariable=self.srs_revert_count, width=10)
        count_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame1, text="題 (預設: 3 題)").grid(row=1, column=2, padx=5, pady=5, sticky="w")

        frame2 = ttk.LabelFrame(parent_frame, text="規則二：每日題量保底機制")
        frame2.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(frame2, text="每天最少要保持幾題未作答的 Ready 翻譯?").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        min_entry = ttk.Entry(frame2, textvariable=self.srs_min_unanswered, width=10)
        min_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame2, text="題 (預設: 2 題)").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        ttk.Label(frame2, text="如果今天的未作答題目不夠，系統會自動從已完成的題目中抽出差額補足。").grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        ttk.Button(parent_frame, text="儲存學習設定", command=self.save_srs_settings).pack(pady=10)

    def save_srs_settings(self):
        try:
            self.db.set_setting("srs_revert_probability", float(self.srs_prob.get()))
            self.db.set_setting("srs_revert_count", int(self.srs_revert_count.get()))
            self.db.set_setting("srs_min_unanswered", int(self.srs_min_unanswered.get()))
                
            messagebox.showinfo("成功", "學習複習設定已成功儲存至資料庫！")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{str(e)}")

    # -----------------------------
    # 3. 系統設定 (Config JSON Editor)
    # -----------------------------
    def create_config_ui(self, parent_frame):
        # Create a canvas and scrollbar
        canvas = tk.Canvas(parent_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- UI for Form ---
        ttk.Label(scrollable_frame, text="雲端與 Email 設定", font=("Helvetica", 14, "bold")).pack(pady=(10, 5), padx=10, anchor="w")
        
        # Frame for entries
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill="x", padx=10, pady=5)
        
        self.config_vars = {
            "SMTP_SERVER": tk.StringVar(),
            "SMTP_PORT": tk.StringVar(),
            "EMAIL": tk.StringVar(),
            "PASSWORD": tk.StringVar(),
            "GOOGLE_SHEET_CSV_URL": tk.StringVar(),
            "GOOGLE_FORM_BASE_URL": tk.StringVar(),
            "GOOGLE_FORM_ADD_URL": tk.StringVar()
        }
        
        labels = {
            "SMTP_SERVER": "SMTP 伺服器 (預設: smtp.gmail.com)",
            "SMTP_PORT": "SMTP 通訊埠 (預設: 587)",
            "EMAIL": "Email 信箱 (發送與接收)",
            "PASSWORD": "Email 應用程式密碼",
            "GOOGLE_SHEET_CSV_URL": "Google Sheet CSV 網址",
            "GOOGLE_FORM_BASE_URL": "Google Form 基礎網址 (含 entry 參數)",
            "GOOGLE_FORM_ADD_URL": "Google Form 新增用網址 (短網址)"
        }
        
        row = 0
        for key in ["SMTP_SERVER", "SMTP_PORT", "EMAIL", "PASSWORD", "GOOGLE_SHEET_CSV_URL", "GOOGLE_FORM_BASE_URL", "GOOGLE_FORM_ADD_URL"]:
            ttk.Label(form_frame, text=labels[key] + ":").grid(row=row, column=0, sticky="w", pady=2, padx=5)
            entry = ttk.Entry(form_frame, textvariable=self.config_vars[key], width=50)
            if key == "PASSWORD":
                entry.config(show="*")
            entry.grid(row=row, column=1, sticky="w", pady=2, padx=5)
            row += 1
            
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="重新載入", command=self.refresh_config_editor).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="儲存變更", command=self.save_config_editor).pack(side="left", padx=5)
        
        # --- Tutorial ---
        ttk.Label(scrollable_frame, text="設定教學", font=("Helvetica", 14, "bold")).pack(pady=(20, 5), padx=10, anchor="w")
        
        tutorial_text = """
【Email 設定教學】
1. 若使用 Gmail，請前往 Google 帳戶設定 > 安全性。
2. 開啟「兩步驟驗證」。
3. 搜尋並進入「應用程式密碼 (App Passwords)」。
4. 建立一組新的應用程式密碼 (名稱自訂，例如 LanguageLearning)。
5. 將產生的一組 16 字元密碼 (不含空白) 貼上到上方的「Email 應用程式密碼」欄位。
6. SMTP_SERVER 維持 smtp.gmail.com，SMTP_PORT 維持 587。

【Google 雲端表單與試算表設定教學】
系統可以將單字/句子備份或同步至 Google 表單。
1. 建立 Google 表單 (Google Forms)
   - 新增一個空白表單。
   - 建立三個「簡答題」，請依序命名為：
     第1題: Type (用來放類型，如 SRS/Trans)
     第2題: Question (用來放外文/問題)
     第3題: Answer (用來放中文/答案)
   - 點擊右上角「傳送」圖示旁的選單，點選「取得預先填寫的連結 (Get pre-filled link)」。
   - 在三個題目中分別隨便填入文字 (例如 111, 222, 333)，點擊「取得連結」並複製網址。
   - 您會得到類似這樣的網址：
     https://docs.google.com/forms/d/e/.../viewform?usp=pp_url&entry.123=111&entry.456=222&entry.789=333
   - 【GOOGLE_FORM_BASE_URL】：
     將上述網址中每個 entry 後面的 `111`、`222`、`333` 刪除，並保持 `entry.XXX=` 不變。如果您只複製其中一個 entry 也沒關係，系統主要是靠它來拼湊欄位。請將這個修改後的網址填入「Google Form 基礎網址」。
     範例：https://docs.google.com/forms/d/e/.../viewform?usp=pp_url&entry.123=
   - 【GOOGLE_FORM_ADD_URL】：
     將預先填寫連結中的 `?usp=pp_url...` 全部刪除，只保留到 `viewform`。
     範例：https://docs.google.com/forms/d/e/.../viewform
     請將其填入「Google Form 新增用網址」。

2. 建立 Google 試算表 (Google Sheets)
   - 在您的 Google 表單中，點擊上方「回覆 (Responses)」標籤。
   - 點擊「連結至試算表 (Link to Sheets)」綠色圖示，建立新的試算表。
   - 開啟建立好的試算表。
   - 點擊右上角「共用 (Share)」，將權限設定為「知道連結的使用者皆可檢視」。
   - 複製試算表的網址，網址會長這樣：
     https://docs.google.com/spreadsheets/d/{試算表ID}/edit?usp=sharing
   - 【GOOGLE_SHEET_CSV_URL】：
     將網址最後的 `edit?usp=sharing` 替換為 `export?format=csv`。
     範例：https://docs.google.com/spreadsheets/d/{試算表ID}/export?format=csv
     請將這個 CSV 下載網址填入「Google Sheet CSV 網址」。
"""
        text_widget = tk.Text(scrollable_frame, wrap="word", bg=ttk.Style().lookup("TFrame", "background") or "SystemButtonFace", relief="flat", height=38)
        text_widget.pack(fill="both", expand=True, padx=20, pady=10)
        text_widget.insert(1.0, tutorial_text.strip())
        text_widget.config(state="disabled") # Make it read-only
        
        self.refresh_config_editor()
        
    def refresh_config_editor(self):
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                try:
                    config_data = json.load(f)
                    for key, var in self.config_vars.items():
                        var.set(config_data.get(key, ""))
                except Exception:
                    pass
            
    def save_config_editor(self):
        config_data = {}
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                try:
                    config_data = json.load(f)
                except Exception:
                    pass
                    
        for key, var in self.config_vars.items():
            # Handle empty ports and fallback properly, though simple assignment works for JSON strings.
            val = var.get().strip()
            if key == "SMTP_PORT" and val.isdigit():
                config_data[key] = int(val)
            else:
                config_data[key] = val
            
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", "雲端與 Email 設定已成功儲存！")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{str(e)}")

    # -----------------------------
    # 4. 軟體教學 (Tutorial)
    # -----------------------------
    def create_tutorial_ui(self, parent_frame):
        ttk.Label(parent_frame, text="多國語言學習軟體 - 快速上手指南", font=("Helvetica", 14, "bold")).pack(pady=10, anchor="center")
        
        tutorial_text = """
歡迎使用 Language Learning！這是一個結合「間隔重複 (SRS)」、「雙向翻譯」與「資源整合」的強大語言學習工具。

【核心功能介紹】
1. Dashboard (儀表板)：
   - 這裡會列出每天要看的笑話或小故事。
   - 也可以匯入您自行準備的學習資源。

2. SRS (單字間隔重複)：
   - 將不會的單字存入系統，軟體會透過演算法，在單字快遺忘時提醒您複習。
   - 成功答對則拉長複習間隔，答錯則縮短，幫助長期記憶。

3. 雙向翻譯 (Translation)：
   - 將句子記錄下來，挑戰將中文翻成外文，或是外文翻成中文。
   - 可以標記「完成(Completed)」，而系統每天也會依據設定（在學習與複習機制分頁中），隨機抽考舊句子！

【初次使用須知】
- 如果您將軟體打包成 ZIP 檔並放在全新的電腦上執行，軟體會找不到 config.json，進而觸發「新手初始化精靈」。
- 如果想把現有的設定與學習資料庫完整備份，請務必將 language_learning.db 與 config.json 妥善保存。

【AI Prompt 小助手】
- 軟體內建了向 ChatGPT 討資料的 Prompt 生成器。
- 只要在「AI 產生與匯入」中選好參數，複製 Prompt 給 ChatGPT，再將他回傳的 JSON 貼回系統即可無縫擴充題庫！
"""
        text_widget = tk.Text(parent_frame, wrap="word", bg=ttk.Style().lookup("TFrame", "background") or "SystemButtonFace", relief="flat")
        text_widget.pack(fill="both", expand=True, padx=20, pady=10)
        text_widget.insert(1.0, tutorial_text.strip())
        text_widget.config(state="disabled") # Make it read-only

    def create_about_ui(self, parent_frame):
        import update_checker
        
        # Center content
        center_frame = ttk.Frame(parent_frame)
        center_frame.pack(expand=True)
        
        ttk.Label(center_frame, text="多國語言學習系統", font=("Helvetica", 16, "bold")).pack(pady=(0, 5))
        ttk.Label(center_frame, text=f"目前版本: {update_checker.CURRENT_VERSION}", font=("Helvetica", 12)).pack(pady=(0, 20))
        
        ttk.Button(center_frame, text="檢查更新", command=lambda: update_checker.manual_check(self.app)).pack(pady=10)

    def refresh_data(self):
        pass
