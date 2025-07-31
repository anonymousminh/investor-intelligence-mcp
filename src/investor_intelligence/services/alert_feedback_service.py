import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import json

from investor_intelligence.models.alert_feedback import AlertFeedback, FeedbackType
from investor_intelligence.utils.db import DATABASE_FILE, init_db


class AlertFeedbackService:
    """Service for collecting and managing user feedback on alert relevance."""

    def __init__(self):
        try:
            init_db()  # Ensure database and tables are initialized
            self.create_table()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AlertFeedbackService: {e}")

    def create_table(self):
        """Create the alert_feedback table if it doesn't exist."""
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
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
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Cannot create alert_feedback table: {e}")

    def _get_db_connection(self):
        """Get a database connection."""
        try:
            return sqlite3.connect(DATABASE_FILE)
        except sqlite3.OperationalError as e:
            raise RuntimeError(f"Cannot connect to database: {e}")

    def record_feedback(self, feedback: AlertFeedback) -> AlertFeedback:
        """Record user feedback for an alert."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO alert_feedback 
            (alert_id, user_id, feedback_type, timestamp, rating, relevance_score, 
             interaction_duration, dismiss_reason, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                feedback.alert_id,
                feedback.user_id,
                feedback.feedback_type.value,
                feedback.timestamp.isoformat(),
                feedback.rating,
                feedback.relevance_score,
                feedback.interaction_duration,
                feedback.dismiss_reason,
                feedback.notes,
            ),
        )

        feedback.id = cursor.lastrowid
        conn.commit()
        conn.close()
        return feedback

    def record_alert_view(
        self, alert_id: int, user_id: str, relevance_score: Optional[float] = None
    ) -> AlertFeedback:
        """Record when a user views an alert."""
        feedback = AlertFeedback(
            alert_id=alert_id,
            user_id=user_id,
            feedback_type=FeedbackType.VIEW,
            relevance_score=relevance_score,
        )
        return self.record_feedback(feedback)

    def record_alert_click(
        self, alert_id: int, user_id: str, interaction_duration: Optional[float] = None
    ) -> AlertFeedback:
        """Record when a user clicks on an alert (indicating interest)."""
        feedback = AlertFeedback(
            alert_id=alert_id,
            user_id=user_id,
            feedback_type=FeedbackType.CLICK,
            interaction_duration=interaction_duration,
        )
        return self.record_feedback(feedback)

    def record_alert_dismiss(
        self, alert_id: int, user_id: str, reason: Optional[str] = None
    ) -> AlertFeedback:
        """Record when a user dismisses an alert."""
        feedback = AlertFeedback(
            alert_id=alert_id,
            user_id=user_id,
            feedback_type=FeedbackType.DISMISS,
            dismiss_reason=reason,
        )
        return self.record_feedback(feedback)

    def record_relevance_rating(
        self, alert_id: int, user_id: str, rating: int, notes: Optional[str] = None
    ) -> AlertFeedback:
        """Record explicit relevance rating from user (1-5 scale)."""
        feedback = AlertFeedback(
            alert_id=alert_id,
            user_id=user_id,
            feedback_type=FeedbackType.RATING,
            rating=rating,
            notes=notes,
        )
        return self.record_feedback(feedback)

    def record_relevance_mark(
        self, alert_id: int, user_id: str, is_relevant: bool
    ) -> AlertFeedback:
        """Record when user explicitly marks an alert as relevant or irrelevant."""
        feedback_type = (
            FeedbackType.MARK_RELEVANT if is_relevant else FeedbackType.MARK_IRRELEVANT
        )
        feedback = AlertFeedback(
            alert_id=alert_id, user_id=user_id, feedback_type=feedback_type
        )
        return self.record_feedback(feedback)

    def get_feedback_for_alert(self, alert_id: int) -> List[AlertFeedback]:
        """Get all feedback for a specific alert."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM alert_feedback WHERE alert_id = ? ORDER BY timestamp",
            (alert_id,),
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_feedback(row) for row in rows]

    def get_feedback_for_user(
        self, user_id: str, days_back: int = 30
    ) -> List[AlertFeedback]:
        """Get all feedback for a specific user within a time period."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cursor.execute(
            "SELECT * FROM alert_feedback WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
            (user_id, cutoff_date.isoformat()),
        )
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_feedback(row) for row in rows]

    def get_relevance_training_data(self, days_back: int = 90) -> List[Dict]:
        """Get training data for the relevance model from user feedback."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Get alerts with their feedback for training
        cutoff_date = datetime.now() - timedelta(days=days_back)
        cursor.execute(
            """
            SELECT 
                a.id, a.alert_type, a.symbol, a.message, a.relevance_score,
                af.feedback_type, af.rating, af.interaction_duration,
                af.dismiss_reason, af.timestamp
            FROM alerts a
            LEFT JOIN alert_feedback af ON a.id = af.alert_id
            WHERE a.created_at >= ?
            ORDER BY a.id, af.timestamp
        """,
            (cutoff_date.isoformat(),),
        )
        rows = cursor.fetchall()
        conn.close()

        # Group by alert and aggregate feedback
        training_data = []
        current_alert = None
        current_feedback = []

        for row in rows:
            alert_id = row[0]
            if current_alert is None or current_alert["alert_id"] != alert_id:
                if current_alert is not None:
                    current_alert["feedback"] = current_feedback
                    training_data.append(current_alert)

                current_alert = {
                    "alert_id": alert_id,
                    "alert_type": row[1],
                    "symbol": row[2],
                    "message": row[3],
                    "predicted_relevance": row[4],
                }
                current_feedback = []

            if row[5]:  # feedback_type is not None
                feedback = {
                    "type": row[5],
                    "rating": row[6],
                    "interaction_duration": row[7],
                    "dismiss_reason": row[8],
                    "timestamp": row[9],
                }
                current_feedback.append(feedback)

        # Add the last alert
        if current_alert is not None:
            current_alert["feedback"] = current_feedback
            training_data.append(current_alert)

        return training_data

    def calculate_alert_engagement_score(self, alert_id: int) -> float:
        """Calculate an engagement score for an alert based on user interactions."""
        feedback_list = self.get_feedback_for_alert(alert_id)

        if not feedback_list:
            return 0.0

        score = 0.0
        total_interactions = len(feedback_list)

        for feedback in feedback_list:
            if feedback.feedback_type == FeedbackType.VIEW:
                score += 0.1
            elif feedback.feedback_type == FeedbackType.CLICK:
                score += 0.3
            elif feedback.feedback_type == FeedbackType.MARK_RELEVANT:
                score += 0.5
            elif feedback.feedback_type == FeedbackType.RATING:
                if feedback.rating:
                    score += (feedback.rating / 5.0) * 0.4
            elif feedback.feedback_type == FeedbackType.MARK_IRRELEVANT:
                score -= 0.2
            elif feedback.feedback_type == FeedbackType.DISMISS:
                score -= 0.1

        # Normalize by number of interactions and ensure score is between 0 and 1
        normalized_score = score / max(total_interactions, 1)
        return max(0.0, min(1.0, normalized_score))

    def get_user_feedback_summary(self, user_id: str, days_back: int = 30) -> Dict:
        """Get a summary of user feedback patterns."""
        feedback_list = self.get_feedback_for_user(user_id, days_back)

        summary = {
            "total_interactions": len(feedback_list),
            "feedback_types": {},
            "average_rating": 0.0,
            "engagement_trend": "neutral",
        }

        if not feedback_list:
            return summary

        # Count feedback types
        for feedback in feedback_list:
            feedback_type = feedback.feedback_type.value
            summary["feedback_types"][feedback_type] = (
                summary["feedback_types"].get(feedback_type, 0) + 1
            )

        # Calculate average rating
        ratings = [f.rating for f in feedback_list if f.rating is not None]
        if ratings:
            summary["average_rating"] = sum(ratings) / len(ratings)

        # Determine engagement trend
        positive_interactions = sum(
            1
            for f in feedback_list
            if f.feedback_type in [FeedbackType.CLICK, FeedbackType.MARK_RELEVANT]
        )
        negative_interactions = sum(
            1
            for f in feedback_list
            if f.feedback_type in [FeedbackType.MARK_IRRELEVANT, FeedbackType.DISMISS]
        )

        if positive_interactions > negative_interactions:
            summary["engagement_trend"] = "positive"
        elif negative_interactions > positive_interactions:
            summary["engagement_trend"] = "negative"

        return summary

    def _row_to_feedback(self, row) -> AlertFeedback:
        """Convert a database row to an AlertFeedback object."""
        return AlertFeedback(
            id=row[0],
            alert_id=row[1],
            user_id=row[2],
            feedback_type=FeedbackType(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            rating=row[5],
            relevance_score=row[6],
            interaction_duration=row[7],
            dismiss_reason=row[8],
            notes=row[9],
        )
