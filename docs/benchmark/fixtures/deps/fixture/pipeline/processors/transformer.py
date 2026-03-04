"""Transformer processor — enriches records, imports processor and config."""

from pipeline.core.config import Config
from pipeline.processors.processor import Processor


class Transformer(Processor):
    """Applies a transformation mapping to each record."""

    def __init__(self, config: Config, mapping: dict) -> None:
        super().__init__(config)
        self._mapping = mapping

    def process(self, record: dict) -> dict:
        return {self._mapping.get(k, k): v for k, v in record.items()}
