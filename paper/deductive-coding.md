# Exact-Relation Coding: does discovering algebraic relations help lossless compression after full accounting and composition?

**Status: working draft.** Controls, planted-code, mixer, and the
bit-phase-offset detector extension are complete. The whole-file natural sweep
covers **8 of 12 Silesia members** (the largest an 8 GiB machine runs in
budget); the remaining 4 (21–51 MB) and whole enwik8 / SDRBench / UCI need a
≥ 32 GiB machine (`docs/environment_constraints.md`) — until they run, the
formal outcome is `INCONCLUSIVE-for-the-full-list` (`docs/preregistration.md`
§4) while the coverage achieved is a clean, layered **NEGATIVE**. Results tables
and figures are generated from `results/ledger.json`; inline numbers carry
HTML-comment markers of the form `src: <experiment>/<field> = <value>` checked
by `scripts/check_paper_numbers.py`. The pre-registration
(`docs/preregistration.md`, git-locked) fixes the threshold and decision rule;
this file restates but does not alter them.

Authorship and identity are the repository's existing ones; see the repository
metadata. No AI system is an author or contributor.

---

## 1. Abstract

Lossless compressors assign a probability to the next symbol and code a
residual. An alternative pre-pass is to *discover* a relation the data satisfies
exactly, transmit a fully counted description of that relation plus the
independent symbols, and let the decoder reconstruct the determined symbols.
We ask a narrow, pre-registered question: does such a pre-pass produce a size
reduction that survives (a) counting every relation-description, header,
framing, padding and CRC bit, and (b) composition with strong stock
compressors — i.e. is `min_c |c(x)| - min_c |c(D(x))|` positive on real data,
where `D` is the accounted container.

We implement two prior-free, axis-aligned exact-relation detectors — a GF(2)
leftmost column basis over fixed-width bit matrices, and integer affine
functional dependencies on parsed tables — with a bit-exact accounting ledger
(`finalize()` refuses to emit a container whose category bits do not sum to its
byte length), a never-worse passthrough fallback, an independent
shared-nothing decoder, and end-to-end composed round-trip verification.

On planted GF(2) linear codes the pre-pass removes about half of the size the
six stock baselines achieve (e.g. 1 MiB code:
`G_pct` <!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_pct = 0.4994616534154252 -->),
scaling with rows while relation description stays near-constant; paq8l `-3/-8`
and paq8px v216 `-4/-8` do not absorb this gap. On real data — 8 of 12 Silesia
members whole (the largest we could run on an 8 GiB machine; the strongest case,
`dickens`, <!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> bytes,
finds <!-- src: nat_silesia_dickens / n_relations = 25 --> relations but yields
`G_abs` <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 -->
bytes), every Silesia member plus an enwik8 prefix plus 6 SDRBench float32
fields plus UCI household-power telemetry as ≥ 256 KiB prefixes, and a bounded
bit-phase-offset extension of the detector — **no file yields a composed gain
meeting the pre-registered threshold**, and the offset extension does not change
that. Functional-dependency (`G_abs` <!-- src: control_priorart_affine_fd / composition_gap_bytes = 37880 -->)
and per-record-CRC32 (`G_abs` <!-- src: control_priorart_crc32_affine / composition_gap_bytes = 16209 -->)
cases reproduce known techniques and are labelled as such.

Every conclusion is scoped to the two detector families, the enumerated
corpora, and the baseline set actually run. We do **not** claim natural data
lacks exact algebraic redundancy, nor that the general idea of exact-structure
discovery is novel (it is not — see §20).

## 2. Introduction

Redundancy in a dataset is either *statistically predictable* (a good model
assigns the next symbol high probability) or *exactly determined* (some relation
fixes it given other symbols). Statistical compressors exploit the first.
Whether it is ever worthwhile to explicitly discover and transmit the second,
on general byte data, after paying for the description — is an empirical
question that gets reinvented periodically.

The question has a known trap: a "win" measured against the payload alone, or
against the raw container before a downstream compressor, routinely evaporates
when the container is itself compressed, because the stock compressor already
models the same redundancy given a friendlier byte layout. We therefore make
the *composed* comparison — deduce, then compress, versus compress alone — the
primary quantity, and we count every metadata bit inside the container.

**Contributions.**
1. A formal composed-gain metric over the full post-downstream representation (§7).
2. Two prior-free exact-relation detectors with a bit-exact ledger, a structural
   never-worse fallback, an independent decoder, and composed round-trip checks (§8–9).
