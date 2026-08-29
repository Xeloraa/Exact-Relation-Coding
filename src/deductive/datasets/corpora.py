"""Real-corpus loaders.

Large copyrighted datasets are not stored in git. This module documents
how to obtain public samples and provides tiny built-in fixtures for
automated tests (source snippets, JSON, CSV, logs).
"""

from __future__ import annotations

import io
import json
import sqlite3
import struct
import sys
import tempfile
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusItem:
    dataset_id: str
    data: bytes
    category: str
    notes: str


BUILTIN_C_SNIPPET = b"""/* tiny public-domain-style fixture, not a corpus */
#include <stdio.h>
int checksum(const unsigned char *p, int n) {
    unsigned s = 0;
    for (int i = 0; i < n; i++) s += p[i];
    return (int)s;
}
int main(void) {
    unsigned char buf[4] = {1, 2, 3, 6};
    printf("%d\\n", checksum(buf, 4));
    return 0;
}
"""

BUILTIN_JSON = json.dumps(
    {
        "records": [
            {"id": 1, "x": 10, "y": 20, "sum": 30},
            {"id": 2, "x": 3, "y": 4, "sum": 7},
            {"id": 3, "x": 8, "y": 1, "sum": 9},
        ]
    },
    indent=2,
).encode("utf-8")

BUILTIN_CSV = (
    "a,b,c\n"
    "1,2,3\n"
    "4,5,9\n"
    "10,20,30\n"
    "7,8,15\n"
).encode("ascii")

BUILTIN_LOG = b"""2026-08-29T12:00:00Z INFO start request_id=abc length=12
2026-08-29T12:00:01Z INFO done request_id=abc status=200
2026-08-29T12:00:02Z WARN retry request_id=def length=4
"""


def builtin_sqlite_bytes() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        path = tmp.name
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("create table t (a integer, b integer, c integer)")
        cur.executemany("insert into t values (?,?,?)", [(1, 2, 3), (4, 5, 9), (10, 11, 21)])
        con.commit()
        con.close()
        return Path(path).read_bytes()
    finally:
        Path(path).unlink(missing_ok=True)


def builtin_corpora() -> list[CorpusItem]:
    items = [
        CorpusItem("builtin_c", BUILTIN_C_SNIPPET, "source_code", "tiny C fixture"),
        CorpusItem("builtin_json", BUILTIN_JSON, "json", "tiny JSON with sum field"),
        CorpusItem("builtin_csv", BUILTIN_CSV, "csv", "tiny CSV with c=a+b"),
        CorpusItem("builtin_log", BUILTIN_LOG, "logs", "tiny log lines"),
        CorpusItem("builtin_sqlite", builtin_sqlite_bytes(), "sqlite", "tiny sqlite table"),
    ]
    return items


