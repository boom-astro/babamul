"""Background version check: warn users when a newer version is available."""

import threading
import warnings
from typing import Optional


def _fetch_latest_version(package: str) -> Optional[str]:
    """Fetch the latest version of *package* from PyPI.

    Returns the version string on success, or ``None`` on any error so that
    network failures never propagate to the caller.
    """
    try:
        import httpx

        response = httpx.get(
            f"https://pypi.org/pypi/{package}/json",
            timeout=5.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.json()["info"]["version"]
    except Exception:
        return None


def _check_and_warn(current_version: str, package: str) -> None:
    """Compare *current_version* against PyPI and emit a warning if outdated."""
    latest = _fetch_latest_version(package)
    if latest is None:
        return

    try:
        from packaging.version import Version

        if Version(latest) > Version(current_version):
            warnings.warn(
                f"A newer version of {package} is available: {latest} "
                f"(you have {current_version}). "
                f"Upgrade with: pip install --upgrade {package}",
                UserWarning,
                stacklevel=2,
            )
    except Exception:
        pass


def check_version(current_version: str, package: str = "babamul") -> None:
    """Spawn a background thread that checks for a newer release on PyPI.

    The check is intentionally fire-and-forget so that it never blocks or
    slows down the package import.
    """
    if current_version == "0.0.0+unknown":
        # Development / editable install without VCS version — skip check.
        return

    thread = threading.Thread(
        target=_check_and_warn,
        args=(current_version, package),
        daemon=True,
        name="babamul-version-check",
    )
    thread.start()
