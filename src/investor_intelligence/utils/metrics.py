"""Metrics collection and monitoring for Investor Intelligence Agent."""

import time
import functools
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import sqlite3
from pathlib import Path
import logging

from .config import config


@dataclass
class LatencyMetric:
    """Represents a single latency measurement."""

    operation: str
    service: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "operation": self.operation,
            "service": self.service,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": json.dumps(self.metadata) if self.metadata else None,
        }


class MetricsCollector:
    """Collects and manages latency metrics."""

    def __init__(self, db_path: str = "data/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
        self.logger = logging.getLogger("investor_intelligence.metrics")

    def _init_database(self):
        """Initialize the metrics database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS latency_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    service TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    duration_ms REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for better query performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_operation ON latency_metrics(operation)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_service ON latency_metrics(service)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_start_time ON latency_metrics(start_time)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_success ON latency_metrics(success)"
            )

    def record_metric(self, metric: LatencyMetric):
        """Record a latency metric to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO latency_metrics 
                    (operation, service, start_time, end_time, duration_ms, success, error_message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        metric.operation,
                        metric.service,
                        metric.start_time.isoformat(),
                        metric.end_time.isoformat(),
                        metric.duration_ms,
                        metric.success,
                        metric.error_message,
                        json.dumps(metric.metadata) if metric.metadata else None,
                    ),
                )
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")

    def get_metrics_summary(
        self,
        service: Optional[str] = None,
        operation: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """Get a summary of metrics for the specified time period."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                where_clauses = ["start_time >= ?"]
                params = [cutoff_time.isoformat()]

                if service:
                    where_clauses.append("service = ?")
                    params.append(service)

                if operation:
                    where_clauses.append("operation = ?")
                    params.append(operation)

                where_clause = " AND ".join(where_clauses)

                # Get basic statistics
                cursor = conn.execute(
                    f"""
                    SELECT 
                        COUNT(*) as total_requests,
                        AVG(duration_ms) as avg_duration,
                        MIN(duration_ms) as min_duration,
                        MAX(duration_ms) as max_duration,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                        SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_requests
                    FROM latency_metrics 
                    WHERE {where_clause}
                """,
                    params,
                )

                row = cursor.fetchone()
                if not row or row[0] == 0:
                    return {
                        "total_requests": 0,
                        "avg_duration_ms": 0,
                        "min_duration_ms": 0,
                        "max_duration_ms": 0,
                        "success_rate": 0,
                        "error_rate": 0,
                    }

                (
                    total_requests,
                    avg_duration,
                    min_duration,
                    max_duration,
                    successful,
                    failed,
                ) = row

                return {
                    "total_requests": total_requests,
                    "avg_duration_ms": round(avg_duration, 2) if avg_duration else 0,
                    "min_duration_ms": round(min_duration, 2) if min_duration else 0,
                    "max_duration_ms": round(max_duration, 2) if max_duration else 0,
                    "success_rate": (
                        round((successful / total_requests) * 100, 2)
                        if total_requests > 0
                        else 0
                    ),
                    "error_rate": (
                        round((failed / total_requests) * 100, 2)
                        if total_requests > 0
                        else 0
                    ),
                }

        except Exception as e:
            self.logger.error(f"Failed to get metrics summary: {e}")
            return {}

    def get_service_metrics(self, hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """Get metrics grouped by service."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                cursor = conn.execute(
                    """
                    SELECT service, 
                           COUNT(*) as total_requests,
                           AVG(duration_ms) as avg_duration,
                           MIN(duration_ms) as min_duration,
                           MAX(duration_ms) as max_duration,
                           SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests
                    FROM latency_metrics 
                    WHERE start_time >= ?
                    GROUP BY service
                    ORDER BY total_requests DESC
                """,
                    [cutoff_time.isoformat()],
                )

                services = {}
                for row in cursor.fetchall():
                    service, total, avg_dur, min_dur, max_dur, successful = row
                    services[service] = {
                        "total_requests": total,
                        "avg_duration_ms": round(avg_dur, 2) if avg_dur else 0,
                        "min_duration_ms": round(min_dur, 2) if min_dur else 0,
                        "max_duration_ms": round(max_dur, 2) if max_dur else 0,
                        "success_rate": (
                            round((successful / total) * 100, 2) if total > 0 else 0
                        ),
                    }

                return services

        except Exception as e:
            self.logger.error(f"Failed to get service metrics: {e}")
            return {}

    def get_slowest_operations(
        self, limit: int = 10, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get the slowest operations in the specified time period."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(hours=hours)

                cursor = conn.execute(
                    """
                    SELECT operation, service, duration_ms, start_time, success
                    FROM latency_metrics 
                    WHERE start_time >= ?
                    ORDER BY duration_ms DESC
                    LIMIT ?
                """,
                    [cutoff_time.isoformat(), limit],
                )

                operations = []
                for row in cursor.fetchall():
                    operation, service, duration, start_time, success = row
                    operations.append(
                        {
                            "operation": operation,
                            "service": service,
                            "duration_ms": round(duration, 2),
                            "start_time": start_time,
                            "success": bool(success),
                        }
                    )

                return operations

        except Exception as e:
            self.logger.error(f"Failed to get slowest operations: {e}")
            return []

    def cleanup_old_metrics(self, days: int = 30):
        """Clean up metrics older than specified days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cutoff_time = datetime.now() - timedelta(days=days)
                conn.execute(
                    "DELETE FROM latency_metrics WHERE start_time < ?",
                    [cutoff_time.isoformat()],
                )
                self.logger.info(f"Cleaned up metrics older than {days} days")
        except Exception as e:
            self.logger.error(f"Failed to cleanup old metrics: {e}")


# Global metrics collector instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def track_latency(operation: str, service: str):
    """Decorator to track latency of function calls."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = datetime.now()
            success = True
            error_message = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000

                metric = LatencyMetric(
                    operation=operation,
                    service=service,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                )

                collector.record_metric(metric)

        return wrapper

    return decorator


def track_async_latency(operation: str, service: str):
    """Decorator to track latency of async function calls."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            collector = get_metrics_collector()
            start_time = datetime.now()
            success = True
            error_message = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000

                metric = LatencyMetric(
                    operation=operation,
                    service=service,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                )

                collector.record_metric(metric)

        return wrapper

    return decorator


class LatencyTracker:
    """Context manager for tracking latency of code blocks."""

    def __init__(
        self, operation: str, service: str, metadata: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.service = service
        self.metadata = metadata
        self.start_time = None
        self.collector = get_metrics_collector()

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration_ms = (end_time - self.start_time).total_seconds() * 1000
        success = exc_type is None
        error_message = str(exc_val) if exc_val else None

        metric = LatencyMetric(
            operation=self.operation,
            service=self.service,
            start_time=self.start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata=self.metadata,
        )

        self.collector.record_metric(metric)
