import sqlite3
import os

DATABASE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "..",
    "data",
    "investor_intelligence.db",
)


def init_db():
    """Initializes the SQLite database and creates the alerts table if it doesn't exist."""
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            portfolio_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            symbol TEXT,
            threshold REAL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            triggered_at TEXT
        )
    """
    )
    conn.commit()
    conn.close()
    print(f"Database initialized at {DATABASE_FILE}")


if __name__ == "__main__":
    init_db()
