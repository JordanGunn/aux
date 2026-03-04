"""
tests.test_processor — unit tests for DataProcessor.
"""
from __future__ import annotations

import pytest

from pipeline.processor import DataProcessor, make_processor


class TestDataProcessorInit:
    def test_default_schema(self) -> None:
        proc = DataProcessor()
        assert proc.schema == DataProcessor.DEFAULT_SCHEMA

    def test_strict_flag(self) -> None:
        proc = DataProcessor(strict=True)
        assert proc.strict is True

    def test_make_processor_returns_dataprocessor(self) -> None:
        proc = make_processor()
        assert isinstance(proc, DataProcessor)


class TestDataProcessorProcess:
    def test_passthrough_yields_records(self) -> None:
        proc = DataProcessor()
        records = [{"a": 1}, {"b": 2}]
        result = list(proc.process(records))
        assert result == records

    def test_strict_raises_on_missing_field(self) -> None:
        proc = DataProcessor(schema="order_v2", strict=True)
        with pytest.raises(ValueError):
            list(proc.process([{"amount": 10}]))

    def test_non_strict_skips_invalid(self) -> None:
        proc = DataProcessor(schema="order_v2", strict=False)
        result = list(proc.process([{"amount": 10}, {"order_id": "x", "amount": 5, "currency": "USD"}]))
        assert len(result) == 1

    def test_transform_applied(self) -> None:
        proc = DataProcessor()
        proc.add_transform(lambda r: {**r, "tagged": True})
        result = list(proc.process([{"x": 1}]))
        assert result[0]["tagged"] is True

    def test_reset_clears_transforms(self) -> None:
        proc = DataProcessor()
        proc.add_transform(lambda r: {**r, "tagged": True})
        proc.reset()
        result = list(proc.process([{"x": 1}]))
        assert "tagged" not in result[0]
