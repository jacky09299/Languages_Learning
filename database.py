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
                step INTEGER DEFAULT 0,
                target_language TEXT DEFAULT 'English',
                explanation TEXT DEFAULT ''
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
                is_synced INTEGER DEFAULT 0,
                target_language TEXT DEFAULT 'English'
            )
        ''')

        # 3. Dictogloss
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dictogloss (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                audio_path TEXT NOT NULL,
                reconstructed_text TEXT,
                target_language TEXT DEFAULT 'English'
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

        # 6. Daily Resources (Jokes/Stories & Encouragements)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, -- joke, encouragement
                content TEXT NOT NULL,
                is_used INTEGER DEFAULT 0,
                language TEXT DEFAULT 'Chinese'
            )
        ''')

        # Upgrade schema if older version
        self._upgrade_schema()

        self.conn.commit()

    # --- SRS Methods ---
    def add_srs_item(self, word, sentences="", explanation="", target_language="English"):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            INSERT INTO srs_items (word, sentences, explanation, next_review_date, interval, step, target_language)
            VALUES (?, ?, ?, ?, 0, 0, ?)
        ''', (word, sentences, explanation, today, target_language))
        self.conn.commit()

    def srs_item_exists(self, word, sentences, explanation, target_language):
        self.cursor.execute('''
            SELECT 1 FROM srs_items 
            WHERE word = ? AND sentences = ? AND explanation = ? AND target_language = ?
        ''', (word, sentences, explanation, target_language))
        return self.cursor.fetchone() is not None

    def get_due_srs_items(self, target_language="English"):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            SELECT id, word, sentences, explanation, step FROM srs_items
            WHERE next_review_date <= ? AND target_language = ?
        ''', (today, target_language))
        return self.cursor.fetchall()

    def delete_srs_item(self, item_id):
        self.cursor.execute("DELETE FROM srs_items WHERE id = ?", (item_id,))
        self.conn.commit()

    def update_srs_explanation(self, item_id, explanation):
        self.cursor.execute("UPDATE srs_items SET explanation = ? WHERE id = ?", (explanation, item_id))
        self.conn.commit()

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
    def add_translation(self, l2_text, l1_text, lock_days=3, target_language="English"):
        today = datetime.date.today()
        unlock_date = (today + datetime.timedelta(days=lock_days)).isoformat()
        self.cursor.execute('''
            INSERT INTO translations (l2_text, l1_text, created_date, unlock_date, status, target_language)
            VALUES (?, ?, ?, ?, 'locked', ?)
        ''', (l2_text, l1_text, today.isoformat(), unlock_date, target_language))
        self.conn.commit()

    def translation_exists(self, l2_text, l1_text, target_language="English"):
        self.cursor.execute('''
            SELECT 1 FROM translations 
            WHERE l2_text = ? AND l1_text = ? AND target_language = ?
        ''', (l2_text, l1_text, target_language))
        return self.cursor.fetchone() is not None

    def check_translation_locks(self):
        today = datetime.date.today().isoformat()
        self.cursor.execute('''
            UPDATE translations
            SET status = 'ready'
            WHERE status = 'locked' AND unlock_date <= ?
        ''', (today,))
        self.conn.commit()

    def _upgrade_schema(self):
        # Translations
        self.cursor.execute("PRAGMA table_info(translations)")
        columns = [info[1] for info in self.cursor.fetchall()]
        if "l1_user_translation" not in columns:
            self.cursor.execute("ALTER TABLE translations ADD COLUMN l1_user_translation TEXT DEFAULT ''")
        if "is_synced" not in columns:
            self.cursor.execute("ALTER TABLE translations ADD COLUMN is_synced INTEGER DEFAULT 0")
        if "target_language" not in columns:
            self.cursor.execute("ALTER TABLE translations ADD COLUMN target_language TEXT DEFAULT 'English'")
            
        # SRS Items
        self.cursor.execute("PRAGMA table_info(srs_items)")
        srs_cols = [info[1] for info in self.cursor.fetchall()]
        if "target_language" not in srs_cols:
            self.cursor.execute("ALTER TABLE srs_items ADD COLUMN target_language TEXT DEFAULT 'English'")
        if "explanation" not in srs_cols:
            self.cursor.execute("ALTER TABLE srs_items ADD COLUMN explanation TEXT DEFAULT ''")

        # Dictogloss
        self.cursor.execute("PRAGMA table_info(dictogloss)")
        dicto_cols = [info[1] for info in self.cursor.fetchall()]
        if "target_language" not in dicto_cols:
            self.cursor.execute("ALTER TABLE dictogloss ADD COLUMN target_language TEXT DEFAULT 'English'")
            
        # Migrate Laddering Cards to SRS
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='laddering_cards'")
        if self.cursor.fetchone():
            self.cursor.execute("SELECT l2_prompt, l3_target, notes, target_language FROM laddering_cards")
            old_cards = self.cursor.fetchall()
            today = datetime.date.today().isoformat()
            for l2_prompt, l3_target, notes, target_language in old_cards:
                explanation = l2_prompt
                if notes:
                    explanation += "\n[Notes] " + notes
                self.cursor.execute('''
                    INSERT INTO srs_items (word, sentences, explanation, next_review_date, interval, step, target_language)
                    VALUES (?, ?, ?, ?, 0, 0, ?)
                ''', (l3_target, "", explanation, today, target_language))
            self.cursor.execute("DROP TABLE laddering_cards")

        # Daily Resources
        self.cursor.execute("PRAGMA table_info(daily_resources)")
        res_cols = [info[1] for info in self.cursor.fetchall()]
        if "language" not in res_cols:
            self.cursor.execute("ALTER TABLE daily_resources ADD COLUMN language TEXT DEFAULT 'Chinese'")
            # Ensure all existing items are marked as 'Chinese'
            self.cursor.execute("UPDATE daily_resources SET language = 'Chinese'")

        self.conn.commit()

    def get_ready_translations(self, target_language="English"):
        self.check_translation_locks()
        self.cursor.execute("SELECT id, l1_text, l2_text, l1_user_translation FROM translations WHERE status = 'ready' AND target_language = ?", (target_language,))
        return self.cursor.fetchall()

    def update_user_translation(self, translation_id, user_translation):
        self.cursor.execute('''
            UPDATE translations
            SET l1_user_translation = ?, is_synced = 1
            WHERE id = ? AND is_synced = 0
        ''', (user_translation, translation_id))
        self.conn.commit()

    def get_locked_translations(self, target_language="English"):
        self.cursor.execute("SELECT id, l1_text, unlock_date FROM translations WHERE status = 'locked' AND target_language = ?", (target_language,))
        return self.cursor.fetchall()

    def complete_translation(self, translation_id):
        self.cursor.execute("UPDATE translations SET status = 'completed' WHERE id = ?", (translation_id,))
        self.conn.commit()

    # --- Dictogloss Methods ---
    def add_dictogloss(self, title, audio_path, text="", target_language="English"):
        self.cursor.execute('''
            INSERT INTO dictogloss (title, audio_path, reconstructed_text, target_language)
            VALUES (?, ?, ?, ?)
        ''', (title, audio_path, text, target_language))
        self.conn.commit()

    def get_all_dictogloss(self, target_language="English"):
        self.cursor.execute("SELECT id, title, audio_path, reconstructed_text FROM dictogloss WHERE target_language = ?", (target_language,))
        return self.cursor.fetchall()

    def update_dictogloss_text(self, item_id, text):
        self.cursor.execute("UPDATE dictogloss SET reconstructed_text = ? WHERE id = ?", (text, item_id))
        self.conn.commit()

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

    # --- Daily Resources Methods ---
    def add_daily_resource(self, category, content, language='Chinese'):
        self.cursor.execute('''
            INSERT INTO daily_resources (category, content, is_used, language)
            VALUES (?, ?, 0, ?)
        ''', (category, content, language))
        self.conn.commit()

    def get_unused_resource(self, category, language=None):
        """Fetch one random resource, delete it from the database, and return its content."""
        if language:
            self.cursor.execute('''
                SELECT id, content FROM daily_resources 
                WHERE category = ? AND language = ?
                ORDER BY RANDOM() LIMIT 1
            ''', (category, language))
        else:
            self.cursor.execute('''
                SELECT id, content FROM daily_resources 
                WHERE category = ? 
                ORDER BY RANDOM() LIMIT 1
            ''', (category,))
            
        result = self.cursor.fetchone()
        if result:
            res_id, content = result
            self.cursor.execute('DELETE FROM daily_resources WHERE id = ?', (res_id,))
            self.conn.commit()
            return content
        return None

    def has_any_resources(self):
        self.cursor.execute('SELECT COUNT(*) FROM daily_resources')
        return self.cursor.fetchone()[0] > 0

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = DatabaseManager(":memory:")
    print("Database manager initialized successfully.")
    db.close()
