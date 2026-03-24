import urllib.request
import csv
import io
import json
import os

def load_config(config_path="config.json"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def fetch_and_sync_answers(db_manager):
    config = load_config()
    csv_url = config.get("GOOGLE_SHEET_CSV_URL", "")

    if not csv_url:
        print("未設定有效的 Google Sheet CSV URL (CSV URL not configured).")
        return False

    try:
        response = urllib.request.urlopen(csv_url)
        content = response.read().decode('utf-8')

        # Read CSV
        csv_reader = csv.reader(io.StringIO(content))
        header = next(csv_reader, None)

        if not header:
            print("CSV 檔案為空 (CSV file is empty).")
            return False

        # Find indexes. Header should contain 'Question_id' and '翻譯回原文' or similar based on columns.
        # Let's dynamically find based on some keywords or just assume specific columns if it's simpler.
        # Typically Google Form CSV headers: Timestamp, Question_id, 翻譯回原文
        q_id_idx = -1
        ans_idx = -1

        for i, col_name in enumerate(header):
            if "Question_id" in col_name or "question" in col_name.lower():
                q_id_idx = i
            elif "翻譯" in col_name or "answer" in col_name.lower() or "原文" in col_name:
                ans_idx = i

        # Fallback if names are different
        if q_id_idx == -1 and len(header) >= 2:
            q_id_idx = 1
        if ans_idx == -1 and len(header) >= 3:
            ans_idx = 2

        if q_id_idx == -1 or ans_idx == -1:
            print("找不到對應的欄位標題 (Cannot find matching column headers in CSV).")
            return False

        synced_count = 0
        for row in csv_reader:
            if len(row) > max(q_id_idx, ans_idx):
                q_id_str = row[q_id_idx].strip()
                answer = row[ans_idx].strip()

                if q_id_str.isdigit() and answer:
                    q_id = int(q_id_str)
                    # Update database (will only update if is_synced=0)
                    db_manager.update_user_translation(q_id, answer)
                    synced_count += 1

        print(f"成功同步了 {synced_count} 筆回答 (Successfully synced {synced_count} answers).")
        return True

    except Exception as e:
        print(f"同步表單回答時發生錯誤 (Error syncing form answers): {e}")
        return False

if __name__ == "__main__":
    from database import DatabaseManager
    db = DatabaseManager(":memory:")
    # Create test data
    db.add_translation("Test L2", "Test L1", lock_days=0)
    db.check_translation_locks()
    fetch_and_sync_answers(db)
