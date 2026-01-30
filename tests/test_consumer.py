"""Tests for babamul.consumer."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from babamul import AlertConsumer
from babamul.models import LsstAlert, ZtfAlert


class TestAlertConsumerInit:
    """Tests for AlertConsumer initialization."""

    def test_missing_credentials(self) -> None:
        """Test error when credentials are missing."""
        with pytest.raises(ValueError, match="Username is required"):
            AlertConsumer(topics=["test.topic"])

    def test_missing_password(self) -> None:
        """Test error when password is missing."""
        with pytest.raises(ValueError, match="Password is required"):
            AlertConsumer(username="user", topics=["test.topic"])

    def test_missing_topic(self) -> None:
        """Test error when topic is missing."""
        with pytest.raises(ValueError, match="At least one topic"):
            AlertConsumer(username="user", password="pass", topics=[])

    def test_single_topic(self) -> None:
        """Test initialization with single topic."""
        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["test.topic"],
        )
        assert consumer.topics == ["test.topic"]
        consumer.close()

    def test_multiple_topics(self) -> None:
        """Test initialization with multiple topics."""
        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["topic1", "topic2"],
        )
        assert consumer.topics == ["topic1", "topic2"]
        consumer.close()

    def test_auto_generated_group_id(self) -> None:
        """Test auto-generated group ID."""
        consumer = AlertConsumer(
            username="testuser",
            password="pass",
            topics=["test.topic"],
        )
        assert consumer.group_id == "testuser-client-1"
        consumer.close()

    def test_custom_group_id(self) -> None:
        """Test custom group ID."""
        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["test.topic"],
            group_id="my-custom-group",
        )
        assert consumer.group_id == "user-my-custom-group"
        consumer.close()

    def test_env_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading credentials from environment."""
        monkeypatch.setenv("BABAMUL_KAFKA_USERNAME", "env_user")
        monkeypatch.setenv("BABAMUL_KAFKA_PASSWORD", "env_pass")

        consumer = AlertConsumer(topics=["test.topic"])
        assert consumer.topics == ["test.topic"]
        consumer.close()


class TestAlertConsumerContextManager:
    """Tests for AlertConsumer context manager."""

    def test_context_manager(self) -> None:
        """Test context manager protocol."""
        with AlertConsumer(
            username="user",
            password="pass",
            topics=["test.topic"],
        ) as consumer:
            assert consumer.topics == ["test.topic"]


class TestAlertConsumerIteration:
    """Tests for AlertConsumer iteration."""

    @patch("babamul.consumer.deserialize_alert")
    @patch("babamul.consumer.Consumer")
    def test_iteration_with_messages(
        self,
        mock_consumer_class: MagicMock,
        mock_deserialize: MagicMock,
        sample_ztf_alert_dict: dict[str, Any],
    ) -> None:
        """Test iterating over messages."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_msg1 = MagicMock()
        mock_msg1.error.return_value = None
        mock_msg1.value.return_value = b"fake_avro_data"
        mock_msg1.topic.return_value = "babamul.ztf.lsst-match.hosted"

        mock_msg2 = MagicMock()
        mock_msg2.error.return_value = None
        mock_msg2.value.return_value = b"fake_avro_data"
        mock_msg2.topic.return_value = "babamul.ztf.lsst-match.hosted"

        mock_consumer.poll.side_effect = [mock_msg1, mock_msg2, None]
        mock_deserialize.return_value = sample_ztf_alert_dict

        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["babamul.ztf.lsst-match.hosted"],
            timeout=1.0,
        )

        alerts = list(consumer)
        assert len(alerts) == 2
        assert alerts[0].objectId == "ZTF24aabcdef"
        assert alerts[1].objectId == "ZTF24aabcdef"

    @patch("babamul.consumer.deserialize_alert")
    @patch("babamul.consumer.Consumer")
    def test_iteration_handles_null_value_messages(
        self,
        mock_consumer_class: MagicMock,
        mock_deserialize: MagicMock,
        sample_ztf_alert_dict: dict[str, Any],
    ) -> None:
        """Test that messages with null values are skipped."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_msg_valid = MagicMock()
        mock_msg_valid.error.return_value = None
        mock_msg_valid.value.return_value = b"fake_avro_data"
        mock_msg_valid.topic.return_value = "babamul.ztf.lsst-match.hosted"

        mock_msg_null = MagicMock()
        mock_msg_null.error.return_value = None
        mock_msg_null.value.return_value = None

        mock_consumer.poll.side_effect = [
            mock_msg_valid,
            mock_msg_null,
            mock_msg_valid,
            None,
        ]
        mock_deserialize.return_value = sample_ztf_alert_dict

        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["babamul.ztf.lsst-match.hosted"],
            timeout=0.1,
        )

        alerts = list(consumer)
        assert len(alerts) == 2

    @patch("babamul.consumer.deserialize_alert")
    @patch("babamul.consumer.Consumer")
    def test_close_stops_iteration(
        self,
        mock_consumer_class: MagicMock,
        mock_deserialize: MagicMock,
        sample_ztf_alert_dict: dict[str, Any],
    ) -> None:
        """Test that close() stops iteration."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"fake_avro_data"
        mock_msg.topic.return_value = "babamul.ztf.lsst-match.hosted"
        mock_consumer.poll.return_value = mock_msg
        mock_deserialize.return_value = sample_ztf_alert_dict

        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["babamul.ztf.lsst-match.hosted"],
        )

        count = 0
        for _ in consumer:
            count += 1
            if count >= 2:
                consumer.close()

        assert count == 2

    @patch("babamul.consumer.deserialize_alert")
    @patch("babamul.consumer.Consumer")
    def test_iteration_routes_ztf_topic_to_ztf_model(
        self,
        mock_consumer_class: MagicMock,
        mock_deserialize: MagicMock,
        sample_ztf_alert_dict: dict[str, Any],
    ) -> None:
        """Test that messages from babamul.ztf topics produce BabamulZtfAlert."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"fake_avro_data"
        mock_msg.topic.return_value = "babamul.ztf.no-lsst-match.hostless"

        mock_consumer.poll.side_effect = [mock_msg, None]
        mock_deserialize.return_value = sample_ztf_alert_dict

        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["babamul.ztf.no-lsst-match.hostless"],
            timeout=1.0,
        )

        alerts = list(consumer)
        assert len(alerts) == 1
        assert isinstance(alerts[0], ZtfAlert)

    @patch("babamul.consumer.deserialize_alert")
    @patch("babamul.consumer.Consumer")
    def test_iteration_routes_lsst_topic_to_lsst_model(
        self,
        mock_consumer_class: MagicMock,
        mock_deserialize: MagicMock,
        sample_lsst_alert_dict: dict[str, Any],
    ) -> None:
        """Test that messages from babamul.lsst topics produce BabamulLsstAlert."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        mock_msg = MagicMock()
        mock_msg.error.return_value = None
        mock_msg.value.return_value = b"fake_avro_data"
        mock_msg.topic.return_value = "babamul.lsst.ztf-match.hosted"

        mock_consumer.poll.side_effect = [mock_msg, None]
        mock_deserialize.return_value = sample_lsst_alert_dict

        consumer = AlertConsumer(
            username="user",
            password="pass",
            topics=["babamul.lsst.ztf-match.hosted"],
            timeout=1.0,
        )

        alerts = list(consumer)
        assert len(alerts) == 1
        assert isinstance(alerts[0], LsstAlert)
        assert alerts[0].objectId == "LSST24aabcdef"
