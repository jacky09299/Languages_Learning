import sqlite3
import datetime

class DatabaseManager:
    def __init__(self, db_name="language_learning.db"):
        # check_same_thread=False allows background threads (scheduler, sync, email) to use the connection
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # 1. SRS & Sentence Mining
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS srs_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                sentences TEXT,
                next_review_date DATE NOT NULL,
                interval INTEGER DEFAULT 0,
                step INTEGER DEFAULT 0
            )
        ''')

        # 2. Bidirectional Translation
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                l2_text TEXT NOT NULL,
                l1_text TEXT NOT NULL,
                created_date DATE NOT NULL,
                unlock_date DATE NOT NULL,
                status TEXT DEFAULT 'locked', -- locked, ready, completed
                l1_user_translation TEXT DEFAULT '',
                is_synced INTEGER DEFAULT 0
            )
        ''')

        # Upgrade schema if older version
        self._upgrade_schema()

        # 3. Dictogloss
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictogloss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                reconstructed_text TEXT
            )
        ''')

        # 4. Language Laddering
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS laddering_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                l2_prompt TEXT NOT NULL,
                l3_target TEXT NOT NULL,
                notes TEXT
            )
        ''')

        # 5. Dashboard Sessions & Language Rotation
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS language_rotation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                language TEXT NOT NULL,
                status TEXT NOT NULL, -- core, background
                start_date DATE NOT NULL,
                end_date DATE NOT NULL
            )
        ''')

        self.conn.commit()

    # --- SRS Methods ---
    def add_srs_item(self, word, sentences=""):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            INSERT INTO srs_items (word, sentences, next_review_date, interval, step)
            VALUES (?, ?, ?, 0, 0)
        ''', (word, sentences, today))
        self.conn.commit()

    def get_due_srs_items(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            SELECT id, word, sentences, step FROM srs_items
            WHERE next_review_date <= ?
        ''', (today,))
        return self.cursor.fetchall()

    def update_srs_item(self, item_id, success):
        # Ebbinghaus intervals in days: 1, 2, 4, 7, 15, 30, 60
        intervals = [1, 2, 4, 7, 15, 30, 60]

        self.cursor.execute('SELECT step FROM srs_items WHERE id = ?', (item_id,))
        result = self.cursor.fetchone()
        if not result: return

        current_step = result[0]

        if success:
            next_step = min(current_step + 1, len(intervals) - 1)
        else:
            next_step = max(0, current_step - 1)

        days_to_add = intervals[next_step]
        next_review_date = (datetime.date.today() + datetime.timedelta(days=days_to_add)).isoformat()

        self.cursor.execute('''
            UPDATE srs_items
            SET next_review_date = ?, interval = ?, step = ?
            WHERE id = ?
        ''', (next_review_date, days_to_add, next_step, item_id))
        self.conn.commit()

    # --- Translation Methods ---
    def add_translation(self, l2_text, l1_text, lock_days=3):
        today = datetime.date.today()
        unlock_date = (today + datetime.timedelta(days=lock_days)).isoformat()
        self.cursor.execute('''
            INSERT INTO translations (l2_text, l1_text, created_date, unlock_date, status)
            VALUES (?, ?, ?, ?, 'locked')
        ''', (l2_text, l1_text, today.isoformat(), unlock_date))
        self.conn.commit()

    def check_translation_locks(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            UPDATE translations
            SET status = 'ready'
            WHERE status = 'locked' AND unlock_date <= ?
        ''', (today,))
        self.conn.commit()

    def _upgrade_schema(self):
        self.cursor.execute("PRAGMA table_info(translations)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if "l1_user_translation" not in columns:
            self.cursor.execute("ALTER TABLE translations ADD COLUMN l1_user_translation TEXT DEFAULT ''")
        if "is_synced" not in columns:
            self.cursor.execute("ALTER TABLE translations ADD COLUMN is_synced INTEGER DEFAULT 0")
        self.conn.commit()

    def get_ready_translations(self):
        self.check_translation_locks()
        self.cursor.execute("SELECT id, l1_text, l2_text, l1_user_translation FROM translations WHERE status = 'ready'")
        return self.cursor.fetchall()

    def update_user_translation(self, translation_id, user_translation):
        self.cursor.execute('''
            UPDATE translations
            SET l1_user_translation = ?, is_synced = 1
            WHERE id = ? AND is_synced = 0
        ''', (user_translation, translation_id))
        self.conn.commit()

    def get_locked_translations(self):
        self.cursor.execute("SELECT id, l1_text, unlock_date FROM translations WHERE status = 'locked'")
        return self.cursor.fetchall()

    def complete_translation(self, translation_id):
        self.cursor.execute("UPDATE translations SET status = 'completed' WHERE id = ?", (translation_id,))
        self.conn.commit()

    # --- Dictogloss Methods ---
    def add_dictogloss(self, title, audio_path, text=""):
        self.cursor.execute('''
            INSERT INTO dictogloss (title, audio_path, reconstructed_text)
            VALUES (?, ?, ?)
        ''', (title, audio_path, text))
        self.conn.commit()

    def get_all_dictogloss(self):
        self.cursor.execute("SELECT id, title, audio_path, reconstructed_text FROM dictogloss")
        return self.cursor.fetchall()

    def update_dictogloss_text(self, item_id, text):
        self.cursor.execute("UPDATE dictogloss SET reconstructed_text = ? WHERE id = ?", (text, item_id))
        self.conn.commit()

    # --- Laddering Methods ---
    def add_laddering_card(self, l2_prompt, l3_target, notes=""):
        self.cursor.execute('''
            INSERT INTO laddering_cards (l2_prompt, l3_target, notes)
            VALUES (?, ?, ?)
        ''', (l2_prompt, l3_target, notes))
        self.conn.commit()

    def get_all_laddering_cards(self):
        self.cursor.execute("SELECT id, l2_prompt, l3_target, notes FROM laddering_cards")
        return self.cursor.fetchall()

    # --- Language Rotation Methods ---
    def add_language_rotation(self, language, status, months=3):
        start_date = datetime.date.today()
        end_date = start_date + datetime.timedelta(days=30*months)
        self.cursor.execute('''
            INSERT INTO language_rotation (language, status, start_date, end_date)
            VALUES (?, ?, ?, ?)
        ''', (language, status, start_date.isoformat(), end_date.isoformat()))
        self.conn.commit()

    def get_active_rotations(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            SELECT id, language, status, end_date FROM language_rotation
            WHERE start_date <= ? AND end_date >= ?
        ''', (today, today))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseManager(":memory:")
    print("Database manager initialized successfully.")
    db.close()
