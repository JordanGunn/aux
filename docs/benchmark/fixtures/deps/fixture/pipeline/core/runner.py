"""Pipeline runner — orchestrates processors using config."""

from pipeline.core.config import Config
from pipeline.processors.processor import Processor


class Runner:
    """Runs a sequence of processors against a data stream."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._processors: list[Processor] = []

    def add(self, processor: Processor) -> None:
        self._processors.append(processor)

    def run(self, records: list[dict]) -> list[dict]:
        result = list(records)
        for proc in self._processors:
            result = [proc.process(r) for r in result]
        return result
