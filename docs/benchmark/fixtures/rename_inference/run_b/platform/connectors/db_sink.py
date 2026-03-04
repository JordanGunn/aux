"""Database connector that writes processed stream records to a relational store."""


class DbWriter:
    def write(self, records: list) -> None:
        """Persist processed pipeline stream records to the database."""
