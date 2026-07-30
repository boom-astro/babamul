"""Tests for the babamul version check module."""

import threading
import warnings
from unittest.mock import MagicMock, patch

import pytest

from babamul._version_check import _check_and_warn, check_version


class TestCheckAndWarn:
    def test_warns_when_newer_version_available(self):
        with patch(
            "babamul._version_check._fetch_latest_version",
            return_value="99.0.0",
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _check_and_warn("1.0.0", "babamul")

        assert len(caught) == 1
        w = caught[0]
        assert issubclass(w.category, UserWarning)
        assert "99.0.0" in str(w.message)
        assert "1.0.0" in str(w.message)
        assert "babamul" in str(w.message)

    def test_no_warning_when_up_to_date(self):
        with patch(
            "babamul._version_check._fetch_latest_version",
            return_value="1.0.0",
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _check_and_warn("1.0.0", "babamul")

        assert len(caught) == 0

    def test_no_warning_when_fetch_returns_none(self):
        with patch(
            "babamul._version_check._fetch_latest_version",
            return_value=None,
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _check_and_warn("1.0.0", "babamul")

        assert len(caught) == 0

    def test_no_warning_on_newer_installed_version(self):
        """No warning when the installed version is newer than PyPI."""
        with patch(
            "babamul._version_check._fetch_latest_version",
            return_value="0.9.0",
        ):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                _check_and_warn("1.0.0", "babamul")

        assert len(caught) == 0


class TestCheckVersion:
    def test_skips_unknown_version(self):
        """check_version should not spawn a thread for dev installs."""
        with patch("babamul._version_check.threading.Thread") as mock_thread:
            check_version("0.0.0+unknown")
        mock_thread.assert_not_called()

    def test_spawns_background_thread(self):
        """check_version should start a daemon thread for real versions."""
        mock_thread_instance = MagicMock()
        with patch(
            "babamul._version_check.threading.Thread",
            return_value=mock_thread_instance,
        ) as mock_thread_cls:
            check_version("1.2.3", package="babamul")

        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs.get("daemon") is True
        mock_thread_instance.start.assert_called_once()

    def test_thread_is_daemon(self):
        """The version-check thread must be a daemon so it doesn't block exit."""
        spawned: list[threading.Thread] = []

        original_thread = threading.Thread

        def capture_thread(*args, **kwargs):
            t = original_thread(*args, **kwargs)
            spawned.append(t)
            return t

        with patch("babamul._version_check.threading.Thread", capture_thread):
            with patch(
                "babamul._version_check._check_and_warn"
            ):  # don't actually hit PyPI
                check_version("1.2.3")

        assert len(spawned) == 1
        assert spawned[0].daemon is True
