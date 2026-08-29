"""Independent decoder + accounting checker for DEDC containers.

Deliberately shares NO code with src/deductive/: its own bit reader, its own
container parse, its own GF(2) / affine reconstruction (plain XOR / Python-int
loops, not the packed-uint64 or matmul paths in the main codec). A bug that
lives in both the encoder and the main decoder is unlikely to also be
reproduced here.

What it does for one container `c` and a claimed original SHA-256 `h`:
  1. parse the container from scratch;
  2. reconstruct the original bytes;
  3. assert sha256(reconstruction) == h;
  4. assert the parsed field bit-sizes sum to exactly 8 * len(c)
     (independent re-derivation of the accounting `finalize()` check);
  5. assert the stored CRC32 matches the reconstruction.

Usage:
  python verification/independent_verify.py --self-test
  python verification/independent_verify.py --ledger results/ledger.json   # verify every artifact it can rebuild
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MAGIC = b"DEDC"          # must match deductive.__init__.MAGIC; asserted in --self-test
FORMAT_VERSION = 1
KIND_PASSTHROUGH, KIND_GF2, KIND_TABULAR_AFFINE = 0, 1, 2


class Bits:
    """Minimal LSB-first reader. Independent of deductive.bitstream."""

    def __init__(self, data: bytes) -> None:
        self.d = data
        self.pos = 0

    def bit(self) -> int:
        byte = self.d[self.pos >> 3]
        b = (byte >> (self.pos & 7)) & 1
        self.pos += 1
        return b

    def uint(self, n: int) -> int:
        v = 0
        for i in range(n):
            v |= self.bit() << i
        return v

    def bits(self, n: int) -> list[int]:
        return [self.bit() for _ in range(n)]

    def bytes_(self, n: int) -> bytes:
        return bytes(self.uint(8) for _ in range(n))


def _preamble(b: Bits) -> int:
    magic = b.bytes_(4)
    if magic != MAGIC:
        raise ValueError(f"bad magic {magic!r}")
    ver = b.uint(8)
    if ver != FORMAT_VERSION:
        raise ValueError(f"unsupported version {ver}")
    return b.uint(8)  # kind


def _reconstruct_passthrough(b: Bits) -> tuple[bytes, dict]:
    n = b.uint(64)
    crc = b.uint(32)
    payload = b.bytes_(n)
    acct = {"header": 4 * 8 + 8 + 8 + 64, "crc": 32, "payload": 8 * n}
    if (zlib.crc32(payload) & 0xFFFFFFFF) != crc:
        raise ValueError("passthrough CRC mismatch")
    return payload, acct


def _reconstruct_gf2(b: Bits) -> tuple[bytes, dict]:
    n_rows = b.uint(32)
    n_cols = b.uint(32)
    n_piv = b.uint(32)
    flags = b.uint(8)
    if flags & ~0b111:
        raise ValueError(f"unknown flags {flags:#b}")
    affine = bool(flags & 1)
    ones_is_pivot = bool(flags & 2)
    has_prefix = bool(flags & 4)
    orig_len = b.uint(64)
    leftover_n = b.uint(32)
    leftover = b.bits(leftover_n)
    prefix_n = 0
    prefix = []
    if has_prefix:
        prefix_n = b.uint(32)
        prefix = b.bits(prefix_n)
    mask = b.bits(n_cols)
    pivot_idx = [i for i, m in enumerate(mask) if m]
    free_idx = [i for i, m in enumerate(mask) if not m]
    if len(pivot_idx) != n_piv:
        raise ValueError("pivot count mismatch")
    coeff_width = n_piv + (1 if ones_is_pivot else 0)
    n_free = n_cols - n_piv
    coeffs = [b.bits(coeff_width) for _ in range(n_free)]
    pivot_bits = [b.bits(n_piv) for _ in range(n_rows)]
    crc = b.uint(32)

    acct = {
        "header": 4 * 8 + 8 + 8 + 32 * 3 + 8 + 64,
        "leftover": 32 + leftover_n,
        "relation": n_cols + n_free * coeff_width,
        "payload": n_rows * n_piv,
        "crc": 32,
    }
    if has_prefix:
        acct["prefix"] = 32 + prefix_n

    # reconstruct the matrix, row by row, with a plain XOR loop
    out_rows = []
    for r in range(n_rows):
        row = [0] * n_cols
        for j, p in enumerate(pivot_idx):
            row[p] = pivot_bits[r][j] & 1
        for i, f in enumerate(free_idx):
            acc = 0
            for j, p in enumerate(pivot_idx):
                if coeffs[i][j]:
                    acc ^= row[p]
            if ones_is_pivot and coeffs[i][coeff_width - 1]:
                acc ^= 1
            row[f] = acc
        out_rows.append(row)

    flat = list(prefix) + [bit for row in out_rows for bit in row] + list(leftover)
    need = orig_len * 8
    if len(flat) < need:
        raise ValueError("not enough reconstructed bits")
    flat = flat[:need]
    rec = bytearray()
    for i in range(0, need, 8):
        byte = 0
        for k in range(8):
            byte |= flat[i + k] << k
        rec.append(byte)
    rec = bytes(rec)
    if len(rec) != orig_len:
        raise ValueError("length mismatch")
    if (zlib.crc32(rec) & 0xFFFFFFFF) != crc:
        raise ValueError("gf2 CRC mismatch")
    return rec, acct


def _unzigzag(n: int) -> int:
    return (n >> 1) if (n & 1) == 0 else -((n + 1) >> 1)


def _read_varint(b: Bits) -> tuple[int, int]:
    shift = 0
    n = 0
    nbits = 0
    while True:
        byte = b.uint(8)
        nbits += 8
        n |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return n, nbits
        shift += 7


def _reconstruct_tabular_affine(b: Bits) -> tuple[bytes, dict]:
    n_rows = b.uint(32)
    n_cols = b.uint(32)
    n_ind = b.uint(16)
    n_rel = b.uint(16)
    rel_bits = 0
    independent = [b.uint(16) for _ in range(n_ind)]
    rel_bits += n_ind * 16
    relations = []
    for _ in range(n_rel):
        z = b.uint(16); x = b.uint(16); has_y = b.bit()
        rel_bits += 33
        y = b.uint(16) if has_y else None
        if has_y:
            rel_bits += 16
        coeffs = []
        for _ in range(3):
            v, nb = _read_varint(b)
            coeffs.append(_unzigzag(v))
            rel_bits += nb
        relations.append((z, x, y, *coeffs))
    payload_len = b.uint(64)
    payload = b.bytes_(payload_len)
    crc = b.uint(32)

    import numpy as np

    if independent:
        ind = np.frombuffer(payload, dtype="<i8").reshape(n_rows, len(independent))
        cols = {independent[i]: [int(v) for v in ind[:, i]] for i in range(len(independent))}
    else:
        cols = {}
    table = [[0] * n_cols for _ in range(n_rows)]
    for c, vals in cols.items():
        for r in range(n_rows):
            table[r][c] = vals[r]
    for _ in range(n_cols):  # resolve until all filled (at most n_cols passes)
        for (z, x, y, a, bb, cc) in relations:
            for r in range(n_rows):
                table[r][z] = a * table[r][x] + (bb * table[r][y] if y is not None else 0) + cc
    raw = b"".join(int(table[r][c]).to_bytes(8, "little", signed=True) for r in range(n_rows) for c in range(n_cols))
    acct = {
        "header": 4 * 8 + 8 + 8 + 32 + 32 + 16 + 16 + 64,
        "relation": rel_bits,
        "payload": 8 * payload_len,
        "crc": 32,
    }
    if (zlib.crc32(raw) & 0xFFFFFFFF) != crc:
        raise ValueError("tabular CRC mismatch")
    return raw, acct


def verify_container(container: bytes, expected_sha256: str | None = None) -> dict:
    b = Bits(container)
    kind = _preamble(b)
    if kind == KIND_PASSTHROUGH:
        rec, acct = _reconstruct_passthrough(b)
    elif kind == KIND_GF2:
        rec, acct = _reconstruct_gf2(b)
    elif kind == KIND_TABULAR_AFFINE:
        rec, acct = _reconstruct_tabular_affine(b)
    else:
        raise ValueError(f"unknown kind {kind}")

    consumed = b.pos
    framing = (-consumed) % 8
    acct["framing"] = acct.get("framing", 0) + framing
    total = sum(acct.values())
    accounting_ok = total == 8 * len(container)

    got = hashlib.sha256(rec).hexdigest()
    sha_ok = (expected_sha256 is None) or (got == expected_sha256)
    return {
        "kind": kind,
        "reconstruction_sha256": got,
        "reconstruction_len": len(rec),
        "expected_sha256": expected_sha256,
        "sha256_ok": sha_ok,
        "accounting_bits": total,
        "container_bits": 8 * len(container),
        "accounting_ok": accounting_ok,
        "ok": bool(sha_ok and accounting_ok),
    }


def _self_test() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from deductive import MAGIC as M, FORMAT_VERSION as V  # noqa: PLC0415
    from deductive.codecs.gf2_codec import encode_bytes_gf2  # noqa: PLC0415
    from deductive.codecs.passthrough import encode_passthrough  # noqa: PLC0415
    from deductive.codecs.tabular_codec import encode_tabular_affine  # noqa: PLC0415
    from deductive.datasets.synthetic import (  # noqa: PLC0415
        exact_functional_table, gf2_linear_code, mixed_noise_bits,
    )
    import numpy as np  # noqa: PLC0415

    assert M == MAGIC and V == FORMAT_VERSION, "constants drifted from deductive/__init__.py"
    fails = []

    def check(name, container, original):
        r = verify_container(container, hashlib.sha256(original).hexdigest())
        status = "ok" if r["ok"] else f"FAIL {r}"
        print(f"  {name:34s} {status}")
        if not r["ok"]:
            fails.append(name)

    ds = gf2_linear_code(n_rows=800, n_info=24, n_parity=24, seed=3)
    check("gf2_linear", encode_bytes_gf2(ds.data, 48).data, ds.data)
    ds = gf2_linear_code(n_rows=500, n_info=12, n_parity=12, seed=9)
    check("gf2_affine", encode_bytes_gf2(ds.data, 24, affine=True).data, ds.data)
    from deductive.codecs.gf2_codec import encode_bytes_gf2_offset  # noqa: PLC0415
    ds = gf2_linear_code(n_rows=700, n_info=16, n_parity=16, seed=13)
    for off in (1, 5, 13):
        check(f"gf2_offset{off}", encode_bytes_gf2_offset(ds.data, 32, off).data, ds.data)
    nb = mixed_noise_bits(n_rows=256, n_cols=32, seed=1)
    check("passthrough", encode_passthrough(nb.data).data, nb.data)
    ft = exact_functional_table(n_rows=120, seed=6, fn="affine")
    tbl = np.frombuffer(ft.data, dtype=np.int64).reshape(120, 3).copy()
    check("tabular_affine", encode_tabular_affine(tbl).data, ft.data)

    print("SELF-TEST:", "PASS" if not fails else f"FAIL {fails}")
    return 1 if fails else 0


def _verify_ledger(path: Path) -> int:
    led = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = led if isinstance(led, list) else led.get("records", led.get("rows", []))
    checked = failed = skipped = 0
    for row in rows:
        art = row.get("container_path") or row.get("artifact_path")
        exp = row.get("dataset_sha256")
        if not art or not Path(ROOT / art).is_file():
            skipped += 1
            continue
        r = verify_container((ROOT / art).read_bytes(), exp)
        checked += 1
        if not r["ok"]:
            failed += 1
            print(f"  FAIL {row.get('experiment_id')}: {r}")
    print(f"ledger verify: checked={checked} failed={failed} skipped(no artifact)={skipped}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--ledger", type=str, default=None)
    ap.add_argument("--container", type=str, default=None)
    ap.add_argument("--sha256", type=str, default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.ledger:
        return _verify_ledger(Path(args.ledger))
    if args.container:
        r = verify_container(Path(args.container).read_bytes(), args.sha256)
        print(json.dumps(r, indent=2))
        return 0 if r["ok"] else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
