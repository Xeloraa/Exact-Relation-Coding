"""Bitstream and accounting invariants."""

from __future__ import annotations

from deductive.bitstream import AccountedWriter, BitReader, BitWriter


def test_bitwriter_roundtrip_values():
    w = BitWriter()
    w.write_bits(1, 1)
    w.write_bits(0b1011, 4)
    w.write_bits(0xABC, 12)
    w.write_bytes(b"\x00\xff")
    data, pad = w.finalize()
    assert pad < 8
    r = BitReader(data)
    assert r.read_bits(1) == 1
    assert r.read_bits(4) == 0b1011
    assert r.read_bits(12) == 0xABC
    assert r.read_bytes(2) == b"\x00\xff"


def test_accounted_writer_totals_match_packed_length():
    w = AccountedWriter()
    w.write_bytes("header", b"DEDC")
    w.write_bits("relation", 3, 3)
    w.write_bits("payload", 0x55, 8)
    data, acc = w.finalize()
    assert len(data) * 8 == acc.total_bits
    assert acc.header_bits == 32
    assert acc.relation_description_bits == 3
    assert acc.payload_bits == 8
    assert acc.framing_bits == (8 - ((32 + 3 + 8) % 8)) % 8
    assert acc.total_bytes == len(data)
