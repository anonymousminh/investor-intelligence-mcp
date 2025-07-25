import sqlite3
from datetime import datetime
from typing import List, Optional

from investor_intelligence.models.alert import Alert
from investor_intelligence.utils.db import DATABASE_FILE, init_db

import re
import json


class AlertService:
    """Manages the creation, persistence, and retrieval of alerts."""

    def __init__(self):
        init_db()  # Ensure database and table are initialized
        self.create_table()

    def create_table(self):
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
                preferences TEXT
            )
        """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON alerts (user_id)")
        conn.commit()
        conn.close()

    def _get_db_connection(self):
        return sqlite3.connect(DATABASE_FILE)

    def create_alert(self, alert: Alert) -> Alert:
        """Inserts a new alert into the database and returns the alert with its ID."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alerts (user_id, portfolio_id, alert_type, symbol, threshold, message, created_at, is_active, triggered_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            SET user_id = ?, portfolio_id = ?, alert_type = ?, symbol = ?, threshold = ?, message = ?, created_at = ?, is_active = ?, triggered_at = ?
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

    def set_user_alert_preferences(self, user_id: str, preferences: dict):
        """Sets or updates alert preferences for a user.

        Args:
            user_id (str): The ID of the user.
            preferences (dict): A dictionary of preferences (e.g., {"min_price_change_percent": 2.0}).
        """
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Check if preferences already exist for the user
        cursor.execute(
            "SELECT preferences FROM alerts WHERE user_id = ? LIMIT 1", (user_id,)
        )
        existing_preferences_row = cursor.fetchone()

        if existing_preferences_row and existing_preferences_row[0]:
            existing_prefs = json.loads(existing_preferences_row[0])
            existing_prefs.update(preferences)
            updated_prefs_json = json.dumps(existing_prefs)
            cursor.execute(
                "UPDATE alerts SET preferences = ? WHERE user_id = ?",
                (updated_prefs_json, user_id),
            )
        else:
            # If no existing preferences, insert a dummy alert row with preferences
            # This is a workaround as preferences are tied to an alert row. A better design
            # would be a separate 'user_preferences' table.
            dummy_alert = Alert(
                user_id=user_id,
                portfolio_id="preferences",
                alert_type="preference_setting",
                symbol="",
                message="User preferences set",
                triggered_at=datetime.now(),
            )
            self.create_alert(dummy_alert)  # Create a dummy alert to attach preferences
            cursor.execute(
                "UPDATE alerts SET preferences = ? WHERE user_id = ? AND alert_type = ?",
                (json.dumps(preferences), user_id, "preference_setting"),
            )
        conn.commit()
        conn.close()

    def get_user_alert_preferences(self, user_id: str) -> dict:
        """Retrieves alert preferences for a user.

        Args:
            user_id (str): The ID of the user.

        Returns:
            dict: A dictionary of preferences, or an empty dict if none are set.
        """
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT preferences FROM alerts WHERE user_id = ? AND preferences IS NOT NULL LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            return json.loads(row[0])
        return {}

    def filter_alerts(self, alerts: List[Alert], user_id: str) -> List[Alert]:
        """Filters a list of alerts based on user preferences.

        Args:
            alerts (List[Alert]): The list of alerts to filter.
            user_id (str): The ID of the user for whom to apply preferences.

        Returns:
            List[Alert]: The filtered list of alerts.
        """
        preferences = self.get_user_alert_preferences(user_id)
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


if __name__ == "__main__":
    alert_service = AlertService()
    test_user_id = "user_with_prefs"

    # Set a preference for min price change
    alert_service.set_user_alert_preferences(
        test_user_id, {"min_price_change_percent": 1.5}
    )
    print(
        f"User preferences for {test_user_id}: {alert_service.get_user_alert_preferences(test_user_id)}"
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
