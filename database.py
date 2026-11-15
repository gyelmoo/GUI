"""Database layer (SQLite)."""

import sqlite3
from datetime import date, timedelta

from config import DB_FILE, REPEAT_DAYS
from helpers import hash_password, parse_date


class Database:
    def __init__(self, path=DB_FILE):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    salt     TEXT NOT NULL,
                    pw_hash  TEXT NOT NULL,
                    avatar   TEXT
                );
                CREATE TABLE IF NOT EXISTS plants (
                    user_id    INTEGER NOT NULL,
                    plant_id   TEXT NOT NULL,
                    plant_name TEXT NOT NULL,
                    PRIMARY KEY (user_id, plant_id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER NOT NULL,
                    plant_id      TEXT NOT NULL,
                    task_type     TEXT NOT NULL,
                    due_date      TEXT NOT NULL,
                    base_priority TEXT NOT NULL,
                    repeat        TEXT NOT NULL DEFAULT 'One-time',
                    notes         TEXT NOT NULL DEFAULT '',
                    status        TEXT NOT NULL DEFAULT 'Pending',
                    completed_on  TEXT,
                    last_alert    TEXT,
                    FOREIGN KEY (user_id, plant_id) REFERENCES plants(user_id, plant_id)
                );
                """
            )
        # Older databases (made before profile pictures) get the new column added.
        columns = [r["name"] for r in self.conn.execute("PRAGMA table_info(users)")]
        if "avatar" not in columns:
            with self.conn:
                self.conn.execute("ALTER TABLE users ADD COLUMN avatar TEXT")
        # Plant pictures: one optional photo per plant (older databases get the column).
        plant_columns = [r["name"] for r in self.conn.execute("PRAGMA table_info(plants)")]
        if "photo" not in plant_columns:
            with self.conn:
                self.conn.execute("ALTER TABLE plants ADD COLUMN photo TEXT")

    def _seed_demo_data(self):
        # No demo account is created. Users create their own account.
        return

    # -- users ---------------------------------------------------------------
    def create_user(self, username, password):
        salt, digest = hash_password(password)
        try:
            with self.conn:
                self.conn.execute(
                    "INSERT INTO users (username, salt, pw_hash) VALUES (?, ?, ?)",
                    (username, salt, digest),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def username_exists(self, username):
        row = self.conn.execute("SELECT 1 FROM users WHERE username = ?",
                                (username,)).fetchone()
        return row is not None

    def verify_user(self, username, password):
        row = self.conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is None:
            return None
        _, digest = hash_password(password, row["salt"])
        return dict(row) if digest == row["pw_hash"] else None

    def set_avatar(self, user_id, filename):
        """Store the profile picture file name (or None to remove it)."""
        with self.conn:
            self.conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (filename, user_id))

    # -- plants (unique Plant ID check) ---------------------------------------
    def find_plant(self, user_id, plant_id):
        """The saved plant with this ID (ignoring upper/lower case), or None."""
        row = self.conn.execute(
            "SELECT * FROM plants WHERE user_id = ? AND lower(plant_id) = lower(?)",
            (user_id, plant_id),
        ).fetchone()
        return dict(row) if row else None

    def set_plant_photo(self, user_id, plant_id, filename):
        """Store the plant picture file name (or None to remove it)."""
        with self.conn:
            self.conn.execute(
                "UPDATE plants SET photo = ? WHERE user_id = ? AND lower(plant_id) = lower(?)",
                (filename, user_id, plant_id))

    def count_plant_tasks(self, user_id, plant_id, exclude_task_id=None, pending_only=False):
        """How many tasks use this Plant ID (optionally not counting one task)."""
        sql = """SELECT COUNT(*) AS n FROM tasks
                 WHERE user_id = ? AND lower(plant_id) = lower(?) AND id != ?"""
        if pending_only:
            sql += " AND status = 'Pending'"
        row = self.conn.execute(
            sql, (user_id, plant_id, exclude_task_id if exclude_task_id is not None else -1),
        ).fetchone()
        return row["n"]

    def plant_task_label(self, user_id, plant_id, exclude_task_id=None):
        """Short description of the pending task already using this Plant ID."""
        row = self.conn.execute(
            """SELECT t.task_type, t.due_date, p.plant_name FROM tasks t
               JOIN plants p ON p.user_id = t.user_id AND p.plant_id = t.plant_id
               WHERE t.user_id = ? AND lower(t.plant_id) = lower(?) AND t.id != ?
                     AND t.status = 'Pending' ORDER BY t.due_date LIMIT 1""",
            (user_id, plant_id, exclude_task_id if exclude_task_id is not None else -1),
        ).fetchone()
        return f"{row['plant_name']} - {row['task_type']}, due {row['due_date']}" if row else ""

    # -- tasks ---------------------------------------------------------------
    def fetch_tasks(self, user_id):
        rows = self.conn.execute(
            """SELECT t.*, p.plant_name, p.photo
               FROM tasks t
               JOIN plants p ON p.user_id = t.user_id AND p.plant_id = t.plant_id
               WHERE t.user_id = ?
               ORDER BY t.due_date, t.id""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def save_task(self, user_id, d, task_id=None):
        """Insert a new task, or update task `task_id`."""
        with self.conn:
            self.conn.execute(
                """INSERT INTO plants (user_id, plant_id, plant_name) VALUES (?, ?, ?)
                   ON CONFLICT(user_id, plant_id) DO UPDATE SET plant_name = excluded.plant_name""",
                (user_id, d["plant_id"], d["plant_name"]),
            )
            if task_id is None:
                self.conn.execute(
                    """INSERT INTO tasks (user_id, plant_id, task_type, due_date, base_priority,
                                          repeat, notes, status, completed_on)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, d["plant_id"], d["task_type"], d["due_date"], d["base_priority"],
                     d["repeat"], d["notes"], d.get("status", "Pending"), d.get("completed_on")),
                )
            else:
                # last_alert is reset so a changed date can trigger reminders again
                self.conn.execute(
                    """UPDATE tasks SET plant_id=?, task_type=?, due_date=?, base_priority=?,
                                        repeat=?, notes=?, last_alert=NULL
                       WHERE id=? AND user_id=?""",
                    (d["plant_id"], d["task_type"], d["due_date"], d["base_priority"],
                     d["repeat"], d["notes"], task_id, user_id),
                )

    def delete_task(self, task_id):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    def mark_alert(self, task_id, key):
        with self.conn:
            self.conn.execute("UPDATE tasks SET last_alert = ? WHERE id = ?", (key, task_id))

    def complete_task(self, task_id, today=None):
        """Mark a pending task completed.

        For Daily/Weekly tasks the next occurrence is created automatically and its
        due date (ISO string) is returned. Returns None otherwise.
        """
        today = today or date.today()
        with self.conn:
            row = self.conn.execute(
                "SELECT * FROM tasks WHERE id = ? AND status = 'Pending'", (task_id,)
            ).fetchone()
            if row is None:
                return None
            self.conn.execute(
                "UPDATE tasks SET status='Completed', completed_on=? WHERE id=?",
                (today.isoformat(), task_id),
            )
            step = REPEAT_DAYS.get(row["repeat"])
            if not step:
                return None
            # on time -> +step from the due date; late -> +step from today
            next_due = max(parse_date(row["due_date"]), today) + timedelta(days=step)
            self.conn.execute(
                """INSERT INTO tasks (user_id, plant_id, task_type, due_date, base_priority,
                                      repeat, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (row["user_id"], row["plant_id"], row["task_type"], next_due.isoformat(),
                 row["base_priority"], row["repeat"], row["notes"]),
            )
            return next_due.isoformat()

    def close(self):
        self.conn.close()
