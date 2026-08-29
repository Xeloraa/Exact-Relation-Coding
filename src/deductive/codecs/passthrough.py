"""Passthrough codec: original bytes plus a counted header and CRC.

Used when deduction would not reduce total transmitted size. The header
and CRC are still counted; a "win" that ignores them is not a win.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

from deductive.bitstream import AccountedWriter, Accounting, BitReader
from deductive.codecs.container import Kind, read_preamble, write_preamble


@dataclass
class Encoded:
    data: bytes
    accounting: Accounting
    kind: Kind
    n_relations: int
    n_independent: int
    recovered_bits: int
    notes: str = ""


def encode_passthrough(payload: bytes) -> Encoded:
    w = AccountedWriter()
    write_preamble(w, Kind.PASSTHROUGH)
    w.write_bits("header", len(payload), 64)
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    w.write_bits("crc", crc, 32)
    w.write_bytes("payload", payload)
    data, acc = w.finalize()
    return Encoded(
        data=data,
        accounting=acc,
        kind=Kind.PASSTHROUGH,
        n_relations=0,
        n_independent=len(payload) * 8,
        recovered_bits=0,
        notes="passthrough",
    )


def decode_passthrough(data: bytes) -> bytes:
    r = BitReader(data)
    kind = read_preamble(r)
    if kind != Kind.PASSTHROUGH:
        raise ValueError(f"expected passthrough, got {kind}")
    n = r.read_bits(64)
    crc = r.read_bits(32)
    payload = r.read_bytes(n)
    if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
        raise ValueError("CRC mismatch")
    return payload