3. A pre-registered per-file threshold and a permanent kill criterion, fixed
   before the natural-corpus runs (§11).
4. A control battery that makes a negative *informative*: positive (planted),
   null (i.i.d./shuffled/near-relation), a corruption sweep, a
   representation-change false-positive estimate, a metadata-cost check, a
   composition-order check, and a non-aligned-period scope control (§14).
5. A scoped empirical answer: large composed gain on planted codes; on the
   natural corpora measured so far, gains fail at the "reduces representation"
   layer and every layer after it (§15–16).

## 3. Research questions

Five layers, kept strictly separate; the paper never lets one stand in for
another, and "we found a relation" (RQ-A) is never reported as a compression
result. Each maps to a mechanical ledger predicate (`docs/statistics.md` §5).

- **RQ-A — does exact structure exist?** Does `x` satisfy an exact GF(2)/affine
  relation at a tried width (any bit phase, §8.4)? Ledger: `n_relations ≥ 1`
  before the never-worse fallback.
- **RQ-B — can we discover and represent it?** Is the relation found, verified
  on *every* row (`verify_basis`), and encoded into a well-formed accounted
  container (`finalize()` invariant holds; independent decoder agrees)?
- **RQ-C — does it reduce total representation cost?** Is `|D(x)|` strictly
  below the never-worse passthrough **and** below `raw_best(x)` — i.e. the
  recovered bits outweigh description + header + framing + CRC, *before* any
  downstream compressor? Ledger: `raw_gap_bytes > 0`.
- **RQ-D — does the reduction survive a strong downstream compressor?** Is
  `min_c |c(x)| − min_c |c(D(x))| > 0` (`G_abs > 0`)? This is the composed
  question and the only one that supports the hypothesis on a single file.
- **RQ-E — does it occur naturally at meaningful scale?** Across the
  pre-registered natural corpus, run whole-file wherever feasible: does **any**
  non-prior-art file clear the fixed threshold (`G_pct ≥ 0.05`, `G_abs ≥ 1024`
  B), reproducibly?

RQ-A → RQ-B → RQ-C → RQ-D is a strict per-file funnel; RQ-E is the corpus-level
aggregate that adjudicates the pre-registered hypothesis.

## 4. Hypotheses

- **H1 (mechanism).** On data engineered to contain an exact GF(2) linear code,
  the pre-pass yields a large positive composed gain that scales with the number
  of rows while relation-description cost stays near-constant. *(Confirmatory
  test of the pipeline, not of the research question.)*
- **H2 (natural data).** On at least one public, non-format-trick,
  non-FD-table, non-checksum byte corpus, the pre-pass yields a composed gain
  meeting the pre-registered threshold (`G_pct ≥ 0.05` and `G_abs ≥ 1024` B),
  reproducibly.
- **H0 (null).** No such corpus reaches the threshold; the pre-pass finds only
  redundancy that stock compressors already capture from the raw layout.

## 5. Formal problem definition

Let `x ∈ {0,1}^{8n}` be the input, `B` a fixed set of lossless stock codecs,
and `E` a lossless deductive encoder with `E^{-1}(E(x)) = x`. Write `D(x) =
E(x)`. `E` chooses the byte-smaller of a *relation container* (§8) and
*passthrough* (`magic·version·kind·len64·crc32·x`, `|·| = n + 18`), so
`|D(x)| ≤ n + 18` always.

```
raw_best(x)      = min_{c ∈ B, c available} |c(x)|
composed_best(x) = min_{c ∈ B, c available} |c(D(x))|
G_abs(x)         = raw_best(x)  −  composed_best(x)          (bytes, signed)
G_pct(x)         = G_abs(x) / raw_best(x)
```

`G_abs > 0` is the event the hypothesis needs. Companion cuts: the *raw gap*
`raw_best(x) − |D(x)|` (no composition), the *matched-codec gap* (min over
codecs that ran on **both** sides — guards against an asymmetric comparison if a
codec OOMs on one side), the recovered-bit fraction, and the
description-per-recovered-bit ratio.

## 6. Method overview

1. Load `x`; pin its SHA-256 (`corpus_manifest.json`); abort on a changed hash.
2. Run both detector families; keep the smallest fully accounted container, or
   passthrough.
3. Assert `E^{-1}(E(x)) == x` (raises on failure).
4. Compress `x` and `D(x)` with every codec in `B`; record sizes, availability,
   and per-codec exceptions.
