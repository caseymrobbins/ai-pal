"""
Visualization Library - Dashboard Charts and Graphs

Provides reusable visualization components for:
- Time series charts (agency trends, skill development)
- Distribution charts (strength profiles)
- Timeline views (progress tapestry)
- Forecast charts (predictive analytics)

Supports multiple output formats:
- ASCII art for CLI
- JSON data for web frontends
- Plotly HTML (optional, for rich web dashboards)
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math


class ChartType(Enum):
    """Supported chart types"""
    LINE = "line"
    BAR = "bar"
    SPARKLINE = "sparkline"
    DISTRIBUTION = "distribution"
    TIMELINE = "timeline"
    FORECAST = "forecast"


class OutputFormat(Enum):
    """Output formats for visualizations"""
    ASCII = "ascii"  # CLI-friendly ASCII art
    JSON = "json"    # Data for web frontends
    PLOTLY = "plotly"  # Rich HTML with Plotly (optional)


@dataclass
class DataPoint:
    """Single data point for visualization"""
    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChartData:
    """Data for a chart"""
    title: str
    data_points: List[DataPoint]
    x_label: str = "Time"
    y_label: str = "Value"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    threshold_lines: Optional[Dict[str, float]] = None  # name -> value


class ASCIIChart:
    """Generate ASCII art charts for CLI display"""

    @staticmethod
    def sparkline(values: List[float], width: int = 20) -> str:
        """
        Generate a sparkline (compact line chart)

        Args:
            values: List of numeric values
            width: Character width of sparkline

        Returns:
            ASCII sparkline string
        """
        if not values:
            return "─" * width

        # Normalize values to 0-8 range (for block characters)
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Unicode block characters for vertical levels
        blocks = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        # Sample values if we have more than width
        if len(values) > width:
            step = len(values) / width
            sampled = [values[int(i * step)] for i in range(width)]
        else:
            sampled = values + [values[-1]] * (width - len(values))

        # Convert to block characters
        result = ""
        for val in sampled:
            normalized = (val - min_val) / range_val
            block_index = min(8, int(normalized * 8))
            result += blocks[block_index]

        return result

    @staticmethod
    def bar_chart(data: ChartData, height: int = 10, width: int = 60) -> str:
        """
        Generate ASCII bar chart

        Args:
            data: Chart data
            height: Chart height in lines
            width: Chart width in characters

        Returns:
            Multi-line ASCII bar chart
        """
        if not data.data_points:
            return f"{data.title}\n(No data)"

        values = [dp.value for dp in data.data_points]
        labels = [dp.label or f"{i+1}" for i, dp in enumerate(data.data_points)]

        # Determine value range
        min_val = data.min_value if data.min_value is not None else min(values)
        max_val = data.max_value if data.max_value is not None else max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Build chart
        lines = [data.title, ""]

        # Draw bars
        bar_width = max(1, (width - 10) // len(values))
        for i in range(height, 0, -1):
            line = ""
            threshold = min_val + (range_val * i / height)

            # Y-axis label
            line += f"{threshold:6.2f} │ "

            # Bars
            for val in values:
                if val >= threshold:
                    line += "█" * bar_width + " "
                else:
                    line += " " * bar_width + " "

            lines.append(line)

        # X-axis
        lines.append("       └" + "─" * (width - 8))

        # Labels
        label_line = "         "
        for label in labels:
            # Truncate labels to bar width
            truncated = label[:bar_width]
            label_line += truncated + " " * (bar_width + 1 - len(truncated))
        lines.append(label_line)

        return "\n".join(lines)

    @staticmethod
    def line_chart(data: ChartData, height: int = 15, width: int = 60) -> str:
        """
        Generate ASCII line chart

        Args:
            data: Chart data
            height: Chart height in lines
            width: Chart width in characters

        Returns:
            Multi-line ASCII line chart
        """
        if not data.data_points:
            return f"{data.title}\n(No data)"

        values = [dp.value for dp in data.data_points]

        # Determine value range
        min_val = data.min_value if data.min_value is not None else min(values)
        max_val = data.max_value if data.max_value is not None else max(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Build chart grid
        lines = [data.title, ""]
        grid = [[" " for _ in range(width)] for _ in range(height)]

        # Plot data points
        num_points = len(values)
        for i, val in enumerate(values):
            # Map to grid coordinates
            x = int((i / max(1, num_points - 1)) * (width - 1))
            y = height - 1 - int(((val - min_val) / range_val) * (height - 1))
            y = max(0, min(height - 1, y))  # Clamp

            grid[y][x] = "●"

            # Connect with previous point
            if i > 0:
                prev_val = values[i - 1]
                prev_x = int(((i - 1) / max(1, num_points - 1)) * (width - 1))
                prev_y = height - 1 - int(((prev_val - min_val) / range_val) * (height - 1))
                prev_y = max(0, min(height - 1, prev_y))

                # Draw line between points
                x_range = range(min(prev_x, x), max(prev_x, x) + 1)
                for xi in x_range:
                    # Linear interpolation
                    if x != prev_x:
                        t = (xi - prev_x) / (x - prev_x)
                        yi = int(prev_y + t * (y - prev_y))
                        yi = max(0, min(height - 1, yi))
                        if grid[yi][xi] == " ":
                            grid[yi][xi] = "·"

        # Add threshold lines
        if data.threshold_lines:
            for name, threshold_val in data.threshold_lines.items():
                if min_val <= threshold_val <= max_val:
                    threshold_y = height - 1 - int(((threshold_val - min_val) / range_val) * (height - 1))
                    threshold_y = max(0, min(height - 1, threshold_y))
                    for xi in range(width):
                        if grid[threshold_y][xi] == " ":
                            grid[threshold_y][xi] = "-"

        # Render grid with Y-axis
        for i, row in enumerate(grid):
            y_val = max_val - (i / (height - 1)) * range_val
            line = f"{y_val:6.2f} │ " + "".join(row)
            lines.append(line)

        # X-axis
        lines.append("       └" + "─" * width)

        # X-axis labels (timestamps)
        if data.data_points:
            first_time = data.data_points[0].timestamp.strftime("%H:%M")
            last_time = data.data_points[-1].timestamp.strftime("%H:%M")
            time_line = f"         {first_time}" + " " * (width - len(first_time) - len(last_time)) + last_time
            lines.append(time_line)

        return "\n".join(lines)

    @staticmethod
    def timeline(events: List[Dict[str, Any]], width: int = 60) -> str:
        """
        Generate ASCII timeline visualization

        Args:
            events: List of events with 'timestamp', 'title', 'type' keys
            width: Chart width in characters

        Returns:
            Multi-line ASCII timeline
        """
        if not events:
            return "Timeline\n(No events)"

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e['timestamp'])

        lines = ["Timeline", ""]

        for event in sorted_events:
            timestamp = event['timestamp'].strftime("%Y-%m-%d %H:%M")
            title = event.get('title', 'Event')
            event_type = event.get('type', 'info')

            # Choose marker based on event type
            markers = {
                'win': '✓',
                'bottleneck': '⚠',
                'milestone': '★',
                'task': '○',
                'info': '·'
            }
            marker = markers.get(event_type, '·')

            # Format event line
            line = f"{timestamp} {marker} {title}"
            if len(line) > width:
                line = line[:width - 3] + "..."
            lines.append(line)

        return "\n".join(lines)


class JSONChart:
    """Generate JSON data for web frontend charts"""

    @staticmethod
    def line_chart(data: ChartData) -> Dict[str, Any]:
        """
        Generate JSON data for line chart

        Returns:
            Chart data in format compatible with Chart.js, Plotly, etc.
        """
        return {
            "type": "line",
            "title": data.title,
            "xLabel": data.x_label,
            "yLabel": data.y_label,
            "data": {
                "labels": [dp.timestamp.isoformat() for dp in data.data_points],
                "datasets": [{
                    "label": data.y_label,
                    "data": [dp.value for dp in data.data_points],
                    "borderColor": "rgb(75, 192, 192)",
                    "tension": 0.1
                }]
            },
            "thresholds": data.threshold_lines or {}
        }

    @staticmethod
    def bar_chart(data: ChartData) -> Dict[str, Any]:
        """Generate JSON data for bar chart"""
        return {
            "type": "bar",
            "title": data.title,
            "xLabel": data.x_label,
            "yLabel": data.y_label,
            "data": {
                "labels": [dp.label or str(i) for i, dp in enumerate(data.data_points)],
                "datasets": [{
                    "label": data.y_label,
                    "data": [dp.value for dp in data.data_points],
                    "backgroundColor": "rgba(75, 192, 192, 0.2)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 1
                }]
            }
        }

    @staticmethod
    def distribution(values: List[float], bins: int = 10) -> Dict[str, Any]:
        """
        Generate histogram distribution

        Args:
            values: List of values to distribute
            bins: Number of histogram bins

        Returns:
            Histogram data
        """
        if not values:
            return {"type": "histogram", "data": {"labels": [], "datasets": []}}

        # Calculate histogram
        min_val = min(values)
        max_val = max(values)
        range_val = max_val - min_val if max_val != min_val else 1
        bin_width = range_val / bins

        # Create bins
        histogram = [0] * bins
        bin_labels = []

        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = bin_start + bin_width
            bin_labels.append(f"{bin_start:.2f}-{bin_end:.2f}")

            # Count values in this bin
            for val in values:
                if bin_start <= val < bin_end or (i == bins - 1 and val == max_val):
                    histogram[i] += 1

        return {
            "type": "histogram",
            "title": "Distribution",
            "data": {
                "labels": bin_labels,
                "datasets": [{
                    "label": "Frequency",
                    "data": histogram,
                    "backgroundColor": "rgba(54, 162, 235, 0.2)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1
                }]
            }
        }


class VisualizationEngine:
    """Main visualization engine - generates charts in multiple formats"""

    def __init__(self, default_format: OutputFormat = OutputFormat.ASCII):
        """
        Initialize visualization engine

        Args:
            default_format: Default output format
        """
        self.default_format = default_format

    def render(
        self,
        data: ChartData,
        chart_type: ChartType,
        output_format: Optional[OutputFormat] = None,
        **kwargs
    ) -> Any:
        """
        Render a chart

        Args:
            data: Chart data
            chart_type: Type of chart to render
            output_format: Output format (uses default if None)
            **kwargs: Additional rendering options

        Returns:
            Rendered chart (string for ASCII, dict for JSON)
        """
        fmt = output_format or self.default_format

        if fmt == OutputFormat.ASCII:
            return self._render_ascii(data, chart_type, **kwargs)
        elif fmt == OutputFormat.JSON:
            return self._render_json(data, chart_type, **kwargs)
        elif fmt == OutputFormat.PLOTLY:
            return self._render_plotly(data, chart_type, **kwargs)
        else:
            raise ValueError(f"Unsupported output format: {fmt}")

    def _render_ascii(self, data: ChartData, chart_type: ChartType, **kwargs) -> str:
        """Render ASCII chart"""
        if chart_type == ChartType.LINE:
            return ASCIIChart.line_chart(
                data,
                height=kwargs.get('height', 15),
                width=kwargs.get('width', 60)
            )
        elif chart_type == ChartType.BAR:
            return ASCIIChart.bar_chart(
                data,
                height=kwargs.get('height', 10),
                width=kwargs.get('width', 60)
            )
        elif chart_type == ChartType.SPARKLINE:
            values = [dp.value for dp in data.data_points]
            return ASCIIChart.sparkline(values, width=kwargs.get('width', 20))
        elif chart_type == ChartType.TIMELINE:
            events = kwargs.get('events', [])
            return ASCIIChart.timeline(events, width=kwargs.get('width', 60))
        else:
            return f"Chart type {chart_type} not supported for ASCII output"

    def _render_json(self, data: ChartData, chart_type: ChartType, **kwargs) -> Dict[str, Any]:
        """Render JSON chart data"""
        if chart_type == ChartType.LINE:
            return JSONChart.line_chart(data)
        elif chart_type == ChartType.BAR:
            return JSONChart.bar_chart(data)
        elif chart_type == ChartType.DISTRIBUTION:
            values = [dp.value for dp in data.data_points]
            return JSONChart.distribution(values, bins=kwargs.get('bins', 10))
        else:
            return {"type": str(chart_type), "error": "Not implemented"}

    def _render_plotly(self, data: ChartData, chart_type: ChartType, **kwargs) -> str:
        """
        Render Plotly HTML (optional - requires plotly package)

        Note: This is optional and will gracefully degrade if plotly is not installed
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
        except ImportError:
            return "<html><body>Plotly not installed. Run: pip install plotly</body></html>"

        # Create figure based on chart type
        if chart_type == ChartType.LINE:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[dp.timestamp for dp in data.data_points],
                y=[dp.value for dp in data.data_points],
                mode='lines+markers',
                name=data.y_label
            ))

            # Add threshold lines
            if data.threshold_lines:
                for name, value in data.threshold_lines.items():
                    fig.add_hline(y=value, line_dash="dash", annotation_text=name)

            fig.update_layout(
                title=data.title,
                xaxis_title=data.x_label,
                yaxis_title=data.y_label,
                hovermode='x unified'
            )

        elif chart_type == ChartType.BAR:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[dp.label or str(i) for i, dp in enumerate(data.data_points)],
                y=[dp.value for dp in data.data_points],
                name=data.y_label
            ))

            fig.update_layout(
                title=data.title,
                xaxis_title=data.x_label,
                yaxis_title=data.y_label
            )

        else:
            return f"<html><body>Chart type {chart_type} not implemented for Plotly</body></html>"

        # Return HTML
        return fig.to_html()


# Convenience functions for quick chart generation

def sparkline(values: List[float], width: int = 20) -> str:
    """Quick sparkline generation"""
    return ASCIIChart.sparkline(values, width)


def progress_bar(current: float, total: float, width: int = 20, fill_char: str = "█") -> str:
    """
    Generate a simple progress bar

    Args:
        current: Current value
        total: Total value
        width: Bar width in characters
        fill_char: Character to use for filled portion

    Returns:
        Progress bar string
    """
    percentage = min(1.0, max(0.0, current / total if total > 0 else 0))
    filled = int(width * percentage)
    empty = width - filled

    bar = fill_char * filled + "░" * empty
    percent_text = f"{percentage * 100:.0f}%"

    return f"[{bar}] {percent_text}"
