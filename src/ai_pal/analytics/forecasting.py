"""
ARI Trend Forecasting Module

Implements linear regression-based forecasting for ARI scores and other metrics.
Uses numpy for calculations without heavy ML library dependencies.
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import math


class TimeSeriesForecaster:
    """Simple linear regression forecaster for time series data"""

    @staticmethod
    def linear_regression(
        x_values: List[float], y_values: List[float]
    ) -> Tuple[float, float]:
        """
        Calculate linear regression coefficients (slope, intercept).

        Args:
            x_values: Independent variable values
            y_values: Dependent variable values

        Returns:
            Tuple of (slope, intercept)
        """
        if len(x_values) < 2:
            return 0.0, y_values[0] if y_values else 0.0

        n = len(x_values)
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n

        numerator = sum(
            (x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n)
        )
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return 0.0, y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        return slope, intercept

    @staticmethod
    def calculate_r_squared(
        x_values: List[float], y_values: List[float], slope: float, intercept: float
    ) -> float:
        """
        Calculate R-squared (coefficient of determination).

        Args:
            x_values: Independent variable values
            y_values: Observed values
            slope: Regression slope
            intercept: Regression intercept

        Returns:
            R-squared value (0-1)
        """
        if not y_values:
            return 0.0

        n = len(y_values)
        y_mean = sum(y_values) / n

        # Sum of squares of residuals
        ss_res = sum(
            (y_values[i] - (slope * x_values[i] + intercept)) ** 2 for i in range(n)
        )

        # Total sum of squares
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)

        if ss_tot == 0:
            return 1.0 if ss_res == 0 else 0.0

        return 1 - (ss_res / ss_tot)

    @staticmethod
    def forecast(
        slope: float, intercept: float, x_value: float
    ) -> float:
        """Predict y value for given x using linear regression."""
        return slope * x_value + intercept

    @staticmethod
    def calculate_confidence_interval(
        x_values: List[float],
        y_values: List[float],
        slope: float,
        intercept: float,
        x_predict: float,
        confidence_level: float = 0.95,
    ) -> Tuple[float, float, float]:
        """
        Calculate forecast with confidence interval.

        Args:
            x_values: Historical x values
            y_values: Historical y values
            slope: Regression slope
            intercept: Regression intercept
            x_predict: X value to predict for
            confidence_level: Confidence level (0.95 = 95%)

        Returns:
            Tuple of (predicted_value, lower_bound, upper_bound)
        """
        if len(x_values) < 2:
            predicted = slope * x_predict + intercept
            margin = predicted * 0.15  # ±15% by default
            return predicted, predicted - margin, predicted + margin

        n = len(x_values)
        x_mean = sum(x_values) / n

        # Calculate standard error
        y_predicted = [slope * x + intercept for x in x_values]
        residuals = [y_values[i] - y_predicted[i] for i in range(n)]
        ss_res = sum(r**2 for r in residuals)

        if n <= 2:
            std_error = 0
        else:
            std_error = math.sqrt(ss_res / (n - 2))

        # Forecast
        predicted = slope * x_predict + intercept

        # Calculate margin of error
        x_deviation = (x_predict - x_mean) ** 2
        x_sum_sq = sum((x - x_mean) ** 2 for x in x_values)

        if x_sum_sq == 0:
            margin = predicted * 0.15
        else:
            # t-statistic approximation (using 2 for 95% confidence with large samples)
            t_stat = 1.96
            margin = t_stat * std_error * math.sqrt(
                1 + (1 / n) + (x_deviation / x_sum_sq)
            )

        lower_bound = max(0, predicted - margin)
        upper_bound = predicted + margin

        return predicted, lower_bound, upper_bound


class ARIForecaster:
    """Specialized forecaster for ARI (Agency Retention Index) metrics"""

    @staticmethod
    def forecast_ari_trend(
        ari_history: List[Dict],
        days_ahead: int = 7,
        min_data_points: int = 3,
    ) -> Dict:
        """
        Forecast ARI score trend.

        Args:
            ari_history: List of ARI snapshot dicts with 'timestamp' and 'autonomy_retention'
            days_ahead: Number of days to forecast
            min_data_points: Minimum data points required for forecasting

        Returns:
            Dict with forecasted score, trend, and confidence
        """
        if not ari_history or len(ari_history) < min_data_points:
            return {
                "can_forecast": False,
                "message": f"Need at least {min_data_points} data points",
                "predicted_score": None,
                "confidence": 0.0,
                "trend": "unknown",
            }

        # Extract data points
        scores = []
        timestamps = []

        for snapshot in sorted(
            ari_history, key=lambda x: x.get("timestamp", "")
        ):
            try:
                score = float(snapshot.get("autonomy_retention", 0))
                ts = snapshot.get("timestamp", "")
                scores.append(score)
                timestamps.append(ts)
            except (ValueError, TypeError):
                continue

        if len(scores) < min_data_points:
            return {
                "can_forecast": False,
                "message": f"Insufficient valid data points",
                "predicted_score": None,
                "confidence": 0.0,
                "trend": "unknown",
            }

        # Create x values (days from start)
        x_values = list(range(len(scores)))

        # Fit linear regression
        slope, intercept = TimeSeriesForecaster.linear_regression(x_values, scores)

        # Calculate R-squared (confidence)
        r_squared = TimeSeriesForecaster.calculate_r_squared(
            x_values, scores, slope, intercept
        )

        # Forecast
        x_forecast = len(scores) - 1 + days_ahead
        predicted, lower, upper = TimeSeriesForecaster.calculate_confidence_interval(
            x_values, scores, slope, intercept, x_forecast
        )

        # Determine trend
        if slope > 2:
            trend = "improving"
        elif slope < -2:
            trend = "declining"
        else:
            trend = "stable"

        # Ensure bounds
        predicted = max(0, min(100, predicted))
        lower = max(0, min(100, lower))
        upper = max(0, min(100, upper))

        return {
            "can_forecast": True,
            "predicted_score": round(predicted, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "confidence": round(max(0, min(1, r_squared)), 2),
            "trend": trend,
            "slope": round(slope, 4),
            "days_ahead": days_ahead,
            "data_points_used": len(scores),
        }

    @staticmethod
    def detect_ari_anomaly(
        current_score: float, previous_scores: List[float], threshold: float = 10.0
    ) -> Dict:
        """
        Detect if current ARI score is an anomaly.

        Args:
            current_score: Current ARI score
            previous_scores: List of previous scores
            threshold: Change threshold in points

        Returns:
            Dict with anomaly detection result
        """
        if not previous_scores:
            return {
                "is_anomaly": False,
                "reason": "No previous data",
                "change": 0,
            }

        average = sum(previous_scores) / len(previous_scores)
        change = current_score - average
        is_anomaly = abs(change) > threshold

        return {
            "is_anomaly": is_anomaly,
            "change": round(change, 2),
            "average": round(average, 2),
            "threshold": threshold,
            "severity": (
                "high" if abs(change) > threshold * 1.5
                else "medium" if abs(change) > threshold
                else "low"
            ),
        }
