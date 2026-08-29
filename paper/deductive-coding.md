# Do automatically discovered exact algebraic relations help lossless compression after full accounting and composition?

**Status: DRAFT SKELETON.** Sections 8–9 and the Section 12 verdict are stubbed
`PENDING` the whole-file / full-baseline sweep on a higher-memory machine
(`docs/environment_constraints.md`). The pre-registration
(`docs/preregistration.md`, git-locked before any natural-corpus run) fixes the
threshold and decision rule; this file must not restate a different one. Do not
circulate as a finished paper.

---

## 1. Abstract

Lossless compressors model a probability for the next symbol and code a residual.
An alternative is to discover a relation the data satisfies *exactly*, transmit a
fully counted description of that relation plus the independent symbols, and let
the decoder reconstruct the determined symbols. We ask whether such a *deductive
pre-pass* produces a size reduction that survives (a) counting every
relation-description, header, framing, padding and CRC bit and (b) composition
with strong stock compressors — i.e. whether `min_c |c(x)| - min_c |c(D(x))|`
is positive on real data, where `D` is the accounted deductive container.

We implement two exact-relation detectors — a GF(2) leftmost column basis over
fixed-width bit matrices, and integer affine functional dependencies on parsed
tables — with a bit-exact accounting ledger and a never-worse passthrough
fallback. On planted GF(2) linear codes the pre-pass removes ≈50% of the size
that the six stock baselines and the paq8l / paq8px v216 context mixers achieve,
and the effect scales with rows while relation description stays constant. On
[PENDING: N] natural byte strings — whole Silesia members, an enwik8 prefix, six
SDRBench EXAALT float32 fields, and UCI household-power telemetry — [PENDING
headline result]. Functional-dependency and per-record-CRC32 cases reproduce
known techniques and are labelled as such. We release the pre-registration,
the metric definition, the accounting code, byte-exact round-trip and
codec-equivalence tests, and a one-command reproduction.

Every conclusion is scoped to the two detector families, the enumerated corpora,
and the baseline set actually run. We do **not** claim natural data lacks exact
algebraic redundancy.

## 2. Introduction

- The redundancy question: how much of a real dataset is *exactly deductively
  recoverable* from other transmitted information, versus merely statistically
  predictable.
- Why the distinction can matter: a long-range exact linear relation with no
  local predictability is a known blind spot of sequential statistical models;
  syndrome / Slepian–Wolf coding exists precisely because linear structure is a
  separate regime.
- Why a negative result here is worth reporting: the idea is repeatedly
  reinvented; a pre-registered, fully accounted, reproducible measurement of
  where a discovery-based deductive layer does and does not help is a useful
  landmark. The methodological contribution — the composed-gain metric plus the
  category-attributed bit ledger plus the never-worse guard as an evaluation
  discipline for *any* pre-pass compression claim — stands regardless of sign.
- Contributions:
  1. a formal composed-gain metric over the full post-downstream representation
     (§6);
  2. two exact-relation detectors with a bit-exact ledger and a structural
     never-worse fallback (§5);
  3. a pre-registered threshold and kill criterion (§7), fixed before the
     natural-corpus runs;
  4. controls that make a negative informative — positive (planted), null
     (i.i.d. / shuffled / near-relation), a corruption sweep, and labelled
     prior-art cases (§7, §8);
  5. a scoped empirical answer on planted codes and [PENDING] natural corpora,
     with one-command reproduction (§11).

## 3. Research questions

Kept strictly separate; one being true does not imply the others.

- **RQ-A (discoverable).** Does an exact relation exist in the data and get found
  and verified on every row? Measured by `n_relations ≥ 1` and
  `verify_basis` / `verify_affine_basis` passing on the full matrix.
- **RQ-B (reduces representation).** Is the accounted container `|D(x)|` strictly
  smaller than the never-worse passthrough, and is `raw_best(x) − |D(x)| > 0`?
- **RQ-C (survives composition).** Is `min_c |c(x)| − min_c |c(D(x))| > 0` — the
  only outcome that supports the deductive-coding hypothesis.

RQ-A → RQ-B → RQ-C is a strict funnel. A raw win that vanishes under xz means the
stock compressor already captured the redundancy given a friendlier arrangement.

