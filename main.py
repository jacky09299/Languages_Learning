import tkinter as tk
from tkinter import ttk
from database import DatabaseManager
from tab_srs import SRSTab
from tab_translation import TranslationTab
from tab_dictogloss import DictoglossTab
from tab_dashboard import DashboardTab
import threading
import time
import datetime
from email_sender import send_translation_emails
from sheet_fetcher import fetch_and_sync_answers

class LanguageLearningApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("多國語言學習系統 (Language Learning System)")
        self.geometry("800x600")

        # Initialize Database
        self.db = DatabaseManager()

        # Add language selector at the top
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="目前學習語言 (Current Language):", font=("Helvetica", 10, "bold")).pack(side="left")
        
        self.current_language_var = tk.StringVar(value="English")
        self.language_cb = ttk.Combobox(top_frame, textvariable=self.current_language_var, values=["English", "Korean", "Japanese", "Spanish", "French", "German"], state="normal")
        self.language_cb.pack(side="left", padx=5)
        self.language_cb.bind("<<ComboboxSelected>>", self.on_language_change)
        self.language_cb.bind("<Return>", self.on_language_change)

        # Setup Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Add Tabs - Pass self (app) to tabs so they can access current_language
        self.srs_tab = SRSTab(self.notebook, self.db, self)
        self.translation_tab = TranslationTab(self.notebook, self.db, self)
        self.dictogloss_tab = DictoglossTab(self.notebook, self.db, self)
        self.dashboard_tab = DashboardTab(self.notebook, self.db, self)

        self.notebook.add(self.srs_tab, text="SRS 間隔重複")
        self.notebook.add(self.translation_tab, text="雙向翻譯")
        self.notebook.add(self.dictogloss_tab, text="聽寫重構")
        self.notebook.add(self.dashboard_tab, text="15/30/15 儀表板")

        # Start Background scheduler thread
        self.scheduler_running = True
        self.schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.schedule_thread.start()

    def get_current_language(self):
        return self.current_language_var.get().strip() or "English"

    def on_language_change(self, event=None):
        # Refresh all tabs data when language changes
        self.srs_tab.refresh_data()
        self.translation_tab.refresh_data()
        self.dictogloss_tab.refresh_data()
        self.dashboard_tab.refresh_data()

    def run_scheduler(self):
        last_sent_date = None
        last_sync_date = None
        last_srs_sync_hour = -1

        while self.scheduler_running:
            now = datetime.datetime.now()
            today_str = now.strftime("%Y-%m-%d")

            # Daily at 08:00 AM: Send Emails
            if now.hour == 8 and now.minute == 0 and last_sent_date != today_str:
                print("Scheduler: Sending daily translation emails at 08:00 AM...")
                try:
                    send_translation_emails(self.db)
                except Exception as e:
                    print("Error in background email task:", e)
                last_sent_date = today_str

            # Daily at 11:59 PM: Sync Answers
            if now.hour == 23 and now.minute == 59 and last_sync_date != today_str:
                print("Scheduler: Syncing daily form answers at 11:59 PM...")
                try:
                    fetch_and_sync_answers(self.db)
                except Exception as e:
                    print("Error in background sync task:", e)
                last_sync_date = today_str

            # Every 12 hours: Sync SRS
            if now.hour % 12 == 0 and now.minute == 0 and last_srs_sync_hour != now.hour:
                print("Scheduler: Syncing SRS items from Google Sheet...")
                try:
                    from sheet_fetcher import fetch_and_sync_srs_items
                    fetch_and_sync_srs_items(self.db)
                except Exception as e:
                    print("Error in background SRS sync task:", e)
                last_srs_sync_hour = now.hour

            time.sleep(30) # Check every 30 seconds

    def on_closing(self):
        self.scheduler_running = False
        self.db.close()
        self.destroy()

if __name__ == "__main__":
    app = LanguageLearningApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
