"""Reads events from the message queue for pipeline processing."""


class EventReader:
    def read(self) -> list:
        """Pull the next batch of events from the upstream topic."""
        return []
