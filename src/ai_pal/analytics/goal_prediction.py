"""
Goal Completion Prediction Module

Predicts goal completion probability and estimated time-to-completion
based on historical progress patterns.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math


class GoalPredictor:
    """Predictor for goal completion and achievement metrics"""

    @staticmethod
    def calculate_completion_probability(
        current_progress: float,
        time_elapsed_days: float,
        deadline_days_remaining: float,
        historical_completion_rate: float = 0.7,
    ) -> Dict:
        """
        Calculate probability of goal completion.

        Args:
            current_progress: Current progress percentage (0-100)
            time_elapsed_days: Days elapsed since goal creation
            deadline_days_remaining: Days until deadline
            historical_completion_rate: Historical completion rate for similar goals

        Returns:
            Dict with completion probability and estimate
        """
        if current_progress >= 100:
            return {
                "completion_probability": 1.0,
                "estimated_days_remaining": 0,
                "risk_level": "none",
                "recommendation": "Goal is already completed",
            }

        if time_elapsed_days == 0:
            # New goal - use historical rate
            return {
                "completion_probability": historical_completion_rate,
                "estimated_days_remaining": deadline_days_remaining,
                "risk_level": "medium",
                "recommendation": "Monitor progress closely",
            }

        # Calculate current progress rate
        progress_per_day = current_progress / time_elapsed_days
        days_to_complete_at_current_rate = (100 - current_progress) / progress_per_day

        # Adjust estimate based on remaining time
        if deadline_days_remaining <= 0:
            # Overdue
            return {
                "completion_probability": 0.1,
                "estimated_days_remaining": 0,
                "risk_level": "critical",
                "recommendation": "Goal is overdue. Consider extending deadline or increasing effort.",
            }

        # Probability calculation
        if days_to_complete_at_current_rate <= deadline_days_remaining:
            # Likely to complete
            completion_probability = 0.8 + (0.2 * (deadline_days_remaining / (days_to_complete_at_current_rate + 1)))
        else:
            # May not complete
            completion_probability = 0.2 + (0.6 * (deadline_days_remaining / (days_to_complete_at_current_rate + 1)))

        # Clamp to 0-1
        completion_probability = max(0.0, min(1.0, completion_probability))

        # Risk level assessment
        if completion_probability >= 0.8:
            risk_level = "low"
            recommendation = "Goal is on track. Maintain current pace."
        elif completion_probability >= 0.5:
            risk_level = "medium"
            recommendation = "Consider increasing effort to improve completion chance."
        else:
            risk_level = "high"
            recommendation = "Goal completion at risk. Significant action needed."

        return {
            "completion_probability": round(completion_probability, 2),
            "estimated_days_remaining": max(0, round(days_to_complete_at_current_rate, 1)),
            "deadline_days_remaining": round(deadline_days_remaining, 1),
            "risk_level": risk_level,
            "recommendation": recommendation,
        }

    @staticmethod
    def estimate_completion_date(
        current_progress: float,
        time_elapsed_days: float,
        goal_created_date: str,
        deadline: Optional[str] = None,
    ) -> Dict:
        """
        Estimate when goal will be completed.

        Args:
            current_progress: Current progress percentage
            time_elapsed_days: Days elapsed
            goal_created_date: ISO format creation date
            deadline: ISO format deadline (optional)

        Returns:
            Dict with estimated completion date
        """
        if current_progress >= 100:
            return {
                "status": "completed",
                "estimated_completion_date": None,
                "days_to_completion": 0,
            }

        if time_elapsed_days == 0:
            # Can't estimate without progress
            return {
                "status": "insufficient_data",
                "estimated_completion_date": None,
                "days_to_completion": None,
                "message": "Goal was just created. Complete some progress first.",
            }

        # Calculate based on current pace
        progress_per_day = current_progress / time_elapsed_days
        remaining_progress = 100 - current_progress

        if progress_per_day <= 0:
            return {
                "status": "no_progress",
                "estimated_completion_date": None,
                "days_to_completion": None,
                "message": "No progress detected. Set a deadline to establish pace.",
            }

        days_to_completion = remaining_progress / progress_per_day

        # Calculate estimated date
        try:
            created = datetime.fromisoformat(goal_created_date.replace("Z", "+00:00"))
            estimated_date = created + timedelta(days=time_elapsed_days + days_to_completion)

            # Check against deadline
            status = "on_track"
            if deadline:
                deadline_date = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
                if estimated_date > deadline_date:
                    status = "at_risk"

            return {
                "status": status,
                "estimated_completion_date": estimated_date.isoformat(),
                "days_to_completion": round(days_to_completion, 1),
            }
        except (ValueError, AttributeError):
            return {
                "status": "error",
                "estimated_completion_date": None,
                "days_to_completion": None,
                "message": "Invalid date format",
            }

    @staticmethod
    def calculate_success_rate_by_complexity(
        completed_goals_by_complexity: Dict[str, int],
        total_goals_by_complexity: Dict[str, int],
    ) -> Dict[str, float]:
        """
        Calculate success rate for each complexity level.

        Args:
            completed_goals_by_complexity: Dict with counts by complexity (easy, medium, hard)
            total_goals_by_complexity: Dict with total counts by complexity

        Returns:
            Dict with success rates (0-1) for each complexity level
        """
        success_rates = {}

        for complexity in ["easy", "medium", "hard"]:
            total = total_goals_by_complexity.get(complexity, 0)
            completed = completed_goals_by_complexity.get(complexity, 0)

            if total == 0:
                success_rates[complexity] = 0.0
            else:
                success_rates[complexity] = completed / total

        return success_rates

    @staticmethod
    def predict_goal_outcome(
        goal: Dict,
        historical_completion_rate: float = 0.7,
    ) -> Dict:
        """
        Comprehensive goal outcome prediction.

        Args:
            goal: Goal dictionary with status, progress, dates, etc.
            historical_completion_rate: Historical completion rate

        Returns:
            Dict with complete prediction analysis
        """
        status = goal.get("status", "unknown")

        if status == "completed":
            return {
                "prediction": "completed",
                "confidence": 1.0,
                "recommendation": "Goal successfully completed",
            }

        # Calculate elapsed time
        created_str = goal.get("created_at")
        if not created_str:
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "recommendation": "Missing creation date",
            }

        try:
            created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            time_elapsed = (datetime.utcnow() - created).total_seconds() / (
                24 * 3600
            )
        except (ValueError, AttributeError):
            time_elapsed = 0

        # Calculate deadline remaining
        deadline_str = goal.get("deadline")
        deadline_remaining = float("inf")

        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
                deadline_remaining = (
                    deadline - datetime.utcnow()
                ).total_seconds() / (24 * 3600)
            except (ValueError, AttributeError):
                pass

        progress = float(goal.get("progress", 0))

        # Get completion probability
        prob_result = GoalPredictor.calculate_completion_probability(
            progress,
            time_elapsed,
            deadline_remaining,
            historical_completion_rate,
        )

        # Get completion date estimate
        date_result = GoalPredictor.estimate_completion_date(
            progress,
            time_elapsed,
            created_str,
            deadline_str,
        )

        return {
            "prediction": "will_complete"
            if prob_result["completion_probability"] > 0.7
            else "at_risk"
            if prob_result["completion_probability"] > 0.3
            else "unlikely",
            "completion_probability": prob_result["completion_probability"],
            "estimated_completion_date": date_result.get("estimated_completion_date"),
            "days_to_completion": date_result.get("days_to_completion"),
            "risk_level": prob_result["risk_level"],
            "recommendation": prob_result["recommendation"],
            "deadline_days_remaining": prob_result.get("deadline_days_remaining"),
        }
