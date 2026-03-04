"""Pipeline engine — top-level coordinator for runner and config."""

from pipeline.core.config import Config
from pipeline.core.runner import Runner


class Engine:
    """Coordinates the full pipeline lifecycle."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.runner = Runner(config)

    def execute(self, records: list[dict]) -> list[dict]:
        return self.runner.run(records)
