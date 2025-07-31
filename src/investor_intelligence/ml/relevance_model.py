from datetime import datetime
from typing import List, Dict, Optional


class RelevanceModel:
    """A machine learning model to assess alert relevance with feedback-based training."""

    def __init__(self):
        # In a real implementation, load a pre-trained model here
        self.feedback_data = []
        self.model_performance = {
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "last_updated": None,
        }

    def predict_relevance(
        self, alert: dict, user_preferences: dict, portfolio_context: dict
    ) -> float:
        """Predicts a relevance score for a given alert based on alert data, user preferences, and portfolio context.

        Args:
            alert (dict): A dictionary representing the alert (e.g., {"type": "price_gain", "symbol": "AAPL", "change": 2.5, "sentiment": "positive"}).
            user_preferences (dict): User-specific preferences (e.g., {"min_price_change_alert": 1.0, "risk_profile": "moderate"}).
            portfolio_context (dict): Context about the user's portfolio (e.g., {"holding_quantity": 100, "portfolio_value": 10000}).

        Returns:
            float: A relevance score between 0 and 1.
        """
        score = 0.5  # Base score

        # Factor 1: Alert Type and Magnitude
        if alert["type"] in ["price_gain", "price_drop"]:
            change_percent = alert.get("change", 0)
            min_change_pref = user_preferences.get("min_price_change_alert", 0.0)
            if abs(change_percent) >= min_change_pref:
                score += 0.2 * (
                    abs(change_percent) / 5.0
                )  # Scale by magnitude, max 5% for full score
            else:
                score -= 0.1  # Less relevant if below user's preferred threshold

        elif alert["type"] == "news_sentiment":
            sentiment = alert.get("sentiment", "neutral")
            if sentiment == "positive":
                score += 0.15
            elif sentiment == "negative":
                score += 0.15
            # Consider if news is about a held stock
            if alert.get("symbol") in portfolio_context.get("symbols_held", []):
                score += 0.1

        elif alert["type"] == "earnings_report":
            # Earnings reports are generally highly relevant for held stocks
            if alert.get("symbol") in portfolio_context.get("symbols_held", []):
                score += 0.2

        # Factor 2: User Preferences (beyond direct filtering)
        risk_profile = user_preferences.get("risk_profile", "moderate")
        if risk_profile == "conservative" and alert["type"] == "price_drop":
            score += 0.1  # More relevant for conservative users
        elif risk_profile == "aggressive" and alert["type"] == "price_gain":
            score += 0.1  # More relevant for aggressive users

        # Factor 3: Portfolio Context
        # Alerts for larger holdings might be more relevant
        if alert.get("symbol") in portfolio_context.get("holding_quantities", {}):
            quantity = portfolio_context["holding_quantities"][alert["symbol"]]
            if quantity > 50:  # Arbitrary threshold for significant holding
                score += 0.05

        return min(1.0, max(0.0, score))  # Ensure score is between 0 and 1

    def train_with_feedback(self, training_data: List[Dict]) -> Dict:
        """Train the model using user feedback data.

        Args:
            training_data: List of dictionaries containing alert data and user feedback

        Returns:
            Dict containing training results and model performance metrics
        """
        if not training_data:
            return {
                "status": "no_data",
                "message": "No training data provided",
                "performance": self.model_performance,
            }

        # Extract features and labels from feedback data
        features = []
        labels = []

        for alert_data in training_data:
            # Extract alert features
            alert_features = self._extract_features(alert_data)

            # Calculate ground truth label from user feedback
            ground_truth = self._calculate_ground_truth(alert_data.get("feedback", []))

            if ground_truth is not None:
                features.append(alert_features)
                labels.append(ground_truth)

        if not features:
            return {
                "status": "no_valid_data",
                "message": "No valid training examples found",
                "performance": self.model_performance,
            }

        # In a real implementation, this would train a machine learning model
        # For now, we'll update the model parameters based on feedback patterns
        self._update_model_parameters(features, labels)

        # Calculate performance metrics
        performance = self._calculate_performance_metrics(features, labels)
        self.model_performance.update(performance)
        self.model_performance["last_updated"] = datetime.now().isoformat()

        return {
            "status": "success",
            "message": f"Trained on {len(features)} examples",
            "performance": self.model_performance,
            "training_samples": len(features),
        }

    def _extract_features(self, alert_data: Dict) -> Dict:
        """Extract features from alert data for training."""
        features = {
            "alert_type": alert_data.get("alert_type", ""),
            "symbol": alert_data.get("symbol", ""),
            "has_symbol": 1 if alert_data.get("symbol") else 0,
            "message_length": len(alert_data.get("message", "")),
            "predicted_relevance": alert_data.get("predicted_relevance", 0.5),
        }

        # Extract text-based features
        message = alert_data.get("message", "").lower()
        features.update(
            {
                "contains_percent": 1 if "%" in message else 0,
                "contains_price": (
                    1
                    if any(word in message for word in ["price", "stock", "share"])
                    else 0
                ),
                "contains_earnings": 1 if "earnings" in message else 0,
                "contains_news": 1 if "news" in message else 0,
                "contains_alert": 1 if "alert" in message else 0,
            }
        )

        return features

    def _calculate_ground_truth(self, feedback_list: List[Dict]) -> Optional[float]:
        """Calculate ground truth relevance score from user feedback."""
        if not feedback_list:
            return None

        # Weight different types of feedback
        total_score = 0.0
        total_weight = 0.0

        for feedback in feedback_list:
            feedback_type = feedback.get("type", "")

            if feedback_type == "rating":
                rating = feedback.get("rating", 3)
                # Convert 1-5 rating to 0-1 scale
                score = (rating - 1) / 4.0
                weight = 2.0  # High weight for explicit ratings

            elif feedback_type == "mark_relevant":
                score = 1.0
                weight = 1.5

            elif feedback_type == "mark_irrelevant":
                score = 0.0
                weight = 1.5

            elif feedback_type == "click":
                score = 0.8  # Click indicates interest
                weight = 1.0

            elif feedback_type == "view":
                score = 0.5  # View is neutral
                weight = 0.5

            elif feedback_type == "dismiss":
                score = 0.2  # Dismiss indicates low relevance
                weight = 1.0

            else:
                continue

            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return None

        return total_score / total_weight

    def _update_model_parameters(self, features: List[Dict], labels: List[float]):
        """Update model parameters based on training data.

        In a real implementation, this would update the actual model weights.
        For now, we'll store the feedback data for analysis.
        """
        self.feedback_data = list(zip(features, labels))

        # Analyze feedback patterns to adjust prediction logic
        self._analyze_feedback_patterns(features, labels)

    def _analyze_feedback_patterns(self, features: List[Dict], labels: List[float]):
        """Analyze feedback patterns to improve prediction logic."""
        # Group by alert type and analyze relevance patterns
        alert_type_relevance = {}

        for feature, label in zip(features, labels):
            alert_type = feature.get("alert_type", "")
            if alert_type not in alert_type_relevance:
                alert_type_relevance[alert_type] = []
            alert_type_relevance[alert_type].append(label)

        # Calculate average relevance by alert type
        for alert_type, relevances in alert_type_relevance.items():
            avg_relevance = sum(relevances) / len(relevances)
            print(f"Alert type '{alert_type}' average relevance: {avg_relevance:.3f}")

    def _calculate_performance_metrics(
        self, features: List[Dict], labels: List[float]
    ) -> Dict:
        """Calculate model performance metrics."""
        if not features or not labels:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}

        # Calculate predictions using current model
        predictions = []
        for feature in features:
            # Create a mock alert dict for prediction
            alert_dict = {
                "type": feature.get("alert_type", ""),
                "symbol": feature.get("symbol", ""),
                "message": "mock message",  # We don't have the original message
            }

            # Mock user preferences and portfolio context
            user_preferences = {
                "min_price_change_alert": 1.0,
                "risk_profile": "moderate",
            }
            portfolio_context = {
                "symbols_held": [],
                "holding_quantities": {},
                "portfolio_value": 10000,
            }

            pred = self.predict_relevance(
                alert_dict, user_preferences, portfolio_context
            )
            predictions.append(pred)

        # Calculate metrics (simplified)
        correct_predictions = 0
        for pred, label in zip(predictions, labels):
            # Consider prediction correct if within 0.2 of ground truth
            if abs(pred - label) <= 0.2:
                correct_predictions += 1

        accuracy = correct_predictions / len(predictions) if predictions else 0.0

        return {
            "accuracy": accuracy,
            "precision": accuracy,  # Simplified
            "recall": accuracy,  # Simplified
            "f1_score": accuracy,  # Simplified
        }

    def get_model_performance(self) -> Dict:
        """Get current model performance metrics."""
        return self.model_performance.copy()

    def get_feedback_insights(self) -> Dict:
        """Get insights from collected feedback data."""
        if not self.feedback_data:
            return {"message": "No feedback data available"}

        total_samples = len(self.feedback_data)
        avg_relevance = sum(label for _, label in self.feedback_data) / total_samples

        # Analyze by alert type
        alert_type_stats = {}
        for features, label in self.feedback_data:
            alert_type = features.get("alert_type", "unknown")
            if alert_type not in alert_type_stats:
                alert_type_stats[alert_type] = {"count": 0, "total_relevance": 0.0}

            alert_type_stats[alert_type]["count"] += 1
            alert_type_stats[alert_type]["total_relevance"] += label

        # Calculate averages
        for alert_type, stats in alert_type_stats.items():
            stats["avg_relevance"] = stats["total_relevance"] / stats["count"]

        return {
            "total_samples": total_samples,
            "average_relevance": avg_relevance,
            "alert_type_statistics": alert_type_stats,
            "last_updated": self.model_performance.get("last_updated"),
        }
