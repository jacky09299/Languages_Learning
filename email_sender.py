import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

def load_config(config_path="config.json"):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def send_translation_emails(db_manager):
    config = load_config()
    smtp_server = config.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = config.get("SMTP_PORT", 587)
    email_acc = config.get("EMAIL", "")
    password = config.get("PASSWORD", "")
    form_base_url = config.get("GOOGLE_FORM_BASE_URL", "")

    if not email_acc or not password or email_acc == "dummy_account@gmail.com":
        print("未設定有效的 Email 或密碼，跳過發信 (Email/Password not configured).")
        return

    ready_translations = db_manager.get_ready_translations()
    if not ready_translations:
        print("沒有待複習的翻譯項目 (No ready translations to send).")
        return

    # Check if we need to send any emails before connecting to SMTP
    translations_to_send = [t for t in ready_translations if not t[3] or not t[3].strip()]
    if not translations_to_send:
        print("所有待複習翻譯皆已回答過，不需再發信 (All ready translations already answered).")
        return

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_acc, password)

        for trans in translations_to_send:
            # trans is (id, l1_text, l2_text, l1_user_translation)
            trans_id = trans[0]
            l1_text = trans[1]

            form_url = f"{form_base_url}{trans_id}"

            msg = MIMEMultipart()
            msg['From'] = email_acc
            msg['To'] = email_acc
            msg['Subject'] = f"翻譯複習題 #{trans_id}"

            body = f"""
今日雙向翻譯複習：

請將以下母語翻回外語：
{l1_text}

請點擊下方連結作答（已自動帶入 Question_id）：
{form_url}
"""
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            server.send_message(msg)
            print(f"已發送 Email 給項目 ID: {trans_id}")

        server.quit()
        print("所有待複習翻譯已發送完畢。")

    except Exception as e:
        print(f"發送 Email 時發生錯誤 (Error sending email): {e}")

if __name__ == "__main__":
    from database import DatabaseManager
    db = DatabaseManager(":memory:")
    # Create test data
    db.add_translation("Hello", "你好", lock_days=0)
    send_translation_emails(db)
