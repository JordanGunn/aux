"""Base processor — imports only config."""

from pipeline.core.config import Config


class Processor:
    """Abstract base for all record processors."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def process(self, record: dict) -> dict:
        raise NotImplementedError
