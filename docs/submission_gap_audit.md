# Submission-gap audit

Reviewer stance: a skeptical DCC / data-compression program-committee member
deciding whether this is a paper. Read against the full repo, `docs/`,
`paper/`, `results/ledger.json`, tests, and `experiments/`.

Legend: **[REQ]** required before any submission · **[REC]** strongly
recommended · **[OPT]** low information value · **[NO]** not worth doing.

## The one thing that gates everything

**[REQ] G1 — the pre-registered whole-file natural sweep must actually run.**
At the start of this pass: 1 whole file (`silesia_dickens`) of a ~19-file
pre-registered list (`docs/preregistration.md` §5: 12 Silesia members + enwik8 +
≥1 SDRBench field + UCI household power). `docs/preregistration.md` §4 makes the
verdict **INCONCLUSIVE** while "resource limits prevent running enough of the
pre-registered corpus". A paper cannot ship INCONCLUSIVE-by-its-own-rule.
- *Action taken:* measured feasibility — the 8 GiB dev machine completes whole
  Silesia members up to ~10 MiB foreground in 2–4 min (`xml` 5.3 MB → 1m54s).
  Ran the 7 members ≤ 10 MiB whole (`xml, ooffice, reymont, sao, x-ray, mr,
  osdb` + the earlier `dickens`).
- *Still open:* `samba` (21 MB), `nci` (34 MB), `webster` (41 MB),
  `mozilla` (51 MB); `enwik8` whole (100 MB); the 6 SDRBench fields whole
  (11.5 MB each); UCI whole (127 MB). These need > 8 GiB. Path: a larger
  machine / container / cloud routine on the pushed branch. If that is not
  obtainable, the paper states exactly which files are whole, which are
  largest-feasible prefixes (labelled), and the verdict is scoped accordingly.

## Evidence completeness

**[REQ] G2 — RQ-E ("occurs naturally at meaningful scale").** Answered only by
G1. The RQ hierarchy in the paper is currently A/B/C; the brief asks for
A/B/C/D/E with per-corpus traceability. *Action:* add RQ-D (survives a strong
downstream compressor) and RQ-E (natural, at scale) to `paper` §3, and a
per-corpus L1..L6 → RQ map in `paper/results_tables.md` (generated).

**[REC] G3 — scientific corpus breadth.** One MD dataset (SDRBench EXAALT, 6
fields = one simulation, effective n ≈ 1–2). A second, *independent* scientific
field (different phenomenon, e.g. a gridded climate/turbulence field) would make
"scientific numeric" a real category rather than a single point. Only if a
public, directly-fetchable one is available without a parser; else document the
limitation. *Not* required if G1 completes and the slice+dickens pattern holds
(negative everywhere) — the conclusion is then robust to it.

**[NO] G4 — more corpus categories.** text / source / executable / DICOM /
binary / float / telemetry / CSV-FD / SQLite / PNG / ZIP are already covered
across the pre-registered list + phases 2–4. Adding more categories inflates
without changing the conclusion.

## Detector scope

**[REQ] G5 — close the axis-aligned objection with the smallest principled
extension.** The kill criterion (`docs/preregistration.md` §7 item 2) *requires*
one bounded detector-broadening attempt before the general question is declared
closed. Chosen extension: **bit-offset search** — for each fixed width `w`, also
try the `w` starting phase offsets (drop `p` leading bits, `p ∈ 0..w−1`, before
reshaping). This directly tests "the negative is a framing artifact": a genuine
`w`-periodic linear relation that starts mid-byte is invisible to phase-0
reshaping and visible at the right phase (as `control_nonaligned_period` shows
for non-power-of-two `w`). Bounded: `Σ w` extra reshapes, no search over
nonlinear forms. *Result that would change the conclusion:* any pre-registered
natural file crossing the 5 % threshold under offset search. *Expected:* none —
strengthens the negative from "axis-aligned, phase 0" to "axis-aligned, any
phase".

**[NO] G6 — nonlinear / learned-permutation / polynomial detectors.** The brief
forbids the unbounded search; these are future work, named in the kill
criterion, not this paper.

## Baselines

**[REC] G7 — cmix on the planted control.** The paper's claim "the strongest
context-mixing compressors we could run (paq8l, paq8px v216) do not absorb the
planted gap" is already correctly hedged. cmix would tighten it. cmix needs
~20–32 GiB (no memory level). If the G1 compute is obtained, run cmix there on
the 10 KiB planted seed 902 and the 1 MiB code; otherwise the wording stands and
`docs/environment_constraints.md` records the attempt.

**[NO] G8 — nncp / LLM-as-compressor.** Needs a GPU; would not change the
planted-control conclusion (paq8px already shows mixers miss XOR); the natural
result is negative regardless of baseline strength. Named as untested.

## Verification

**[REQ] G9 — independent end-to-end composed verification.** `verify_composed_
roundtrip` currently uses the *main* decoder. For every reported result the
chain `raw → encode → artifact → compress → decompress → independent-decode →
raw` must be checked with the shared-nothing decoder. *Action:* add an
`--emit-container` path so the natural runner writes the container to a temp
file, and have `independent_verify.py` do the compress/decompress/decode round
for the ledger rows (or the runner calls `verify_container` after
`decompress(compress(D(x)))`).

**[OPT] G10 — a third decoder.** Two independent implementations agreeing is
sufficient for a compression paper; a third is diminishing returns.

## Reporting / reproducibility

**[REQ] G11 — every paper number from the ledger.** Already enforced by
`scripts/check_paper_numbers.py` + `regen_tables.py`. Keep; extend markers to
cover the new whole-file rows.

**[REC] G12 — a distribution figure.** One figure: per-file `G_pct` for the
natural corpus (whole where available), with the 0 line and the +5 % threshold.
Communicates "every file is well below 0" at a glance. Generated from the ledger.

**[REQ] G13 — final release tag** once the sweep is as complete as it will get.

## Prior art

**[REQ] G14 — one final targeted pass** (syndrome coding; algebraic lossless;
exact-relation discovery; binary matrix rank; FD; reversible preprocessing;
constraint coding; learned algebraic reps; tensor/checkpoint compression;
program-synthesis compression; semantic/deductive compression; format-aware
recompression) dated at submission. For each close system: reproduce / differ /
extend / merely-evaluate. If the mechanism is not novel, the paper says so and
the contribution is the scoped evaluation + methodology.

## Framing

**[REQ] G15 — the paper follows the data.** Title and abstract must read as
"we investigate whether … the measured evidence does/does not show …", not "we
invented …". Already close; final wording pinned once the sweep result is in.

## Adversarial round

**[REQ] G16 — simulate peer review** against the 13 named objections; each
resolved / narrowed / left as a disclosed limitation. Extends
`docs/adversarial_review.md`.

---

## Execution order (highest value first)

1. **G1** run every whole file the dev machine can (done: 8/12 Silesia) → then
   pursue compute for the 4 giants + enwik8 + SDRBench-whole + UCI-whole.
2. **G5** bit-offset detector extension; re-run the corpus with it.
3. **G9** independent composed verification wired in.
4. **G2** RQ-D/RQ-E + per-corpus layer→RQ map.
5. **G14** prior-art pass; **G16** adversarial round.
6. **G11/G12/G13** ledger markers, distribution figure, tag.
7. **G7** cmix *iff* the G1 compute materialises; else narrow wording (already
   narrowed).
8. **G3** second scientific field *iff* cheaply available.

Items not listed (G4, G6, G8, G10) are explicitly declined with reasons above.
