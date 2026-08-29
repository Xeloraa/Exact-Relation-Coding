# Experimental protocol

Companion to `docs/preregistration.md` (fixed thresholds) and `docs/metric.md`
(formal metric). This file describes *how* each experiment is run and *what is
claimed from it*.

## 1. The three claims, kept separate

Every experiment reports these independently. They are never conflated; a paper
sentence that asserts one does not imply the others.

| tag | question | measured by | can be true while others are false |
| --- | --- | --- | --- |
| **A. Discoverable** | Does an exact relation exist and get found and verified on every row? | `n_relations >= 1`, `verify_basis` / `verify_affine_basis` pass on the full matrix | yes — a relation can exist and still cost more to describe than it saves |
| **B. Reduces representation** | Is `\|D(x)\|` strictly smaller than the never-worse passthrough, and smaller than `raw_best(x)`? | `\|D(x)\| < \|passthrough(x)\|`; raw gain `raw_best(x) − \|D(x)\| > 0` | yes — a raw win routinely vanishes under composition |
| **C. Survives composition** | Is `composed_best(x) < raw_best(x)` after full accounting? | `G_abs(x) > 0` (see metric.md §4) | this is the only one that supports the hypothesis |

A→B→C is a strict funnel: C implies B on `\|D(x)\|` vs passthrough but **not**
raw gain; B does not imply C; A implies neither.

## 2. Detector families `D` (this campaign)

1. **GF(2) fixed-width column basis** — reshape the byte stream to an
   `n_rows × w` bit matrix for `w ∈ {8,16,32,64,128,256}`, leftover bits < w
   carried verbatim; leftmost column basis by Gaussian elimination over GF(2);
   each free column expressed as an XOR of pivot columns; verified on every row.
   Homogeneous and affine (`[1 | A]`) variants. Smallest fully accounted
   container over all `w` and both variants, else passthrough.
2. **Tabular integer affine** — for byte streams that parse as an `int64` table:
   relations `z = Σ aᵢ xᵢ + b` solved on a few rows and verified with exact
   Python integers on every row; coefficients as zigzag varints, counted.

Both are **axis-aligned**: relations are among whole bit-columns / whole table
columns at a fixed period. The pre-registered kill criterion requires one
attempt at a broader family before the general question is declared closed;
that attempt is out of scope for this campaign and named as a follow-up.

## 3. Baselines `B`

`{gzip9, zlib9, bz2_9, xz9, zstd19, brotli11}` exactly (metric.md §5). Recorded
with version and wall-clock. A baseline that raises `MemoryError` / times out is
recorded `available=false` with the exception string and excluded from `min`;
the available set is printed per row.

Context-mixing compressors (`paq8l -3/-8`, `paq8px v216 -4/-8`) are run **only**
on the planted-GF(2) positive control (`experiments/controls/`), reusing the
existing `experiments/phase4/paq_probe.py` / `paq8px_probe.py`. `cmix` and
`nncp`: not run — see `docs/environment_constraints.md` §3. No text in the paper
calls the baseline set "the strongest compressors" beyond the six stock codecs
actually used for the corpora.

## 4. Corpora `C` and acquisition

| id | source | obtain | licence / redistribution |
| --- | --- | --- | --- |
| `silesia/<member>` | Silesia corpus, 12 members, **whole files** | `src/deductive/datasets/corpora.py::try_download_silesia_*` | public benchmark corpus; bytes not committed to git |
| `enwik8` | `http://mattmahoney.net/dc/enwik8.zip`, first 10^8 B | `try_download_enwik8_zip` | Wikipedia text, CC BY-SA; bytes not committed |
| `sdrbench/<field>` | SDRBench (sdrbench.github.io) scientific reduction benchmark, raw `float32` binary field | `try_download_sdrbench_field` | public scientific benchmark; cite dataset; bytes not committed |
| `uci_household_power` | UCI ML Repository #235, Individual Household Electric Power Consumption | `try_download_uci_household_power` | UCI, open for research; bytes not committed |

Everything under `data/downloads/` is gitignored. Each corpus is pinned by
SHA-256 in `results/corpus_manifest.json` after first download; a later run that
sees a different hash aborts with a mismatch error rather than silently
proceeding.

