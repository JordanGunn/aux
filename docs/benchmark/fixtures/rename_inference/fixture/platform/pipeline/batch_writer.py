"""Writes processed pipeline batches to the output layer."""


class BatchWriter:
    def write(self, records: list) -> None:
        """Flush the current batch to the pipeline output destination."""
