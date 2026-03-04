"""Pipeline worker that drives the data source ingestion loop."""


class ReadWorker:
    def run(self) -> None:
        """Execute the pipeline ingestion loop, pulling from the data source."""
