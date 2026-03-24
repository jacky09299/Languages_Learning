import tkinter as tk
from tkinter import ttk
from database import DatabaseManager
from tab_srs import SRSTab
from tab_translation import TranslationTab
from tab_dictogloss import DictoglossTab
from tab_laddering import LadderingTab
from tab_dashboard import DashboardTab

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

    def on_closing(self):
        self.db.close()
        self.destroy()

if __name__ == "__main__":
    app = LanguageLearningApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