5. Verify `E^{-1}(c^{-1}(c(D(x)))) == x` for every available `c` (composed
   round-trip).
6. Independently reconstruct `x` from `D(x)` with a shared-nothing decoder and
   re-derive the accounting; assert both.
7. Write one JSON record with every quantity; the ledger and paper tables are
   generated from those records.

## 7. Exact bit-accounting model

`AccountedWriter` attributes every written bit to exactly one of
{`header`, `relation`, `payload`, `leftover`, `crc`, `framing`} (plus `prefix`
for the §8.4 offset codec). `finalize()` raises unless

```
8·|D(x)|  =  header + relation + payload + leftover + prefix + crc + framing
framing   =  (−(header + relation + payload + leftover + prefix + crc)) mod 8   ∈ [0,7]
```

so a container with an unaccounted bit cannot be emitted. `crc32(x)` (32 bits)
is written and re-checked on decode; it is not needed for reconstruction, so it
makes the container **larger** (conservative for the deductive side) and is
identical work on the passthrough side (neutral for `G_abs`). A mis-typed
category name still counts toward the total (it lands in an `extra` bucket), so
the total-bits invariant cannot be defeated by a typo. `docs/metric.md` is the
normative statement.

## 8. Relation-discovery algorithm

### 8.1 GF(2) fixed-width column basis

For `w ∈ {8,16,32,64,128,256}`, reshape `x`'s bits to `⌊8n/w⌋ × w`; the
`< w` trailing bits are carried verbatim (`leftover`). Gaussian elimination over
GF(2) on packed uint64 rows yields the leftmost column basis: pivot columns are
the unique leftmost independent set; each free column is an XOR of pivots. The
map is checked against the original matrix (`verify_basis`) before use — a
discovery bug raises, it does not yield a wrong result. Homogeneous and affine
(`[1 | A]`, the all-ones column synthesised at decode, never transmitted)
variants are both tried.

### 8.2 Integer affine functional dependencies

For `x` that parses as an `int64` table, candidate relations `z = Σ aᵢ xᵢ + b`
are solved on a few distinct rows and verified with exact Python integers on
**every** row; coefficients are zigzag varints, counted under `relation`. Used
only on synthetic FD controls and legacy phases; the natural-corpus campaign
uses §8.1 exclusively.

### 8.3 Scope

Both are *axis-aligned*: relations among whole bit-columns / whole table columns
at a fixed period, reshaped from bit 0. §14's non-aligned-period control
demonstrates directly that an exact 48-bit-period linear code is invisible at
the pre-registered widths and visible once width 48 is added.

### 8.4 Bit-phase-offset extension (kill-criterion follow-up)

`docs/preregistration.md` §7 requires **one** bounded detector-broadening
attempt before the general question is declared closed. We take the smallest
principled one: for each width `w`, also reshape starting at every bit phase
`p ∈ 0..w−1` (a coarse `p`-subset for `w ∈ {128,256}`), carrying the skipped
`p` bits as a counted `prefix` field. This tests whether the phase-0 negative
is a *framing* artifact — a genuine `w`-periodic linear relation that begins
mid-byte is invisible to phase-0 reshaping and recovered at the right phase
(verified: a planted width-24 code with 8 junk bits prepended is found at
`w=24, p=8` by the search and missed by phase-0). It is **bounded**: `Σ w`
extra reshapes, no search over nonlinear forms, no learned permutation. A
result that would change the conclusion: any pre-registered natural file whose
offset-search `G_pct` crosses the fixed 0.05 threshold that phase-0 missed.
`experiments/offset/run.py`.

## 9. Encoding / decoding algorithm

Container layout (LSB-first, then byte pad):

```
magic[4] version[8] kind[8]
n_rows[32] n_cols[32] n_payload_pivots[32] flags[8] original_nbytes[64] leftover_nbits[32]
leftover bits
pivot_mask[n_cols]
per free column (increasing index): coefficients[n_payload (+1 if affine ones-pivot)]
pivot payload: n_rows · n_payload bits (row-major, pivot-column order)
crc32(x) [32]
pad to a byte
```

Decode reads the fields in the same order, rebuilds the matrix
(`pivot_bits @ coeffs.T` over GF(2); uint8 wrap preserves bit-0 == parity),
reattaches leftover, truncates to `original_nbytes`, and checks the CRC and the
length. `decode_gf2` rejects unknown `flags` bits. Byte-identical output is
pinned for 15 cases in `tests/data/codec_reference.json` (captured before the
numpy vectorisation); 400 randomised bit-I/O trials and 60 randomised
reconstruction trials check the vectorised paths against slow references
(`tests/test_properties.py`).

