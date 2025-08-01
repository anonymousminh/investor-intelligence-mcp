import sqlite3
from datetime import datetime
from typing import List, Optional

from investor_intelligence.models.alert import Alert
from investor_intelligence.utils.db import DATABASE_FILE, init_db
from investor_intelligence.services.user_config_service import UserConfigService
from investor_intelligence.services.alert_feedback_service import AlertFeedbackService
from investor_intelligence.tools.gmail_tool import (
    send_message,
    get_gmail_service,
    create_message,
)

import re
import json


class AlertService:
    """Manages the creation, persistence, and retrieval of alerts."""

    def __init__(self):
        try:
            init_db()  # Ensure database and table are initialized
            self.create_table()
            self.user_config_service = UserConfigService()
            self.feedback_service = AlertFeedbackService()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AlertService: {e}")

    def create_table(self):
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    portfolio_id TEXT,
                    alert_type TEXT NOT NULL,
                    symbol TEXT,
                    message TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    relevance_score REAL DEFAULT 0.0,
                    feedback TEXT
                )
            """
            )

            # Add relevance_score column if it doesn't exist (for existing databases)
            try:
                cursor.execute(
                    "ALTER TABLE alerts ADD COLUMN relevance_score REAL DEFAULT 0.0"
                )
            except sqlite3.OperationalError:
                # Column already exists, ignore error
                pass
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON alerts (user_id)")
            conn.commit()
            conn.close()
        except sqlite3.OperationalError as e:
            raise RuntimeError(
                f"Cannot create alerts table in database at {DATABASE_FILE}: {e}"
            )

    def _get_db_connection(self):
        try:
            return sqlite3.connect(DATABASE_FILE)
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Cannot connect to database at {DATABASE_FILE}: {e}")

    def create_alert(self, alert: Alert) -> Alert:
        """Inserts a new alert into the database and returns the alert with its ID."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alerts (user_id, portfolio_id, alert_type, symbol, threshold, message, created_at, is_active, triggered_at, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                alert.user_id,
                alert.portfolio_id,
                alert.alert_type,
                alert.symbol,
                alert.threshold,
                alert.message,
                alert.created_at.isoformat(),
                int(alert.is_active),
                alert.triggered_at.isoformat() if alert.triggered_at else None,
                alert.relevance_score,
            ),
        )
        alert.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return alert

    def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Retrieves an alert by its ID."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return self._row_to_alert(row)
        return None

    def get_alerts_for_user(
        self, user_id: str, active_only: bool = True
    ) -> List[Alert]:
        """Retrieves alerts for a specific user, optionally filtering by active status."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM alerts WHERE user_id = ?"
        params = (user_id,)
        if active_only:
            query += " AND is_active = 1"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_alert(row) for row in rows]

    def update_alert(self, alert: Alert) -> bool:
        """Updates an existing alert in the database."""
        if alert.id is None:
            raise ValueError("Cannot update alert without an ID.")

        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE alerts
            SET user_id = ?, portfolio_id = ?, alert_type = ?, symbol = ?, threshold = ?, message = ?, created_at = ?, is_active = ?, triggered_at = ?, relevance_score = ?
            WHERE id = ?
        """,
            (
                alert.user_id,
                alert.portfolio_id,
                alert.alert_type,
                alert.symbol,
                alert.threshold,
                alert.message,
                alert.created_at.isoformat(),
                int(alert.is_active),
                alert.triggered_at.isoformat() if alert.triggered_at else None,
                alert.relevance_score,
                alert.id,
            ),
        )
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

    def deactivate_alert(self, alert_id: int) -> bool:
        """Deactivates an alert by setting is_active to False."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE alerts SET is_active = 0 WHERE id = ?", (alert_id,))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

    def _row_to_alert(self, row) -> Alert:
        """Converts a database row tuple to an Alert object."""
        # Handle different database schemas (with and without relevance_score)
        if len(row) >= 11:  # New schema with relevance_score
            return Alert(
                id=row[0],
                user_id=row[1],
                portfolio_id=row[2],
                alert_type=row[3],
                symbol=row[4],
                threshold=row[5],
                message=row[6],
                created_at=datetime.fromisoformat(row[7]),
                is_active=bool(row[8]),
                triggered_at=datetime.fromisoformat(row[9]) if row[9] else None,
                relevance_score=row[10] if row[10] is not None else None,
            )
        else:  # Old schema without relevance_score
            return Alert(
                id=row[0],
                user_id=row[1],
                portfolio_id=row[2],
                alert_type=row[3],
                symbol=row[4],
                threshold=row[5],
                message=row[6],
                created_at=datetime.fromisoformat(row[7]),
                is_active=bool(row[8]),
                triggered_at=datetime.fromisoformat(row[9]) if row[9] else None,
            )

    def filter_alerts(self, alerts: List[Alert], user_id: str) -> List[Alert]:
        """Filters a list of alerts based on user preferences.

        Args:
            alerts (List[Alert]): The list of alerts to filter.
            user_id (str): The ID of the user for whom to apply preferences.

        Returns:
            List[Alert]: The filtered list of alerts.
        """
        preferences = self.user_config_service.get_user_config(user_id)
        min_price_change_percent = preferences.get(
            "min_price_change_percent", 0.0
        )  # Default to 0, no filtering

        filtered_alerts = []
        for alert in alerts:
            if alert.alert_type in ["price_gain", "price_drop"]:
                # Extract percentage from message (e.g., "Price changed by X.XX%")
                match = re.search(r"by ([\d\.]+)%", alert.message)
                if match:
                    change_percent = float(match.group(1))
                    if change_percent >= min_price_change_percent:
                        filtered_alerts.append(alert)
                else:
                    # If percentage not found, include by default or log an error
                    filtered_alerts.append(alert)
            else:
                # Include other alert types by default for now
                filtered_alerts.append(alert)
        return filtered_alerts

    def send_admin_error_alert(error_message: str):
        admin_email = "anhminh7802@gmail.com"
        subject = f"CRITICAL ERROR in Investor Intelligence Agent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        body = f"A critical error occurred in the Investor Intelligence Agent MCP Server:\n\n{error_message}\n\nPlease investigate immediately."
        send_message(admin_email, subject, body)

    def track_alert_view(
        self, alert_id: int, user_id: str, relevance_score: Optional[float] = None
    ):
        """Track when a user views an alert for feedback collection."""
        try:
            self.feedback_service.record_alert_view(alert_id, user_id, relevance_score)
        except Exception as e:
            print(f"Failed to track alert view: {e}")

    def track_alert_click(
        self, alert_id: int, user_id: str, interaction_duration: Optional[float] = None
    ):
        """Track when a user clicks on an alert (indicating interest)."""
        try:
            self.feedback_service.record_alert_click(
                alert_id, user_id, interaction_duration
            )
        except Exception as e:
            print(f"Failed to track alert click: {e}")

    def track_alert_dismiss(
        self, alert_id: int, user_id: str, reason: Optional[str] = None
    ):
        """Track when a user dismisses an alert."""
        try:
            self.feedback_service.record_alert_dismiss(alert_id, user_id, reason)
        except Exception as e:
            print(f"Failed to track alert dismiss: {e}")

    def record_relevance_rating(
        self, alert_id: int, user_id: str, rating: int, notes: Optional[str] = None
    ):
        """Record explicit relevance rating from user (1-5 scale)."""
        try:
            self.feedback_service.record_relevance_rating(
                alert_id, user_id, rating, notes
            )
        except Exception as e:
            print(f"Failed to record relevance rating: {e}")

    def record_relevance_mark(self, alert_id: int, user_id: str, is_relevant: bool):
        """Record when user explicitly marks an alert as relevant or irrelevant."""
        try:
            self.feedback_service.record_relevance_mark(alert_id, user_id, is_relevant)
        except Exception as e:
            print(f"Failed to record relevance mark: {e}")

    def get_alert_engagement_score(self, alert_id: int) -> float:
        """Get the engagement score for an alert based on user interactions."""
        try:
            return self.feedback_service.calculate_alert_engagement_score(alert_id)
        except Exception as e:
            print(f"Failed to get alert engagement score: {e}")
            return 0.0

    def get_user_feedback_summary(self, user_id: str, days_back: int = 30) -> dict:
        """Get a summary of user feedback patterns."""
        try:
            return self.feedback_service.get_user_feedback_summary(user_id, days_back)
        except Exception as e:
            print(f"Failed to get user feedback summary: {e}")
            return {
                "total_interactions": 0,
                "feedback_types": {},
                "average_rating": 0.0,
                "engagement_trend": "neutral",
            }

    def get_relevance_training_data(self, days_back: int = 90) -> List[dict]:
        """Get training data for the relevance model from user feedback."""
        try:
            return self.feedback_service.get_relevance_training_data(days_back)
        except Exception as e:
            print(f"Failed to get relevance training data: {e}")
            return []

    def record_alert_feedback(self, alert_id: int, feedback: str):
        """Records user feedback for a specific alert.

        Args:
            alert_id (int): The ID of the alert.
            feedback (str): The feedback (e.g., "relevant", "irrelevant").
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE alerts SET feedback = ? WHERE id = ?", (feedback, alert_id)
        )
        conn.commit()
        conn.close()