## 4. Related work / prior art

Condensed from `docs/prior_art.md` (living audit) and a 2026 literature pass.

- **Functional-dependency / derived-column elimination** — US 8,150,888; Corra
  (2024); Wolpe (2026) derived-column pre-pass; columnar systems (BtrBlocks,
  FastLanes). Occupied for tables; our affine-FD and CRC results are labelled as
  this, not as novelty.
- **Syndrome / distributed source coding** — Slepian–Wolf, DISCUS, LDPC/turbo
  syndrome coders. Compress a source near a linear code via `Hx`; decoder
  reconstructs determined bits from a syndrome and side information. The
  reconstruction mechanism is the same idea; the correlation model there is
  assumed, not discovered from one corpus with description cost on the same
  channel.
- **Low GF(2)-rank / Boolean matrix factorisation** — Fomin et al.; "Boolean and
  F_p-Matrix Factorisation: Theory to Practice". Change-of-basis to expose
  binary rank deficiency; NP-hard in general; the exact (lossless) case is the
  special case our column basis computes at a fixed width.
- **Invariant mining** — Daikon and successors: templated discovery of
  equalities and affine relations among variables; not a compressor,
  false-positive-prone.
- **Format-aware recompression** — Precomp, preflate, packJPG: invert known
  codecs / drop reconstructible CRCs. Our PNG/ZIP/SQLite behaviour is the
  predicted "format-awareness trap", not a counterexample.
- **Context mixing** — PAQ8 family, cmix, lpaq/zpaq. Statistically exploit
  structure with many models. They do not emit a standalone verified relation
  basis with isolated description cost. Whether they absorb planted GF(2)
  parity is an empirical question we test directly (§8).
- **Deductive/semantic compression (2026)** — "Rate-Distortion Theory for
  Deductive Sources" / "Semantic Rate-Distortion: Deductive Compression and
  Closure Fidelity". Lossy, over knowledge bases with a proof system; the term
  "deductive compression" is now used there. Different problem (not byte-exact).
  We rename to avoid the collision.

Gap this work occupies: a pre-registered, fully accounted, composition-tested
measurement of a *discovery-based* deductive layer on general bytes, with
controls and reproduction. Narrow, and the expected answer is negative given the
surrounding literature; that is precisely why a clean measurement is useful.

## 5. Exact-relation detection method

### 5.1 GF(2) fixed-width column basis

Reshape the byte stream to an `n_rows × w` bit matrix for
`w ∈ {8,16,32,64,128,256}`; leftover bits `< w` are carried verbatim. Compute
the leftmost column basis by Gaussian elimination over GF(2) (packed uint64
rows). Each free column is expressed as an XOR of pivot columns; the whole map
is verified against the original matrix before encoding. Homogeneous and affine
(`[1 | A]`, ones column never transmitted) variants. The encoder keeps the
smallest fully accounted container over all `w` and both variants, else
passthrough.

### 5.2 Integer affine functional dependencies

For byte streams that parse as an `int64` table, relations `z = Σ aᵢ xᵢ + b` are
solved on a few distinct rows and verified with exact Python integers on every
row. Coefficients are zigzag varints, counted as relation description.

### 5.3 Scope

Both detectors are **axis-aligned**: relations among whole bit-columns / whole
table columns at a fixed period. Non-axis-aligned families (searched record
width, learned GF(2) column permutation, low-degree polynomial relations) are
out of scope here and named as the single follow-up the kill criterion
(`docs/preregistration.md` §7) requires before the general question is declared
closed.

## 6. Bit accounting and the composed metric

Full statement in `docs/metric.md`. Summary:

`AccountedWriter` attributes every emitted bit to one of
{header, relation, payload, leftover, crc, framing}. `finalize()` raises unless
`8·|D(x)| = Σ categories` and `framing = (−Σ others) mod 8`. `crc32(x)` (32 bits)
is always counted. Passthrough (`magic·version·kind·len·crc·x`, byte-aligned,
`|·| = |x| + 18`) is the never-worse floor.

```
raw_best(x)      = min_{c ∈ B} |c(x)|
composed_best(x) = min_{c ∈ B} |c(D(x))|
G_abs(x)         = raw_best(x) − composed_best(x)       (bytes, signed)
G_pct(x)         = G_abs(x) / raw_best(x)
```

