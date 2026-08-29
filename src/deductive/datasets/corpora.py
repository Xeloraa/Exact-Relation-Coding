"""Real-corpus loaders.

Large copyrighted datasets are not stored in git. This module documents
how to obtain public samples and provides tiny built-in fixtures for
automated tests (source snippets, JSON, CSV, logs).
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

from dataclasses import dataclass


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

Silesia:
  see https://sun.aei.polsl.pl/~sdeor/index.php?page=silesia

CTU-13 NetFlow (tabular / FD control; format-awareness trap):
  public research dataset; treat derived-column wins as known FD elimination
  unless the same mechanism wins on non-tabular bytes.

Place downloads under data/downloads/ (gitignored) and point experiments
at those paths.
"""
