"""
pipeline.batch_runner — run DataProcessor over a list of record batches.

BatchRunner orchestrates multiple DataProcessor instances, one per partition,
and merges results into a single output stream.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, Iterator

from .processor import DataProcessor

logger = logging.getLogger(__name__)


class BatchRunner:
    """Drive a DataProcessor across partitioned record batches.

    BatchRunner accepts a preconfigured DataProcessor and a list of batches.
    Each batch is processed in a thread pool and results are merged in
    completion order.

    Args:
        processor: A DataProcessor instance shared across all batch workers.
        max_workers: Thread pool size (default: 4).
    """

    def __init__(self, processor: DataProcessor, max_workers: int = 4) -> None:
        self.processor: DataProcessor = processor
        self.max_workers = max_workers

    def run(self, batches: list[list[dict]]) -> Iterator[dict]:
        """Process all batches via the DataProcessor and yield results.

        Args:
            batches: List of record batches. Each batch is a list of raw dicts.

        Yields:
            Processed records from all batches in completion order.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {
                pool.submit(list, self.processor.process(batch)): idx
                for idx, batch in enumerate(batches)
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    for record in future.result():
                        yield record
                except Exception as exc:
                    logger.error("BatchRunner: partition %d failed — %s", idx, exc)


def run_batches(
    processor: DataProcessor,
    batches: list[list[dict]],
    max_workers: int = 4,
) -> list[dict]:
    """Convenience wrapper: run all batches through DataProcessor and collect results.

    Args:
        processor: DataProcessor to use.
        batches: Partitioned record lists.
        max_workers: Thread pool concurrency.

    Returns:
        Flat list of all processed records.
    """
    runner = BatchRunner(processor=processor, max_workers=max_workers)
    return list(runner.run(batches))
