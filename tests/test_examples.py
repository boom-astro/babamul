"""Tests for examples."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import cast

import tomlkit
import tomlkit.items

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


def test_api(tmp_path: Path):
    """Test the API example."""
    env = {**os.environ, "MPLBACKEND": "Agg"}
    api_source_dir = REPO_ROOT / "examples" / "api"
    api_work_dir = tmp_path / "api"
    shutil.copytree(api_source_dir, api_work_dir)
    pyproject_path = api_work_dir / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    # Keep the example's pyproject unchanged and inject local source for tests
    pyproject_doc = tomlkit.parse(pyproject_text)
    project = cast(tomlkit.items.Table, pyproject_doc["project"])
    dependencies = cast(tomlkit.items.Array, project["dependencies"])
    local_dep = f"babamul @ file://{REPO_ROOT}"
    replaced = False
    for idx, dep in enumerate(dependencies):
        if dep.unwrap() == "babamul":
            dependencies[idx] = local_dep
            replaced = True
            break
    assert replaced, "Expected babamul dependency in API pyproject"
    pyproject_path.write_text(tomlkit.dumps(pyproject_doc), encoding="utf-8")
    result = subprocess.run(
        [
            "uvx",
            "calk9",
            "nb",
            "exec",
            "-e",
            "pyproject.toml",
            "notebook.ipynb",
        ],
        capture_output=True,
        text=True,
        cwd=api_work_dir,
        env=env,
    )
    generated_notebook = api_work_dir / "notebook.ipynb"
    if generated_notebook.exists():
        shutil.copy2(generated_notebook, api_source_dir / "notebook.ipynb")
    assert result.returncode == 0, f"API example failed: {result.stderr}"
