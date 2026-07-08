import os
import json
import tkinter as tk
from tkinter import ttk, messagebox

def run_initialization_wizard(root_window, db_manager):
    """
    Runs the first-time setup wizard if config.json does not exist.
    Generates config.json and allows the user to selectively inherit data from an existing language_learning.db.
    Returns True if completed successfully, False otherwise.
    """
    # Create default config.json
    default_config = {
        "google_sheets": {
            "credentials_file": "credentials.json",
            "spreadsheet_id": "",
            "srs_sheet_name": "SRS"
        },
        "email": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "receiver_email": ""
        }
    }
    try:
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Failed to create config.json: {e}")

    cursor = db_manager.cursor
    
    # Check if there are tables and any actual data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    languages = set()
    if 'srs_items' in tables:
        cursor.execute("SELECT DISTINCT target_language FROM srs_items WHERE target_language IS NOT NULL")
        languages.update([row[0] for row in cursor.fetchall() if row[0]])
    if 'translations' in tables:
        cursor.execute("SELECT DISTINCT target_language FROM translations WHERE target_language IS NOT NULL")
        languages.update([row[0] for row in cursor.fetchall() if row[0]])
    if 'daily_resources' in tables:
        cursor.execute("SELECT DISTINCT language FROM daily_resources WHERE language IS NOT NULL")
        languages.update([row[0] for row in cursor.fetchall() if row[0]])
        
    if not languages:
        # DB exists but is empty of language data (or completely fresh DB just created by DatabaseManager)
        return True
        
    # Open Wizard Window
    wizard = tk.Toplevel(root_window)
    wizard.title("初次設定與資料繼承 (First-Time Setup & Data Inheritance)")
    wizard.geometry("700x550")
    wizard.transient(root_window)
    wizard.grab_set()
    
    # Force focus
    wizard.focus_force()
    
    ttk.Label(wizard, text="歡迎！系統偵測到這是您第一次執行軟體，且發現了既有的資料庫檔案。\n請針對不同的語言，勾選您希望保留前主人的哪些資料（預設皆為不保留）：", wraplength=650, justify="left", font=("Helvetica", 11)).pack(padx=10, pady=10)

    # Frame for scrolling
    container = ttk.Frame(wizard)
    container.pack(fill="both", expand=True, padx=10, pady=5)
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    vars_dict = {}
    
    for lang in sorted(list(languages)):
        lf = ttk.LabelFrame(scrollable_frame, text=f"語言: {lang}")
        lf.pack(fill="x", padx=5, pady=5, ipadx=5, ipady=5)
        
        vars_dict[lang] = {
            "srs_content": tk.BooleanVar(value=False),
            "srs_progress": tk.BooleanVar(value=False),
            "trans_content": tk.BooleanVar(value=False),
            "trans_progress": tk.BooleanVar(value=False),
            "daily": tk.BooleanVar(value=False)
        }
        
        # SRS
        ttk.Checkbutton(lf, text="保留單字/句子 (僅內容，進度歸零)", variable=vars_dict[lang]["srs_content"]).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Checkbutton(lf, text="保留單字/句子學習進度", variable=vars_dict[lang]["srs_progress"]).grid(row=0, column=1, sticky="w", padx=5)
        
        # Translations
        ttk.Checkbutton(lf, text="保留雙向翻譯句子 (僅內容，進度歸零)", variable=vars_dict[lang]["trans_content"]).grid(row=1, column=0, sticky="w", padx=5)
        ttk.Checkbutton(lf, text="保留雙向翻譯進度", variable=vars_dict[lang]["trans_progress"]).grid(row=1, column=1, sticky="w", padx=5)
        
        # Daily resources
        ttk.Checkbutton(lf, text="保留笑話/小故事/鼓勵語 (Daily Resources)", variable=vars_dict[lang]["daily"]).grid(row=2, column=0, columnspan=2, sticky="w", padx=5)
        
        def on_srs_prog_change(l=lang):
            if vars_dict[l]["srs_progress"].get():
                vars_dict[l]["srs_content"].set(True)
        def on_srs_cont_change(l=lang):
            if not vars_dict[l]["srs_content"].get():
                vars_dict[l]["srs_progress"].set(False)
                
        def on_trans_prog_change(l=lang):
            if vars_dict[l]["trans_progress"].get():
                vars_dict[l]["trans_content"].set(True)
        def on_trans_cont_change(l=lang):
            if not vars_dict[l]["trans_content"].get():
                vars_dict[l]["trans_progress"].set(False)
                
        vars_dict[lang]["srs_progress"].trace_add("write", lambda *args, l=lang: on_srs_prog_change(l))
        vars_dict[lang]["srs_content"].trace_add("write", lambda *args, l=lang: on_srs_cont_change(l))
        vars_dict[lang]["trans_progress"].trace_add("write", lambda *args, l=lang: on_trans_prog_change(l))
        vars_dict[lang]["trans_content"].trace_add("write", lambda *args, l=lang: on_trans_cont_change(l))

    # Global options
    global_frame = ttk.LabelFrame(scrollable_frame, text="全域設定 (Global Settings)")
    global_frame.pack(fill="x", padx=5, pady=5, ipadx=5, ipady=5)
    keep_prompts = tk.BooleanVar(value=False)
    ttk.Checkbutton(global_frame, text="保留前主人的自訂 AI Prompts 範本", variable=keep_prompts).pack(anchor="w", padx=5)
    
    result_status = {"finished": False}
    
    def apply_changes():
        if messagebox.askyesno("確認", "即將清除您未勾選的資料，清除後無法復原。確定要繼續嗎？", parent=wizard):
            try:
                for lang in languages:
                    vd = vars_dict[lang]
                    
                    # SRS
                    if not vd["srs_content"].get():
                        cursor.execute("DELETE FROM srs_items WHERE target_language=?", (lang,))
                    elif not vd["srs_progress"].get():
                        cursor.execute("UPDATE srs_items SET step=0, interval=0, next_review_date=date('now') WHERE target_language=?", (lang,))
                        
                    # Translations
                    if not vd["trans_content"].get():
                        cursor.execute("DELETE FROM translations WHERE target_language=?", (lang,))
                    elif not vd["trans_progress"].get():
                        cursor.execute("UPDATE translations SET status='ready', unlock_date=date('now'), l1_user_translation='', is_synced=0 WHERE target_language=?", (lang,))
                        
                    # Daily
                    if not vd["daily"].get():
                        cursor.execute("DELETE FROM daily_resources WHERE language=?", (lang,))
                        
                # Prompts
                if 'custom_prompts' in tables and not keep_prompts.get():
                    cursor.execute("DELETE FROM custom_prompts")
                    
                db_manager.conn.commit()
                result_status["finished"] = True
                wizard.destroy()
            except Exception as e:
                messagebox.showerror("錯誤", f"清除資料時發生錯誤: {e}", parent=wizard)
                
    btn_frame = ttk.Frame(wizard)
    btn_frame.pack(pady=10)
    
    ttk.Button(btn_frame, text="套用設定並開始使用 (Apply & Start)", command=apply_changes, style="Accent.TButton").pack(side="left", padx=10)
    
    def on_close():
        if messagebox.askyesno("取消", "如果您現在離開，將不會套用設定並關閉程式。確定嗎？", parent=wizard):
            wizard.destroy()
            
    wizard.protocol("WM_DELETE_WINDOW", on_close)
    
    root_window.wait_window(wizard)
    return result_status["finished"]
