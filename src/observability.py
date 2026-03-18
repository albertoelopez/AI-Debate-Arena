#!/usr/bin/env python3

import json
import logging
import os
import threading
from contextlib import contextmanager
from enum import Enum
from typing import Any, Dict, Iterable, Optional

try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    except ImportError:
        OTLPSpanExporter = None

    OTEL_AVAILABLE = True
except ImportError:
    trace = None
    Resource = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    OTLPSpanExporter = None
    OTEL_AVAILABLE = False


logger = logging.getLogger("observability")
_setup_lock = threading.Lock()
_is_configured = False


class NullSpan:
    def set_attribute(self, key: str, value: Any) -> None:
        return None

    def set_attributes(self, attributes: Dict[str, Any]) -> None:
        return None

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        return None

    def record_exception(self, exception: BaseException) -> None:
        return None

    def set_status(self, status: Any) -> None:
        return None


def _as_attribute_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, dict):
        return json.dumps({str(k): _as_attribute_value(v) for k, v in value.items()}, sort_keys=True)
    if isinstance(value, (list, tuple, set)):
        values = [_as_attribute_value(item) for item in value]
        filtered = [item for item in values if isinstance(item, (str, bool, int, float))]
        if len(filtered) == len(values):
            return filtered
        return json.dumps(values, sort_keys=True)
    return str(value)


def normalize_attributes(attributes: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in (attributes or {}).items():
        converted = _as_attribute_value(value)
        if converted is not None:
            normalized[key] = converted
    return normalized


def setup_observability(service_name: str = "ai-debate-arena") -> bool:
    global _is_configured

    if _is_configured:
        return OTEL_AVAILABLE

    with _setup_lock:
        if _is_configured:
            return OTEL_AVAILABLE

        _is_configured = True
        if not OTEL_AVAILABLE:
            logger.info("OpenTelemetry packages not installed; observability spans disabled")
            return False

        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        exporter_added = False

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        if endpoint and OTLPSpanExporter is not None:
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
            exporter_added = True

        if not exporter_added and os.getenv("OBSERVABILITY_CONSOLE_EXPORTER", "0") == "1":
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
            exporter_added = True

        try:
            trace.set_tracer_provider(provider)
        except Exception:
            logger.debug("Tracer provider already configured; using existing provider")

        if exporter_added:
            logger.info("Observability configured for service '%s'", service_name)
        else:
            logger.info("Observability active without exporter; set OTEL_EXPORTER_OTLP_ENDPOINT to export traces")

        return True


def get_tracer(name: str = "ai_debate_arena"):
    if OTEL_AVAILABLE:
        return trace.get_tracer(name)
    return None


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None, tracer_name: str = "ai_debate_arena"):
    attrs = normalize_attributes(attributes)
    tracer = get_tracer(tracer_name)

    if tracer is None:
        yield NullSpan()
        return

    with tracer.start_as_current_span(name) as span:
        if attrs:
            span.set_attributes(attrs)
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            raise


def add_event(span: Any, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    if span is None:
        return
    span.add_event(name, normalize_attributes(attributes))


def log_event(event_name: str, **fields: Any) -> None:
    payload = normalize_attributes({"event": event_name, **fields})
    logger.info("obs %s", json.dumps(payload, sort_keys=True))


def turn_attributes(
    debate_id: str,
    topic: str,
    round_number: int,
    phase: str,
    speaker_name: str,
    position_name: str,
    has_audio: bool,
    relevance_score: Optional[float] = None,
    is_relevant: Optional[bool] = None,
    confidence_level: Optional[float] = None,
) -> Dict[str, Any]:
    return normalize_attributes({
        "debate.id": debate_id,
        "debate.topic": topic,
        "round.number": round_number,
        "debate.phase": phase,
        "speaker.name": speaker_name,
        "speaker.position": position_name,
        "audio.generated": has_audio,
        "relevance.score": relevance_score,
        "relevance.on_topic": is_relevant,
        "argument.confidence": confidence_level,
    })
