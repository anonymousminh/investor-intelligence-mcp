"""Metrics service for analyzing and reporting on latency metrics."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from ..utils.metrics import get_metrics_collector, LatencyTracker
from ..utils.config import config


class MetricsService:
    """Service for analyzing and reporting on latency metrics."""

    def __init__(self):
        self.collector = get_metrics_collector()
        self.logger = logging.getLogger("investor_intelligence.metrics_service")

    def get_overall_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get overall performance summary for the specified time period."""
        with LatencyTracker("get_overall_performance_summary", "metrics_service"):
            summary = self.collector.get_metrics_summary(hours=hours)

            # Add performance indicators
            if summary.get("total_requests", 0) > 0:
                avg_duration = summary.get("avg_duration_ms", 0)
                success_rate = summary.get("success_rate", 0)

                # Performance thresholds (configurable)
                performance_status = "excellent"
                if avg_duration > 1000:  # > 1 second
                    performance_status = "poor"
                elif avg_duration > 500:  # > 500ms
                    performance_status = "fair"
                elif avg_duration > 200:  # > 200ms
                    performance_status = "good"

                if success_rate < 95:
                    performance_status = "poor"

                summary["performance_status"] = performance_status
                summary["performance_grade"] = self._calculate_performance_grade(
                    avg_duration, success_rate
                )

            return summary

    def get_service_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get detailed performance report by service."""
        with LatencyTracker("get_service_performance_report", "metrics_service"):
            service_metrics = self.collector.get_service_metrics(hours=hours)
            slowest_operations = self.collector.get_slowest_operations(
                limit=5, hours=hours
            )

            # Analyze each service
            service_analysis = {}
            for service, metrics in service_metrics.items():
                avg_duration = metrics.get("avg_duration_ms", 0)
                success_rate = metrics.get("success_rate", 0)

                service_analysis[service] = {
                    **metrics,
                    "performance_status": self._get_performance_status(
                        avg_duration, success_rate
                    ),
                    "performance_grade": self._calculate_performance_grade(
                        avg_duration, success_rate
                    ),
                    "recommendations": self._get_service_recommendations(
                        avg_duration, success_rate
                    ),
                }

            return {
                "services": service_analysis,
                "slowest_operations": slowest_operations,
                "report_generated_at": datetime.now().isoformat(),
                "time_period_hours": hours,
            }

    def get_performance_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance alerts for issues detected in the specified time period."""
        with LatencyTracker("get_performance_alerts", "metrics_service"):
            alerts = []
            service_metrics = self.collector.get_service_metrics(hours=hours)

            for service, metrics in service_metrics.items():
                avg_duration = metrics.get("avg_duration_ms", 0)
                success_rate = metrics.get("success_rate", 0)
                total_requests = metrics.get("total_requests", 0)

                # Alert thresholds
                if avg_duration > 1000:  # > 1 second average
                    alerts.append(
                        {
                            "type": "high_latency",
                            "service": service,
                            "severity": "high" if avg_duration > 2000 else "medium",
                            "message": f"Service {service} has high average latency: {avg_duration:.2f}ms",
                            "metric": "avg_duration_ms",
                            "value": avg_duration,
                            "threshold": 1000,
                        }
                    )

                if success_rate < 95:  # < 95% success rate
                    alerts.append(
                        {
                            "type": "low_success_rate",
                            "service": service,
                            "severity": "high" if success_rate < 90 else "medium",
                            "message": f"Service {service} has low success rate: {success_rate:.2f}%",
                            "metric": "success_rate",
                            "value": success_rate,
                            "threshold": 95,
                        }
                    )

                if total_requests == 0:
                    alerts.append(
                        {
                            "type": "no_activity",
                            "service": service,
                            "severity": "low",
                            "message": f"Service {service} has no activity in the last {hours} hours",
                            "metric": "total_requests",
                            "value": 0,
                            "threshold": 1,
                        }
                    )

            return alerts

    def get_trend_analysis(self, days: int = 7) -> Dict[str, Any]:
        """Get trend analysis for the specified number of days."""
        with LatencyTracker("get_trend_analysis", "metrics_service"):
            trends = {}

            for day in range(days):
                date = datetime.now() - timedelta(days=day)
                hours = 24

                # Get metrics for each day
                summary = self.collector.get_metrics_summary(hours=hours)
                service_metrics = self.collector.get_service_metrics(hours=hours)

                trends[date.strftime("%Y-%m-%d")] = {
                    "summary": summary,
                    "services": service_metrics,
                }

            return {
                "trends": trends,
                "analysis_period_days": days,
                "generated_at": datetime.now().isoformat(),
            }

    def get_performance_recommendations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance improvement recommendations."""
        with LatencyTracker("get_performance_recommendations", "metrics_service"):
            recommendations = []
            service_metrics = self.collector.get_service_metrics(hours=hours)
            slowest_operations = self.collector.get_slowest_operations(
                limit=10, hours=hours
            )

            # Analyze slowest operations
            for operation in slowest_operations[:3]:  # Top 3 slowest
                if operation["duration_ms"] > 1000:
                    recommendations.append(
                        {
                            "type": "optimize_operation",
                            "priority": "high",
                            "title": f"Optimize {operation['operation']} in {operation['service']}",
                            "description": f"This operation takes {operation['duration_ms']:.2f}ms on average",
                            "suggestions": [
                                "Consider caching frequently accessed data",
                                "Optimize database queries",
                                "Implement async processing if applicable",
                                "Review external API calls",
                            ],
                        }
                    )

            # Analyze service performance
            for service, metrics in service_metrics.items():
                avg_duration = metrics.get("avg_duration_ms", 0)
                success_rate = metrics.get("success_rate", 0)

                if avg_duration > 500:
                    recommendations.append(
                        {
                            "type": "service_optimization",
                            "priority": "medium",
                            "title": f"Optimize {service} performance",
                            "description": f"Average response time is {avg_duration:.2f}ms",
                            "suggestions": [
                                "Review service architecture",
                                "Consider horizontal scaling",
                                "Optimize resource usage",
                                "Monitor external dependencies",
                            ],
                        }
                    )

                if success_rate < 98:
                    recommendations.append(
                        {
                            "type": "error_reduction",
                            "priority": "high" if success_rate < 95 else "medium",
                            "title": f"Reduce errors in {service}",
                            "description": f"Success rate is {success_rate:.2f}%",
                            "suggestions": [
                                "Review error logs",
                                "Implement better error handling",
                                "Add retry mechanisms",
                                "Monitor external service health",
                            ],
                        }
                    )

            return recommendations

    def _get_performance_status(self, avg_duration: float, success_rate: float) -> str:
        """Get performance status based on metrics."""
        if avg_duration > 1000 or success_rate < 95:
            return "poor"
        elif avg_duration > 500 or success_rate < 98:
            return "fair"
        elif avg_duration > 200 or success_rate < 99:
            return "good"
        else:
            return "excellent"

    def _calculate_performance_grade(
        self, avg_duration: float, success_rate: float
    ) -> str:
        """Calculate performance grade (A-F)."""
        if avg_duration <= 200 and success_rate >= 99:
            return "A"
        elif avg_duration <= 500 and success_rate >= 98:
            return "B"
        elif avg_duration <= 1000 and success_rate >= 95:
            return "C"
        elif avg_duration <= 2000 and success_rate >= 90:
            return "D"
        else:
            return "F"

    def _get_service_recommendations(
        self, avg_duration: float, success_rate: float
    ) -> List[str]:
        """Get specific recommendations for a service."""
        recommendations = []

        if avg_duration > 1000:
            recommendations.append("Consider performance optimization")
        if avg_duration > 500:
            recommendations.append("Monitor response times closely")
        if success_rate < 95:
            recommendations.append("Investigate error patterns")
        if success_rate < 98:
            recommendations.append("Review error handling")

        return recommendations
