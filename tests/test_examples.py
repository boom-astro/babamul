"""Tests for examples."""

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import cast

import pytest
import tomlkit
import tomlkit.items

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_example_notebook(
    source_dir: Path,
    tmp_path: Path,
    no_copy_paths: list[str] | None = None,
    params: dict[str, str] | None = None,
) -> None:
    """Copy an example directory to tmp_path, patch babamul to the local repo,
    run the notebook with Calkit, then copy the executed notebook back.
    """
    work_dir = tmp_path / source_dir.name
    # If no_copy_paths is provided, we need to copy files individually instead
    # of the entire directory
    if no_copy_paths:
        work_dir.mkdir()
        for item in source_dir.iterdir():
            if item.name not in no_copy_paths:
                dest = work_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
    else:
        shutil.copytree(source_dir, work_dir)
    pyproject_path = work_dir / "pyproject.toml"
    pyproject_doc = tomlkit.parse(pyproject_path.read_text(encoding="utf-8"))
    project = cast(tomlkit.items.Table, pyproject_doc["project"])
    dependencies = cast(tomlkit.items.Array, project["dependencies"])
    local_dep = f"babamul @ file://{REPO_ROOT}"
    replaced = False
    for idx, dep in enumerate(dependencies):
        if dep.unwrap() == "babamul":
            dependencies[idx] = local_dep
            replaced = True
            break
    assert replaced, f"Expected babamul dependency in {pyproject_path}"
    pyproject_path.write_text(tomlkit.dumps(pyproject_doc), encoding="utf-8")
    params_json = json.dumps(params) if params else None
    result = subprocess.run(
        [
            "uv",
            "run",
            "calkit",
            "nb",
            "exec",
            "-e",
            "pyproject.toml",
            "notebook.ipynb",
        ]
        + (["--params-json", params_json] if params_json else []),
        capture_output=True,
        text=True,
        cwd=work_dir,
    )
    # Copy notebook back to working directory so we can commit it
    executed_notebook = work_dir / "notebook.ipynb"
    if executed_notebook.exists():
        shutil.copy2(executed_notebook, source_dir / "notebook.ipynb")
    assert (
        result.returncode == 0
    ), f"{source_dir.name} notebook failed: {result.stderr}"


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
    """Test the API example notebook."""
    _run_example_notebook(REPO_ROOT / "examples" / "api", tmp_path)


@pytest.mark.skip(reason="Takes a long time to run")
def test_stream_basic(tmp_path: Path):
    """Test the stream-basic example notebook."""
    _run_example_notebook(REPO_ROOT / "examples" / "stream-basic", tmp_path)


def test_stream_cached(tmp_path: Path):
    """Test the stream-cached example notebook."""
    _run_example_notebook(
        REPO_ROOT / "examples" / "stream-cached",
        tmp_path,
        no_copy_paths=["data"],
        params={"group_id": uuid.uuid4().hex[:8]},
    )
