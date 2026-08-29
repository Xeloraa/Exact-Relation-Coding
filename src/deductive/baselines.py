"""Strong statistical compressor baselines.

Every baseline is run on the exact same byte string as the raw dataset.
Missing compressors are recorded as unavailable rather than skipped silently.
"""

from __future__ import annotations

import bz2
import gc
import gzip
import io
import lzma
import time
import zlib
from typing import Callable

from deductive.results import BaselineSize

try:
    import zstandard
except ImportError:  # pragma: no cover
    zstandard = None

try:
    import brotli
except ImportError:  # pragma: no cover
    brotli = None


def _timed(fn: Callable[[], bytes]) -> tuple[bytes, float]:
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def gzip_compress(data: bytes, level: int = 9) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=level, mtime=0) as f:
        f.write(data)
    return buf.getvalue()


def zstd_compress(data: bytes, level: int = 19) -> bytes:
    if zstandard is None:
        raise RuntimeError("zstandard is not installed")
    cctx = zstandard.ZstdCompressor(level=level)
    return cctx.compress(data)


def xz_compress(data: bytes, preset: int = 9) -> bytes:
    return lzma.compress(data, format=lzma.FORMAT_XZ, preset=preset)


def bz2_compress(data: bytes, level: int = 9) -> bytes:
    return bz2.compress(data, compresslevel=level)


def brotli_compress(data: bytes, quality: int = 11) -> bytes:
    if brotli is None:
        raise RuntimeError("brotli is not installed")
    return brotli.compress(data, quality=quality)


def zlib_compress(data: bytes, level: int = 9) -> bytes:
    return zlib.compress(data, level)


_CODECS: list[tuple[str, Callable[[bytes], bytes]]] = [
    ("gzip9", lambda d: gzip_compress(d, 9)),
    ("zlib9", lambda d: zlib_compress(d, 9)),
    ("bz2_9", lambda d: bz2_compress(d, 9)),
    ("xz9", lambda d: xz_compress(d, 9)),
    ("zstd19", lambda d: zstd_compress(d, 19)),
    ("brotli11", lambda d: brotli_compress(d, 11)),
]


def run_baselines(data: bytes, *, skip_slow: bool = False) -> list[BaselineSize]:
    results: list[BaselineSize] = []
    for name, fn in _CODECS:
        if skip_slow and name in {"xz9", "brotli11"} and len(data) > 8_000_000:
            results.append(
                BaselineSize(name=name, bytes=-1, seconds=0.0, available=False, notes="skipped_slow")
            )
            continue
        try:
            gc.collect()
            out, seconds = _timed(lambda fn=fn: fn(data))
            results.append(BaselineSize(name=name, bytes=len(out), seconds=seconds, available=True))
        except Exception as exc:  # noqa: BLE001 — record unavailability honestly
            results.append(
                BaselineSize(
                    name=name,
                    bytes=-1,
                    seconds=0.0,
                    available=False,
                    notes=f"{type(exc).__name__}: {exc}",
                )
            )
    return results


def compress_named(data: bytes, name: str) -> bytes:
    mapping = {n: fn for n, fn in _CODECS}
    if name not in mapping:
        raise KeyError(name)
    return mapping[name](data)


def composition_sizes(encoded: bytes) -> dict[str, dict[str, float | int | bool | str]]:
    """Compress an already-encoded deductive container with each baseline."""
    out: dict[str, dict[str, float | int | bool | str]] = {}
    for b in run_baselines(encoded):
        out[b.name] = {
            "bytes": b.bytes,
            "seconds": b.seconds,
            "available": b.available,
            "notes": b.notes,
        }
    return out
