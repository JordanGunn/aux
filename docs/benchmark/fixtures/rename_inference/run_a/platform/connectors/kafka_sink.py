"""Kafka connector that writes processed stream data to a Kafka topic."""


class KafkaWriter:
    def write(self, records: list) -> None:
        """Publish processed stream records to the Kafka output topic."""
