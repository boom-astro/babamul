"""Tests for examples."""

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stream_app():
    """Test the stream app example."""
    env = {**os.environ, "MPLBACKEND": "Agg"}
    result = subprocess.run(
        ["uv", "run", "--with-editable", str(REPO_ROOT), "python", "main.py"],
        capture_output=True,
        text=True,
        cwd="examples/stream-app",
        env=env,
    )
    assert result.returncode == 0, f"Stream app failed: {result.stderr}"