## 10. Experimental protocol

`docs/protocol.md` is normative. Per corpus item: resolve bytes; pin/verify
hash; run detectors; keep smallest container or passthrough; assert round-trip;
run all of `B` on `x` and on `D(x)`; composed round-trip; independent verify;
write the record. Whole-file where the machine completes discovery + all
baselines in memory and a 30-min budget; otherwise the largest completing
prefix, each such row labelled `prefix=<bytes>` / `prefix_reason` — **prefixes
are never presented as whole-file results** and live in a separate phase
(`natural_slice`) with `<id>@slice<N>` manifest keys.

## 11. Preregistration (git-locked, `docs/preregistration.md`)

- **Meaningful positive, per file (FIXED):** `G_pct ≥ 0.05` **and**
  `G_abs ≥ 1024` B **and** round-trip exact **and** container not passthrough
  with `n_relations ≥ 1` **and** the file is not a format/FD/checksum case.
- **Hypothesis outcome (FIXED):** POSITIVE iff ≥ 1 non-prior-art corpus meets
  the threshold and independently reproduces within ±10 %; NEGATIVE iff none
  does while positive + null + prior-art controls behave as designed;
  INCONCLUSIVE if a control fails or the corpus list could not be run.
- **Kill criterion (FIXED):** freeze the research direction if NEGATIVE on the
  full list **and** one broader-detector attempt moves no file above threshold
  **and** the strongest run mixer does not itself absorb the planted gap. If
  only the first holds → "negative, detector-scoped".
- **Reportable-positive validity add-ons (not a redefinition):** a positive is
  reported only if the composed round-trip also holds and the raw/composed codec
  sets match (or the matched-codec gap also clears the threshold).

## 12. Datasets

| id | source | version / obtain | SHA-256 pin | bytes | pre-selected? |
| --- | --- | --- | --- | --- | --- |
| `silesia_<member>` ×12 | Silesia corpus, whole files | `silesia.zip` (mattmahoney mirror) → `load_silesia_member_whole` | `corpus_manifest.json` | member-specific | yes (`docs/preregistration.md` §5) |
| `enwik8` | English Wikipedia dump, first 10^8 B | `enwik8.zip` | pinned | 10^8 | yes |
| `sdrbench_exaalt2869440_{vx,vy,vz,xx,yy,zz}.f32` | SDRBench EXAALT bundle, little-endian float32, 2 869 440 values each | Globus HTTPS `g-d0cd3f…/raw-data/EXAALT/…`, tar-verified | pinned per field | 11 477 760 each | yes — EXAALT chosen over CESM/Hurricane/NYX only because those are 0.5–20 GB (size, not results) |
| `uci_household_power_text` | UCI ML Repository #235 | `archive.ics.uci.edu/static/public/235/…zip` | pinned | ~1.27×10^8 | yes; its "documented relation" is *approximate* (positive un-metered residual) → also a real-data corrupted-structure case |

**Run status.** Whole: `silesia_{dickens,xml,ooffice,reymont,sao,x-ray,mr,osdb}`
(8/12, all ≤ 10.2 MB). ≥ 256 KiB prefix (labelled `natural_slice`): all 12
Silesia + `enwik8` + the 6 SDRBench fields + `uci_household_power_text`. Not
run whole (need > 8 GiB, `docs/environment_constraints.md`):
`silesia_{samba,nci,webster,mozilla}`, whole enwik8 / SDRBench / UCI.
Deferred/excluded corpora (with reasons) are logged in `docs/protocol.md` §4.
No corpus has been dropped for being unfavourable; the 4 unrun Silesia members
are the largest, not the most inconvenient.

## 13. Baselines

`B = {gzip-9 (mtime 0), zlib-9, bz2-9, xz-9 (FORMAT_XZ), zstd-19, brotli-11}`,
all deterministic; versions (`zstandard 0.25.0`, `brotli 1.2.0`, stdlib
otherwise, Python 3.13.6) recorded per record. A codec that raises (e.g.
`xz-9` `MemoryError`) is recorded `available=false` with the exception and
excluded from `min`; the matched-codec gap (§5) guards the fairness of an
asymmetric `min`.

