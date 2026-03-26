import sqlite3
import os
from datasets import load_dataset
from tqdm import tqdm

def import_jokes():
    db_path = "jokes.db"
    
    # Connect to the new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table with necessary columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jokes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reddit_id TEXT,
            setup TEXT,
            punchline TEXT,
            score INTEGER
        )
    """)
    conn.commit()
    
    print("Loading dataset 'SocialGrep/one-million-reddit-jokes' in streaming mode...")
    try:
        # Load the dataset using streaming to avoid memory issues
        ds = load_dataset("SocialGrep/one-million-reddit-jokes", split="train", streaming=True)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    batch_size = 5000
    batch = []
    imported_count = 0
    filtered_count = 0
    
    excluded_patterns = {"[removed]", "[deleted]"}
    
    print("Starting import and filtering process...")
    # Since it's a streaming dataset, we don't know the exact total during iteration,
    # but the dataset name says 'one-million', so we can use that as an estimate for the progress bar.
    pbar = tqdm(desc="Jokes Processed", unit=" jokes")
    
    for entry in ds:
        setup = (entry.get("title") or "").strip()
        punchline = (entry.get("selftext") or "").strip()
        reddit_id = entry.get("id", "")
        score = entry.get("score", 0)
        
        # Filter out removed, deleted, or empty jokes
        if not setup or not punchline:
            filtered_count += 1
            pbar.update(1)
            continue
            
        if setup.lower() in excluded_patterns or punchline.lower() in excluded_patterns:
            filtered_count += 1
            pbar.update(1)
            continue
            
        batch.append((reddit_id, setup, punchline, score))
        imported_count += 1
        pbar.update(1)
        
        # Batch insert for performance
        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT INTO jokes (reddit_id, setup, punchline, score) VALUES (?, ?, ?, ?)", 
                batch
            )
            conn.commit()
            batch = []
            
    # Insert any remaining jokes in the final batch
    if batch:
        cursor.executemany(
            "INSERT INTO jokes (reddit_id, setup, punchline, score) VALUES (?, ?, ?, ?)", 
            batch
        )
        conn.commit()
        
    pbar.close()
    conn.close()
    
    print("\nImport Summary:")
    print(f"Successfully imported: {imported_count} jokes")
    print(f"Filtered out: {filtered_count} (removed/deleted/empty)")
    print(f"Total processed: {imported_count + filtered_count}")
    print(f"Database saved to: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    import_jokes()
