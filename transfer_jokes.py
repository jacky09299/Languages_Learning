import sqlite3
import os

def transfer_100_jokes():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_db_path = os.path.join(base_dir, 'jokes.db')
    target_db_path = os.path.join(base_dir, 'language_learning.db')
    
    if not os.path.exists(source_db_path):
        print(f"Source database {source_db_path} not found.")
        return
    if not os.path.exists(target_db_path):
        print(f"Target database {target_db_path} not found.")
        return

    source_conn = sqlite3.connect(source_db_path)
    target_conn = sqlite3.connect(target_db_path)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    # 1. Select the 100 highest scoring jokes
    print("Selecting 100 highest scoring jokes from jokes.db...")
    source_cursor.execute("SELECT id, setup, punchline, score FROM jokes ORDER BY score DESC LIMIT 100;")
    selected_jokes = source_cursor.fetchall()
    
    if not selected_jokes:
        print("No jokes found in source database.")
        source_conn.close()
        target_conn.close()
        return

    print(f"Transferring {len(selected_jokes)} jokes...")
    
    ids_to_delete = []
    
    for joke in selected_jokes:
        joke_id, setup, punchline, score = joke
        
        # 2. Format the content
        content = f"{setup}\n\n{punchline}"
        
        # 3. Insert into language_learning.db
        target_cursor.execute('''
            INSERT INTO daily_resources (category, content, is_used, language)
            VALUES (?, ?, ?, ?)
        ''', ('joke', content, 0, 'English'))
        
        ids_to_delete.append((joke_id,))
        
    # 4. Delete from jokes.db
    print(f"Deleting 100 jokes from jokes.db...")
    source_cursor.executemany("DELETE FROM jokes WHERE id = ?;", ids_to_delete)
    
    source_conn.commit()
    target_conn.commit()
    
    print(f"Successfully transferred and deleted {len(selected_jokes)} jokes.")
    
    source_conn.close()
    target_conn.close()

if __name__ == "__main__":
    transfer_100_jokes()
