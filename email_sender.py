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

        msg = MIMEMultipart()
        msg['From'] = email_acc
        msg['To'] = email_acc
        msg['Subject'] = f"今日雙向翻譯複習 (共 {len(translations_to_send)} 題)"

        body_lines = ["今日雙向翻譯複習：\n"]
        for trans in translations_to_send:
            trans_id = trans[0]
            l1_text = trans[1]
            form_url = f"{form_base_url}{trans_id}"

            body_lines.append(f"{l1_text}")
            body_lines.append(f"{form_url}\n")

        body = "\n".join(body_lines)
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server.send_message(msg)
        print("已成功發送合併的複習 Email。")

        server.quit()

    except Exception as e:
        print(f"發送 Email 時發生錯誤 (Error sending email): {e}")

def send_addition_reminder(db_manager):
    config = load_config()
    smtp_server = config.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = config.get("SMTP_PORT", 587)
    email_acc = config.get("EMAIL", "")
    password = config.get("PASSWORD", "")
    form_url = config.get("GOOGLE_FORM_ADD_URL", "https://docs.google.com/forms/d/YOUR_FORM_ID/viewform")

    if not email_acc or not password or email_acc == "dummy_account@gmail.com":
        print("未設定有效的 Email 或密碼，跳過發信 (Email/Password not configured).")
        return

    joke = db_manager.get_unused_resource("joke")
    encouragement = db_manager.get_unused_resource("encouragement")

    if not joke and not encouragement:
        print("資料庫中沒有可用的笑話或鼓勵的話，不發送提醒。")
        return

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_acc, password)

        msg = MIMEMultipart()
        msg['From'] = email_acc
        msg['To'] = email_acc
        msg['Subject'] = "今日目標：新增 10 個語言學習題目！"

        body = (
            f"早安！今天也是學習的好日子。\n\n"
            f"記得新增 10 個新的雙向翻譯題目喔！\n"
            f"表單連結：{form_url}\n\n"
            f"--- 今天的鼓勵 ---\n"
            f"{encouragement if encouragement else '加油！'}\n\n"
            f"--- 休息一下，聽個小故事 ---\n"
            f"{joke if joke else '今天沒有故事，快去讀書吧！'}\n\n"
            f"祝您今天學習愉快！"
        )

        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        server.send_message(msg)
        print("已發送每日新增題目提醒 Email。")

        server.quit()
    except Exception as e:
        print(f"發送提醒 Email 時發生錯誤: {e}")

if __name__ == "__main__":
    from database import DatabaseManager
    db = DatabaseManager(":memory:")
    # Create test data
    db.add_translation("Hello", "你好", lock_days=0)
    send_translation_emails(db)
