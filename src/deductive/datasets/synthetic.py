"""Synthetic datasets with known exact structure, plus null controls."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from deductive.codecs.gf2_codec import bytes_from_bits
from deductive.codecs.tabular_codec import table_to_bytes


@dataclass(frozen=True)
class SyntheticDataset:
    dataset_id: str
    data: bytes
    seed: int
    meta: dict


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def gf2_linear_code(
    *,
    n_rows: int,
    n_info: int,
    n_parity: int,
    seed: int,
    dense: bool = True,
) -> SyntheticDataset:
    """Random information bits plus exact GF(2) parity bits.

    Each parity column is a random nonempty XOR of information columns.
    The planted map is NOT passed to the codec; discovery must find some
    equivalent basis.
    """
    rng = _rng(seed)
    info = rng.integers(0, 2, size=(n_rows, n_info), dtype=np.uint8)
    parity = np.zeros((n_rows, n_parity), dtype=np.uint8)
    planted: list[list[int]] = []
    for p in range(n_parity):
        if dense:
            mask = rng.integers(0, 2, size=n_info, dtype=np.uint8)
            if mask.sum() == 0:
                mask[int(rng.integers(0, n_info))] = 1
        else:
            k = int(rng.integers(2, min(5, n_info + 1)))
            idx = rng.choice(n_info, size=k, replace=False)
            mask = np.zeros(n_info, dtype=np.uint8)
            mask[idx] = 1
        acc = np.zeros(n_rows, dtype=np.uint8)
        for j in range(n_info):
            if mask[j]:
                acc ^= info[:, j]
        parity[:, p] = acc
        planted.append(mask.tolist())
    matrix = np.concatenate([info, parity], axis=1)
    data = bytes_from_bits(matrix.reshape(-1))
    return SyntheticDataset(
        dataset_id=f"gf2_n{n_rows}_k{n_info}_p{n_parity}_s{seed}",
        data=data,
        seed=seed,
        meta={
            "kind": "gf2",
            "n_rows": n_rows,
            "n_info": n_info,
            "n_parity": n_parity,
            "n_cols": n_info + n_parity,
            "planted_masks": planted,
            "dense": dense,
        },
    )


def exact_functional_table(
    *,
    n_rows: int,
    seed: int,
    fn: str = "xor_plus",
) -> SyntheticDataset:
    """Tabular data with one exact derived column.

    fn:
      xor_plus: C = (A XOR B) + 3, with A,B uint16-range integers stored int64
      affine:   C = 3A + 5B + 7
      product:  C = A*B + 1  (not affine; map/FD path, affine should fail)
    """
    rng = _rng(seed)
    # Full 31-bit magnitude so independent columns are not strings of zeros.
    A = rng.integers(-(2**30), 2**30, size=n_rows, dtype=np.int64)
    B = rng.integers(-(2**30), 2**30, size=n_rows, dtype=np.int64)
    if fn == "affine":
        C = 3 * A + 5 * B + 7
    elif fn == "xor_plus":
        C = (A ^ B) + 3
    elif fn == "product":
        # keep product in int64: use smaller factors
        A = rng.integers(-2**14, 2**14, size=n_rows, dtype=np.int64)
        B = rng.integers(-2**14, 2**14, size=n_rows, dtype=np.int64)
        C = A * B + 1
    else:
        raise ValueError(fn)
    table = np.column_stack([A, B, C])
    return SyntheticDataset(
        dataset_id=f"fd_{fn}_n{n_rows}_s{seed}",
        data=table_to_bytes(table),
        seed=seed,
        meta={"kind": "functional", "fn": fn, "n_rows": n_rows, "n_cols": 3, "table_dtype": "int64"},
    )


def integer_linear_table(
    *,
    n_rows: int,
    seed: int,
    extra_independent: int = 1,
) -> SyntheticDataset:
    """z = 2x + 3y + 5, plus optional extra independent noise columns."""
    rng = _rng(seed)
    x = rng.integers(-(2**30), 2**30, size=n_rows, dtype=np.int64)
    y = rng.integers(-(2**30), 2**30, size=n_rows, dtype=np.int64)
    z = 2 * x + 3 * y + 5
    cols = [x, y, z]
    for _ in range(extra_independent):
        cols.append(rng.integers(-(2**30), 2**30, size=n_rows, dtype=np.int64))
    table = np.column_stack(cols)
    return SyntheticDataset(
        dataset_id=f"intlin_n{n_rows}_x{extra_independent}_s{seed}",
        data=table_to_bytes(table),
        seed=seed,
        meta={
            "kind": "integer_linear",
            "relation": "z=2x+3y+5",
            "n_rows": n_rows,
            "n_cols": table.shape[1],
        },
    )


def mixed_noise_bits(*, n_rows: int, n_cols: int, seed: int) -> SyntheticDataset:
    """Cryptographically-unrelated: independent fair bits. No planted relation."""
    rng = _rng(seed)
    matrix = rng.integers(0, 2, size=(n_rows, n_cols), dtype=np.uint8)
    data = bytes_from_bits(matrix.reshape(-1))
    return SyntheticDataset(
        dataset_id=f"noise_bits_n{n_rows}_c{n_cols}_s{seed}",
        data=data,
        seed=seed,
        meta={"kind": "noise_bits", "n_rows": n_rows, "n_cols": n_cols},
    )


def mixed_noise_table(*, n_rows: int, n_cols: int, seed: int) -> SyntheticDataset:
    rng = _rng(seed)
    table = rng.integers(-(2**30), 2**30, size=(n_rows, n_cols), dtype=np.int64)
    return SyntheticDataset(
        dataset_id=f"noise_table_n{n_rows}_c{n_cols}_s{seed}",
        data=table_to_bytes(table),
        seed=seed,
        meta={"kind": "noise_table", "n_rows": n_rows, "n_cols": n_cols},
    )


def near_relation_bits(*, n_rows: int, n_info: int, seed: int, n_flips: int = 1) -> SyntheticDataset:
    """One parity column equal to XOR of all info bits, then n_flips corrupted."""
    rng = _rng(seed)
    info = rng.integers(0, 2, size=(n_rows, n_info), dtype=np.uint8)
    parity = np.bitwise_xor.reduce(info, axis=1, keepdims=True)
    matrix = np.concatenate([info, parity], axis=1)
    if n_flips > 0 and n_rows > 0:
        rows = rng.choice(n_rows, size=min(n_flips, n_rows), replace=False)
        for r in rows:
            matrix[r, -1] ^= 1
    data = bytes_from_bits(matrix.reshape(-1))
    return SyntheticDataset(
        dataset_id=f"near_gf2_n{n_rows}_k{n_info}_flips{n_flips}_s{seed}",
        data=data,
        seed=seed,
        meta={"kind": "near_gf2", "n_rows": n_rows, "n_info": n_info, "n_flips": n_flips},
    )


def shuffled_bits(ds: SyntheticDataset, seed: int) -> SyntheticDataset:
    """Permute bytes. Destroys column alignment of planted relations."""
    rng = _rng(seed)
    buf = np.frombuffer(ds.data, dtype=np.uint8).copy()
    rng.shuffle(buf)
    return SyntheticDataset(
        dataset_id=f"shuffled_{ds.dataset_id}_s{seed}",
        data=buf.tobytes(),
        seed=seed,
        meta={"kind": "shuffled", "source": ds.dataset_id},
    )