`B = {gzip-9, zlib-9, bz2-9, xz-9, zstd-19, brotli-11}`. `c(D(x))` is the
composition; the decoder inverts `c⁻¹` then `E⁻¹`; round-trip is checked end to
end. An unavailable compressor (MemoryError/timeout) is recorded and excluded
from the `min`, with the available set reported per row. Context mixers
(paq8l, paq8px v216) are applied only to the planted-GF(2) control (§8); the
natural-corpus baseline is exactly `B` and is never described as more than that.

## 7. Experimental protocol

From `docs/protocol.md` and `docs/preregistration.md`.

- **Corpora.** 12 whole Silesia members; enwik8 prefix; six SDRBench EXAALT
  float32 fields (MD position/velocity); UCI household-power text. Whole-file
  where the machine permits; otherwise the largest completing prefix, each such
  row labelled `prefix=<bytes>` / `prefix_reason`. Every corpus pinned by
  SHA-256 (`corpus_manifest.json`); a changed hash aborts the run.
- **Pre-registered meaningful positive (per dataset, FIXED):** `G_pct ≥ 0.05`
  **and** `G_abs ≥ 1024` B **and** round-trip exact **and** container not
  passthrough with `n_relations ≥ 1` **and** the dataset is not a
  format/FD/checksum case.
- **Hypothesis outcome (FIXED):** POSITIVE iff ≥1 non-prior-art corpus meets the
  threshold and independently reproduces within ±10%; NEGATIVE iff none does
  while positive+null+prior-art controls all behave as designed; INCONCLUSIVE if
  a control fails or the corpus list could not be run.
- **Controls** (`experiments/controls/run.py`): positive (planted GF(2), 3
  seeds); null (i.i.d. bits, shuffled planted, 1-flip near-relation); corruption
  sweep (`φ ∈ {0, 1e-4, 1e-3, 1e-2, 5e-2}`); prior-art (affine FD, CRC32
  records) — recorded, labelled, never counted toward the hypothesis.
- **Independent reproduction** of any positive: fresh process, different machine
  or seed, identical corpus bytes by hash, `G_abs` within ±10%.

## 8. Results

### 8.1 Controls — COMPLETE (dev machine)

`results/controls/` (git commit in each JSON). All gates pass.

| control | outcome |
| --- | --- |
| positive: planted GF(2) ×3 | `G_pct` 0.48–0.50, round-trip ok |
| null: i.i.d. bits / shuffled / 1-flip | passthrough, `|G_abs| ≤ 19` B |
| corruption sweep `φ = 0 → 5e-2` | `G_abs` 16 213 → 13 238 → 1 402 → −18 → −18 B; monotone non-increasing; never below −64 |
| prior art: affine FD | `G_abs` +37 880 B — **LABEL: FD elimination** |
| prior art: CRC32 records (affine) | `G_abs` +16 209 B — **LABEL: checksum inversion** |

Interpretation: the pipeline exploits exact linear structure when present
(positive), invents nothing when it is absent (null), degrades gracefully and
never-worse under corruption (sweep), and the FD/CRC wins are the known
techniques.

### 8.2 Planted GF(2) vs context mixers — COMPLETE (from prior phases)

`results/phase1/`, `results/phase4_paq/`. 1 MiB 64+64 code: `D` = 524 850 B vs
best baseline 1 048 581 B; `G_abs` ≈ +523 726 B. Relation description 4 224 bits,
constant as rows scale (`results/phase4_scaling/`). paq8l `-3/-8` and paq8px
v216 `-4/-8` on a 10 KiB planted code: mixer-relative gap +4 968…+4 974 B,
matching the gzip/xz gap (+4 949 B) — the composed gap is not a weak-baseline
artefact for these mixers. cmix / nncp: not run (`docs/environment_constraints.md`
§3).

### 8.3 Natural corpora — PENDING (heavy-sweep machine, `--mode whole`)

