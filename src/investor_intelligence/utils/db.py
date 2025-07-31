import sqlite3
import os


def get_project_root():
    """Get the project root directory reliably."""
    # Try multiple approaches to find the project root
    current_file = os.path.abspath(__file__)

    # Approach 1: Go up from utils/db.py to project root
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    )

    # Approach 2: If that doesn't work, try to find it by looking for setup.py or requirements.txt
    if not os.path.exists(os.path.join(project_root, "setup.py")):
        # Try to find the project root by looking for common project files
        current_dir = os.path.dirname(current_file)
        while current_dir != os.path.dirname(current_dir):  # Stop at root
            if (
                os.path.exists(os.path.join(current_dir, "setup.py"))
                or os.path.exists(os.path.join(current_dir, "requirements.txt"))
                or os.path.exists(os.path.join(current_dir, "README.md"))
            ):
                project_root = current_dir
                break
            current_dir = os.path.dirname(current_dir)

    return project_root


# Get the project root directory
PROJECT_ROOT = get_project_root()
DATABASE_FILE = os.path.join(PROJECT_ROOT, "data", "investor_intelligence.db")


def ensure_data_directory():
    """Ensure the data directory exists and is writable."""
    data_dir = os.path.dirname(DATABASE_FILE)
    try:
        os.makedirs(data_dir, exist_ok=True)
        # Test if the directory is writable
        test_file = os.path.join(data_dir, ".test_write")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        return True
    except (OSError, IOError) as e:
        print(f"Warning: Could not create or write to data directory {data_dir}: {e}")
        return False


def init_db():
    """Initializes the SQLite database and creates the alerts table if it doesn't exist."""
    if not ensure_data_directory():
        raise RuntimeError(
            f"Cannot create or write to data directory: {os.path.dirname(DATABASE_FILE)}"
        )

    try:
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
                triggered_at TEXT,
                relevance_score REAL
            )
        """
        )

        # Create alert feedback table for tracking user interactions and relevance feedback
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                rating INTEGER,
                relevance_score REAL,
                interaction_duration REAL,
                dismiss_reason TEXT,
                notes TEXT,
                FOREIGN KEY (alert_id) REFERENCES alerts (id) ON DELETE CASCADE
            )
        """
        )

        # Create indexes for better query performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_feedback_alert_id ON alert_feedback (alert_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_feedback_user_id ON alert_feedback (user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_alert_feedback_timestamp ON alert_feedback (timestamp)"
        )
        conn.commit()
        conn.close()
        print(f"Database initialized at {DATABASE_FILE}")
    except sqlite3.OperationalError as e:
        raise RuntimeError(f"Cannot create database at {DATABASE_FILE}: {e}")


if __name__ == "__main__":
    init_db()