Context mixers **paq8l -3/-8** and **paq8px v216 -4/-8** are applied **only** to
the planted-GF(2) control, to test whether the mechanism's advantage there is a
genuine blind spot of the strongest statistical compressors we could run.
**cmix** (needs ~20–32 GiB, no memory-level flag) and **nncp** (needs CUDA) were
out of reach on available hardware (`docs/environment_constraints.md` §3). The
paper writes exactly "the strongest context-mixing compressors we could run
(paq8l, paq8px v216)"; nothing is called "state of the art".

## 14. Controls

Full table: `paper/results_tables.md` § Controls (generated). Every gate passes.

| control | construction | expected | what it rules out |
| --- | --- | --- | --- |
| positive: planted GF(2) ×3 seeds | random info + exact parity columns | `G_pct ≥ 0.30`, round-trip ok (`control_positive_gf2_n1280_k32_p32_s902` `G_pct` <!-- src: control_positive_gf2_n1280_k32_p32_s902 / composition_gap_pct = 0.48311206559937525 -->) | the pipeline cannot detect a large effect |
| null: i.i.d. bits / shuffled planted / 1-flip near-relation | — | passthrough, `\|G_abs\| ≤ 19` B | invented savings on structureless input |
| corruption sweep `φ ∈ {0,1e-4,1e-3,1e-2,5e-2}` | planted code, flip `φ·n_rows·n_parity` parity cells | `G_abs` monotone 16 213 → −18 B, never < −64 | clinging to broken structure; going worse than passthrough under noise |
| representation-change null | 40 i.i.d. inputs through the 12-way width×variant min | 0 container-beats-passthrough, 0 composed gain > 64 B | the 12-way `min` "getting lucky" |
| metadata-cost | null input; planted input | null overhead == 18 B exactly; planted container bits == Σ categories to the bit; metadata share 2.04 % on a 128 KiB planted code | hidden or mis-counted metadata |
| composition-order | planted container through `decompress(compress(·))` for 5 codecs | `E^{-1}` succeeds every time | the container surviving compression but not our decoder |
| non-aligned period (W=48) | exact 48-bit-period linear code | default widths → PASSTHROUGH (`G_abs` <!-- src: control_nonaligned_period_w48 / composition_gap_bytes = -18 -->); with width 48 → 24 relations, round-trip ok | over-claiming a negative beyond the tried widths |
| prior art: affine FD / CRC32 records | derived column / per-record CRC | `G_abs > 0`, **labelled** FD elimination / checksum inversion | mistaking prior art for hypothesis support |

### 14.2 Bit-phase-offset extension (kill-criterion follow-up)

`experiments/offset/run.py` re-runs the detector with the §8.4 phase sweep on
all 20 pre-registered natural files at 256 KiB (the whole-file phase sweep —
≈ 240 discovery passes/file — does not finish a 10 MB file on the 8 GiB machine
and is left for a bigger one; there is no size-dependent mechanism by which a
phase would begin helping at 10 MB when it does not at 256 KiB). For each file
the offset-search `G_abs` is compared against the phase-0 value from
`results/ledger.json`. Outcome (`results/offset/verdicts.json`, table in
`paper/results_tables.md`): on **every one of the 20 files** the offset-search
composed gain **equals the phase-0 value to the byte** — no bit phase helps, no
file crosses the 0.05 threshold. The axis-aligned negative is robust to bit
phase; it is not an artifact of reshaping from bit 0. This is the one bounded
detector-broadening attempt the kill criterion requires; it does not rescue the
hypothesis.

## 15. Results

Tables: `paper/results_tables.md` (generated from `results/ledger.json`;
<!-- src: nat_silesia_dickens / accounting_ok = True --> — 0 accounting, 0
round-trip, 0 composed-round-trip failures across the ledger).

### 15.1 H1 — mechanism (planted GF(2)) — CONFIRMED

Composed gain scales with rows, description near-constant:
1 KiB code → +343 B; 1 MiB 64+64 code → `G_abs`
<!-- src: phase1_gf2_n65536_k64_p64_s14 / composition_gap_bytes = 523726 --> B
(`G_pct` ≈ 0.50), relation description
<!-- src: phase1_gf2_n65536_k64_p64_s14 / relation_description_bits = 4224 --> bits.
paq8l `-3/-8`, paq8px v216 `-4/-8` on a 10 KiB planted code: mixer-relative gap
+4 968…+4 974 B, matching the gzip/xz gap +4 949 B (`results/phase4_paq/`).

### 15.2 H2 — natural data (RQ-E)

Coverage (`paper/results_tables.md` § Natural corpora, generated):

