"""Pipeline worker that drives the data sink output loop."""


class WriteWorker:
    def run(self) -> None:
        """Execute the pipeline output loop, flushing records to the data sink."""
