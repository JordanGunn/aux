"""Database connector that reads stream data records from a relational store."""


class DbReader:
    def read(self) -> list:
        """Query the database for the next window of pipeline stream records."""
        return []
