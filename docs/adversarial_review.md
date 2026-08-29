# Adversarial review — every credible objection, and its disposition

Written as a hostile reviewer trying to reject the work. Each objection is
marked **FIXED** (addressed experimentally/methodologically), **WEAKENED**
(claim narrowed to match evidence), or **ACKNOWLEDGED** (a real limitation left
standing and disclosed). Nothing is hidden.

## A. "The gain is a measurement artifact"

**A1. You compare a raw representation against a compressed baseline.**
FIXED. The metric is `min_c |c(x)| − min_c |c(D(x))|` — both sides compressed
(`docs/metric.md` §4). The raw gap `raw_best − |D(x)|` is reported only as a
companion cut and is explicitly *not* the claim.

**A2. Metadata is under-counted / hidden.**
FIXED. `AccountedWriter.finalize()` refuses to emit a container whose six
category bit-counts do not sum to `8·|D(x)|`, with `framing ∈ [0,7]` forced. A
second, shared-nothing decoder re-derives the accounting from parsed field sizes
and asserts the same (`verification/independent_verify.py`). Control
`control_metadata_cost`: null overhead is exactly 18 B; a planted container's
category sum equals its bit length exactly.

**A3. The 12-way width×variant `min` cherry-picks a lucky representation.**
FIXED (bounded). `never_worse` caps the downside at passthrough. Control
`control_repr_change_null`: on 40 i.i.d. byte strings the `min` container beat
passthrough 0 times and produced a composed gain > 64 B 0 times. Null controls
(i.i.d., shuffled planted, 1-flip) all land on passthrough.

**A4. The container just happens to compress well for boring reasons (zeros).**
FIXED. That is exactly why composition is the metric: if `c(D(x))` is small
because `D(x)` is full of zeros, `composed_best` is small and `G_abs` does not
inflate. On natural data `G_abs` is large-*negative*, i.e. the container
compresses *worse*.

**A5. Encoder and decoder share a bug that cancels.**
FIXED. `verification/independent_verify.py` shares no code with
`src/deductive/`: own bit reader, own container parse, plain-Python XOR / int
reconstruction, independent accounting. It reconstructs all four container
kinds in `--self-test`, is run in CI (`tests/test_independent_verify.py`), and
was run on the 10 MB `silesia_dickens` whole-file container (`sha256_ok`,
`accounting_ok`).

**A6. The vectorised numpy paths are wrong.**
FIXED. `tests/test_properties.py`: 200 + 200 randomised bit-array trials vs the
per-bit loop (random pre/post misalignment); 60 randomised `reconstruct` trials
vs a per-column XOR reference (bases to width 130); `column_basis` vs planted
ground truth. Plus 15 byte-frozen container cases captured *before* the
vectorisation (`tests/data/codec_reference.json`).

**A7. The composed artifact does not actually decode back.**
FIXED. `verify_composed_roundtrip` checks `E^{-1}(c^{-1}(c(D(x)))) == x` for
every codec in `B` (fast subset above 4 MB). 0 failures across all 95 ledger
rows. A failure prefixes the verdict with `FAIL_COMPOSED_ROUNDTRIP`.

**A8. Asymmetric baseline availability makes the comparison unfair.**
FIXED. `available_raw_codecs` and `available_composed_codecs` are recorded;
`composition_gap_matched_bytes` is the gap over the intersection. A *reportable*
positive requires the sets to match or the matched-gap to also clear the
threshold. (Pre-registered primary metric unchanged.)

## B. "The controls do not establish what you say"

**B1. The positive control is circular — you planted the structure.**
WEAKENED/ACKNOWLEDGED. Correct, and stated: H1 is a *confirmatory test of the
pipeline*, not of the research question (`paper` §4). Its value is to show the
pipeline detects and exploits a large effect end-to-end (`G_pct` ≈ 0.48), so a
natural-data negative is not a sensitivity failure.

**B2. Null controls only cover i.i.d. — real data is not i.i.d.**
FIXED. `control_nonaligned_period` uses *structured* data (a genuine 48-bit
linear code) and shows the detector correctly misses it at the tried widths and
finds it at width 48. The corruption sweep covers the continuum from exact to
broken structure. The natural corpora themselves are the non-i.i.d. test.

**B3. The corruption sweep's `φ=1e-4` point still shows a huge gain — the method
is suspiciously robust.**
ACKNOWLEDGED and explained. 13 flipped cells in 128 K barely dent a
strongly-structured matrix; discovery routes around the bad rows with a slightly
larger exact basis. This is a real property (graceful degradation), reported as
such, not a hypothesis claim (synthetic data).

## C. "The natural-corpus evidence is too thin"

**C1. You substituted 256 KiB prefixes for whole files.**
FIXED (partially). Slices are quarantined in a separate phase
(`natural_slice`), separate manifest keys (`<id>@slice<N>`), `prefix_reason` on
every row, and are labelled in the paper as provenance, **not** the answer. One
whole file (`silesia_dickens`, 10.19 MB) is done and is a clean negative. The
rest is **ACKNOWLEDGED PENDING** — the dev machine cannot run them
(`docs/environment_constraints.md`), and the pre-registration says the verdict
is INCONCLUSIVE until they run on a ≥ 32 GiB machine.

