from pathlib import Path
import sqlite3
from datetime import datetime

DB_PATH = Path(__file__).resolve().parents[1] / "logs" / "mapre_events.db"

class EventStore:
    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
                category TEXT NOT NULL, severity TEXT NOT NULL, source TEXT,
                destination TEXT, description TEXT NOT NULL, details TEXT)""")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def add(self, category, severity, description, source="", destination="", details=""):
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with self._connect() as db:
            cur = db.execute("INSERT INTO events(timestamp,category,severity,source,destination,description,details) VALUES(?,?,?,?,?,?,?)",
                (stamp, category, severity, source, destination, description, details))
            return cur.lastrowid

    def recent(self, limit=200):
        with self._connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]

    def count(self, category=None):
        with self._connect() as db:
            if category:
                return db.execute("SELECT COUNT(*) FROM events WHERE category=?", (category,)).fetchone()[0]
            return db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
