import tkinter as tk
from tkinter import ttk
import sqlite3

class DatabaseViewer(tk.Toplevel):
    def __init__(self, parent, db_manager):
        super().__init__(parent)
        self.title("Database Viewer (資料庫檢視)")
        self.geometry("900x600")
        self.db = db_manager
        
        # Notebook for different tables
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.tables = ["srs_items", "translations", "dictogloss", "language_rotation"]
        
        for table in self.tables:
            self.create_table_tab(table)
            
    def create_table_tab(self, table_name):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=table_name)
        
        # Treeview to show data
        tree = ttk.Treeview(frame, show="headings")
        
        # Scrollbars
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        
        # Refresh Button
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(column=0, row=2, columnspan=2, pady=5)
        
        ttk.Button(btn_frame, text="Refresh (重新整理)", command=lambda t=tree, n=table_name: self.load_data(t, n)).pack()
        
        self.load_data(tree, table_name)
        
    def load_data(self, tree, table_name):
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
            
        try:
            # Get columns
            self.db.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in self.db.cursor.fetchall()]
            
            tree["columns"] = columns
            for col in columns:
                tree.heading(col, text=col)
                # Adjust column width based on typical content
                if col in ["id", "interval", "step", "is_synced"]:
                    tree.column(col, minwidth=50, width=50, stretch=tk.NO)
                elif col in ["sentences", "explanation", "reconstructed_text", "l1_user_translation"]:
                    tree.column(col, minwidth=200, width=300)
                else:
                    tree.column(col, minwidth=100, width=150)
                
            # Get data
            self.db.cursor.execute(f"SELECT * FROM {table_name}")
            rows = self.db.cursor.fetchall()
            
            for row in rows:
                # Replace newlines/carriage returns and truncate long texts for Treeview display
                clean_row = []
                for cell in row:
                    if cell is None:
                        clean_row.append("")
                    else:
                        text = str(cell).replace('\n', ' ').replace('\r', '')
                        if len(text) > 500:
                            text = text[:500] + "..."
                        clean_row.append(text)
                tree.insert("", "end", values=clean_row)
                
        except sqlite3.Error as e:
            print(f"Error loading {table_name}: {e}")
