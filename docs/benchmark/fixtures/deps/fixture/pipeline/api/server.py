"""API server — wires engine and transformer together."""

from pipeline.core.engine import Engine
from pipeline.processors.transformer import Transformer


class Server:
    """Minimal HTTP-like server that exposes the pipeline as an API."""

    def __init__(self, engine: Engine, transformer: Transformer) -> None:
        self.engine = engine
        self.transformer = transformer

    def handle(self, payload: dict) -> dict:
        records = payload.get("records", [])
        transformed = [self.transformer.process(r) for r in records]
        return {"results": self.engine.execute(transformed)}
