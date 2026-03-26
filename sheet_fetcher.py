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

def fetch_and_sync_answers(db_manager, default_lang="English"):
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

        # Find indexes
        q_id_idx = -1
        orig_idx = -1
        trans_idx = -1
        lang_idx = -1

        for i, col_name in enumerate(header):
            col_lower = col_name.lower()
            if "question_id" in col_lower or "題目編號" in col_name:
                q_id_idx = i
            elif "原文" in col_name or "original" in col_lower:
                orig_idx = i
            elif "翻譯" in col_name or "translation" in col_lower:
                trans_idx = i
            elif "語言" in col_name or "language" in col_lower:
                lang_idx = i

        # Fallback if names are different
        if q_id_idx == -1 and len(header) >= 1: q_id_idx = 0
        if orig_idx == -1 and len(header) >= 2: orig_idx = 1
        if trans_idx == -1 and len(header) >= 3: trans_idx = 2

        if q_id_idx == -1 or orig_idx == -1:
            print("找不到對應的欄位標題 (Cannot find matching column headers in CSV).")
            return False

        synced_count = 0
        new_task_count = 0
        
        lang_map = {
            "英文": "English", "韓文": "Korean", "日文": "Japanese",
            "德文": "German", "泰文": "Thai", "西班牙文": "Spanish"
        }

        for row in csv_reader:
            if len(row) <= max(q_id_idx, orig_idx):
                continue
                
            q_id_str = row[q_id_idx].strip() if q_id_idx < len(row) else ""
            original_text = row[orig_idx].strip() if orig_idx < len(row) else ""
            translation_text = row[trans_idx].strip() if trans_idx != -1 and trans_idx < len(row) else ""
            
            # Determine language
            row_lang = default_lang
            if lang_idx != -1 and lang_idx < len(row):
                lang_val = row[lang_idx].strip()
                row_lang = lang_map.get(lang_val, lang_val if lang_val else default_lang)

            # Scenario A: Back-translation answer (Matching existing ID)
            if q_id_str.isdigit() and int(q_id_str) > 0:
                q_id = int(q_id_str)
                # Only update if it's an answer (translation_text is typically empty for answers in this flow)
                if original_text and not translation_text:
                    db_manager.update_user_translation(q_id, original_text)
                    synced_count += 1
            
            # Scenario B: New translation task (Both Original and Translation present)
            elif original_text and translation_text:
                if not db_manager.translation_exists(original_text, translation_text, row_lang):
                    # Form items are always locked for 3 days as per user request
                    db_manager.add_translation(original_text, translation_text, lock_days=3, target_language=row_lang)
                    new_task_count += 1

        print(f"同步完成：解鎖了 {synced_count} 筆回答，新增了 {new_task_count} 筆翻譯任務。")
        return True

    except Exception as e:
        print(f"同步表單回答時發生錯誤 (Error syncing form answers): {e}")
        return False

def fetch_and_sync_srs_items(db_manager):
    config = load_config()
    # Default URL if not provided in config
    csv_url = config.get("GOOGLE_SHEET_SRS_URL", "https://docs.google.com/spreadsheets/d/1MXLBfBRtEDMYDUO3DHlYeG2VTPzySuEyS9U2NOce8dI/export?format=csv")

    try:
        response = urllib.request.urlopen(csv_url)
        content = response.read().decode('utf-8')

        csv_reader = csv.reader(io.StringIO(content))
        header = next(csv_reader, None)
        if not header:
            print("SRS CSV 檔案為空 (SRS CSV file is empty).")
            return 0

        lang_map = {
            "英文": "English",
            "韓文": "Korean",
            "日文": "Japanese",
            "德文": "German",
            "泰文": "Thai",
            "西班牙文": "Spanish"
        }

        lang_idx, word_idx, sent_idx, expl_idx = -1, -1, -1, -1
        for i, col in enumerate(header):
            col = col.strip()
            if "語言" in col: lang_idx = i
            elif "單字" in col: word_idx = i
            elif "句子" in col: sent_idx = i
            elif "解釋" in col: expl_idx = i

        if -1 in [lang_idx, word_idx]:
            print("找不到必要的欄位 (Missing required columns in SRS CSV).")
            return 0

        synced_count = 0
        for row in csv_reader:
            if len(row) > max(lang_idx, word_idx, sent_idx, expl_idx):
                lang_zh = row[lang_idx].strip()
                word = row[word_idx].strip()
                sentences = row[sent_idx].strip() if sent_idx != -1 else ""
                explanation = row[expl_idx].strip() if expl_idx != -1 else ""

                if not word and not sentences:
                    continue

                target_lang = lang_map.get(lang_zh, "English")

                # Check if exact item exists
                if not db_manager.srs_item_exists(word, sentences, explanation, target_lang):
                    db_manager.add_srs_item(word, sentences, explanation, target_lang)
                    synced_count += 1
                    
        print(f"成功同步了 {synced_count} 筆 SRS 項目 (Successfully synced {synced_count} SRS items).")
        return synced_count

    except Exception as e:
        print(f"同步 SRS 表單時發生錯誤 (Error syncing SRS form): {e}")
        return 0

if __name__ == "__main__":
    from database import DatabaseManager
    db = DatabaseManager(":memory:")
    # Create test data
    db.add_translation("Test L2", "Test L1", lock_days=0)
    db.check_translation_locks()
    fetch_and_sync_answers(db)
