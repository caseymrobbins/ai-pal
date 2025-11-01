"""
OpenTelemetry distributed tracing for AI-PAL.

Provides end-to-end request tracing across all components.
"""

from typing import Dict, Optional, Any, Callable
from contextlib import contextmanager
from datetime import datetime
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Span:
    """A single trace span"""

    span_id: str
    trace_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: list = field(default_factory=list)
    status: str = "ok"  # ok, error

    def finish(self):
        """Finish the span"""
        if not self.end_time:
            self.end_time = datetime.utcnow()
            start_ts = self.start_time.timestamp()
            end_ts = self.end_time.timestamp()
            self.duration_ms = (end_ts - start_ts) * 1000

    def set_tag(self, key: str, value: Any):
        """Set a tag on the span"""
        self.tags[key] = value

    def log(self, message: str, **kwargs):
        """Add a log entry to the span"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message,
            **kwargs,
        }
        self.logs.append(log_entry)

    def set_error(self, error: Exception):
        """Mark span as error"""
        self.status = "error"
        self.set_tag("error", True)
        self.set_tag("error.type", type(error).__name__)
        self.set_tag("error.message", str(error))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat() + "Z",
            "end_time": self.end_time.isoformat() + "Z" if self.end_time else None,
            "duration_ms": self.duration_ms,
            "tags": self.tags,
            "logs": self.logs,
            "status": self.status,
        }


class Tracer:
    """
    Tracer for creating and managing spans.

    Provides OpenTelemetry-compatible distributed tracing.
    """

    def __init__(self, service_name: str = "ai-pal"):
        """
        Initialize tracer.

        Args:
            service_name: Name of this service
        """
        self.service_name = service_name
        self._active_spans: Dict[str, Span] = {}
        self._finished_spans: list[Span] = []
        self._current_trace_id: Optional[str] = None
        self._current_span_id: Optional[str] = None

    def start_trace(self, operation_name: str, **tags) -> Span:
        """
        Start a new trace (root span).

        Args:
            operation_name: Name of the operation
            **tags: Tags to add to the span

        Returns:
            Root Span
        """
        trace_id = str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=None,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            tags={"service.name": self.service_name, **tags},
        )

        self._active_spans[span_id] = span
        self._current_trace_id = trace_id
        self._current_span_id = span_id

        return span

    def start_span(
        self,
        operation_name: str,
        parent_span_id: Optional[str] = None,
        **tags,
    ) -> Span:
        """
        Start a new span.

        Args:
            operation_name: Name of the operation
            parent_span_id: Optional parent span ID (uses current if not specified)
            **tags: Tags to add to the span

        Returns:
            New Span
        """
        # Use current span as parent if not specified
        if parent_span_id is None:
            parent_span_id = self._current_span_id

        # Get trace ID from parent or create new trace
        if parent_span_id and parent_span_id in self._active_spans:
            trace_id = self._active_spans[parent_span_id].trace_id
        else:
            trace_id = self._current_trace_id or str(uuid.uuid4())

        span_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow(),
            tags={"service.name": self.service_name, **tags},
        )

        self._active_spans[span_id] = span
        self._current_span_id = span_id

        return span

    def finish_span(self, span: Span):
        """
        Finish a span.

        Args:
            span: Span to finish
        """
        span.finish()

        # Move to finished spans
        if span.span_id in self._active_spans:
            del self._active_spans[span.span_id]
        self._finished_spans.append(span)

        # Update current span to parent
        if span.parent_span_id and span.parent_span_id in self._active_spans:
            self._current_span_id = span.parent_span_id
        else:
            self._current_span_id = None

    @contextmanager
    def span(self, operation_name: str, **tags):
        """
        Context manager for creating a span.

        Example:
            with tracer.span("database_query", query="SELECT ..."):
                result = execute_query()

        Args:
            operation_name: Name of the operation
            **tags: Tags to add to the span

        Yields:
            Span object
        """
        span = self.start_span(operation_name, **tags)
        try:
            yield span
        except Exception as e:
            span.set_error(e)
            raise
        finally:
            self.finish_span(span)

    def get_active_spans(self) -> list[Span]:
        """Get all active spans"""
        return list(self._active_spans.values())

    def get_finished_spans(self) -> list[Span]:
        """Get all finished spans"""
        return self._finished_spans.copy()

    def export_jaeger_format(self) -> Dict[str, Any]:
        """
        Export traces in Jaeger format.

        Returns:
            Dictionary in Jaeger JSON format
        """
        spans_by_trace: Dict[str, list[Span]] = {}

        # Group spans by trace ID
        for span in self._finished_spans:
            if span.trace_id not in spans_by_trace:
                spans_by_trace[span.trace_id] = []
            spans_by_trace[span.trace_id].append(span)

        # Convert to Jaeger format
        traces = []
        for trace_id, spans in spans_by_trace.items():
            trace_spans = []
            for span in spans:
                trace_span = {
                    "traceID": span.trace_id,
                    "spanID": span.span_id,
                    "operationName": span.operation_name,
                    "startTime": int(span.start_time.timestamp() * 1_000_000),
                    "duration": int(span.duration_ms * 1000) if span.duration_ms else 0,
                    "tags": [
                        {"key": k, "type": "string", "value": str(v)}
                        for k, v in span.tags.items()
                    ],
                    "logs": [
                        {
                            "timestamp": log["timestamp"],
                            "fields": [
                                {"key": k, "type": "string", "value": str(v)}
                                for k, v in log.items()
                                if k != "timestamp"
                            ],
                        }
                        for log in span.logs
                    ],
                }

                if span.parent_span_id:
                    trace_span["references"] = [
                        {
                            "refType": "CHILD_OF",
                            "traceID": span.trace_id,
                            "spanID": span.parent_span_id,
                        }
                    ]

                trace_spans.append(trace_span)

            traces.append(
                {
                    "traceID": trace_id,
                    "spans": trace_spans,
                    "processes": {
                        "p1": {
                            "serviceName": self.service_name,
                            "tags": [],
                        }
                    },
                }
            )

        return {"data": traces}

    def clear_finished_spans(self):
        """Clear finished spans (useful for memory management)"""
        self._finished_spans.clear()


class TracerProvider:
    """
    Provider for managing tracers.

    Allows creating separate tracers for different services/components.
    """

    def __init__(self):
        """Initialize tracer provider"""
        self._tracers: Dict[str, Tracer] = {}
        self._default_tracer: Optional[Tracer] = None

    def get_tracer(self, service_name: str = "ai-pal") -> Tracer:
        """
        Get or create a tracer for a service.

        Args:
            service_name: Service name

        Returns:
            Tracer instance
        """
        if service_name not in self._tracers:
            self._tracers[service_name] = Tracer(service_name)

        if self._default_tracer is None:
            self._default_tracer = self._tracers[service_name]

        return self._tracers[service_name]

    def get_default_tracer(self) -> Tracer:
        """Get default tracer"""
        if self._default_tracer is None:
            self._default_tracer = self.get_tracer()
        return self._default_tracer


# Global tracer provider
_tracer_provider: Optional[TracerProvider] = None


def get_tracer_provider() -> TracerProvider:
    """
    Get global tracer provider (singleton).

    Returns:
        TracerProvider instance
    """
    global _tracer_provider
    if _tracer_provider is None:
        _tracer_provider = TracerProvider()
    return _tracer_provider


def get_tracer(service_name: str = "ai-pal") -> Tracer:
    """
    Get a tracer.

    Args:
        service_name: Service name

    Returns:
        Tracer instance
    """
    return get_tracer_provider().get_tracer(service_name)


# Decorator for automatic tracing
def trace(operation_name: Optional[str] = None, **tags):
    """
    Decorator for automatic tracing of functions.

    Example:
        @trace("process_request", component="api")
        async def process_request(user_id, query):
            ...

    Args:
        operation_name: Optional operation name (uses function name if not specified)
        **tags: Tags to add to the span

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        actual_operation_name = operation_name or func.__name__

        if hasattr(func, "__call__") and hasattr(func, "__name__"):
            # Async function
            if hasattr(func, "__await__"):

                async def async_wrapper(*args, **kwargs):
                    tracer = get_tracer()
                    with tracer.span(actual_operation_name, **tags) as span:
                        span.set_tag("function", func.__name__)
                        try:
                            result = await func(*args, **kwargs)
                            return result
                        except Exception as e:
                            span.set_error(e)
                            raise

                return async_wrapper
            else:
                # Sync function
                def sync_wrapper(*args, **kwargs):
                    tracer = get_tracer()
                    with tracer.span(actual_operation_name, **tags) as span:
                        span.set_tag("function", func.__name__)
                        try:
                            result = func(*args, **kwargs)
                            return result
                        except Exception as e:
                            span.set_error(e)
                            raise

                return sync_wrapper

        return func

    return decorator


# Example usage
if __name__ == "__main__":
    import asyncio

    tracer = get_tracer()

    # Manual tracing
    root_span = tracer.start_trace("process_user_request", user_id="user-123")
    root_span.set_tag("endpoint", "/api/chat")

    with tracer.span("gate_validation") as gate_span:
        gate_span.set_tag("gate", "gate1_net_agency")
        gate_span.log("Validating net agency")
        time.sleep(0.1)
        gate_span.set_tag("result", "passed")

    with tracer.span("model_execution") as model_span:
        model_span.set_tag("model", "claude-3-5-sonnet")
        model_span.log("Executing model")
        time.sleep(0.2)
        model_span.set_tag("tokens", 150)

    tracer.finish_span(root_span)

    # Export
    traces = tracer.export_jaeger_format()
    print("Exported traces:")
    print(f"  Traces: {len(traces['data'])}")
    print(f"  Spans: {sum(len(t['spans']) for t in traces['data'])}")

    # Decorator usage
    @trace("database_query", component="database")
    def query_database(query: str):
        time.sleep(0.05)
        return {"results": []}

    result = query_database("SELECT * FROM users")
