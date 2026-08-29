# Results

Measured 2026-08-29 on Windows 11, Python 3.13.6, numpy 2.2.6, zstandard 0.25.0, brotli 1.2.0.
Git commit at measurement time: **UNCOMMITTED** (this file is part of the first commit that freezes the code that produced the JSON).
Commands: `python -m pytest tests`; `python experiments/phase0/run.py`; `python experiments/phase1/run.py`; `python experiments/phase2/run.py`; `python experiments/phase3/run.py`.
Machine: Intel 4-core, `results/phase0/environment.json`.

All listed experiments had `roundtrip_ok=true` (`decode(encode(x))==x`).
Sizes are bytes. Gaps: `best_stat - deductive` (raw gap) and `min c(raw) - min c(container)` (composed gap). Positive composed gap means deduction helped even after gzip/zlib/bz2/xz/zstd/brotli.

Full ledgers: `results/phase*/**.json` and `summary.csv`.

## Headline (not a success claim for real data)

1. **Planted GF(2) linear codes: yes, a large composed deduction gap.** Strong byte compressors leave XOR parity bits almost untouched. After counting relation description, header, CRC, and padding, omitting those bits still wins, and compressing the container does not close the gap.
2. **Nulls: no invented net savings** on iid bits, shuffled planted codes, near-relations with flipped bits, or non-affine exact functions under the affine codec.
3. **Ordinary source/docs text: no.** GF(2) on this repo's own files slightly shrinks raw size and then **loses badly** to xz/brotli, including after composition.
4. **Affine derived columns: composition win, labeled prior art** (functional-dependency elimination). The uncompressed DEDC container loses to xz; `deduce then xz` beats `xz` alone.

The project is **not killed**. The synthetic mechanism works. The live question is whether any *natural* byte corpus behaves like (1) rather than (3). FD tables behave like (4) and must not be sold as a new phenomenon.

## Phase 0

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels | kind |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| passthrough_noise | 256 | 274 | 260 | -14 | -18 | 0 | PASSTHROUGH |
| gf2_tiny (8 info + 8 parity, 128 rows) | 256 | 172 | 260 | +88 | +84 | 8 | GF2 |

Passthrough header+CRC is counted (18 extra bytes). Tiny planted code already beats every baseline, including composition. Rank discovery: 8 = n_info.

## Phase 1 — synthetic falsification (gate: PASS)

### A. Planted GF(2)

| dataset | raw | DEDC | payload_bits | relation_bits | header+crc+framing+leftover | best_stat (brotli11 except as noted) | raw_gap | composed_gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| n=1024 k=16 p=16 | 4096 | 2118 | 16384 | 288 | 240 | 4100 | +1982 | +1978 |
| n=4096 k=32 p=32 | 32768 | 16554 | 131072 | 1088 | 240 | 32772 | +16218 | +16214 |
| n=16384 k=32 p=32 | 131072 | 65706 | 524288 | 1088 | 240 | 131077 | +65371 | +65366 |
| n=65536 k=64 p=64 | 1048576 | 524850 | 4194304 | 4224 | 272 | 1048581 | +523731 | +523726 |

SHA-256 of the 1 MiB set: `9e300c474c1358cce32559616193d51a5d8fdcd9715bd671928dc42c7dd09e09`.
On that file every baseline is *larger* than raw (brotli 1048581, zstd 1048609, xz 1048688, gzip 1048914). Deductive payload is exactly the 64 independent columns; 64 parity columns are reconstructed. Relation description is 4224 bits (528 bytes) vs 512 KiB recovered. Encode 26.2 s / decode 14.5 s (unoptimized Python bit packing).

**Interpretation:** gzip/zstd/xz/brotli do not implement these XOR relations on this bitstream. That is an empirical fact about those compressors, not a theorem that autoregressive models cannot represent parity.

### B. Functional dependency

| dataset | raw | DEDC | best_stat | raw_gap | composed_gap | rels | notes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| affine C=3A+5B+7, 8192 rows | 196608 | 131116 | 108208 (xz) | -22908 | **+37880** | 1 | FD elimination; container loses to xz, pre-pass wins |
| xor_plus C=(A XOR B)+3 | 98304 | 98322 | 52992 (xz) | -45330 | -4 | 0 | affine codec correctly refuses; passthrough |

### C. Integer linear z=2x+3y+5 plus one noise column

| raw | DEDC | best_stat | raw_gap | composed_gap | rels |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 262144 | 196654 | 142032 (xz) | -54622 | **+36680** | 1 |

