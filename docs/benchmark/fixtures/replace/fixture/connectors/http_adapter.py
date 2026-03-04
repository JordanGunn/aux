"""
connectors.http_adapter — HTTP polling adapter for DataProcessor pipelines.

HttpAdapter periodically fetches records from a REST endpoint and passes
them through a DataProcessor before forwarding to downstream consumers.
"""
from __future__ import annotations

import logging
from typing import Iterator
from urllib.request import urlopen
import json

from pipeline.processor import DataProcessor

logger = logging.getLogger(__name__)


class HttpAdapter:
    """Poll an HTTP endpoint and feed results into DataProcessor.

    HttpAdapter calls a JSON REST endpoint on each :meth:`fetch` invocation,
    decodes the response body, and delegates record processing to DataProcessor.

    Args:
        url: Fully-qualified HTTP URL to poll.
        processor: DataProcessor used to validate and transform each record.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        url: str,
        processor: DataProcessor,
        timeout: int = 10,
    ) -> None:
        self.url = url
        self.processor: DataProcessor = processor
        self.timeout = timeout

    def fetch(self) -> Iterator[dict]:
        """Fetch one page of records and yield DataProcessor output.

        Yields:
            Validated, transformed records produced by DataProcessor.
        """
        raw = self._get()
        yield from self.processor.process(raw)

    def _get(self) -> list[dict]:
        """Stub: simulate an HTTP GET and return synthetic records."""
        logger.debug("HttpAdapter._get stub called for url=%r", self.url)
        return [{"source": "http", "url": self.url, "seq": i} for i in range(5)]