**C2. You only test one scientific dataset, and its 6 fields are one
simulation.**
ACKNOWLEDGED. `docs/statistics.md` §2: the 6 EXAALT fields have effective
n ≈ 1–2; they are reported individually with no CI. EXAALT was chosen over
CESM/Hurricane/NYX purely on download size (`docs/protocol.md` §4), before any
result was seen. A broader scientific-corpus sweep is future work.

**C3. Corpus selection could be biased.**
FIXED. The corpus list is in `docs/preregistration.md` §5, git-locked before any
`load_*` output was inspected. Every corpus is SHA-256-pinned; a changed hash
aborts the run. Deferred/excluded corpora are logged with reasons.

**C4. The whole-file `dickens` result predates half your audit fixes.**
FIXED. Re-run at commit `e890739`, after A1–A7; it carries `composed_roundtrip`
(fast subset, all ok) and was independently verified. `docs/audit.md` C1
records the discarded stale `mozilla` record.

## D. "The baseline is not strong enough"

**D1. You did not test cmix / nncp / the 2026 SOTA (StateSMix, LLM-as-
compressor).**
WEAKENED. True. cmix needs ~20–32 GiB (no memory-level flag); nncp needs CUDA;
neither is runnable here (`docs/environment_constraints.md` §3). The paper's
baseline is written as exactly `{gzip9,zlib9,bz2_9,xz9,zstd19,brotli11}` plus
`paq8l/paq8px v216` on the planted control only; nothing is called "state of the
art". The planted-code result (paq8l/paq8px do **not** absorb the XOR gap)
*bounds* — does not eliminate — the "a stronger mixer would" objection, and the
paper says so.

**D2. `skip_slow` could be silently weakening the baseline.**
FIXED. `skip_slow` (xz9/brotli11 skipped above 8 MB) is **not** used by
`experiments/natural/run.py`; it exists only for legacy phase-4 helpers and is
recorded when used. `silesia_dickens` ran all six baselines at 10 MB.

## E. "The framing / claims are inflated"

**E1. "Deductive Coding" is a taken term.**
FIXED. Renamed **Exact-Relation Coding** (`docs/naming.md`) — "deductive coding"
is qualitative-research jargon and a 2026 semantic-compression line.

**E2. You claim novelty for exact-structure discovery.**
FIXED. The paper (§20) states this idea is **not** novel: grammar compression,
syndrome-source-coding (Ancheta 1976), and Brevis (2026, program synthesis for
tensor compression, a real composed win). The contribution is narrow: a
prior-free axis-aligned GF(2)/affine family, pre-registered composed test,
public corpora — reporting where it does and does not help.

**E3. You'd spin a negative as a positive.**
FIXED by construction. The pre-registered decision rule and threshold are
git-locked; `meaningful_positive_prereg` is computed mechanically from the
ledger; the layered L1–L6 reporting (`docs/statistics.md` §5) makes "structure
exists but doesn't survive metadata" the honest headline.

## F. "The statistics are wrong / missing"

**F1. No confidence intervals, no significance tests.**
ACKNOWLEDGED and correct. `docs/statistics.md`: the compressors are
deterministic, so repeated-run statistics measure OS-scheduler noise, not the
phenomenon; there is no random sampling from a defined population, so no
inferential CI is claimed. The only interval form used is a labelled
"descriptive bootstrap over the 12 Silesia members". The headline is a per-file
**max** `G_pct` vs the threshold, not a mean.

**F2. Multiple comparisons across 20 corpora.**
FIXED (reframed). `G_pct` per file is exact, not noisy, so Bonferroni is not the
right tool. The question is "does any file have real exploitable structure",
answered directly per file; the representation-change null bounds the
false-positive rate of the per-file `min`.

## G. "Reproducibility gaps"

**G1. Numbers in the paper are hand-typed.**
FIXED. All tables come from `results/ledger.json` via `regen_tables.py`; inline
numbers carry `src:` markers; `check_paper_numbers.py` fails on staleness or a
bad marker.

**G2. Corpora are not committed — I can't reproduce.**
ACKNOWLEDGED (licence/size). Acquisition is fully scripted and hash-pinned;
`scripts/reproduce.py` fetches, verifies, and aborts on a hash change. Every
result JSON records the dataset SHA-256.

**G3. A background process corrupted a result.**
FIXED and disclosed (`docs/audit.md` C1). Whole-file runs are now foreground
with an explicit timeout; the bad record was deleted; the ledger has 0
accounting / round-trip / composed-round-trip failures.

## The 13 canonical objections (submission round 2)

