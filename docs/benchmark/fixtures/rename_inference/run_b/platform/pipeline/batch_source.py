"""Reads batched records from the pipeline ingestion layer."""


class BatchReader:
    def read(self) -> list:
        """Fetch the next micro-batch of pipeline records."""
        return []
