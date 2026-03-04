"""
pipeline.stream_handler — real-time record stream handler backed by DataProcessor.

StreamHandler wraps a DataProcessor and exposes a blocking iterator interface
suitable for use in an asyncio event loop via :func:`run_in_executor`.
"""
from __future__ import annotations

import logging
from typing import Callable, Iterable, Iterator

from .processor import DataProcessor

logger = logging.getLogger(__name__)


class StreamHandler:
    """Push records through a DataProcessor as they arrive.

    Unlike BatchRunner, StreamHandler processes records one at a time and
    immediately forwards each result to registered output callbacks.

    Args:
        processor: DataProcessor used for validation and transformation.
        on_error: Optional callback invoked with ``(record, exc)`` on failure.
    """

    def __init__(
        self,
        processor: DataProcessor,
        on_error: Callable[[dict, Exception], None] | None = None,
    ) -> None:
        self.processor = processor
        self.on_error = on_error
        self._callbacks: list[Callable[[dict], None]] = []

    def subscribe(self, callback: Callable[[dict], None]) -> None:
        """Register a callback to receive DataProcessor output records."""
        self._callbacks.append(callback)

    def handle(self, records: Iterable[dict]) -> None:
        """Process *records* through DataProcessor and fan out to subscribers.

        Args:
            records: Iterable of raw dicts from an upstream connector.
        """
        for result in self.processor.process(records):
            for cb in self._callbacks:
                cb(result)
