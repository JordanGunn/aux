"""Writes processed events to the downstream pipeline topic."""


class EventWriter:
    def write(self, records: list) -> None:
        """Publish processed events to the output topic."""
