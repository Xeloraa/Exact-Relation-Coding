# Results

Measured 2026-08-29 on Windows 11, Python 3.13.6, numpy 2.2.6, zstandard 0.25.0, brotli 1.2.0.
Git commit at measurement time: see each JSON `git_commit` field (phase 4 was `aea7e6c-dirty`).
Commands: `python -m pytest tests`; `python experiments/phase0/run.py`; `python experiments/phase1/run.py`; `python experiments/phase2/run.py`; `python experiments/phase3/run.py`; `python experiments/phase4/run.py`.
Machine: Intel 4-core, `results/phase0/environment.json`.

All listed experiments had `roundtrip_ok=true` (`decode(encode(x))==x`).
Sizes are bytes. Gaps: `best_stat - deductive` (raw gap) and `min c(raw) - min c(container)` (composed gap). Positive composed gap means deduction helped even after gzip/zlib/bz2/xz/zstd/brotli.

Full ledgers: `results/phase*/**.json` and `summary.csv`.

## Headline (not a success claim for real data)

1. **Planted GF(2) linear codes: yes, a large composed deduction gap.** Strong byte compressors leave XOR parity bits almost untouched. After counting relation description, header, CRC, and padding, omitting those bits still wins, and compressing the container does not close the gap.
2. **Nulls: no invented net savings** on iid bits, shuffled planted codes, near-relations with flipped bits, or non-affine exact functions under the affine codec.
3. **Ordinary source/docs/enwik8/stdlib/Silesia text and binaries: no.** GF(2) on this repo, local CPython `Lib/*.py`, a 1 MB enwik8 prefix, and 512 KB Silesia prefixes (dickens, xml, x-ray, ooffice) does not yield a composed gap. Statistical codecs still dominate.
4. **Affine derived columns: composition win, labeled prior art** (functional-dependency elimination). The uncompressed DEDC container loses to xz; `deduce then xz` beats `xz` alone. Same pattern on a parsed CSV `c=a+b` table in Phase 4.
5. **PNG / ZIP / SQLite as whole-file bit matrices: no composed gap.** General GF(2) does not invert per-chunk CRCs. Passthrough / `n_relations==0` composed deltas are header perturbation.

The project is **not killed**. The synthetic mechanism works and scales. No measured *arbitrary-byte* corpus behaves like (1). FD tables and checksums behave like (4) and must not be sold as a new phenomenon.

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

## Phase 4 — natural bytes, format traps, scaling

JSON ledgers: `results/phase4_natural/`, `results/phase4_formats/`, `results/phase4_scaling/`, `results/phase4_structured/`, `results/phase4_pack/`, `results/phase4_silesia/`. `summary.csv` may contain duplicate reruns; the JSON file for each `experiment_id` is canonical. Large dumps stay under `data/downloads/` (gitignored).

`n_relations==0` in `encode_gf2_matrix` materializes the original bytes, then returns passthrough (`tests/test_corpora.py::test_n_rel_zero_equals_passthrough_size`). Composed deltas on those rows are header perturbation, not deduction.

### A. Natural / local bytes (dumps not committed)

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels | kind |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CPython `Lib/*.py` prefix (local) | 400000 | 350037 | 74546 (brotli11) | -275491 | **-65177** | 1 | GF2 |
| `sys.executable` prefix (local PE stub) | 104928 | 104946 | 51104 (xz9) | -53842 | -24 | 0 | PASSTHROUGH |
| enwik8 first 1 MB | 1000000 | 1000018 | 281012 (brotli11) | -719006 | -80 | 0 | PASSTHROUGH |
| CSV text `c=a+b`, 8000 rows (GF2 on bytes) | 122204 | 93699 | 50904 (bz2) | -42795 | **-21753** | 15 | GF2 |
| same CSV as int64 table (tabular affine) | 192000 | 128044 | 43436 (xz9) | -84608 | **+15560** | 1 | TABULAR_AFFINE |

enwik8 1 MB prefix SHA-256: `369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad`. xz-9 raised `MemoryError` immediately after GF(2) discovery on a 4-core machine; a later `gc.collect()` retry gave xz 290692 (worse than brotli). Best-stat and the composed gap therefore use brotli. The dump is not in git.

Stdlib GF(2): 8-bit view, 7 independent columns, 400000 recovered bits — a zero high bit on mostly-ASCII source, not a deep relation. gzip/brotli already use that. The PE sample is a 102 KiB Windows `python.exe` launcher, not a full interpreter image.

**Interpretation:** on these byte strings, general GF(2) does not beat composition. The only composed win in this block is the *parsed* integer table, which is FD column elimination (prior art). GF(2) on the same relation *as text* loses to bz2/xz.

### B. Format-awareness traps (not a parser)

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels | kind |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| PNG 48×48 RGB (chunk CRCs present) | 7028 | 7046 | 7032 (brotli11) | -14 | -18 | 0 | PASSTHROUGH |
| ZIP stored (8 KiB random + text; fixed mtime) | 8431 | 8449 | 8343 (brotli11) | -106 | -15 | 0 | PASSTHROUGH |
| SQLite `c=a+b`, 4000 rows | 69632 | 69650 | 30796 (brotli11) | -38854 | -246 | 0 | PASSTHROUGH |

ZIP SHA-256 with frozen DOS mtime `(2026,8,29,0,0,0)`: `17a5a7760809830d3a17587d001e95313d7508f7c632bda29b217d8d7e00b0cd`. A whole-file bit matrix does not invert PNG/ZIP CRC32 at variable layout offsets. The larger SQLite file is passthrough at the tried widths (unlike the 8 KiB builtin fixture, which shrank zeros and still lost to xz). Label: format / sparsity, not a general-corpus gap.

