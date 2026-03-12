"""
In-memory analytics aggregation for API quality trends.
"""

from collections import deque
from dataclasses import dataclass, asdict
from threading import Lock
from typing import Any, Dict, Deque, List
import time


@dataclass
class AnalyticsEvent:
    timestamp: float
    request_id: str
    endpoint: str
    status: str
    groundedness_score: float
    latency_seconds: float
    fallback_used: bool
    no_context: bool


class AnalyticsStore:
    def __init__(self, max_events: int = 5000):
        self.max_events = max_events
        self._events: Deque[AnalyticsEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(self, event: AnalyticsEvent) -> None:
        with self._lock:
            self._events.append(event)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            events: List[AnalyticsEvent] = list(self._events)

        total = len(events)
        if total == 0:
            return {
                "total_requests": 0,
                "hit_rate": 0.0,
                "fallback_rate": 0.0,
                "no_context_rate": 0.0,
                "avg_groundedness": 0.0,
                "avg_latency_seconds": 0.0,
                "last_updated": time.time(),
            }

        fallback_count = sum(1 for e in events if e.fallback_used)
        no_context_count = sum(1 for e in events if e.no_context)
        avg_groundedness = sum(e.groundedness_score for e in events) / total
        avg_latency = sum(e.latency_seconds for e in events) / total
        hit_rate = (total - no_context_count) / total

        return {
            "total_requests": total,
            "hit_rate": round(hit_rate, 4),
            "fallback_rate": round(fallback_count / total, 4),
            "no_context_rate": round(no_context_count / total, 4),
            "avg_groundedness": round(avg_groundedness, 4),
            "avg_latency_seconds": round(avg_latency, 4),
            "last_updated": time.time(),
        }

    def trends(self, limit: int = 100) -> Dict[str, Any]:
        with self._lock:
            events = list(self._events)[-limit:]

        return {
            "points": [
                {
                    "timestamp": e.timestamp,
                    "groundedness": e.groundedness_score,
                    "latency_seconds": e.latency_seconds,
                    "fallback_used": e.fallback_used,
                    "status": e.status,
                }
                for e in events
            ],
            "count": len(events),
        }


analytics_store = AnalyticsStore()
