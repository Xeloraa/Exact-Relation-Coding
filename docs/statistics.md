# Statistical treatment

The brief asks for a reviewer-proof analysis. The honest answer for this
experiment is that most conventional statistics do **not** apply, and saying so
precisely is the rigorous move.

## 1. The measurements are deterministic

Every compressor in `B` (`gzip9, zlib9, bz2_9, xz9, zstd19, brotli11`) is a
deterministic function of its input bytes; `gzip` is pinned with `mtime=0`. The
deductive encoder is deterministic (asserted: `make().data == make().data` for
every equivalence case). Therefore, for a fixed `(input, codec)`:

- `|c(x)|`, `|D(x)|`, `|c(D(x))|`, `G_abs`, `G_pct` are **exact constants**.
  Re-running changes only wall-clock timings and the UTC timestamp (verified:
  control JSONs re-run differ solely in `*_seconds`).
- "Mean ± SD over N reruns" of any size is **meaningless** here and is never
  reported. Repeated-run statistics would be reporting the noise of the OS
  scheduler, not of the phenomenon.

So there is no sampling distribution over reruns, no p-value over reruns, no
CI over reruns.

## 2. The unit of analysis is the file

The variation that matters is **across corpus members**. Each file is one
observation of "what does Exact-Relation Coding do on this byte string". A
per-file table (`paper/results_tables.md`) is the primary result object.
Aggregates are descriptive summaries of *the tested set*, not inferences about a
population.

### Independence caveats (important)

- The **6 SDRBench EXAALT fields** (`vx, vy, vz, xx, yy, zz`) are the position
  and velocity components of **one** molecular-dynamics simulation. They are
  strongly correlated; they are **not 6 independent observations**. Effective
  n ≈ 1–2. They are reported individually; any "mean over the exaalt fields" is
  annotated with this and is not given a CI.
- The **12 Silesia members** are deliberately heterogeneous (novels, XML,
  DICOM, executables, a DLL, a database). They are closer to 12 distinct data
  *types* than to a random sample, but there is no defined super-population they
  are drawn from. A bootstrap over the 12 is reported **only** as a compact
  description of the spread of `G_pct` on this standard corpus — never as
  "natural data has mean `G_pct` = …".
- `enwik8` (1 member) and `uci_household_power` (1 member) are single points.

Because there is no random sampling from a defined population anywhere, **no
inferential confidence interval is claimed**. Where an interval is shown it is
labelled "descriptive bootstrap over the N tested files" and is a statement
about those files.

## 3. Effect size and the pre-registered threshold

`G_pct` is already a standardised effect size: composed bytes saved as a
fraction of what the best stock compressor achieves. The pre-registration
(`docs/preregistration.md` §3) fixes the decision at `G_pct ≥ 0.05` **and**
`G_abs ≥ 1024` B per file. The hypothesis-level question is a **max**, not a
mean: *does any non-prior-art file clear the threshold?* A mean near zero with
one file at +20% would be a POSITIVE; twelve files at −40% and one at +2% is a
NEGATIVE.

Reported per campaign:
- `max G_pct`, `min G_pct`, `median G_pct` over the tested files;
- count of files POSITIVE at each claim layer (§5);
- the single best file and its full ledger row.

## 4. Multiple comparisons

Two surfaces, handled explicitly:

1. **Per-file 12-way min** (`encode_bytes_best_gf2` tries 6 widths × {homogeneous,
   affine} and keeps the smallest container). This can only *lower* the
   container, so it is a false-positive surface. The
   `control_repr_change_null` control estimates its rate directly: on 40
   independent i.i.d. byte strings, the min-container beat passthrough **0**
   times and produced a composed gain > 64 B **0** times. The never-worse guard
   caps the downside at passthrough.
2. **20+ corpora vs one threshold.** This is *not* a sampling-error surface —
   `G_pct` per file is exact, not noisy — so a Bonferroni-style correction is
   not the right tool. The question "is there real exploitable exact structure
   in any of these files" is answered directly by the per-file `G_pct`, and the
   controls show the pipeline finds such structure when it is present (positive
   control `G_pct` ≈ 0.48; `control_nonaligned_period` finds a planted code once
   its width is tried).

## 5. What a negative result establishes — the RQ layers

A NEGATIVE is not "the idea failed". It is a precise statement per research
question (paper §3), read mechanically from the ledger:

| RQ | question | ledger predicate | typical natural-corpus finding |
| --- | --- | --- | --- |
| **A** structure exists | exact GF(2)/affine relation at a tried width **or bit phase**? | `n_relations ≥ 1` before never-worse | often yes (constant bit-planes, ASCII high bit); sometimes no (binaries → passthrough) |
| **B** discoverable & represented | verified on every row; well-formed accounted container? | `verify_basis` passes; `finalize()` invariant holds; independent decoder agrees | yes whenever A holds |
| **C** reduces total cost (pre-composition) | `\|D(x)\| < passthrough` and `< raw_best`? | `raw_gap_bytes > 0` | **no** on every natural file — description + header + framing + CRC exceed the recovered bits |
| **D** survives strong downstream compressor | `G_abs > 0`? | `composition_gap_bytes > 0` | **no**, usually large-negative |
| **E** occurs naturally at meaningful scale | any non-prior-art file ≥ threshold? | `G_pct ≥ 0.05 ∧ G_abs ≥ 1024 ∧ ¬passthrough` | **no** — 0 of all natural files (8 whole + 12 slices + 6 float fields + telemetry + offset extension) |
| *(planted only)* | does a context mixer close the planted gap? | paq(raw) vs paq(D(x)) | **no** — paq8l / paq8px v216 do not absorb it |

For the tested natural corpora: **A/B frequently yes, C onward no.** That is the
scientifically useful content — the redundancy the detector finds is real but
trivial, and is already captured by stock compressors given the raw layout. The
bit-phase-offset extension does not move any file across C or D.

## 6. Power / sensitivity

- The positive control (`G_pct` ≈ 0.48 on planted GF(2), all seeds) shows the
  pipeline **detects and exploits a large effect** end to end. The negative is
  therefore not a sensitivity failure for large effects.
- By pre-registration the method will not report an effect below 5%; that is a
  deliberate relevance threshold, not a limitation of measurement precision
  (which is exact).
- The corruption sweep shows graceful degradation: `G_abs` falls monotonically
  from +16 213 B (`φ`=0) to header noise (`φ`≥1e-2) as exact structure is
  broken — the method neither clings to broken structure nor goes negative
  beyond header perturbation.
- Detector sensitivity is bounded by the tried widths:
  `control_nonaligned_period` shows a genuine 48-bit-period linear code is
  invisible at `{8,16,32,64,128,256}` and visible once width 48 is tried. A
  natural-corpus negative is scoped to the tried widths.

## 7. Reporting rules (applied in the paper)

- No size or gap is hand-typed; all come from `results/ledger.json` via
  `scripts/regen_tables.py`, checked by `scripts/check_paper_numbers.py`.
- Every aggregate names its N and its independence caveat.
- No inferential CI or p-value is stated. "Descriptive bootstrap over the N
  tested files" is the only interval form used, and only for the 12 Silesia
  members.
- The headline is the per-file `max G_pct` versus the pre-registered threshold,
  not a mean.