Same pattern as affine FD.

### D. Null / adversarial

| dataset | kind | rels | raw_gap | composed_gap |
| --- | --- | ---: | ---: | ---: |
| iid bits 8192×64 | PASSTHROUGH | 0 | -14 | -19 |
| iid int table 2048×4 | PASSTHROUGH | 0 | -30174 | -24 |
| near-GF2, 1 flipped parity | GF2 full-rank then overhead | 0 | -33 | -37 |
| shuffled planted GF(2) | PASSTHROUGH | 0 | -14 | -18 |

No invented saving. Near-relation overhead was later guarded by never-worse passthrough (Phase 2).

**Phase 1 gate:** substantial net saving on planted GF(2) after full accounting: **PASS**.

## Phase 2 — blind discovery and traps

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels | kind |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| blind sparse GF(2) 8192×(24+24) | 49152 | 24688 | 49156 | +24468 | +24464 | 24 | GF2 |
| iid bits 4096×128 | 65536 | 65554 | 65540 | -14 | -19 | 0 | PASSTHROUGH |
| near-relation 3 flips | 33792 | 33810 | 33796 | -14 | -18 | 0 | PASSTHROUGH |
| product C=A*B+1 (not affine) | 49152 | 49170 | 18548 | -30622 | +168 | 0 | PASSTHROUGH |
| builtin C fixture | 314 | 311 | 192 | -119 | -123 | 1 | GF2 |
| builtin JSON | 237 | 244 | 92 | -152 | -98 | 1 | GF2 |
| builtin CSV | 34 | 52 | 37 | -15 | -18 | 0 | PASSTHROUGH |
| builtin log | 170 | 185 | 98 | -87 | -78 | 1 | GF2 |
| builtin sqlite | 8192 | 3104 | 145 | -2959 | -99 | 41 | GF2 |

Notes:

- Blind discovery works on sparse planted parities (no planted mask is passed in).
- Product `+168` composed gap is **not deduction**: codec is passthrough; xz(header||raw) happened to be 18380 vs xz(raw) 18548. Header perturbation. Do not cite as a win.
- SQLite: GF(2) finds many relations (zero-page / format sparsity) and shrinks raw 8192→3104, but xz already reaches 145 bytes. **Format-awareness trap.** Not a composed gap.

## Phase 3 — in-repo text vs labeled FD vs CRC trap

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| repo src+tests+docs+experiments `.py`/`.md` | 116597 | 114857 | 26135 | -88722 | **-43830** | 2 |
| affine table 32768 rows (labeled prior art) | 786432 | 524332 | 429788 | -94544 | **+149936** | 1 |

Repo text SHA-256: `6d75c5a7a911d13260cbd6ef22e3a693cde9a16fd30f29d21bf2b6cacbb106b0` (snapshot; later edits change it).
GF(2) recovered 14574 bits but the container still compresses far worse than xz on the original (composed min 69965 vs raw min 26135).

Affine 32k SHA-256: `bccec2f031a0794a41def665582cb5ae8cf96fb59b15e4173d81bf56b51e47eb`. Composition win is derived-column elimination.

### CRC32 records (format-awareness trap)

4096 records of 4 random bytes + IEEE CRC32 (little-endian). 32768 raw bytes, 64 bit-columns.

| view | rank | relations | DEDC | best_stat | composed_gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| homogeneous GF(2) | 33/64 | 31 | 17067 | 32772 | **+15701** |
| affine GF(2) (implicit ones) | 32 payload cols | 32 | 16559 | 32772 | **+16209** |

gzip/zstd/xz/brotli all stay at ~raw size: the CRC bits look random. Homogeneous deduction recovers 31/32 CRC bits; affine GF(2) recovers all 32. **Label: known checksum, not a general-corpus discovery.** Do not cite this as novelty on “real files.”

## Deduction-gap definitions (applied)

On planted GF(2) 1 MiB: `deduction_gap_raw ≈ +523731`, `deduction_gap_composed ≈ +523726`.
On repo text: both large **negative**.
On affine tables: raw negative, composed positive (prior art).

## What this does *not* show

- No enwik8 / Silesia / binaries / packet captures yet (not downloaded; not committed).
- No PAQ/cmix/bsc comparison (not installed).
- No claim that neural compressors fail on parity.
- No novelty claim for FD column drop.

## Next experiments (ordered by how much they change the conclusion)

1. Local enwik8 and a binary/object file, not committed.
2. Whether packing independent bits before xz changes anything (it should not, on planted GF(2), because those bits are already nearly incompressible).