| # | objection | resolution |
| --- | --- | --- |
| 1 | **"This is just syndrome coding."** | **B / acknowledged.** Correct that compressing a source near a *known* linear code via its syndrome is classical (Ancheta 1976). The paper (§20, `docs/prior_art.md`) states the mechanism is not novel. The only distinction is *discovering* the code from one input with description cost charged — a thin axis — and the contribution is the pre-registered, fully accounted, composed evaluation on public corpora, whose answer is negative. |
| 2 | **"Your positive control is tautological."** | **C / disclosed.** H1 is explicitly a confirmatory test of the *pipeline*, not the research question (§4). Its role: show the pipeline detects and exploits a large effect end-to-end (`G_pct`≈0.48–0.50), so the natural-data negative is not a sensitivity failure. |
| 3 | **"Your detector is too narrow."** | **A (bounded) + C.** The kill-criterion follow-up is done: `experiments/offset/run.py` runs the §8.4 bit-phase-offset extension on every pre-registered file. No file crosses the threshold; the negative is phase-robust. Non-axis-aligned / nonlinear / learned-permutation detectors remain future work, named in the kill criterion. The paper's negative is scoped to "axis-aligned linear, any bit phase". |
| 4 | **"Your corpora are biased."** | **A.** Corpus list git-locked in `docs/preregistration.md` §5 before any `load_*` output was seen; every file SHA-256-pinned; a changed hash aborts; deferred/excluded files logged with reasons (`docs/protocol.md` §4). |
| 5 | **"Your files are too small."** | **A (partial) + C.** 8 of 12 Silesia members are now whole (up to `osdb`/`mr` ≈ 10 MB, the largest an 8 GiB machine runs in budget); the strongest case `dickens` is 10 MB whole with `G_pct` −94 %. The 4 largest members (21–51 MB) + enwik8/SDRBench/UCI whole need > 8 GiB — not available; reported as ≥ 256 KiB prefixes and labelled. Every slice + the 8 whole files + the offset extension agree: negative. A top venue would want the 4 giants (see `docs/venue_assessment.md`). |
| 6 | **"Your downstream comparison is unfair."** | **A.** Matched-codec-set gap (`composition_gap_matched_*`), both available-codec sets recorded per row; a reportable positive needs matched sets. `verify_composed_roundtrip` (main decoder) + `verify_composed` (independent decoder) check `decode(c⁻¹(c(D)))==x` for every codec — 0 failures. |
| 7 | **"Your metadata accounting is incomplete."** | **A.** `finalize()` refuses to emit a container whose 6 (now 7, with `prefix`) category bit-counts do not sum to `8·\|D(x)\|`; the independent decoder re-derives the same from parsed field sizes. `control_metadata_cost`: null overhead = exactly 18 B; planted container bits = Σ categories to the bit. |
| 8 | **"Your strongest baseline is missing."** | **B.** cmix (~20–32 GiB) / nncp (CUDA) not runnable here; paq8l/paq8px v216 on the planted control show mixers do not absorb the XOR gap, which *bounds* the objection. Wording is exactly "the strongest context-mixing compressors we could run"; nothing is "state of the art". |
| 9 | **"Your negative result is underpowered."** | **B / disclosed.** The positive control shows the pipeline resolves a ≥ 30 % effect; the pre-registration will not report < 5 % by design (relevance, not precision — measurements are exact). Coverage: 8/12 Silesia whole + all as slices + offset extension. The remaining power gap is the 4 giants (hardware). `docs/statistics.md`. |
| 10 | **"Your result is already known."** | **B / acknowledged.** The *general* idea (grammar compression; syndrome coding; Brevis 2026) is not novel — stated plainly. The contribution is the scoped empirical evaluation + the methodology (bit-exact ledger, never-worse, independent decoder, composed metric, pre-registration). |
| 11 | **"Your implementation could be wrong."** | **A.** Independent shared-nothing decoder + accounting re-derivation, run in CI, on the 10 MB `dickens` container, and now end-to-end through the compressor (`verify_composed`). 620+ tests incl. 400 randomised bit-I/O and 60 `reconstruct` trials vs slow references; 15 byte-frozen container cases. |
| 12 | **"Your statistical treatment is inappropriate."** | **A.** `docs/statistics.md`: deterministic measurements → no repeated-run stats; unit = file; SDRBench 6 fields = one simulation (no CI); no inferential CI/p-value; headline is per-file max `G_pct` vs threshold. |
| 13 | **"Your conclusion is broader than your experiment."** | **A.** Every conclusion is written scoped to `(D, C, B)` — the axis-aligned (+ offset) GF(2)/affine families, the enumerated corpora, the six stock codecs (+ paq on the planted control). The paper explicitly does not claim natural data lacks algebraic redundancy. |

## Residual objections left standing (honest)

1. **The whole-file natural sweep is not done** (2 of ~19 corpus files). The
   verdict is INCONCLUSIVE until it runs on adequate hardware. This is the
   single biggest gap and it is hardware, not method.
2. **Detector scope is narrow.** A negative is about axis-aligned fixed-width
   GF(2)/affine; §17 + `control_nonaligned_period` show structure at other
   periods is missed by construction. The kill criterion requires one
   broader-detector attempt before the general question is closed.
3. **No cmix/nncp/2026-SOTA baseline.** The planted control bounds this; it does
   not remove it.
4. **One scientific and one telemetry corpus**, not a broad sweep of either.

A reviewer who rejects on (1) is correct that the paper is not finished; a
reviewer who rejects the *finished* version on (2)–(4) is rejecting a scoped
negative-results contribution, which is a venue-fit question, not a soundness
one.