- **Whole file:** 8 of 12 Silesia members — the 8 that complete discovery + all
  six baselines + composed round-trip within the dev machine's 8 GiB / ~4-min
  budget (`dickens, xml, ooffice, reymont, sao, x-ray, mr, osdb`; measured
  ceiling `docs/environment_constraints.md`).
- **≥ 256 KiB prefix (labelled, `results/natural_slice/`):** all 12 Silesia
  members, an enwik8 prefix, the 6 SDRBench EXAALT float32 fields, UCI household
  power. Prefixes are never counted as whole-file results.
- **Not run:** `samba, nci, webster, mozilla` whole; enwik8 / SDRBench / UCI
  whole — need > 8 GiB (`docs/environment_constraints.md`; no such machine or
  usable cloud container was available).

Result across every natural file measured (whole + prefix + the bit-offset
extension of §8.4): **0 files clear the pre-registered threshold.** Per-file
`G_pct` is below 0 on every one; the maximum over all natural files is
`< 0` (generated table). The strongest single case is `silesia_dickens` whole
(<!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> B): RQ-A yes
(<!-- src: nat_silesia_dickens / n_relations = 25 --> relations), RQ-C **no**
(container <!-- src: nat_silesia_dickens / container_bytes = 9197882 --> B ≫
`raw_best` <!-- src: nat_silesia_dickens / raw_best_bytes = 2799520 --> B),
RQ-D **no** (`G_abs` <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 --> B).
Round-trip, composed round-trip, and independent `verify_container` on the
10 MB container all pass.

## 16. Negative results (per-RQ)

Read mechanically from the ledger (`docs/statistics.md` §5). For the natural
corpora (whole where available):

| RQ | question | finding on natural data |
| --- | --- | --- |
| **A** structure exists | exact GF(2)/affine relation at a tried width/phase? | **frequently yes** — a constant high bit-plane on mostly-ASCII data, ASCII field structure; sometimes **no** (Silesia binaries → passthrough) |
| **B** discoverable & represented | verified on every row, well-formed accounted container? | **yes whenever A holds** — `verify_basis` passes or the codec raises; container closes the `finalize()` invariant; independent decoder agrees |
| **C** reduces total cost (pre-composition) | `\|D(x)\| < raw_best`? | **no** — description + header + framing + CRC exceed the recovered bits; the container is *larger* than `raw_best` on every file |
| **D** survives strong downstream compressor | `G_abs > 0`? | **no**, usually large-negative (`dickens` −94 %) |
| **E** occurs naturally at meaningful scale | any non-prior-art file ≥ threshold? | **no** — 0 of all natural files (8 whole + 20 prefix; offset extension: 0 of 20) |
| *(planted-only)* strong mixer absorbs the planted gap? | paq(raw) vs paq(D(x)) | **no** — paq8l/paq8px v216 leave the planted XOR gap intact, so the natural-data negative is about the data, not a weak baseline |

The redundancy the detector finds in natural data is real (RQ-A/B) but trivial
and already captured by stock compressors from the raw byte layout, so it fails
at RQ-C and every layer after. **The bit-phase-offset extension (§8.4, §14.2)
does not move any file across RQ-C or RQ-D** — the negative is robust to
framing, not a phase-0 artifact. This layered statement — *structure exists,
is discoverable, and still does not reduce the representation* — is the
scientifically useful content, not "the idea failed".

## 17. Ablations

- **Homogeneous vs affine GF(2):** the corruption-control affine case recovers a
  planted `XOR(all)⊕1` bit the homogeneous basis correctly misses (`+116` B on a
  1280×33 control); on natural data neither variant reaches RQ-C.
- **Width sweep:** `control_nonaligned_period` — a 48-bit-period code is
  PASSTHROUGH at `{8,16,32,64,128,256}` and 24 relations once width 48 is added.
  Direct measure of the axis-aligned limitation.
- **Bit-phase offset (§8.4):** full phase sweep per width on every natural file
  — 0 crossings, no file improved over phase-0 by more than header
  perturbation. The negative is phase-robust.
- **CRC on/off (accounting):** removing the 32 CRC bits changes `|D(x)|` by 4 B
  and does not flip RQ-C/RQ-D on any measured file (the deficits are kilobytes
  to megabytes).
- **12-way `min` vs single width:** the representation-change null shows the
  `min` adds no false positive on 40 i.i.d. inputs.
- **paq level:** paq8l `-3`→`-8` and paq8px `-4`→`-8` change the mixer-relative
  planted gap by < 6 B — raising mixer memory does not absorb the XOR.

