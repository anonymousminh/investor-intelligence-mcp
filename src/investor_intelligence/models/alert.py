from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Alert:
    """Represents a generic alert in the system."""

    user_id: str
    portfolio_id: str
    alert_type: str  # e.g., "price_change", "earnings_report", "news_sentiment"
    message: str
    id: Optional[int] = None  # Will be set by the database upon insertion
    symbol: Optional[str] = None
    threshold: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    triggered_at: Optional[datetime] = None
    relevance_score: Optional[float] = None  # Added for prioritization

    def __post_init__(self):
        if not self.user_id:
            raise ValueError("Alert must be associated with a user_id.")
        if not self.portfolio_id:
            raise ValueError("Alert must be associated with a portfolio_id.")
        if not self.alert_type:
            raise ValueError("Alert must have an alert_type.")
        if not self.message:
            raise ValueError("Alert must have a message.")