CORPUS_PREP = """
# Real corpora (not shipped)

Do not commit copyrighted datasets.

enwik8:
  wget http://mattmahoney.net/dc/enwik8.zip
  unzip enwik8.zip

Silesia (dumps not committed):
  wget http://mattmahoney.net/dc/silesia.zip
  # mirrors: https://www.mattmahoney.net/dc/silesia.zip
  # original index: https://sun.aei.polsl.pl/~sdeor/index.php?page=silesia

CTU-13 NetFlow (tabular / FD control; format-awareness trap):
  public research dataset; treat derived-column wins as known FD elimination
  unless the same mechanism wins on non-tabular bytes.

Place downloads under data/downloads/ (gitignored) and point experiments
at those paths.
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def downloads_dir() -> Path:
    d = _repo_root() / "data" / "downloads"
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_png(width: int = 32, height: int = 32, seed: int = 0) -> bytes:
    """Minimal RGB PNG. Chunk CRCs are present; a general bit-matrix should not parse PNG."""
    import numpy as np

    rng = np.random.default_rng(seed)
    pixels = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw.extend(pixels[y].tobytes())
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(b"IEND", b"")


# DOS date/time in the ZIP local header; must be fixed or SHA-256 changes every run.
_ZIP_STORED_MTIME = (2026, 8, 29, 0, 0, 0)


def make_zip_stored(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as zf:
        for name, data in files.items():
            info = zipfile.ZipInfo(filename=name, date_time=_ZIP_STORED_MTIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 0
            info.external_attr = 0
            zf.writestr(info, data)
    return buf.getvalue()


def make_sqlite_fd(*, n_rows: int, seed: int) -> bytes:
    """SQLite table with an exact derived column c = a + b. FD / format trap."""
    import numpy as np

    rng = np.random.default_rng(seed)
    a = rng.integers(0, 10_000, size=n_rows)
    b = rng.integers(0, 10_000, size=n_rows)
    c = a + b
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as tmp:
        path = tmp.name
    try:
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("create table t (a integer, b integer, c integer)")
        cur.executemany("insert into t values (?,?,?)", zip(map(int, a), map(int, b), map(int, c)))
        con.commit()
        con.close()
        return Path(path).read_bytes()
    finally:
        Path(path).unlink(missing_ok=True)


def make_csv_fd(*, n_rows: int, seed: int) -> bytes:
    import numpy as np

    rng = np.random.default_rng(seed)
    a = rng.integers(0, 10_000, size=n_rows)
    b = rng.integers(0, 10_000, size=n_rows)
    lines = ["a,b,c"]
    for x, y in zip(a, b):
        lines.append(f"{int(x)},{int(y)},{int(x + y)}")
    return ("\n".join(lines) + "\n").encode("ascii")


def python_stdlib_sample(*, max_bytes: int = 400_000) -> bytes | None:
    """Concatenate .py files from the local standard library. Not uploaded to git."""
    lib = Path(sys.base_prefix) / "Lib"
    if not lib.is_dir():
        return None
    chunks: list[bytes] = []
    total = 0
    for path in sorted(lib.glob("*.py")):
        try:
            data = path.read_bytes()
        except OSError:
            continue
        chunks.append(data)
        chunks.append(b"\n")
        total += len(data) + 1
        if total >= max_bytes:
            break
    blob = b"".join(chunks)[:max_bytes]
    return blob or None


def local_pe_sample(*, max_bytes: int = 512_000) -> bytes | None:
    """Prefix of the running Python interpreter (PE/ELF). Not uploaded to git."""
    path = Path(sys.executable)
    if not path.is_file():
        return None
    data = path.read_bytes()[:max_bytes]
    return data or None


def load_enwik8_prefix(n_bytes: int = 1_000_000) -> tuple[bytes | None, str]:
    """Load a prefix of enwik8 from data/downloads if present. Never commits the dump."""
    root = downloads_dir()
    for name in ("enwik8", "enwik8.txt"):
        path = root / name
        if path.is_file():
            data = path.read_bytes()[:n_bytes]
            return data, f"local {path.name} prefix {len(data)}"
    zpath = root / "enwik8.zip"
    if zpath.is_file():
        with zipfile.ZipFile(zpath) as zf:
            names = zf.namelist()
            target = "enwik8" if "enwik8" in names else names[0]
            with zf.open(target) as f:
                data = f.read(n_bytes)
            return data, f"zip {zpath.name} prefix {len(data)}"
    return None, "enwik8 not present under data/downloads/"


def try_download_enwik8_zip(timeout: int = 60) -> str:
    """Best-effort download. Failures are recorded, not retried forever."""
    import urllib.request

    dest = downloads_dir() / "enwik8.zip"
    if dest.is_file() and dest.stat().st_size > 1_000_000:
        return f"already have {dest}"
    url = "http://mattmahoney.net/dc/enwik8.zip"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            dest.write_bytes(resp.read())
        return f"downloaded {dest.stat().st_size} bytes"
    except Exception as exc:  # noqa: BLE001
        return f"download failed: {type(exc).__name__}: {exc}"


SILESIA_ZIP_URLS = (
    "http://mattmahoney.net/dc/silesia.zip",
    "https://www.mattmahoney.net/dc/silesia.zip",
    "https://github.com/DataCompression/corpus-collection/raw/main/Silesia-Corpus/silesia.zip",
)

SILESIA_MEMBERS = (
    "dickens",
    "mozilla",
    "mr",
    "nci",
    "ooffice",
    "osdb",
    "reymont",
    "samba",
    "sao",
    "webster",
    "x-ray",
    "xml",
)
SILESIA_MEMBER_URLS = {
    name: f"https://raw.githubusercontent.com/MiloszKrajewski/SilesiaCorpus/master/{name}.zip"
    for name in SILESIA_MEMBERS
}


def try_download_silesia_zip(timeout: int = 180) -> str:
    """Best-effort Silesia zip. Failures are recorded, not retried forever."""
    import urllib.request

    dest = downloads_dir() / "silesia.zip"
    if dest.is_file() and dest.stat().st_size > 10_000_000:
        return f"already have {dest.name} ({dest.stat().st_size} bytes)"
    tmp = dest.with_suffix(".zip.part")
    last = "no urls"
    for url in SILESIA_ZIP_URLS:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                tmp.write_bytes(resp.read())
            size = tmp.stat().st_size
            if size < 1_000_000:
                last = f"{url}: too small ({size})"
                tmp.unlink(missing_ok=True)
                continue
            tmp.replace(dest)
            return f"downloaded {dest.stat().st_size} bytes from {url}"
        except Exception as exc:  # noqa: BLE001
            last = f"{url}: {type(exc).__name__}: {exc}"
            tmp.unlink(missing_ok=True)
    return f"download failed: {last}"


def _silesia_entry_name(zf: zipfile.ZipFile, member: str) -> str | None:
    files = [name for name in zf.namelist() if not name.endswith("/")]
    for name in files:
        base = name.rstrip("/").split("/")[-1]
        if base == member:
            return name
    if len(files) == 1:
        return files[0]
    return None


def try_download_silesia_member(member: str, timeout: int = 90) -> str:
    """Fetch one Silesia file (GitHub stores each as a zip). Not committed."""
    import urllib.request

    if member not in SILESIA_MEMBER_URLS:
        return f"unknown member {member}"
    dest = downloads_dir() / member
    if dest.is_file() and dest.stat().st_size > 100_000:
        with dest.open("rb") as f:
            magic = f.read(2)
        if magic != b"PK":
            return f"already have {dest.name} ({dest.stat().st_size} bytes)"
    url = SILESIA_MEMBER_URLS[member]
    tmp = dest.with_suffix(".zip.part")
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            tmp.write_bytes(resp.read())
        if tmp.stat().st_size < 1000:
            tmp.unlink(missing_ok=True)
            return f"download failed: {url} too small"
        with zipfile.ZipFile(tmp) as zf:
            target = _silesia_entry_name(zf, member)
            if target is None:
                tmp.unlink(missing_ok=True)
                return f"download failed: {member} not in member zip"
            with zf.open(target) as src:
                dest.write_bytes(src.read())
        tmp.unlink(missing_ok=True)
        return f"downloaded {dest.stat().st_size} bytes ({member})"
    except Exception as exc:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        return f"download failed: {type(exc).__name__}: {exc}"


def load_silesia_member_prefix(member: str, n_bytes: int = 512_000) -> tuple[bytes | None, str]:
    """Load a prefix of one Silesia file. Never commits the dump."""
    root = downloads_dir()
    for path in (root / member, root / "silesia" / member):
        if not path.is_file():
            continue
        with path.open("rb") as f:
            magic = f.read(2)
        if magic == b"PK":
            with zipfile.ZipFile(path) as zf:
                target = _silesia_entry_name(zf, member)
                if target is None:
                    continue
                with zf.open(target) as src:
                    data = src.read(n_bytes)
            return data, f"local zip {path.name}:{target} prefix {len(data)}"
        with path.open("rb") as f:
            data = f.read(n_bytes)
        return data, f"local {path.name} prefix {len(data)}"
    for zpath in (root / f"{member}.zip", root / "silesia.zip"):
        if not zpath.is_file():
            continue
        with zipfile.ZipFile(zpath) as zf:
            target = _silesia_entry_name(zf, member)
            if target is None:
                if zpath.name == "silesia.zip":
                    return None, f"{member} not in silesia.zip"
                continue
            with zf.open(target) as src:
                data = src.read(n_bytes)
        return data, f"zip {zpath.name}:{target} prefix {len(data)}"
    return None, "silesia not present under data/downloads/"

