"""
pipeline.processor — core DataProcessor implementation.

DataProcessor is the central unit of the pipeline. It receives raw records,
validates schema, applies transformations, and emits typed output events.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Iterable, Iterator, Optional

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process raw records into structured output events.

    DataProcessor is stateless between batches. Each call to :meth:`process`
    creates an isolated execution context so DataProcessor instances can be
    shared across threads without synchronisation overhead.

    Example::

        processor = DataProcessor(schema="order_v2", strict=True)
        for event in processor.process(raw_records):
            sink.emit(event)
    """

    #: Default field used by DataProcessor when no schema is specified.
    DEFAULT_SCHEMA = "passthrough"

    def __init__(
        self,
        schema: str = DEFAULT_SCHEMA,
        strict: bool = False,
        transforms: Optional[list[Callable[[dict], dict]]] = None,
    ) -> None:
        """Initialise a DataProcessor.

        Args:
            schema: Name of the validation schema. DataProcessor looks this up
                    in the internal schema registry at construction time.
            strict: When *True*, DataProcessor raises on the first validation
                    error rather than skipping the record.
            transforms: Optional list of callables applied by DataProcessor
                        in order after validation.
        """
        self.schema = schema
        self.strict = strict
        self.transforms: list[Callable[[dict], dict]] = transforms or []
        self._schema_def = self._load_schema(schema)
        logger.debug("DataProcessor initialised with schema=%r strict=%r", schema, strict)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, records: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        """Yield validated and transformed records.

        DataProcessor applies each transform in :attr:`transforms` sequentially.
        Malformed records are skipped (or raise if ``strict=True``).

        Args:
            records: Iterable of raw dicts as produced by a connector.

        Yields:
            Validated, transformed dicts ready for downstream consumers.
        """
        for record in records:
            try:
                validated = self._validate(record)
                yield self._apply_transforms(validated)
            except ValueError as exc:
                if self.strict:
                    raise
                logger.warning("DataProcessor skipping invalid record: %s", exc)

    def add_transform(self, fn: Callable[[dict], dict]) -> "DataProcessor":
        """Register a transform and return *self* for chaining.

        Args:
            fn: Callable that accepts and returns a dict.  DataProcessor calls
                transforms in registration order.

        Returns:
            This DataProcessor instance (fluent interface).
        """
        self.transforms.append(fn)
        return self

    def reset(self) -> None:
        """Clear all registered transforms from this DataProcessor."""
        self.transforms.clear()
        logger.debug("DataProcessor transforms cleared")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_schema(self, name: str) -> dict:
        """Return the schema definition for *name*.

        DataProcessor falls back to an empty schema dict when the name is
        not registered, unless ``strict=True``.
        """
        registry: dict[str, dict] = {
            "passthrough": {},
            "order_v2": {"required": ["order_id", "amount", "currency"]},
        }
        if name not in registry and self.strict:
            raise KeyError(f"DataProcessor: unknown schema {name!r}")
        return registry.get(name, {})

    def _validate(self, record: dict[str, Any]) -> dict[str, Any]:
        required = self._schema_def.get("required", [])
        missing = [k for k in required if k not in record]
        if missing:
            raise ValueError(f"DataProcessor validation failed — missing fields: {missing}")
        return record

    def _apply_transforms(self, record: dict[str, Any]) -> dict[str, Any]:
        for fn in self.transforms:
            record = fn(record)
        return record


def make_processor(schema: str = "passthrough", strict: bool = False) -> DataProcessor:
    """Factory helper that returns a ready-to-use DataProcessor.

    Equivalent to ``DataProcessor(schema=schema, strict=strict)``.
    """
    return DataProcessor(schema=schema, strict=strict)
