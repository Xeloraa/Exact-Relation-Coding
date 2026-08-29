"""DEDC container kinds and shared header helpers."""

from __future__ import annotations

from enum import IntEnum

from deductive import FORMAT_VERSION, MAGIC
from deductive.bitstream import AccountedWriter, BitReader


class Kind(IntEnum):
    PASSTHROUGH = 0
    GF2 = 1
    TABULAR_AFFINE = 2


def write_preamble(w: AccountedWriter, kind: Kind) -> None:
    w.write_bytes("header", MAGIC)
    w.write_bits("header", FORMAT_VERSION, 8)
    w.write_bits("header", int(kind), 8)


def read_preamble(r: BitReader) -> Kind:
    magic = r.read_bytes(4)
    if magic != MAGIC:
        raise ValueError(f"bad magic {magic!r}")
    version = r.read_bits(8)
    if version != FORMAT_VERSION:
        raise ValueError(f"unsupported version {version}")
    kind = r.read_bits(8)
    return Kind(kind)