### C. Structured text with an exact `sum` field (FD-in-text)

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| JSON array, 2000 records | 81457 | 62503 | 16167 (brotli11) | -46336 | **-11194** | 15 |
| log lines, 2000 records | 106618 | 93328 | 12203 (zstd19) | -81125 | **-5152** | 1 |

GF(2) can shrink the raw container. gzip/xz/brotli still win on composition. Label: text FD / format trap.

### D. Planted GF(2) scaling (fixed width, not `encode_bytes_best_gf2`)

Relation description stays **1088 bits** while recovered bits scale with `n_rows`. Round-trip OK on all rows.

| size | raw | DEDC | recovered_bits | best_stat | composed_gap | encode_s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 KiB (128×64) | 1024 | 683 | 4096 | 1028 | **+343** | 0.28–0.60 |
| 10 KiB (1280×64) | 10240 | 5291 | 40960 | 10244 | **+4949** | 0.95–1.94 |
| 100 KiB (12800×64) | 102400 | 51371 | 409600 | 102405 | **+51030** | 4.6–23 |
| 256 KiB (32000×64) | 256000 | 128171 | 1024000 | 256005 | **+127829** | 8.6–52 |

Affine control, 1280 rows × 32 info + parity `XOR(all) XOR 1` (5280 bytes):

| view | rels | DEDC | composed_gap |
| --- | ---: | ---: | ---: |
| homogeneous GF(2) | 0 | 5298 (passthrough) | -18 |
| affine GF(2) | 1 | 5164 | **+116** |

Homogeneous discovery correctly misses the constant offset. Affine recovery is the planted affine bit, not a natural-corpus claim.

### E. Pack independent bits, then xz/brotli

Same planted codes as scaling 10 KiB / 100 KiB. Pivot bits packed to bytes, then the same statistical baselines run on that payload alone. Relation description + header + CRC + leftover must still be transmitted for decode.

| size | packed pivots | best_stat(packed) | extra (rel+hdr+crc) | payload_then_stat | DEDC container | composed_gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10 KiB | 5120 | 5124 | 171 | 5295 | 5291 | **+4949** |
| 100 KiB | 51200 | 51204 | 171 | 51375 | 51371 | **+51030** |

**Interpretation:** the independent bits are already incompressible (best_stat is 4 bytes above packed size). Adding description cost back matches DEDC within 4 bytes. Packing pivots before xz does **not** close or expand the planted composed gap. JSON: `results/phase4_pack/`.

### F. Silesia public-corpus prefixes (dumps not committed)

512 KB prefixes from `silesia.zip` (Matt Mahoney mirror; 12 members). General GF(2) on bytes, not a format parser. Round-trip OK. Dump is gitignored.

| experiment | raw | DEDC | best_stat | raw_gap | composed_gap | rels | kind |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| dickens (ASCII novels) | 512000 | 496043 | 140096 (bz2_9) | -355947 | **-114679** | 1 | GF2 |
| xml (concatenated XML tar) | 512000 | 448037 | 15438 (bz2_9) | -432599 | **-24245** | 1 | GF2 |
| x-ray (16-bit DICOM) | 512000 | 480073 | 240711 (bz2_9) | -239362 | **-75917** | 4 | GF2 |
| ooffice (Windows DLL) | 512000 | 512018 | 238012 (xz9) | -274006 | -20 | 0 | PASSTHROUGH |

Prefix SHA-256: dickens `3d2b8a388908b800ded23f8d2f6b3e181c9951fef6039649acd04d51ccd462f6`; xml `1ae008042047777d47732811e4baef57ac075ee6d39a55d0cee925539fab9fc8`; x-ray `34d420201364c7b288ae907f72cf850e42c35bcff9ba5184c37030ec8e2e752c`; ooffice `dee624c889febeebcc4712ceee0006cd4a6bc044119584ba566980e529df2325`.

Dickens/xml: one bit-plane (xml is an 8-column view, 7 independent — ASCII high bit). x-ray: four relations on a 64-column view (typical unused high bits in 16-bit samples). ooffice: `n_relations==0` passthrough; composed −20 is header perturbation, not deduction. None of these is a composed win. bz2/xz already exploit the same sparsity plus the actual language/XML/DLL structure.

**Interpretation:** all four composed gaps are negative. That is falsification of a Silesia GF(2) composed gap, not a success and not novelty. JSON: `results/phase4_silesia/`.

## Deduction-gap definitions (applied)

On planted GF(2) 1 MiB: `deduction_gap_raw ≈ +523731`, `deduction_gap_composed ≈ +523726`.
On repo text, stdlib, enwik8, Silesia prefixes, PNG/ZIP, structured JSON/logs: both large **negative** (or header-sized on passthrough).
On affine tables / parsed CSV FD: raw negative, composed positive (prior art).

## What this does *not* show

- No remaining Silesia members (mozilla, mr, nci, …) or packet captures.
- No PAQ/cmix/bsc comparison (none of those binaries on PATH, Program Files, or this repo as of 2026-08-29).
- No claim that neural compressors fail on parity.
- No novelty claim for FD column drop or CRC inversion.
- Local stdlib and `python.exe` hashes are machine-specific; enwik8 and Silesia prefix SHAs are from the public dumps (dumps not in git).

## Next experiments (ordered by how much they change the conclusion)

1. PAQ/cmix if a binary is available; if they absorb the planted-GF(2) composed gap, that weakens the “statistical codecs leave XOR unused” claim relative to the strongest mixers.
2. Remaining Silesia members only if a new *kind* of byte string is needed; four prefixes already cover text, XML, medical 16-bit, and a DLL.