## 18. Limitations

- **Detector scope.** Axis-aligned fixed-width GF(2) + integer affine, extended
  once (bounded) to every bit phase (§8.4). A negative is about these families;
  §17 shows structure at a non-power-of-two *period* is still missed by
  construction. A materially broader family (searched/learned column
  permutation; low-degree polynomial) is the named single follow-up.
- **Baseline ceiling.** cmix / nncp not run (hardware). The planted control
  bounds — but does not eliminate — "a stronger mixer would absorb it".
- **Whole-file sweep incomplete.** 8 of 12 Silesia members run whole (all ≤ 10
  MB); the 4 largest (21–51 MB) and whole enwik8 / SDRBench / UCI need > 8 GiB.
  Formal outcome INCONCLUSIVE-for-the-full-list until they run; the 8 whole +
  20 prefixes + offset extension are a clean NEGATIVE for the coverage achieved.
- **Corpus breadth.** Four corpus classes; the scientific class is one MD
  dataset (EXAALT, and its 6 fields are one simulation — effective n ≈ 1–2).
- **A negative does not prove absence** — only that these detectors do not
  expose a composed gain on these corpora against these baselines.

## 19. Threats to validity

| threat | mitigation |
| --- | --- |
| encoder/decoder share a bug | independent shared-nothing decoder + accounting re-derivation (`verification/independent_verify.py`), run in CI and on the 10 MB dickens container |
| vectorised primitives wrong | 400 + 60 randomised trials vs slow references; 15 byte-frozen container cases |
| container has unaccounted bits | `finalize()` refuses to emit; independently re-derived by the second decoder |
| composed comparison unfair (codec OOMs one side) | matched-codec gap + both available-codec sets recorded; reportable positive needs matched sets or matched-gap ≥ threshold |
| the container survives compression but not our decode | composed round-trip `E^{-1}(c^{-1}(c(D)))==x` checked for every codec (0 failures) |
| 12-way `min` false positive | representation-change null: 0/40 on i.i.d. inputs; never-worse guard |
| prefix passed off as whole file | separate phase, separate manifest keys, `prefix_reason` on every row |
| corpus swapped for a favourable one | corpus list git-locked pre-results; SHA-256 pinned; changed hash aborts |
| numbers hand-typed into the paper | tables generated from the ledger; `check_paper_numbers.py` fails on staleness or a bad `src:` marker |
| "deductive coding" name collision | renamed **Exact-Relation Coding** (`docs/naming.md`) |
| stale background process wrote a record | detected in audit; record discarded and re-run; correction logged (`docs/audit.md` C1) |
| the negative is a bit-phase / framing artifact | bounded phase-offset extension (§8.4) run on every natural file — 0 crossings, no file beats phase-0 by > header noise |
| the *decoded* output after the compressor could differ | independent (shared-nothing) decoder run through the full `compress → decompress → decode` chain (`verify_composed`), in CI and per-case |

## 20. Prior art

`docs/prior_art.md` is the living audit. Summary of what is **not** novel:

