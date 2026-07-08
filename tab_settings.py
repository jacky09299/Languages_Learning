import tkinter as tk
from tkinter import ttk, messagebox
import json

class SettingsTab(ttk.Frame):
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db = db_manager
        self.app = app
        self.create_ui()

    def create_ui(self):
        # Frame for Prompt Generation
        prompt_frame = ttk.LabelFrame(self, text="AI Prompt 生成器 (Prompt Generator)")
        prompt_frame.pack(fill="x", padx=10, pady=10)

        # Controls for generating prompt
        control_frame = ttk.Frame(prompt_frame)
        control_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(control_frame, text="語言 (Language):").pack(side="left", padx=5)
        self.lang_var = tk.StringVar(value="繁體中文")
        ttk.Combobox(control_frame, textvariable=self.lang_var, values=["繁體中文", "英文"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Label(control_frame, text="類型 (Type):").pack(side="left", padx=5)
        self.type_var = tk.StringVar(value="鼓勵的話")
        ttk.Combobox(control_frame, textvariable=self.type_var, values=["鼓勵的話", "笑話", "小故事"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Label(control_frame, text="數量 (Quantity):").pack(side="left", padx=5)
        self.quantity_var = tk.IntVar(value=5)
        ttk.Entry(control_frame, textvariable=self.quantity_var, width=5).pack(side="left", padx=5)

        ttk.Label(control_frame, text="格式 (Format):").pack(side="left", padx=5)
        self.format_var = tk.StringVar(value="JSON")
        ttk.Combobox(control_frame, textvariable=self.format_var, values=["JSON", "SQLite DB"], state="readonly", width=10).pack(side="left", padx=5)

        ttk.Button(control_frame, text="生成 Prompt", command=self.generate_prompt).pack(side="left", padx=10)

        # Custom preferences
        pref_frame = ttk.Frame(prompt_frame)
        pref_frame.pack(fill="x", padx=5, pady=5)
        ttk.Label(pref_frame, text="自訂偏好 (例如：要幽默、要黑暗幽默、主角是貓):").pack(side="left", padx=5)
        self.pref_var = tk.StringVar()
        ttk.Entry(pref_frame, textvariable=self.pref_var, width=50).pack(side="left", padx=5)

        # Text area to show prompt
        self.prompt_text = tk.Text(prompt_frame, height=8, width=60)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        btn_frame = ttk.Frame(prompt_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="複製 Prompt", command=self.copy_prompt).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="編輯目前範本", command=self.open_template_editor).pack(side="left", padx=5)

        # Frame for Importing AI Output
        import_frame = ttk.LabelFrame(self, text="匯入 AI 生成結果 (Import AI Output)")
        import_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(import_frame, text="請將 AI 輸出的 JSON 格式貼在下方：").pack(anchor="w", padx=5, pady=5)

        self.json_text = tk.Text(import_frame, height=10, width=60)
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(import_frame, text="儲存至資料庫 (Save to Database)", command=self.save_to_database).pack(pady=10)

        # Frame for Importing Database
        db_import_frame = ttk.LabelFrame(self, text="匯入外部資料庫 (Import SQLite DB)")
        db_import_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(db_import_frame, text="支援匯入您的 jokes.db (笑話) 或 story.db (小故事) 格式").pack(anchor="w", padx=5, pady=5)
        
        db_control_frame = ttk.Frame(db_import_frame)
        db_control_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(db_control_frame, text="選擇並匯入 DB 檔...", command=self.import_db_file).pack(side="left", padx=5)

    def get_default_template(self, key):
        if key == "JSON":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "請嚴格使用以下 JSON 陣列格式輸出，不要包含任何其他文字或 markdown 標籤：\n"
                "[\n"
                '  {{"content": "第一個內容"}},\n'
                '  {{"content": "第二個內容"}}\n'
                "]\n"
                "{extra}"
            )
        elif key == "DB_story":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "我需要你將生成的內容存入 SQLite 資料庫中。\n"
                "請建立一個名為 story.db 的 SQLite 資料庫檔案。\n"
                "其中必須包含一個名為 stories 的資料表，欄位格式為：(storyid INTEGER PRIMARY KEY, storytitle TEXT, sentence1 TEXT, sentence2 TEXT, sentence3 TEXT, sentence4 TEXT, sentence5 TEXT)。\n"
                "請將生成的資料寫入這個資料庫中。\n"
                "如果你具備 Python 程式執行環境 (例如 ChatGPT 的 Data Analysis)，請直接執行程式碼，並在對話中提供這個 .db 檔案的下載連結給我。\n"
                "否則，請給我一段完整的 Python 程式碼，讓我可以直接複製到自己的電腦上執行來產生這個 .db 檔案。\n"
            )
        elif key == "DB_joke":
            return (
                "請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
                "{pref_text}\n"
                "我需要你將生成的內容存入 SQLite 資料庫中。\n"
                "請建立一個名為 jokes.db 的 SQLite 資料庫檔案。\n"
                "其中必須包含一個名為 jokes 的資料表，欄位格式為：(id INTEGER PRIMARY KEY, setup TEXT, punchline TEXT)。如果內容不是笑話，也可將其拆分為兩段填入 setup 和 punchline 中。\n"
                "請將生成的資料寫入這個資料庫中。\n"
                "如果你具備 Python 程式執行環境 (例如 ChatGPT 的 Data Analysis)，請直接執行程式碼，並在對話中提供這個 .db 檔案的下載連結給我。\n"
                "否則，請給我一段完整的 Python 程式碼，讓我可以直接複製到自己的電腦上執行來產生這個 .db 檔案。\n"
            )
        return ""

    def generate_prompt(self):
        lang = self.lang_var.get()
        item_type = self.type_var.get()
        quantity = self.quantity_var.get()
        output_format = self.format_var.get()
        custom_pref = self.pref_var.get().strip()
        
        if output_format == "JSON": prompt_key = "JSON"
        elif item_type == "小故事": prompt_key = "DB_story"
        else: prompt_key = "DB_joke"

        if item_type == "鼓勵的話": description = "鼓勵的話"
        elif item_type == "笑話": description = "笑話"
        elif item_type == "小故事": description = "有分段的小故事"
        else: description = "內容"

        lang_desc = "繁體中文" if lang == "繁體中文" else "英文"
        
        pref_text = ""
        if custom_pref:
            pref_text = f"【內容偏好與限制】：{custom_pref} (請確保內容符合此偏好，但不影響最終的輸出格式要求)。\n"
            
        extra = ""
        if output_format == "JSON" and item_type == "小故事":
            extra = "請確保故事內容有適當的分段（可使用 \\n 換行）。\n"
            
        template = self.db.get_prompt(prompt_key)
        if not template:
            template = self.get_default_template(prompt_key)
            
        try:
            prompt = template.format(
                quantity=quantity,
                lang_desc=lang_desc,
                description=description,
                pref_text=pref_text,
                extra=extra
            )
        except Exception as e:
            messagebox.showerror("範本錯誤", f"自訂範本變數格式有誤：\n{str(e)}\n請檢查是否使用了正確的括號 {{}}，或點擊「編輯目前範本」還原預設值。")
            return

        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, prompt)

    def open_template_editor(self):
        output_format = self.format_var.get()
        item_type = self.type_var.get()
        if output_format == "JSON": prompt_key = "JSON"
        elif item_type == "小故事": prompt_key = "DB_story"
        else: prompt_key = "DB_joke"
        
        template = self.db.get_prompt(prompt_key)
        if not template:
            template = self.get_default_template(prompt_key)
            
        editor = tk.Toplevel(self)
        editor.title(f"編輯範本 - {prompt_key}")
        editor.geometry("700x500")
        
        info_text = (
            "可用變數 (請保留大括號 {}):\n"
            "{quantity} = 數量\n"
            "{lang_desc} = 語言 (如英文)\n"
            "{description} = 類型 (如笑話)\n"
            "{pref_text} = 自訂偏好區塊\n"
            "{extra} = 額外說明 (例如要求小故事分段)"
        )
        ttk.Label(editor, text=info_text, justify="left").pack(pady=5, padx=10, anchor="w")
        
        text_area = tk.Text(editor, wrap="word", height=20)
        text_area.pack(fill="both", expand=True, padx=10, pady=5)
        text_area.insert("1.0", template)
        
        btn_frame = ttk.Frame(editor)
        btn_frame.pack(pady=10)
        
        def save():
            new_template = text_area.get("1.0", tk.END).strip()
            self.db.save_prompt(prompt_key, new_template)
            messagebox.showinfo("成功", "已儲存自訂範本！")
            editor.destroy()
            self.generate_prompt()
            
        def reset():
            if messagebox.askyesno("確認", "確定要還原成預設範本嗎？(此動作無法復原)"):
                self.db.delete_prompt(prompt_key)
                text_area.delete("1.0", tk.END)
                text_area.insert("1.0", self.get_default_template(prompt_key))
                messagebox.showinfo("成功", "已還原預設範本！")
                self.generate_prompt()
                
        ttk.Button(btn_frame, text="儲存 (Save)", command=save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="還原預設 (Reset)", command=reset).pack(side="left", padx=5)

    def copy_prompt(self):
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if prompt:
            self.clipboard_clear()
            self.clipboard_append(prompt)
            messagebox.showinfo("成功", "Prompt 已複製到剪貼簿！")
        else:
            messagebox.showwarning("警告", "沒有可複製的 Prompt")

    def save_to_database(self):
        json_str = self.json_text.get(1.0, tk.END).strip()
        if not json_str:
            messagebox.showwarning("警告", "請貼上 JSON 內容")
            return

        try:
            # Try to parse the JSON
            data = json.loads(json_str)
            if not isinstance(data, list):
                raise ValueError("JSON 最外層必須是陣列 (Array)")

            # Determine correct db_category and language
            lang = "Chinese" if self.lang_var.get() == "繁體中文" else "English"
            item_type = self.type_var.get()
            db_category = "encouragement" if item_type == "鼓勵的話" else "joke"

            count = 0
            for item in data:
                if "content" in item and item["content"].strip():
                    self.db.add_daily_resource(category=db_category, content=item["content"].strip(), language=lang)
                    count += 1

            messagebox.showinfo("成功", f"成功匯入 {count} 筆資料至 {lang} 的 {item_type} ({db_category}) 中！")
            self.json_text.delete(1.0, tk.END)

        except json.JSONDecodeError:
            messagebox.showerror("錯誤", "無法解析 JSON，請確認 AI 的輸出格式正確，且沒有包含額外的文字。")
        except Exception as e:
            messagebox.showerror("錯誤", f"發生錯誤：{str(e)}")

    def import_db_file(self):
        from tkinter import filedialog
        import sqlite3
        import os

        filepath = filedialog.askopenfilename(filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")])
        if not filepath:
            return

        try:
            conn = sqlite3.connect(filepath)
            cursor = conn.cursor()
            
            # Check what tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            count = 0
            # Import jokes
            if "jokes" in tables:
                cursor.execute("SELECT id, setup, punchline FROM jokes")
                jokes = cursor.fetchall()
                for j in jokes:
                    content = f"{j[1]}\n\n{j[2]}"
                    self.db.add_daily_resource(category="joke", content=content, language="English")
                    count += 1
            
            # Import stories
            if "stories" in tables:
                cursor.execute("SELECT storyid, storytitle, sentence1, sentence2, sentence3, sentence4, sentence5 FROM stories")
                stories = cursor.fetchall()
                for s in stories:
                    content = f"{s[1]}\n{s[2]}\n{s[3]}\n{s[4]}\n{s[5]}"
                    self.db.add_daily_resource(category="joke", content=content, language="English")
                    count += 1
                    
            if count == 0:
                messagebox.showwarning("警告", "找不到支援的資料表 (jokes 或 stories)，或資料表為空。")
            else:
                messagebox.showinfo("成功", f"成功從資料庫匯入 {count} 筆資料至 English 的 joke 分類中！")
                
            conn.close()
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入失敗：{str(e)}")

    def refresh_data(self):
        # Required by the app architecture when language changes
        pass
