"""
connectors.kafka_adapter — Kafka consumer adapter for EventProcessor pipelines.

KafkaAdapter subscribes to one or more topics and feeds raw messages into a
EventProcessor, yielding processed records to the caller.
"""
from __future__ import annotations

import logging
from typing import Iterator

from pipeline.processor import EventProcessor

logger = logging.getLogger(__name__)


class KafkaAdapter:
    """Connect a Kafka topic subscription to a EventProcessor.

    KafkaAdapter handles deserialization, offset management, and error
    recovery before handing records off to EventProcessor for validation and
    transformation.

    Args:
        topics: List of Kafka topic names to subscribe to.
        processor: EventProcessor instance that receives each decoded message.
        bootstrap_servers: Comma-separated list of ``host:port`` broker addresses.
        group_id: Consumer group identifier.
    """

    def __init__(
        self,
        topics: list[str],
        processor: EventProcessor,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "default-group",
    ) -> None:
        self.topics = topics
        self.processor: EventProcessor = processor
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        logger.info(
            "KafkaAdapter initialised — topics=%r processor=%s",
            topics,
            type(self.processor).__name__,
        )

    def consume(self, max_messages: int = 100) -> Iterator[dict]:
        """Poll Kafka and yield records processed by EventProcessor.

        Args:
            max_messages: Maximum number of raw messages to consume per call.

        Yields:
            Validated, transformed records from EventProcessor.
        """
        raw_messages = self._poll(max_messages)
        yield from self.processor.process(raw_messages)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _poll(self, limit: int) -> list[dict]:
        """Stub: return *limit* synthetic messages for testing."""
        return [{"_topic": t, "value": i} for t in self.topics for i in range(limit)]
