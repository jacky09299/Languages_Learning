import tkinter as tk
from tkinter import ttk
from database import DatabaseManager
from tab_srs import SRSTab
from tab_translation import TranslationTab
from tab_dictogloss import DictoglossTab
from tab_laddering import LadderingTab
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

        # Setup Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Add Tabs
        self.notebook.add(SRSTab(self.notebook, self.db), text="SRS 間隔重複")
        self.notebook.add(TranslationTab(self.notebook, self.db), text="雙向翻譯")
        self.notebook.add(DictoglossTab(self.notebook, self.db, self), text="聽寫重構")
        self.notebook.add(LadderingTab(self.notebook, self.db), text="語言階梯法")
        self.notebook.add(DashboardTab(self.notebook, self.db), text="15/30/15 儀表板")

        # Start Background scheduler thread
        self.scheduler_running = True
        self.schedule_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.schedule_thread.start()

    def run_scheduler(self):
        last_sent_date = None
        last_sync_date = None

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

            time.sleep(30) # Check every 30 seconds

    def on_closing(self):
        self.scheduler_running = False
        self.db.close()
        self.destroy()

if __name__ == "__main__":
    app = LanguageLearningApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
