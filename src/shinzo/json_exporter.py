"""Custom JSON-based OTLP exporters for HTTP transport."""

import json
from typing import Dict, Optional, Sequence
from urllib.parse import urljoin

import httpx
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult
from opentelemetry.sdk.metrics.export import MetricsData


class OTLPJsonSpanExporter(SpanExporter):
    """Export spans to OTLP backend using JSON format over HTTP."""

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        """
        Initialize the JSON span exporter.

        Args:
            endpoint: Base OTLP endpoint URL (e.g., http://localhost:8000/telemetry/ingest_http)
            headers: Optional HTTP headers (e.g., for authentication)
            timeout: Request timeout in seconds
        """
        self.endpoint = urljoin(endpoint + "/", "traces")
        self.headers = headers or {}
        self.headers["Content-Type"] = "application/json"
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to the backend."""
        if not spans:
            return SpanExportResult.SUCCESS

        # Convert spans to OTLP JSON format
        payload = self._spans_to_otlp_json(spans)

        try:
            response = self.client.post(self.endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return SpanExportResult.SUCCESS
        except Exception as e:
            print(f"Failed to export spans: {e}")
            return SpanExportResult.FAILURE

    def _spans_to_otlp_json(self, spans: Sequence[ReadableSpan]) -> dict:
        """Convert spans to OTLP JSON format."""
        # Group spans by resource
        resource_spans = {}

        for span in spans:
            # Get resource attributes
            resource_attrs = {}
            if span.resource:
                resource_attrs = {
                    k: self._value_to_json(v) for k, v in span.resource.attributes.items()
                }

            resource_key = json.dumps(resource_attrs, sort_keys=True)

            if resource_key not in resource_spans:
                resource_spans[resource_key] = {
                    "resource": {
                        "attributes": [
                            {"key": k, "value": self._attr_value_to_json(v)}
                            for k, v in (span.resource.attributes.items() if span.resource else {})
                        ]
                    },
                    "scopeSpans": [],
                }

            # Convert span to JSON
            span_json = {
                "traceId": format(span.context.trace_id, "032x"),
                "spanId": format(span.context.span_id, "016x"),
                "name": span.name,
                "kind": span.kind.value if span.kind else 1,
                "startTimeUnixNano": str(span.start_time),
                "endTimeUnixNano": str(span.end_time) if span.end_time else str(span.start_time),
                "attributes": [
                    {"key": k, "value": self._attr_value_to_json(v)}
                    for k, v in (span.attributes.items() if span.attributes else {})
                ],
                "status": {"code": span.status.status_code.value if span.status else 0},
            }

            # Add parent span ID if present
            if span.parent and span.parent.span_id:
                span_json["parentSpanId"] = format(span.parent.span_id, "016x")

            # Add to scope spans
            scope_span = {
                "scope": {
                    "name": span.instrumentation_scope.name if span.instrumentation_scope else "",
                    "version": (
                        span.instrumentation_scope.version if span.instrumentation_scope else ""
                    ),
                },
                "spans": [span_json],
            }

            resource_spans[resource_key]["scopeSpans"].append(scope_span)

        return {"resourceSpans": list(resource_spans.values())}

    def _value_to_json(self, value):
        """Convert attribute value to JSON-serializable format."""
        if isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        else:
            return str(value)

    def _attr_value_to_json(self, value):
        """Convert attribute value to OTLP JSON attribute format."""
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, bool):
            return {"boolValue": value}
        elif isinstance(value, int):
            return {"intValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        else:
            return {"stringValue": str(value)}

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        self.client.close()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending spans."""
        return True


