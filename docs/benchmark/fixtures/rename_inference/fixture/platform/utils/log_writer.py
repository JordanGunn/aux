"""Writes structured log entries to the application log backend."""


class LogWriter:
    def write(self, message: str, level: str = "info") -> None:
        """Emit a structured log entry at the specified severity level."""