if __name__ == "__main__":
    alert_service = AlertService()
    test_user_id = "user_with_prefs"

    # Set a preference for min price change using UserConfigService directly
    user_config_service = UserConfigService()
    user_config = user_config_service.get_user_config(test_user_id)
    user_config["min_price_change_percent"] = 1.5
    user_config_service.save_user_config(test_user_id, user_config)
    print(
        f"User preferences for {test_user_id}: {user_config_service.get_user_config(test_user_id)}"
    )

    # Create some dummy alerts
    alert1 = Alert(
        user_id=test_user_id,
        portfolio_id="p1",
        alert_type="price_gain",
        symbol="AAPL",
        message="Price changed by 2.0%",
        triggered_at=datetime.now(),
    )
    alert2 = Alert(
        user_id=test_user_id,
        portfolio_id="p1",
        alert_type="price_drop",
        symbol="MSFT",
        message="Price changed by 1.0%",
        triggered_at=datetime.now(),
    )
    alert3 = Alert(
        user_id=test_user_id,
        portfolio_id="p1",
        alert_type="news_sentiment",
        symbol="GOOG",
        message="Positive news detected",
        triggered_at=datetime.now(),
    )

    alert_service.create_alert(alert1)
    alert_service.create_alert(alert2)
    alert_service.create_alert(alert3)

    # Retrieve and filter alerts
    all_alerts = alert_service.get_alerts_for_user(test_user_id, active_only=True)
    print(f"\nAll active alerts for {test_user_id}: {len(all_alerts)}")
    for alert in all_alerts:
        print(f"  - {alert.alert_type} {alert.symbol}: {alert.message}")

    filtered_alerts = alert_service.filter_alerts(all_alerts, test_user_id)
    print(
        f"\nFiltered alerts for {test_user_id} (min_price_change_percent=1.5): {len(filtered_alerts)}"
    )
    for alert in filtered_alerts:
        print(f"  - {alert.alert_type} {alert.symbol}: {alert.message}")

    # Test with no preferences
    test_user_id_no_prefs = "user_no_prefs"
    alert_service.create_alert(
        Alert(
            user_id=test_user_id_no_prefs,
            portfolio_id="p2",
            alert_type="price_gain",
            symbol="AMZN",
            message="Price changed by 0.5%",
            triggered_at=datetime.now(),
        )
    )
    all_alerts_no_prefs = alert_service.get_alerts_for_user(
        test_user_id_no_prefs, active_only=True
    )
    filtered_alerts_no_prefs = alert_service.filter_alerts(
        all_alerts_no_prefs, test_user_id_no_prefs
    )
    print(
        f"\nFiltered alerts for {test_user_id_no_prefs} (no preferences): {len(filtered_alerts_no_prefs)}"
    )
    for alert in filtered_alerts_no_prefs:
        print(f"  - {alert.alert_type} {alert.symbol}: {alert.message}")
