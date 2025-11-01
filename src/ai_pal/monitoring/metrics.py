"""
Prometheus metrics for AI-PAL.

Provides comprehensive metrics collection for monitoring:
- Request metrics (latency, throughput, errors)
- Gate metrics (pass/fail rates, scores)
- ARI metrics (scores, trends)
- FFE metrics (goal completion, momentum states)
- Model metrics (usage, costs, latency)
- System metrics (resource usage)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import time
import threading


@dataclass
class MetricValue:
    """A single metric value"""

    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metric_type: str = "gauge"  # counter, gauge, histogram, summary


class MetricsCollector:
    """
    Prometheus-compatible metrics collector.

    Collects metrics and exports them in Prometheus format.
    """

    def __init__(self):
        """Initialize metrics collector"""
        # Counters (monotonically increasing)
        self._counters: Dict[str, float] = defaultdict(float)

        # Gauges (can go up and down)
        self._gauges: Dict[str, float] = {}

        # Histograms (distributions)
        self._histograms: Dict[str, List[float]] = defaultdict(list)

        # Labels for metrics
        self._labels: Dict[str, Dict[str, str]] = {}

        # Lock for thread safety
        self._lock = threading.Lock()

        # Histogram buckets (in seconds for latency)
        self.latency_buckets = [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
        ]

    # Counter methods

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ):
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Amount to increment
            labels: Optional labels
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            if labels:
                self._labels[key] = labels

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        with self._lock:
            key = self._make_key(name, labels)
            return self._counters.get(key, 0.0)

    # Gauge methods

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Set a gauge metric.

        Args:
            name: Metric name
            value: Current value
            labels: Optional labels
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        with self._lock:
            key = self._make_key(name, labels)
            return self._gauges.get(key, 0.0)

    # Histogram methods

    def observe_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ):
        """
        Observe a histogram value.

        Args:
            name: Metric name
            value: Observed value
            labels: Optional labels
        """
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            if labels:
                self._labels[key] = labels

    def get_histogram(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> List[float]:
        """Get histogram values"""
        with self._lock:
            key = self._make_key(name, labels)
            return self._histograms.get(key, []).copy()

    # Helper methods

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key from name and labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    # High-level recording methods

    def record_request(
        self,
        endpoint: str,
        method: str = "POST",
        status_code: int = 200,
        latency_seconds: float = 0.0,
        model_used: Optional[str] = None,
    ):
        """
        Record an API request.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            latency_seconds: Request latency in seconds
            model_used: Optional model name
        """
        labels = {
            "endpoint": endpoint,
            "method": method,
            "status": str(status_code),
        }

        if model_used:
            labels["model"] = model_used

        # Increment request counter
        self.increment_counter("ai_pal_requests_total", labels=labels)

        # Record latency
        self.observe_histogram("ai_pal_request_duration_seconds", latency_seconds, labels)

        # Track errors
        if status_code >= 400:
            error_labels = {
                "endpoint": endpoint,
                "status": str(status_code),
            }
            self.increment_counter("ai_pal_request_errors_total", labels=error_labels)

    def record_gate_result(
        self, gate_name: str, passed: bool, score: float, user_id: Optional[str] = None
    ):
        """
        Record Four Gates validation result.

        Args:
            gate_name: Gate name (gate1_net_agency, etc.)
            passed: Whether gate passed
            score: Gate score (0-1)
            user_id: Optional user ID
        """
        labels = {
            "gate": gate_name,
            "result": "passed" if passed else "failed",
        }

        # Count gate results
        self.increment_counter("ai_pal_gate_checks_total", labels=labels)

        # Record gate score
        score_labels = {"gate": gate_name}
        self.set_gauge(f"ai_pal_gate_score", score, labels=score_labels)

        # Track gate failures
        if not passed:
            self.increment_counter(
                "ai_pal_gate_failures_total", labels={"gate": gate_name}
            )

    def record_ari_update(
        self, user_id: str, ari_score: float, trend: str, skill_category: Optional[str] = None
    ):
        """
        Record ARI (Agency Retention Index) update.

        Args:
            user_id: User identifier
            ari_score: Current ARI score (0-1)
            trend: Trend (improving, stable, declining)
            skill_category: Optional skill category
        """
        labels = {"user_id": user_id}

        if skill_category:
            labels["skill"] = skill_category

        # Set current ARI score
        self.set_gauge("ai_pal_ari_score", ari_score, labels)

        # Track trend
        trend_labels = {"user_id": user_id, "trend": trend}
        self.increment_counter("ai_pal_ari_updates_total", labels=trend_labels)

        # Alert on decline
        if trend == "declining":
            self.increment_counter(
                "ai_pal_ari_declines_total", labels={"user_id": user_id}
            )

    def record_edm_analysis(
        self, debt_score: float, flagged_claims: int, requires_review: bool
    ):
        """
        Record EDM (Epistemic Debt Management) analysis.

        Args:
            debt_score: Epistemic debt score (0-1)
            flagged_claims: Number of flagged claims
            requires_review: Whether human review is needed
        """
        # Set debt score
        self.set_gauge("ai_pal_edm_debt_score", debt_score)

        # Count flagged claims
        self.set_gauge("ai_pal_edm_flagged_claims", float(flagged_claims))

        # Track reviews needed
        if requires_review:
            self.increment_counter("ai_pal_edm_reviews_required_total")

    def record_ffe_goal(
        self,
        user_id: str,
        goal_id: str,
        status: str,
        clarity_score: float,
        completion_percentage: float = 0.0,
    ):
        """
        Record FFE (Fractal Flow Engine) goal metrics.

        Args:
            user_id: User identifier
            goal_id: Goal identifier
            status: Goal status (active, completed, abandoned)
            clarity_score: Goal clarity (0-1)
            completion_percentage: Completion percentage (0-100)
        """
        labels = {
            "user_id": user_id,
            "goal_id": goal_id,
            "status": status,
        }

        # Track goal count by status
        status_labels = {"status": status}
        self.increment_counter("ai_pal_ffe_goals_total", labels=status_labels)

        # Set clarity score
        self.set_gauge("ai_pal_ffe_goal_clarity", clarity_score, labels)

        # Set completion percentage
        self.set_gauge("ai_pal_ffe_goal_completion", completion_percentage, labels)

    def record_ffe_momentum(
        self, user_id: str, goal_id: str, state: str, score: float
    ):
        """
        Record FFE momentum state.

        Args:
            user_id: User identifier
            goal_id: Goal identifier
            state: Momentum state (friction, flow, win, pride)
            score: Momentum score (0-1)
        """
        labels = {
            "user_id": user_id,
            "goal_id": goal_id,
            "state": state,
        }

        # Track momentum state transitions
        self.increment_counter("ai_pal_ffe_momentum_transitions_total", labels)

        # Set current momentum score
        score_labels = {"user_id": user_id, "goal_id": goal_id}
        self.set_gauge("ai_pal_ffe_momentum_score", score, labels=score_labels)

    def record_model_usage(
        self,
        model_name: str,
        provider: str,
        tokens_used: int,
        cost_usd: float,
        latency_seconds: float,
        success: bool = True,
    ):
        """
        Record model usage metrics.

        Args:
            model_name: Model name
            provider: Provider (anthropic, openai, local)
            tokens_used: Number of tokens
            cost_usd: Cost in USD
            latency_seconds: Latency in seconds
            success: Whether call succeeded
        """
        labels = {
            "model": model_name,
            "provider": provider,
            "success": str(success),
        }

        # Count model calls
        self.increment_counter("ai_pal_model_calls_total", labels=labels)

        # Sum tokens
        self.increment_counter(
            "ai_pal_model_tokens_total",
            value=float(tokens_used),
            labels={"model": model_name, "provider": provider},
        )

        # Sum costs
        self.increment_counter(
            "ai_pal_model_cost_usd_total",
            value=cost_usd,
            labels={"model": model_name, "provider": provider},
        )

        # Record latency
        latency_labels = {"model": model_name, "provider": provider}
        self.observe_histogram(
            "ai_pal_model_latency_seconds", latency_seconds, latency_labels
        )

    def record_plugin_execution(
        self, plugin_id: str, success: bool, execution_time_seconds: float
    ):
        """
        Record plugin execution metrics.

        Args:
            plugin_id: Plugin identifier
            success: Whether execution succeeded
            execution_time_seconds: Execution time
        """
        labels = {
            "plugin": plugin_id,
            "success": str(success),
        }

        # Count executions
        self.increment_counter("ai_pal_plugin_executions_total", labels=labels)

        # Record execution time
        self.observe_histogram(
            "ai_pal_plugin_execution_seconds",
            execution_time_seconds,
            labels={"plugin": plugin_id},
        )

    def record_system_resource(
        self, resource_type: str, value: float, unit: str = ""
    ):
        """
        Record system resource usage.

        Args:
            resource_type: Resource type (cpu, memory, disk, etc.)
            value: Current value
            unit: Optional unit
        """
        labels = {"resource": resource_type}
        if unit:
            labels["unit"] = unit

        self.set_gauge("ai_pal_system_resources", value, labels)

    # Export methods

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics
        """
        lines = []
        lines.append("# AI-PAL Metrics")
        lines.append(f"# Generated at {datetime.utcnow().isoformat()}Z")
        lines.append("")

        with self._lock:
            # Export counters
            for key, value in sorted(self._counters.items()):
                metric_name = key.split("{")[0]
                labels_str = ""
                if key in self._labels:
                    label_items = [
                        f'{k}="{v}"' for k, v in self._labels[key].items()
                    ]
                    labels_str = "{" + ",".join(label_items) + "}"

                lines.append(f"# TYPE {metric_name} counter")
                lines.append(f"{metric_name}{labels_str} {value}")
                lines.append("")

            # Export gauges
            for key, value in sorted(self._gauges.items()):
                metric_name = key.split("{")[0]
                labels_str = ""
                if key in self._labels:
                    label_items = [
                        f'{k}="{v}"' for k, v in self._labels[key].items()
                    ]
                    labels_str = "{" + ",".join(label_items) + "}"

                lines.append(f"# TYPE {metric_name} gauge")
                lines.append(f"{metric_name}{labels_str} {value}")
                lines.append("")

            # Export histograms
            for key, values in sorted(self._histograms.items()):
                if not values:
                    continue

                metric_name = key.split("{")[0]
                labels_str = ""
                if key in self._labels:
                    label_items = [
                        f'{k}="{v}"' for k, v in self._labels[key].items()
                    ]
                    labels_str = "{" + ",".join(label_items) + "}"

                lines.append(f"# TYPE {metric_name} histogram")

                # Calculate histogram buckets
                sorted_values = sorted(values)
                for bucket in self.latency_buckets:
                    count = sum(1 for v in sorted_values if v <= bucket)
                    bucket_labels = labels_str.rstrip("}") + f',le="{bucket}"' + "}"
                    lines.append(f"{metric_name}_bucket{bucket_labels} {count}")

                # +Inf bucket
                inf_labels = labels_str.rstrip("}") + ',le="+Inf"}'
                lines.append(f"{metric_name}_bucket{inf_labels} {len(values)}")

                # Sum and count
                total = sum(values)
                lines.append(f"{metric_name}_sum{labels_str} {total}")
                lines.append(f"{metric_name}_count{labels_str} {len(values)}")
                lines.append("")

        return "\n".join(lines)

    def export_json(self) -> Dict[str, Any]:
        """
        Export metrics as JSON.

        Returns:
            Dictionary of metrics
        """
        with self._lock:
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: {"values": v, "count": len(v), "sum": sum(v)}
                    for k, v in self._histograms.items()
                },
            }

    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._labels.clear()


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """
    Get global metrics collector (singleton).

    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# Context manager for timing
class Timer:
    """Context manager for timing operations"""

    def __init__(self, callback):
        """
        Initialize timer.

        Args:
            callback: Function to call with elapsed time (in seconds)
        """
        self.callback = callback
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *args):
        elapsed = time.time() - self.start_time
        self.callback(elapsed)


# Example usage
if __name__ == "__main__":
    metrics = get_metrics()

    # Record request
    metrics.record_request(
        endpoint="/api/chat",
        method="POST",
        status_code=200,
        latency_seconds=0.25,
        model_used="claude-3-5-sonnet",
    )

    # Record gate result
    metrics.record_gate_result(
        gate_name="gate1_net_agency", passed=True, score=0.85
    )

    # Record ARI update
    metrics.record_ari_update(
        user_id="user-123",
        ari_score=0.75,
        trend="improving",
        skill_category="python_programming",
    )

    # Time an operation
    def record_latency(seconds):
        metrics.observe_histogram("operation_duration", seconds)

    with Timer(record_latency):
        time.sleep(0.1)  # Simulate operation

    # Export metrics
    print(metrics.export_prometheus())
