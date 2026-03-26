import sqlite3
import os
import random

def transfer_100_stories():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_db_path = os.path.join(base_dir, 'story.db')
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
    
    # 1. Randomly select 100 stories
    print("Selecting 100 random stories from story.db...")
    source_cursor.execute("SELECT storyid, storytitle, sentence1, sentence2, sentence3, sentence4, sentence5 FROM stories ORDER BY RANDOM() LIMIT 100;")
    selected_stories = source_cursor.fetchall()
    
    if not selected_stories:
        print("No stories found in source database.")
        source_conn.close()
        target_conn.close()
        return

    print(f"Transferring {len(selected_stories)} stories...")
    
    ids_to_delete = []
    
    for story in selected_stories:
        storyid, title, s1, s2, s3, s4, s5 = story
        
        # 2. Format the content
        content = f"{title}\n{s1}\n{s2}\n{s3}\n{s4}\n{s5}"
        
        # 3. Insert into language_learning.db
        target_cursor.execute('''
            INSERT INTO daily_resources (category, content, is_used, language)
            VALUES (?, ?, ?, ?)
        ''', ('joke', content, 0, 'English'))
        
        ids_to_delete.append((storyid,))
        
    # 4. Delete from story.db
    print(f"Deleting 100 stories from story.db...")
    source_cursor.executemany("DELETE FROM stories WHERE storyid = ?;", ids_to_delete)
    
    source_conn.commit()
    target_conn.commit()
    
    print(f"Successfully transferred and deleted {len(selected_stories)} stories.")
    
    source_conn.close()
    target_conn.close()

if __name__ == "__main__":
    transfer_100_stories()
