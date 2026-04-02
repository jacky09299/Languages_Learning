import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import os
import shutil
import datetime
import threading
from sheet_fetcher import fetch_and_sync_answers
from email_sender import send_translation_emails

class TranslationTab(ttk.Frame):
    def __init__(self, parent, db_manager, app):
        super().__init__(parent)
        self.db = db_manager
        self.app = app
        self.CACHE_FILE = "recently_compared.json"
        self._load_recently_compared()
        self.create_ui()
        self.load_translations()

    def _load_recently_compared(self):
        import json
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.recently_compared_ids = set(json.load(f))
            except Exception:
                self.recently_compared_ids = set()
        else:
            self.recently_compared_ids = set()

    def _save_recently_compared(self):
        import json
        try:
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(list(self.recently_compared_ids), f)
        except Exception:
            pass

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
        ttk.Button(btn_frame, text="上傳教材 PDF (Upload PDF)", command=self.upload_material_pdf).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="查看教材 (View Materials)", command=self.view_materials).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="顯示分數曲線 (Score Curve)", command=self.show_score_curve).pack(side="left", padx=5)

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
        trans_id = self.ready_trans[idx][0]
        l1_text_intermediate = self.ready_trans[idx][1]
        l2_text_original = self.ready_trans[idx][2]
        l2_text_user = self.trans_back_input.get("1.0", tk.END).strip()

        if l2_text_user:
            self.db.update_user_translation_manual(trans_id, l2_text_user)

        self.recently_compared_ids.add(trans_id)
        self._save_recently_compared()

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

    def upload_material_pdf(self):
        if not self.recently_compared_ids:
            confirm = messagebox.askyesno("提示", "你尚未在這段時間內「對比」任何句子。確定要上傳沒有關聯任何句子的教材嗎？\n(建議先對比幾句話再上傳，系統會自動將教材與剛才對比過的句子連結)")
            if not confirm:
                return

        file_path = filedialog.askopenfilename(
            title="選擇教材 PDF",
            filetypes=[("PDF Files", "*.pdf")]
        )
        if not file_path:
            return

        score = simpledialog.askinteger("輸入分數 (Score)", "請為這次對比練習輸入分數 (例如: 0~100)\n取消則預設為 0 分:", minvalue=0, maxvalue=100)
        if score is None:
             score = 0

        materials_dir = "materials"
        if not os.path.exists(materials_dir):
            os.makedirs(materials_dir)

        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H%M%S")
        safe_original_name = os.path.basename(file_path).replace(" ", "_")
        new_filename = f"{date_str}_{safe_original_name}"
        dest_path = os.path.join(materials_dir, new_filename)

        try:
            shutil.copy(file_path, dest_path)
            current_lang = self.app.get_current_language()
            count = len(self.recently_compared_ids)
            self.db.add_translation_material(new_filename, list(self.recently_compared_ids), score=score, target_language=current_lang)
            self.recently_compared_ids.clear()
            self._save_recently_compared()
            messagebox.showinfo("成功", f"教材已成功儲存並連結到剛才對比的 {count} 個句子！")
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存教材時發生錯誤: {str(e)}")

    def show_score_curve(self):
        try:
            import matplotlib.pyplot as plt
            from datetime import datetime
        except ImportError:
            messagebox.showerror("錯誤", "需要安裝 matplotlib 庫才能顯示圖表。\n請在終端機執行 pip install matplotlib")
            return
            
        current_lang = self.app.get_current_language()
        materials = self.db.get_translation_materials(target_language=current_lang)
        if not materials:
            messagebox.showinfo("提示", "目前沒有教材資料，無法繪製曲線。")
            return
            
        # Reverse to get chronological order (they are sorted DESC by ID)
        materials_chronological = list(reversed(materials))
        
        valid_materials = []
        for mat in materials_chronological:
            try:
                # mat: (id, pdf_name, created_date, translation_ids, score)
                dt = datetime.strptime(mat[2], "%Y-%m-%d %H:%M:%S")
                score = mat[4] if len(mat) > 4 and mat[4] is not None else 0
                valid_materials.append((dt, score))
            except Exception:
                pass
                
        if not valid_materials:
            messagebox.showinfo("提示", "沒有可以繪製的有效資料。")
            return
            
        first_date = valid_materials[0][0]
        
        days_list = []
        scores_list = []
        
        for dt, score in valid_materials:
            delta = dt - first_date
            # Provide decimal days or integer days? Let's use decimal days to spread same-day uploads
            days = delta.total_seconds() / (24 * 3600)
            days_list.append(days)
            scores_list.append(score)
            
        plt.figure(figsize=(8, 5))
        plt.plot(days_list, scores_list, marker='o', linestyle='-', color='b')
        plt.title(f"Score Curve ({current_lang})")
        plt.xlabel("Days since first upload (Day 0)")
        plt.ylabel("Score")
        plt.grid(True)
        plt.show()

    def view_materials(self):
        top = tk.Toplevel(self)
        top.title("查看教材 (View Materials)")
        top.geometry("800x600")

        left_frame = ttk.Frame(top)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        right_frame = ttk.Frame(top)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ttk.Label(left_frame, text="教材列表:").pack(anchor="w")
        materials_listbox = tk.Listbox(left_frame, width=40)
        materials_listbox.pack(fill="y", expand=True, pady=5)

        ttk.Label(right_frame, text="關聯的句子:").pack(anchor="w")
        sentences_text = tk.Text(right_frame, wrap="word")
        sentences_text.pack(fill="both", expand=True, pady=5)

        open_btn = ttk.Button(right_frame, text="打開此 PDF", state="disabled")
        open_btn.pack(pady=5)

        current_lang = self.app.get_current_language()
        materials = self.db.get_translation_materials(target_language=current_lang)
        
        for mat in materials:
            # mat: (id, pdf_name, created_date, translation_ids)
            materials_listbox.insert(tk.END, f"[{mat[2][:10]}] {mat[1][:25]}...")

        def on_select(event):
            selection = materials_listbox.curselection()
            if not selection: return
            idx = selection[0]
            mat = materials[idx]
            
            pdf_name = mat[1]
            translation_ids_str = mat[3]
            
            pdf_path = os.path.join("materials", pdf_name)
            if hasattr(os, 'startfile'):
                if os.path.exists(pdf_path):
                    open_btn.config(state="normal", command=lambda: os.startfile(os.path.abspath(pdf_path)))
                else:
                    open_btn.config(state="disabled")
            else:
                # Fallback for non-Windows
                if os.path.exists(pdf_path):
                    import subprocess
                    import platform
                    def open_file():
                        if platform.system() == 'Darwin':
                            subprocess.call(('open', pdf_path))
                        elif platform.system() == 'Linux':
                            subprocess.call(('xdg-open', pdf_path))
                    open_btn.config(state="normal", command=open_file)
                else:
                    open_btn.config(state="disabled")
            
            sentences_text.config(state="normal")
            sentences_text.delete("1.0", tk.END)
            
            if not translation_ids_str:
                sentences_text.insert(tk.END, "此教材沒有關聯任何句子。")
            else:
                ids_list = []
                for x in translation_ids_str.split(","):
                    try:
                        ids_list.append(int(x.strip()))
                    except ValueError:
                        pass
                
                translations = self.db.get_translations_by_ids(ids_list)
                for t in translations:
                    # t: (id, l2_text, l1_text, l1_user_translation)
                    sentences_text.insert(tk.END, f"--- ID: {t[0]} ---\n")
                    sentences_text.insert(tk.END, f"原文: {t[1]}\n")
                    sentences_text.insert(tk.END, f"提示: {t[2]}\n")
                    if t[3]:
                        sentences_text.insert(tk.END, f"我的翻譯: {t[3]}\n")
                    sentences_text.insert(tk.END, "\n")
            
            sentences_text.config(state="disabled")

        materials_listbox.bind("<<ListboxSelect>>", on_select)
