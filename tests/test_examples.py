"""Tests for examples."""

import subprocess


def test_stream_app():
    """Test the stream app example."""
    result = subprocess.run(
        ["uv", "run", "python", "main.py"],
        capture_output=True,
        text=True,
        cwd="examples/stream-app",
    )
    assert result.returncode == 0, f"Stream app failed: {result.stderr}"
