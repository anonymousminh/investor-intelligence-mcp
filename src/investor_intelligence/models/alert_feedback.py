from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback that can be collected."""

    VIEW = "view"
    CLICK = "click"
    DISMISS = "dismiss"
    MARK_RELEVANT = "mark_relevant"
    MARK_IRRELEVANT = "mark_irrelevant"
    RATING = "rating"


@dataclass
class AlertFeedback:
    """Represents user feedback on alert relevance and interactions."""

    alert_id: int
    user_id: str
    feedback_type: FeedbackType
    timestamp: datetime = field(default_factory=datetime.now)
    id: Optional[int] = None  # Will be set by the database upon insertion

    # Optional feedback data
    rating: Optional[int] = None  # 1-5 scale for relevance
    relevance_score: Optional[float] = (
        None  # Predicted relevance score at time of feedback
    )
    interaction_duration: Optional[float] = None  # Time spent viewing alert in seconds
    dismiss_reason: Optional[str] = (
        None  # Reason for dismissing (e.g., "not relevant", "already aware")
    )
    notes: Optional[str] = None  # Additional user notes

    def __post_init__(self):
        if not self.alert_id:
            raise ValueError("AlertFeedback must be associated with an alert_id.")
        if not self.user_id:
            raise ValueError("AlertFeedback must be associated with a user_id.")
        if not self.feedback_type:
            raise ValueError("AlertFeedback must have a feedback_type.")

        # Validate rating if provided
        if self.rating is not None and not (1 <= self.rating <= 5):
            raise ValueError("Rating must be between 1 and 5.")

        # Validate relevance score if provided
        if self.relevance_score is not None and not (
            0.0 <= self.relevance_score <= 1.0
        ):
            raise ValueError("Relevance score must be between 0.0 and 1.0.")
