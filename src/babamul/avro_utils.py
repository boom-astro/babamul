"""Avro deserialization utilities for Babamul alerts."""

import io
from typing import Any

import fastavro


def deserialize_alert(data: bytes) -> dict[str, Any]:
    """Deserialize an Avro-encoded Babamul alert.

    Parameters
    ----------
    data : bytes
        The Avro-encoded alert data.

    Returns
    -------
    dict[str, Any]
        The deserialized alert as a dictionary.

    Raises
    ------
    fastavro._reader.SchemaResolutionError
        If the data cannot be deserialized due to schema mismatch.
    """
    reader = fastavro.reader(io.BytesIO(data))
    result: dict[str, Any] = next(reader)
    return result