**Whole-file vs prefix.** Whole file whenever the running machine completes
discovery + all baselines within memory and a 30-min per-configuration budget.
Otherwise the largest power-of-two prefix that does complete, with the row
labelled `prefix=<bytes>` and `prefix_reason=<MemoryError|timeout>`. The current
development machine (8 GB RAM, ~0.5 GB free) can only do small prefixes; the
whole-file sweep is deferred to a higher-memory machine and re-run from
`scripts/reproduce.py`. This is recorded, not hidden.

**Excluded corpora log.** Any dataset downloaded or attempted and then dropped
is listed here with a reason. (none yet)

## 5. Controls (`experiments/controls/run.py`)

| control | construction | expected | gate it enforces |
| --- | --- | --- | --- |
| null: i.i.d. bits | `mixed_noise_bits` | passthrough, `\|G_abs\| ≤ 64` | no invented gain |
| null: shuffled planted code | `shuffled_bits(gf2_linear_code(...))` | passthrough, `\|G_abs\| ≤ 64` | column alignment, not magic, drives the positive |
| null: 1-flip near-relation | `near_relation_bits(n_flips=1)` | `n_relations = 0`, passthrough | approximate ≠ exact; guard holds |
| positive: planted GF(2) | `gf2_linear_code`, seeds fixed | `G_pct ≥ 0.30`, round-trip ok | pipeline exploits exact linear structure when present |
| corrupted sweep | planted code, flip fraction `φ ∈ {0, 1e-4, 1e-3, 1e-2, 5e-2}` | monotone: gain collapses to ~0 as `φ` grows; never negative beyond header | graceful degradation, never-worse holds under noise |
| prior art: affine FD | `exact_functional_table(fn="affine")` | raw gain < 0, `G_abs > 0`; **labelled FD elimination** | sanity only, not hypothesis support |
| prior art: CRC32 records | `experiments/phase3/crc_trap.py` | `G_abs > 0`; **labelled checksum inversion** | sanity only |

The corrupted sweep is new in this campaign; the rest consolidate existing
Phase 0–2 checks under one runner with explicit gate assertions.

## 6. Per-experiment procedure

1. Resolve corpus bytes; assert SHA-256 against `corpus_manifest.json` (write it
   on first sight).
2. `t0`; run detector family / families; pick the smallest accounted container
   or passthrough; `encode_seconds`.
3. `decode`; assert `decode(encode(x)) == x`; `decode_seconds`. Any failure
   aborts the experiment and is reported as `FAIL_ROUNDTRIP`, never smoothed
   over.
4. Run every baseline in `B` on `x`; run every baseline on `D(x)`.
5. Compute `G_abs`, `G_pct`, raw gain, companion cuts (metric.md §4).
6. Write `results/<phase>/<experiment_id>.json` + append `summary.csv`.
7. `scripts/reproduce.py` re-runs 1–6 for the whole campaign and regenerates a
   top-level `results/REPRODUCE.md` with all hashes, machine info, timings.

## 7. Independent reproduction of any positive

Required before the paper calls a positive result significant
(`docs/preregistration.md` §4): a from-scratch re-run in a fresh process, on a
different machine *or* with a different RNG seed for any stochastic step, on the
identical corpus bytes (SHA-256 verified), landing within ±10% of the first
`G_abs`. The reproduction command and its result JSON are committed alongside
the original.

## 8. What each possible result licenses the paper to say

- **C true and reproduced, non-prior-art corpus** → "on dataset(s) `…`, detector
  family `…`, baseline set `…`, a deductive pre-pass yields a composed size
  reduction of `G_pct` (`G_abs` bytes), round-trip verified and independently
  reproduced." No generalisation beyond the tested tuple.
- **C false everywhere, all gates pass** → "across corpora `C`, detector families
  `D`, baselines `B`, no composed size reduction was observed; the positive and
  null controls behaved as designed, so the pipeline detects exact structure
  when present. We do not claim natural data lacks algebraic redundancy; we
  claim these detectors do not expose a composed gain on these corpora against
  these baselines."
- **a gate fails** → INCONCLUSIVE; report the failure, no hypothesis verdict.