class OTLPJsonMetricExporter(MetricExporter):
    """Export metrics to OTLP backend using JSON format over HTTP."""

    def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None, timeout: int = 10):
        """
        Initialize the JSON metric exporter.

        Args:
            endpoint: Base OTLP endpoint URL
            headers: Optional HTTP headers
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.endpoint = urljoin(endpoint + "/", "metrics")
        self.headers = headers or {}
        self.headers["Content-Type"] = "application/json"
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

        # Required attributes for OpenTelemetry SDK
        from opentelemetry.sdk.metrics.export import AggregationTemporality
        from opentelemetry.sdk.metrics._internal.instrument import (
            Counter,
            UpDownCounter,
            Histogram,
            ObservableCounter,
            ObservableUpDownCounter,
            ObservableGauge,
        )

        self._preferred_temporality = {
            Counter: AggregationTemporality.DELTA,
            UpDownCounter: AggregationTemporality.CUMULATIVE,
            Histogram: AggregationTemporality.DELTA,
            ObservableCounter: AggregationTemporality.DELTA,
            ObservableUpDownCounter: AggregationTemporality.CUMULATIVE,
            ObservableGauge: AggregationTemporality.CUMULATIVE,
        }
        self._preferred_aggregation = {}

    def export(
        self, metrics_data: MetricsData, timeout_millis: float = 10000
    ) -> MetricExportResult:
        """Export metrics to the backend."""
        if not metrics_data or not metrics_data.resource_metrics:
            return MetricExportResult.SUCCESS

        # Convert metrics to OTLP JSON format
        payload = self._metrics_to_otlp_json(metrics_data)

        try:
            response = self.client.post(self.endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return MetricExportResult.SUCCESS
        except Exception as e:
            print(f"Failed to export metrics: {e}")
            return MetricExportResult.FAILURE

    def _metrics_to_otlp_json(self, metrics_data: MetricsData) -> dict:
        """Convert metrics to OTLP JSON format."""
        resource_metrics = []

        for rm in metrics_data.resource_metrics:
            resource_json = {
                "resource": {
                    "attributes": [
                        {"key": k, "value": self._attr_value_to_json(v)}
                        for k, v in (rm.resource.attributes.items() if rm.resource else {})
                    ]
                },
                "scopeMetrics": [],
            }

            for sm in rm.scope_metrics:
                scope_json = {
                    "scope": {
                        "name": sm.scope.name if sm.scope else "",
                        "version": sm.scope.version if sm.scope else "",
                    },
                    "metrics": [],
                }

                for metric in sm.metrics:
                    metric_json = {
                        "name": metric.name,
                        "description": metric.description or "",
                        "unit": metric.unit or "",
                    }

                    # Handle different metric types
                    if hasattr(metric.data, "data_points"):
                        data_points = []
                        for dp in metric.data.data_points:
                            dp_json = {
                                "timeUnixNano": str(dp.time_unix_nano),
                                "attributes": [
                                    {"key": k, "value": self._attr_value_to_json(v)}
                                    for k, v in (dp.attributes.items() if dp.attributes else {})
                                ],
                            }

                            # Add value based on metric type
                            if hasattr(dp, "value"):
                                if isinstance(dp.value, int):
                                    dp_json["asInt"] = str(dp.value)
                                else:
                                    dp_json["asDouble"] = float(dp.value)

                            data_points.append(dp_json)

                        # Determine metric type
                        metric_type = metric.data.__class__.__name__.lower()
                        if "sum" in metric_type:
                            metric_json["sum"] = {
                                "dataPoints": data_points,
                                "aggregationTemporality": 2,
                            }
                        elif "gauge" in metric_type:
                            metric_json["gauge"] = {"dataPoints": data_points}
                        elif "histogram" in metric_type:
                            metric_json["histogram"] = {
                                "dataPoints": data_points,
                                "aggregationTemporality": 2,
                            }

                    scope_json["metrics"].append(metric_json)

                resource_json["scopeMetrics"].append(scope_json)

            resource_metrics.append(resource_json)

        return {"resourceMetrics": resource_metrics}

    def _attr_value_to_json(self, value):
        """Convert attribute value to OTLP JSON attribute format."""
        if isinstance(value, str):
            return {"stringValue": value}
        elif isinstance(value, bool):
            return {"boolValue": value}
        elif isinstance(value, int):
            return {"intValue": str(value)}
        elif isinstance(value, float):
            return {"doubleValue": value}
        else:
            return {"stringValue": str(value)}

    def shutdown(self, timeout_millis: float = 30000, **kwargs) -> None:
        """Shutdown the exporter."""
        self.client.close()

    def force_flush(self, timeout_millis: float = 10000) -> bool:
        """Force flush any pending metrics."""
        return True
