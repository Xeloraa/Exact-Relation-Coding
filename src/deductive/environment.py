"""Environment and reproducibility metadata."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any


def git_commit(repo: Path | None = None) -> str:
    cwd = str(repo) if repo is not None else None
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        dirty = subprocess.call(
            ["git", "diff", "--quiet"],
            cwd=cwd,
            stderr=subprocess.DEVNULL,
        )
        if dirty != 0:
            return f"{out}-dirty"
        return out
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "UNCOMMITTED"


def _pkg_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def compressor_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {
        "python": sys.version.split()[0],
        "gzip": "stdlib",
        "bz2": "stdlib",
        "lzma": "stdlib",
        "zlib": "stdlib",
        "numpy": _pkg_version("numpy"),
        "zstandard": _pkg_version("zstandard"),
        "brotli": _pkg_version("brotli"),
    }
    return versions


def machine_info() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python": sys.version,
        "executable": sys.executable,
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "node": platform.node(),
        "utc_timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "package_versions": compressor_versions(),
    }


def command_line() -> str:
    return subprocess.list2cmdline(sys.argv) if os.name == "nt" else " ".join(
        _quote(a) for a in sys.argv
    )


def _quote(arg: str) -> str:
    if not arg or any(c.isspace() for c in arg):
        return '"' + arg.replace('"', '\\"') + '"'
    return arg