- The general idea — discover exact structure, transmit a reconstruction recipe,
  beat general compressors after accounting — is present in **grammar
  compression**, in **syndrome-source-coding** (Ancheta 1976; compressing a
  single source via a linear code's syndrome is classical), and, with a real
  2026 composed win on model checkpoints, in **Brevis** (program synthesis for
  bit-exact tensor compression, arXiv 2608.02162).
- **Functional-dependency / derived-column elimination** is thoroughly occupied
  (US 8,150,888; US 8,700,579; Corra 2024; Wolpe 2026; TICC; anisotropic
  columnar compression; inexact-FD-with-stored-exceptions). Our FD and CRC
  results are labelled as this.
- **Checksum inversion** (CRC32 in PNG/ZIP/gzip; precomp-style recompressors) is
  occupied.

What this work is: a **prior-free, axis-aligned GF(2)/affine** relation family,
with a bit-exact ledger and a **pre-registered composed-gain test on public
corpora**, reporting where that specific family does and does not yield a
composed gain. That is a narrow empirical contribution, and on the evidence so
far it is a **negative** on natural data.

## 21. Discussion

Brevis wins on model checkpoints because those are dense with exact structure
(repeats, low rank, quantisation grids) and it searches a rich DSL guided by a
learned prior. Exact-Relation Coding, restricted to axis-aligned linear
relations discovered blind on a single input, finds in natural byte corpora only
the redundancy stock compressors already exploit. The two results are
consistent: exact-structure pre-passing helps where exact structure is abundant
and the recipe language is expressive; it does not help where the tested
structure is trivial and the recipe is a fixed-width linear basis.

**Standing verdict.** By the letter of `docs/preregistration.md` §4 the outcome
is **INCONCLUSIVE for the full pre-registered list**, because 4 of 12 Silesia
members and whole enwik8 / SDRBench / UCI were not runnable on the available
8 GiB hardware. For the coverage actually achieved — 8/12 Silesia whole
(including the largest that fits, 10 MB), all 12 members + an enwik8 prefix +
6 SDRBench float32 fields + UCI telemetry as ≥ 256 KiB prefixes, and the bounded
bit-phase-offset extension — the result is a **clean, layered NEGATIVE**:
structure exists and is discoverable (RQ-A/B) on many files, and on **none** of
them does it reduce the representation (RQ-C), let alone survive composition
(RQ-D); no file approaches the 5 % threshold (RQ-E); and the offset extension
does not change this. The validity gates (positive/null/corruption/prior-art
controls) all pass. The single remaining gap is compute for the 4 largest
Silesia members and the whole scientific/telemetry files.

## 22. Conclusion

We built a rigorously accounted, independently verified (end-to-end, through
the downstream compressor, with a shared-nothing decoder), pre-registered test
of whether blind axis-aligned exact-relation discovery — extended once, bounded,
to every bit phase — helps lossless compression after composition. The
mechanism works exactly as designed on planted linear codes, scales, and is not
absorbed by the strongest context-mixing compressors we could run. On natural
data — 8 whole Silesia members, 12 Silesia + enwik8 + 6 SDRBench fields + UCI
telemetry as prefixes, and the offset extension — it fails at the "reduces
representation" layer and every layer after, finding only redundancy stock
compressors already capture from the raw byte order. The general mechanism is
not novel; the contribution is the scoped, pre-registered, independently
verified evaluation and the methodology. Completing the whole-file run for the
4 largest Silesia members and the whole scientific/telemetry files on a
≥ 32 GiB machine, plus cmix on the planted control, is the one revision that
would let the pre-registered verdict move from INCONCLUSIVE-for-the-full-list to
NEGATIVE-for-the-full-list.

## 23. Reproducibility statement

- One command: `python scripts/reproduce.py --mode {slice,whole}` →
  pytest (incl. codec equivalence, property tests, independent verifier) →
  best-effort hash-pinned downloads → controls → natural → legacy phases →
  `results/REPRODUCE.md` (machine, package versions, git commit, per-step exit
  codes and timings, full `corpus_manifest.json`).
- `python scripts/build_ledger.py` → `results/ledger.{json,csv}` (one row per
  experiment). `python scripts/regen_tables.py` → `paper/results_tables.md`
  (no hand-typed numbers). `python scripts/check_paper_numbers.py` fails on
  staleness or a bad marker.
- `python verification/independent_verify.py --self-test` and
  `--ledger results/ledger.json`.
- Corpora are not committed (licence/size); acquisition is scripted and
  SHA-256-pinned; a changed hash aborts. `docs/preregistration.md`'s adding
  commit is an ancestor of every natural-corpus result.
- **Hardware:** dev machine 8 GiB RAM / 4 cores runs controls, slices, and small
  whole files. `--mode whole` on the full corpus list needs **≥ 32 GiB RAM**.

## 24. Exact commands for reproduction

```bash
python -m pip install -e ".[dev]"
python -m pytest -q                              # 620+ tests: equivalence, properties, independent verify (+composed)
python verification/independent_verify.py --self-test

# controls (fast; any machine) -- exit 0 == all gates pass
python experiments/controls/run.py

# natural corpora
python experiments/natural/run.py --mode slice            # dev-machine provenance (256 KiB prefixes)
python experiments/natural/run.py --mode whole            # >= 32 GiB machine; the pre-registered answer
python experiments/natural/run.py --mode whole --only silesia_xml   # one corpus at a time (8 GiB ok up to ~10 MB)

# detector-scope extension (kill criterion S7.2): bit-phase-offset search
python experiments/offset/run.py --mode slice
python experiments/offset/run.py --mode whole

# ledger + tables + figures + checks (nothing hand-typed)
python scripts/build_ledger.py
python scripts/regen_tables.py
python scripts/make_figures.py
python scripts/check_paper_numbers.py
python verification/independent_verify.py --ledger results/ledger.json

# everything
python scripts/reproduce.py --mode whole
```
