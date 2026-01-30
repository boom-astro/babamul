"""Kafka consumer for Babamul alerts."""

import logging
from collections.abc import Iterator

from confluent_kafka import Consumer, KafkaError, KafkaException

from .avro_utils import deserialize_alert
from .config import MAIN_KAFKA_SERVER, BabamulConfig
from .exceptions import (
    AuthenticationError,
    BabamulConnectionError,
    DeserializationError,
)
from .models import LsstAlert, ZtfAlert
from .topics import TopicType

logger = logging.getLogger(__name__)


class AlertConsumer:
    """Consumer for Babamul Kafka alert streams.

    A simple iterator-based interface for consuming astronomical transient
    alerts from Babamul's Kafka topics.
    """

    def __init__(
        self,
        topics: TopicType | list[TopicType] | str | list[str] = "",
        username: str | None = None,
        password: str | None = None,
        server: str = MAIN_KAFKA_SERVER,
        group_id: str | None = None,
        offset: str = "latest",
        timeout: float | None = None,
        auto_commit: bool = True,
        as_raw: bool = False,
    ) -> None:
        """Initialize the alert consumer.

        Parameters
        ----------
        topics : str | list[str]
            Kafka topic(s) to subscribe to. Can be a string or list of strings.
            Example: "babamul.ztf.*" or ["babamul.ztf.*", "babamul.lsst.*"]
        username : str | None
            Babamul Kafka username. Can also be set via BABAMUL_KAFKA_USERNAME env var.
        password : str | None
            Babamul Kafka password. Can also be set via BABAMUL_KAFKA_PASSWORD env var.
        server : str
            Kafka bootstrap server. Defaults to Babamul's server.
            Can also be set via BABAMUL_SERVER env var.
        group_id : str | None
            Kafka consumer group ID. Auto-generated if not provided.
        offset : str
            Where to start consuming: "latest" (default) or "earliest".
        timeout : float | None
            Timeout in seconds between messages. None means wait forever.
        auto_commit : bool
            Whether to auto-commit offsets.
        as_raw : bool
            If True, yields raw alert dictionaries instead of model instances.

        Returns
        -------
        None

        Raises
        -------
        ValueError
            If required credentials are missing.
        BabamulConnectionError
            If connection to Kafka fails.
        AuthenticationError
            If authentication fails.
        """
        # Load configuration (supports environment variables)
        self._config = BabamulConfig.from_env(
            username=username,
            password=password,
            server=server,
            group_id=group_id,
            offset=offset,
            timeout=timeout,
            auto_commit=auto_commit,
        )

        # Normalize topics to a list
        if isinstance(topics, str):
            self._topics = [topics] if topics else []
        else:
            self._topics = list(topics)

        if not self._topics:
            raise ValueError("At least one topic must be specified")

        # Generate group_id if not provided
        self._group_id = (
            self._config.group_id or f"{self._config.username}-client-1"
        )
        # Group ID must start with username-
        if not self._group_id.startswith(f"{self._config.username}-"):
            self._group_id = f"{self._config.username}-{self._group_id}"

        # Timeout in seconds for poll(), -1 means infinite
        self._poll_timeout = (
            self._config.timeout if self._config.timeout is not None else -1
        )

        # Whether to yield raw alerts or model instances
        self._as_raw = as_raw

        # Create Kafka consumer
        self._consumer: Consumer | None = None
        self._closed = False

    def _create_consumer(self) -> Consumer:
        """Create and configure the Kafka consumer."""
        config: dict[str, str | int | bool] = {
            "bootstrap.servers": self._config.server,
            "group.id": self._group_id,
            "auto.offset.reset": self._config.offset,
            "enable.auto.commit": self._config.auto_commit,
            "security.protocol": "SASL_PLAINTEXT",
            "sasl.mechanism": "SCRAM-SHA-512",
            "sasl.username": self._config.username,
            "sasl.password": self._config.password,
            # Performance tuning
            "fetch.min.bytes": 1,
            "fetch.wait.max.ms": 500,
        }

        try:
            consumer = Consumer(config)  # type: ignore
            consumer.subscribe(self._topics)
            logger.info(f"Subscribed to topics: {self._topics}")
            return consumer
        except KafkaException as e:
            error_str = str(e)
            if (
                "authentication" in error_str.lower()
                or "sasl" in error_str.lower()
            ):
                raise AuthenticationError(f"Authentication failed: {e}") from e
            raise BabamulConnectionError(
                f"Failed to connect to Kafka: {e}"
            ) from e

    def _ensure_consumer(self) -> Consumer:
        """Ensure the consumer is created and return it."""
        if self._consumer is None:
            self._consumer = self._create_consumer()
        return self._consumer

    def __iter__(self) -> Iterator[ZtfAlert | LsstAlert | dict]:
        """Iterate over alerts from the subscribed topics.

        Yields:
            BabamulZtfAlert | BabamulLsstAlert | dict objects as they are received from Kafka (dict if as_raw=True).
        Raises:
            BabamulConnectionError: If connection to Kafka is lost.
            DeserializationError: If alert deserialization fails.
        """
        consumer = self._ensure_consumer()

        while not self._closed:
            try:
                msg = consumer.poll(timeout=self._poll_timeout)

                if msg is None:
                    # Timeout reached
                    if self._config.timeout is not None:
                        logger.debug("Poll timeout reached, no more messages")
                        break
                    continue

                error = msg.error()
                if error:
                    # Use getattr for KafkaError constants for better type compatibility
                    partition_eof = getattr(KafkaError, "_PARTITION_EOF", None)
                    all_brokers_down = getattr(
                        KafkaError, "_ALL_BROKERS_DOWN", None
                    )

                    if (
                        partition_eof is not None
                        and error.code() == partition_eof
                    ):
                        # End of partition, continue polling
                        logger.debug(
                            f"Reached end of partition {msg.partition()}"
                        )
                        continue
                    elif (
                        all_brokers_down is not None
                        and error.code() == all_brokers_down
                    ):
                        raise BabamulConnectionError(
                            "All Kafka brokers are down"
                        )
                    else:
                        logger.warning(f"Kafka error: {error}")
                        continue

                # Deserialize the Avro message
                try:
                    data = msg.value()
                    if data is None:
                        continue

                    alert_dict = deserialize_alert(data)

                    if self._as_raw:
                        yield alert_dict
                        continue

                    # if the topic starts with babamul.ztf, use BabamulZtfAlert
                    if msg.topic().startswith("babamul.ztf"):  # type: ignore
                        alert = ZtfAlert.model_validate(alert_dict)
                    elif msg.topic().startswith("babamul.lsst"):  # type: ignore
                        alert = LsstAlert.model_validate(alert_dict)
                    else:
                        logger.error(f"Unknown topic format: {msg.topic()}")
                        continue
                    yield alert

                except DeserializationError as e:
                    logger.error(f"Failed to deserialize message: {e}")
                    # Continue to next message instead of failing
                    continue

            except KeyboardInterrupt:
                logger.info("Interrupted by user")
                break

    def __enter__(self) -> "AlertConsumer":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit context manager and close consumer."""
        self.close()

    def close(self) -> None:
        """Close the Kafka consumer and release resources."""
        if self._closed:
            return

        self._closed = True
        if self._consumer is not None:
            try:
                self._consumer.close()
                logger.info("Kafka consumer closed")
            except Exception as e:
                logger.warning(f"Error closing consumer: {e}")
            finally:
                self._consumer = None

    @property
    def topics(self) -> list[str]:
        """Return the list of subscribed topics."""
        return self._topics.copy()

    @property
    def group_id(self) -> str:
        """Return the consumer group ID."""
        return self._group_id
