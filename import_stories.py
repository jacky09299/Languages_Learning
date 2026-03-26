import sqlite3
import csv
import os

def import_csv_to_sqlite(csv_path, db_path, table_name, source_name):
    """Imports a specific CSV file into the SQLite table."""
    if not os.path.exists(csv_path):
        print(f"File {csv_path} not found.")
        return

    print(f"Importing {csv_path} as source '{source_name}'...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            # storyid,storytitle,sentence1,sentence2,sentence3,sentence4,sentence5
            data.append((
                row.get('storyid'),
                row.get('storytitle'),
                row.get('sentence1'),
                row.get('sentence2'),
                row.get('sentence3'),
                row.get('sentence4'),
                row.get('sentence5'),
                source_name
            ))
            
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            storyid TEXT PRIMARY KEY,
            storytitle TEXT,
            sentence1 TEXT,
            sentence2 TEXT,
            sentence3 TEXT,
            sentence4 TEXT,
            sentence5 TEXT,
            source TEXT
        )
    ''')
    
    # Insert data
    cursor.executemany(f'''
        INSERT OR IGNORE INTO {table_name} (storyid, storytitle, sentence1, sentence2, sentence3, sentence4, sentence5, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    conn.commit()
    print(f"Successfully imported {len(data)} rows from {source_name}.")
    conn.close()

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    story_dir = os.path.join(base_dir, 'story')
    db_path = os.path.join(base_dir, 'story.db')
    table_name = 'stories'
    
    # List of (filename, source_label)
    files_to_import = [
        ('ROCStories_test.csv', 'test'),
        ('ROCStories_train.csv', 'train'),
        ('ROCStories_val.csv', 'val')
    ]
    
    for filename, source in files_to_import:
        csv_path = os.path.join(story_dir, filename)
        import_csv_to_sqlite(csv_path, db_path, table_name, source)

if __name__ == "__main__":
    main()
