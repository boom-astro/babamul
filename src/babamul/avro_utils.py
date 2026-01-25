"""Avro deserialization utilities for BOOM alerts."""

import io
from typing import Any

import fastavro

def deserialize_alert(data: bytes) -> dict[str, Any]:
    """Deserialize an Avro-encoded BOOM alert.

    Args:
        data: Raw Avro bytes from Kafka message

    Returns:
        Deserialized alert as a dictionary

    Raises:
        DeserializationError: If deserialization fails
    """
    reader = fastavro.reader(io.BytesIO(data))
    result: dict[str, Any] = next(reader)
    return result
