import sqlite3
from datetime import datetime
from typing import List, Optional

from investor_intelligence.models.alert import Alert
from investor_intelligence.utils.db import DATABASE_FILE, init_db


class AlertService:
    """Manages the creation, persistence, and retrieval of alerts."""

    def __init__(self):
        init_db()  # Ensure database and table are initialized

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


if __name__ == "__main__":
    alert_service = AlertService()

    # Test 1: Create a new alert
    print("\n--- Test: Creating a new alert ---")
    new_alert = Alert(
        user_id="user_abc",
        portfolio_id="port_123",
        alert_type="price_change",
        symbol="MSFT",
        threshold=300.0,
        message="MSFT price exceeded $300!",
        is_active=True,
    )
    created_alert = alert_service.create_alert(new_alert)
    print(f"Created Alert: {created_alert}")
    assert created_alert.id is not None

    # Test 2: Retrieve alert by ID
    print("\n--- Test: Retrieving alert by ID ---")
    retrieved_alert = alert_service.get_alert_by_id(created_alert.id)
    print(f"Retrieved Alert: {retrieved_alert}")
    assert retrieved_alert == created_alert

    # Test 3: Create another alert for the same user
    print("\n--- Test: Creating another alert ---")
    another_alert = Alert(
        user_id="user_abc",
        portfolio_id="port_123",
        alert_type="earnings_report",
        symbol="AAPL",
        message="AAPL earnings report due soon.",
        is_active=True,
    )
    created_another_alert = alert_service.create_alert(another_alert)
    print(f"Created Another Alert: {created_another_alert}")

    # Test 4: Get all active alerts for a user
    print("\n--- Test: Getting active alerts for user_abc ---")
    user_alerts = alert_service.get_alerts_for_user("user_abc")
    for alert in user_alerts:
        print(f"  - {alert}")
    assert len(user_alerts) == 2

    # Test 5: Deactivate an alert
    print("\n--- Test: Deactivating an alert ---")
    deactivated = alert_service.deactivate_alert(created_alert.id)
    print(f"Alert {created_alert.id} deactivated: {deactivated}")
    assert deactivated is True

    # Test 6: Get active alerts again (should be 1 now)
    print("\n--- Test: Getting active alerts for user_abc after deactivation ---")
    user_alerts_after_deactivation = alert_service.get_alerts_for_user("user_abc")
    for alert in user_alerts_after_deactivation:
        print(f"  - {alert}")
    assert len(user_alerts_after_deactivation) == 1
    assert user_alerts_after_deactivation[0].id == created_another_alert.id

    # Test 7: Get all alerts (including inactive)
    print("\n--- Test: Getting all alerts for user_abc (including inactive) ---")
    all_user_alerts = alert_service.get_alerts_for_user("user_abc", active_only=False)
    for alert in all_user_alerts:
        print(f"  - {alert}")
    assert len(all_user_alerts) == 2

    print("\nAll Alert Service tests passed!")
