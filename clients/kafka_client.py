import json
import os
from typing import Callable, Optional

from kafka import KafkaConsumer, KafkaProducer


class KafkaClient:
    def __init__(
        self,
        producer_value_serializer: Optional[Callable] = None,
        producer_key_serializer: Optional[Callable] = None,
    ):
        self.broker = os.getenv("KAFKA_BROKER")
        version = os.getenv("KAFKA_VERSION", "0.0.0")
        self.version = tuple(int(n) for n in version.split("."))
        self.producer_value_serializer = producer_value_serializer or (
            lambda obj: obj.json().encode("utf-8")
        )
        self.producer_key_serializer = producer_key_serializer or (
            lambda k: k.encode("utf-8")
        )

        self._consumer = None
        self._producer = None

    def consumer(
        self,
        key_deserializer: Optional[Callable] = None,
        value_deserializer: Optional[Callable] = None,
    ):
        if not self._consumer:
            print("Initializing Kafka Consumer...")
            self._consumer = KafkaConsumer(
                bootstrap_servers=self.broker,
                api_version=self.version,
                key_deserializer=key_deserializer or (lambda k: k.decode("utf-8")),
                value_deserializer=value_deserializer
                or (lambda v: json.loads(v.decode("utf-8"))),
            )

        return self._consumer

    @property
    def producer(self):
        if not self._producer:
            print("Initializing Kafka Producer...")
            self._producer = KafkaProducer(
                bootstrap_servers=self.broker,
                api_version=self.version,
                compression_type="snappy",
                value_serializer=self.producer_value_serializer,
                key_serializer=self.producer_key_serializer,
            )

        return self._producer

    def publish(self, topic: str, value: dict, key: Optional[str] = None):
        self.producer.send(topic, key=key, value=value)
