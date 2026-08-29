# The composed deduction gain — formal definition

This supersedes the provisional notes in `docs/theory.md` §"Provisional deduction
gap". The quantity adjudicated by `docs/preregistration.md` is
`G_abs` / `G_pct` defined in §4 below.

## 1. Objects

- `x ∈ {0,1}^{8n}` — the raw input byte string, `|x| = n` bytes.
- `B` — the fixed baseline compressor set (Section 5). Each `c ∈ B` is a
  lossless map with `c⁻¹(c(y)) = y` for all `y`; `|c(y)|` is the output length
  in bytes **including that compressor's own container/header**.
- `E` — the deductive encoder. `E(x)` is a self-delimiting byte string from
  which `x` is exactly recoverable: `E⁻¹(E(x)) = x`.
- `D(x) = E(x)` — the deductive container. Written `D(x)` when emphasising it is
  the object handed to a downstream compressor.

## 2. The deductive container and its accounting

`E` chooses the smaller (in whole bytes, ties → passthrough) of:

- **passthrough**: `magic ‖ version ‖ kind ‖ len(x) ‖ crc32(x) ‖ x`, padded to a
  byte. No symbol is omitted.
- **a relation codec** (GF(2) column basis, or tabular affine): a header, the
  relation description, the independent symbols, any leftover bits, and
  `crc32(x)`, padded to a byte.

Every emitted bit is attributed by `AccountedWriter` to exactly one category.
For a relation-codec container:

```
|D(x)| · 8  =  H(x)            header bits      — magic, version, kind, shape fields, flags
            +  R(x)            relation bits    — pivot/'free' mask + coefficient matrix
            +  P(x)            payload bits     — the independent (pivot) symbols, verbatim
            +  L(x)            leftover bits    — bits outside the last full matrix row
            +  K(x)            crc bits         — 32, crc32 of x
            +  F(x)            framing bits     — 0..7 pad bits to the next byte boundary
```

with, by construction and checked at run time
(`AccountedWriter.finalize` raises if violated):

```
|D(x)| = ceil( (H + R + P + L + K + F) / 8 )      and      F = (−(H+R+P+L+K)) mod 8
```

For passthrough, `R = P_dep = 0`, `P(x) = 8·|x|`, `H(x)` is the passthrough
header, `K(x) = 32`.

### Derived per-container quantities

- **recovered bits** `ρ(x)` — number of dependent symbols the decoder
  reconstructs from `R(x)` and `P(x)` without them being transmitted. For the
  GF(2) codec `ρ = n_rows · n_relations`. For passthrough `ρ = 0`.
- **relation-description cost** `R(x)` in bits, as above.
- **independent-symbol cost** `P(x)` in bits.
- **overhead** `H(x) + L(x) + K(x) + F(x)`.
- **container size** `|D(x)|` in bytes = everything above, byte-aligned.

There is no term that is not in one of these categories. A "win" that is
computed against `P(x)` alone, or against `|D(x)|` before the downstream
compressor, is **not** the metric.

## 3. Raw and composed baseline sizes

```
raw_best(x)       = min_{c ∈ B, c available}  |c(x)|
composed_best(x)  = min_{c ∈ B, c available}  |c(D(x))|
```

"available" = the compressor ran to completion on this machine for this input
(no `MemoryError`, no timeout). Unavailable compressors are recorded with the
exception and excluded from the `min`; the set of available compressors is
reported per row so a reader can see whether the `min` was taken over the full
`B`.

`c(D(x))` is the composition: run the deductive encoder, then compress its
container with a stock compressor. The decoder inverts in the other order
(`c⁻¹` then `E⁻¹`); round-trip is checked end to end.

## 4. The composed deduction gain (THE metric)

```
G_abs(x)  =  raw_best(x)  −  composed_best(x)          bytes,  signed
G_pct(x)  =  G_abs(x) / raw_best(x)                    fraction, signed
```

- `G_abs > 0` — the deductive pre-pass reduced the total size achievable by the
  strongest available stock compressor, after full accounting. This is the only
  event that supports the hypothesis.
- `G_abs ≈ 0` (|G_abs| ≤ 64 B) — no effect beyond header perturbation. Typical
  when `D(x)` is passthrough: `c(passthrough(x))` ≈ `c(x)` up to a few container
  bytes.
- `G_abs < 0` — the deductive container is *harder* to compress than `x` (it
  reorders bits into a layout the stock compressor models worse, or spends
  description bits the compressor would have got for free). Falsification, not a
  near miss.

### Companion cuts (reported, not adjudicated)

- **raw gain** `raw_best(x) − |D(x)|` — deduction vs stock compressors with **no**
  downstream composition. A positive raw gain that vanishes under composition
  means the stock compressor captures the same redundancy given a friendlier
  arrangement. Kept only to expose that case.
- **recovered fraction** `ρ(x) / (8|x|)`.
- **description ratio** `R(x) / max(ρ(x), 1)` — bits spent describing the
  relation per bit it recovers. Must be `< 1` for the relation to pay for
  itself before overhead.
- **bits/byte** of `|D(x)|` and of `composed_best(x)`.

## 5. Baseline set `B` (FIXED with the pre-registration)

| name | library | setting |
| --- | --- | --- |
| `gzip9` | Python stdlib `gzip` | level 9, mtime 0 |
| `zlib9` | Python stdlib `zlib` | level 9 |
| `bz2_9` | Python stdlib `bz2` | level 9 |
| `xz9` | Python stdlib `lzma` | `FORMAT_XZ`, preset 9 |
| `zstd19` | `zstandard` | level 19 |
| `brotli11` | `brotli` | quality 11 |

Context-mixing baselines (`paq8l`, `paq8px`, and `cmix` / `nncp` if ever
runnable) are applied **only** to the planted-GF(2) positive control, to test
whether the mechanism's advantage there is a genuine blind spot of the strongest
statistical compressors. They are not part of `raw_best` / `composed_best` for
the natural corpora (they cannot be run at those sizes on available hardware —
see `docs/environment_constraints.md`). The paper's natural-corpus baseline is
stated as exactly `{gzip9, zlib9, bz2_9, xz9, zstd19, brotli11}` and nothing is
described as "the strongest compressors" beyond what was run.

## 6. Reproducibility fields per experiment

Recorded in `results/<phase>/<experiment_id>.json` (see `src/deductive/results.py`):

dataset id and SHA-256; dataset byte length; RNG seed(s); full config; codec
kind; `n_relations`, `n_independent`, `recovered_bits`; the six accounting
categories in bits; `|D(x)|`; `roundtrip_ok`; encode / decode / discovery
seconds; every baseline `(name, bytes, seconds, available, error)`; every
composition `(name, bytes, seconds, available)`; `G_abs`, `G_pct`, raw gain;
UTC timestamp; `git_commit` (with `-dirty` suffix if the tree was not clean);
command line; machine info (platform, processor, cpu count, RAM); package
versions.
