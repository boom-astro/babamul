"""Warn when a newer babamul release is available on PyPI."""

from __future__ import annotations

import json
import os
import threading
import time
import warnings
from pathlib import Path

import httpx
from packaging.version import InvalidVersion, Version

PYPI_URL = "https://pypi.org/pypi/babamul/json"
CHECK_INTERVAL_SECONDS = 24 * 3600


def _cache_path() -> Path:
    cache_home = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(cache_home) / "babamul" / "releases.json"


def _read_cached_releases() -> list[str] | None:
    try:
        cached = json.loads(_cache_path().read_text())
        if time.time() - cached["checked_at"] < CHECK_INTERVAL_SECONDS:
            return list(cached["releases"])
    except Exception:
        pass
    return None


def _write_cached_releases(releases: list[str]) -> None:
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(
            json.dumps({"checked_at": time.time(), "releases": releases})
        )
        tmp.replace(path)
    except OSError:
        pass


def _fetch_releases() -> list[str]:
    response = httpx.get(PYPI_URL, timeout=5.0)
    response.raise_for_status()
    return [
        release
        for release, files in response.json()["releases"].items()
        if files and not all(f.get("yanked") for f in files)
    ]


def _latest(installed: Version, releases: list[str]) -> Version | None:
    versions = []
    for release in releases:
        try:
            version = Version(release)
        except InvalidVersion:
            continue
        if version.is_prerelease and not installed.is_prerelease:
            continue
        versions.append(version)
    return max(versions, default=None)


def _warn_if_outdated(installed: Version, releases: list[str]) -> None:
    latest = _latest(installed, releases)
    if latest is not None and latest > installed:
        warnings.warn(
            f"babamul {latest} is available (you have {installed}). "
            "Upgrade with: pip install --upgrade babamul",
            UserWarning,
            stacklevel=1,
        )


def _refresh_and_warn(installed: Version) -> None:
    try:
        releases = _fetch_releases()
    except Exception:
        return
    _write_cached_releases(releases)
    _warn_if_outdated(installed, releases)


def check_version(installed_version: str) -> None:
    """Warn if a newer release exists, without slowing down the import.

    PyPI is queried at most once a day, in a background thread; in between,
    the cached release list is used. Set ``BABAMUL_NO_VERSION_CHECK=1`` to
    turn this off.
    """
    if os.environ.get("BABAMUL_NO_VERSION_CHECK"):
        return
    try:
        installed = Version(installed_version)
    except InvalidVersion:
        return
    if installed.is_devrelease or installed.local:
        return

    releases = _read_cached_releases()
    if releases is not None:
        _warn_if_outdated(installed, releases)
        return
    threading.Thread(
        target=_refresh_and_warn, args=(installed,), daemon=True
    ).start()
