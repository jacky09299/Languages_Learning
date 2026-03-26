import sqlite3
import os
import random

def import_english_jokes(count=100):
    source_db_path = "jokes.db"
    target_db_path = "language_learning.db"
    
    if not os.path.exists(source_db_path):
        print(f"Source database {source_db_path} not found.")
        return

    # 1. Fetch random jokes from source
    source_conn = sqlite3.connect(source_db_path)
    source_cursor = source_conn.cursor()
    
    source_cursor.execute('''
        SELECT setup, punchline FROM jokes 
        WHERE score > 10 
        ORDER BY RANDOM() LIMIT ?
    ''', (count,))
    
    jokes = source_cursor.fetchall()
    source_conn.close()
    
    print(f"Fetched {len(jokes)} random jokes from {source_db_path}.")

    # 2. Insert into target
    target_conn = sqlite3.connect(target_db_path)
    target_cursor = target_conn.cursor()
    
    inserted_count = 0
    for setup, punchline in jokes:
        content = f"{setup}\n\n{punchline}"
        target_cursor.execute('''
            INSERT INTO daily_resources (category, content, is_used, language)
            VALUES ('joke', ?, 0, 'English')
        ''', (content,))
        inserted_count += 1
        
    target_conn.commit()
    target_conn.close()
    
    print(f"Successfully imported {inserted_count} English jokes into {target_db_path}.")

if __name__ == "__main__":
    import_english_jokes(100)
