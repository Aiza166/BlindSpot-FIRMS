"""Input hashes and code commit for results JSON."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from blindspot.download import sha256_file


def hash_path(path: Path) -> dict:
    """sha256 of a file, or of a directory as the hash of its sorted (relative path, sha256)
    list. Missing paths are reported, not hidden."""
    path = Path(path)
    if path.is_file():
        return {"path": str(path), "sha256": sha256_file(path), "n_files": 1}
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
        h = hashlib.sha256()
        for f in files:
            h.update(f"{f.relative_to(path).as_posix()}\t{sha256_file(f)}\n".encode())
        return {"path": str(path), "sha256": h.hexdigest(), "n_files": len(files)}
    return {"path": str(path), "sha256": None, "missing": True}


def git_state(repo: Path) -> dict:
    def run(*args: str) -> str:
        return subprocess.run(  # noqa: S603 - fixed git arguments, no user input
            ["git", "-C", str(repo), *args],  # noqa: S607 - git from PATH
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

    commit = run("rev-parse", "HEAD")
    dirty = run("status", "--porcelain", "--", "pipeline", "Makefile", "pyproject.toml")
    return {"commit": commit or None, "code_dirty": bool(dirty)}


def collect(inputs: dict[str, Path], repo: Path) -> dict:
    return {"inputs": {k: hash_path(v) for k, v in inputs.items()}, "code": git_state(repo)}
