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

        ttk.Button(control_frame, text="生成 Prompt", command=self.generate_prompt).pack(side="left", padx=10)

        # Text area to show prompt
        self.prompt_text = tk.Text(prompt_frame, height=5, width=60)
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(prompt_frame, text="複製 Prompt", command=self.copy_prompt).pack(pady=5)

        # Frame for Importing AI Output
        import_frame = ttk.LabelFrame(self, text="匯入 AI 生成結果 (Import AI Output)")
        import_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(import_frame, text="請將 AI 輸出的 JSON 格式貼在下方：").pack(anchor="w", padx=5, pady=5)

        self.json_text = tk.Text(import_frame, height=10, width=60)
        self.json_text.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(import_frame, text="儲存至資料庫 (Save to Database)", command=self.save_to_database).pack(pady=10)

    def generate_prompt(self):
        lang = self.lang_var.get()
        item_type = self.type_var.get()
        quantity = self.quantity_var.get()

        if item_type == "鼓勵的話":
            description = "鼓勵的話"
            db_category = "encouragement"
        elif item_type == "笑話":
            description = "笑話"
            db_category = "joke"
        elif item_type == "小故事":
            description = "有分段的小故事"
            db_category = "joke"
        else:
            description = "內容"

        lang_desc = "繁體中文" if lang == "繁體中文" else "英文"

        prompt = (
            f"請幫我生成 {quantity} 個{lang_desc}的{description}。\n"
            "請嚴格使用以下 JSON 陣列格式輸出，不要包含任何其他文字或 markdown 標籤：\n"
            "[\n"
            '  {"content": "第一個內容"},\n'
            '  {"content": "第二個內容"}\n'
            "]\n"
        )
        if item_type == "小故事":
            prompt += "請確保故事內容有適當的分段（可使用 \\n 換行）。\n"

        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(tk.END, prompt)

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

    def refresh_data(self):
        # Required by the app architecture when language changes
        pass