Dev-machine **feasibility slices** only so far (`results/natural_slice/`,
256 KiB prefixes; provenance, NOT the pre-registered answer): 20/20 round-trip
ok, **0 meaningful positives**; GF(2) finds constant-bit-plane relations on text
and float fields (RQ-A often true) but `|D(x)|` never beats raw and composition
worsens it (RQ-B, RQ-C false); Silesia binaries fall to passthrough.

`PENDING`: whole-file table — per corpus: bytes, `n_relations`, `|D(x)|`,
`raw_best`, `composed_best`, `G_abs`, `G_pct`, RQ-A/B/C, round-trip,
`prefix_reason` if any.

## 9. Analysis — PENDING

To be written against the whole-file numbers, structured as:
1. RQ-A/B/C funnel per corpus category (Silesia text vs binary; float fields;
   telemetry text).
2. Where relations are found, what they are (bit-plane constants, ASCII
   high-bit, endianness padding) and why composition erases them.
3. The pre-registered decision rule applied verbatim → POSITIVE / NEGATIVE /
   INCONCLUSIVE.
4. If NEGATIVE: the explicit `(D, C, B)` scope statement; the single named
   follow-up (broader detector) from the kill criterion.
5. Threats to validity (§10) revisited with the actual data.

## 10. Limitations

- **Detector scope.** Axis-aligned GF(2) at six widths + integer affine on
  parsed tables. A negative is about *these* families; non-axis-aligned exact
  structure is untested (named follow-up).
- **Baseline scope.** `B` plus paq8l / paq8px v216 on the planted control only.
  cmix (needs ~20–32 GiB, no memory-level flag) and nncp (needs CUDA) were out
  of reach on available hardware; "strongest context-mixing compressors we could
  run" is the exact phrasing used.
- **Hardware.** Dev machine 8 GiB RAM / ~0.5 GiB free / no C toolchain. Whole
  Silesia members, whole SDRBench fields, whole UCI text, and enwik8-whole
  cannot be processed there; those rows come from the heavy-sweep machine.
  Round-trip is asserted on every row regardless of machine.
- **Corpus breadth.** Four corpus classes; not exhaustive. Scientific class is
  one MD dataset (EXAALT); larger gridded-simulation bundles (CESM, Hurricane,
  NYX) are deferred by size, not excluded on results.
- **A negative result does not prove absence** — only that these detectors do
  not expose a composed gain on these corpora against these baselines.

## 11. Reproducibility

- `python scripts/reproduce.py --mode {slice,whole}` runs pytest (incl. codec
  equivalence) → best-effort downloads → controls → natural → legacy phases,
  then writes `results/REPRODUCE.md` (machine, package versions, git commit,
  per-step exit codes and timings, full `corpus_manifest.json`).
- Every experiment JSON records dataset SHA-256, byte length, seed(s), config,
  codec kind, the six accounting categories, `|D(x)|`, `roundtrip_ok`,
  encode/decode/discovery seconds, every baseline `(name, bytes, seconds,
  available, error)`, every composition size, `G_abs`, `G_pct`, raw gap, UTC
  timestamp, `git_commit` (`-dirty` if the tree was not clean), command line,
  machine info.
- `tests/test_codec_equivalence.py` pins container bytes, accounting totals, and
  the reconstructed object against a frozen reference captured before the codec
  was vectorised; `tests/data/codec_reference.json` is that reference.
- Corpora are not committed (licence/size); acquisition is scripted and
  hash-pinned. A changed corpus hash aborts.
- `docs/preregistration.md` is git-locked; its adding commit is an ancestor of
  every natural-corpus result.

## 12. Conclusion — PENDING

One of, per `docs/preregistration.md` §4 and the campaign decision gate:

- **A. PAPER-WORTHY POSITIVE** — a reproducible whole-file composed gain meeting
  the fixed threshold exists on a non-prior-art corpus.
- **B. PAPER-WORTHY NEGATIVE** — no corpus meets the threshold, controls hold;
  report as a scoped negative with the named follow-up.
- **C. TECHNICAL REPORT ONLY** — evidence insufficient (e.g. the whole-file
  sweep could not be completed).
- **D. KILL** — the question is answered and the kill criterion's three
  conditions are all met.

Current standing: controls complete and passing; planted/​mixer results
complete; natural-corpus whole-file sweep **not yet run** → **INCONCLUSIVE by
the pre-registration** until that data exists.
