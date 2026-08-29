# Exact-Relation Coding: does discovering algebraic relations help lossless compression after full accounting and composition?

**Status: working draft.** Controls, planted-code, and mixer results are
complete; the whole-file natural-corpus sweep is partial (2 of the
pre-registered corpus list run so far, remainder needs a ≥ 32 GiB machine —
`docs/environment_constraints.md`). The Results/Discussion tables come from
`paper/results_tables.md`, regenerated from `results/ledger.json`; inline numbers
carry HTML-comment markers of the form `src: <experiment>/<field> = <value>`
checked by `scripts/check_paper_numbers.py`. The pre-registration
(`docs/preregistration.md`, git-locked) fixes the threshold and decision rule;
this file restates but does not alter them. The Section 21 verdict is
`INCONCLUSIVE` until the whole-file sweep completes.

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
and paq8px v216 `-4/-8` do not absorb this gap. On the first whole natural file
completed — Silesia `dickens`,
<!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> bytes — the pre-pass
finds <!-- src: nat_silesia_dickens / n_relations = 25 --> relations but the
container is larger than what stock compressors achieve and composition makes it
worse (`G_abs` <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 -->
bytes). Twenty dev-machine feasibility slices show the same pattern. Functional-
dependency (`G_abs` <!-- src: control_priorart_affine_fd / composition_gap_bytes = 37880 -->)
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

Kept strictly separate; the paper never lets one stand in for another.

- **RQ-A (discoverable).** Does an exact relation exist and get found and
  verified on every row? (`n_relations ≥ 1`, `verify_basis` passes.)
- **RQ-B (reduces representation).** Is `|D(x)|` strictly below the never-worse
  passthrough, and is `raw_best(x) − |D(x)| > 0`?
- **RQ-C (survives composition).** Is `min_c |c(x)| − min_c |c(D(x))| > 0`? This
  is the only outcome that supports the hypothesis.

RQ-A → RQ-B → RQ-C is a strict funnel.

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
{`header`, `relation`, `payload`, `leftover`, `crc`, `framing`}. `finalize()`
raises unless

```
8·|D(x)|  =  header + relation + payload + leftover + crc + framing
framing   =  (−(header + relation + payload + leftover + crc)) mod 8   ∈ [0,7]
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
at a fixed period. §14's non-aligned-period control demonstrates directly that
an exact 48-bit-period linear code is invisible at the tried widths and visible
once width 48 is added.

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

Deferred/excluded corpora (with reasons) are logged in `docs/protocol.md` §4.
No corpus has been dropped for being unfavourable.

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

### 15.2 H2 — natural data — PENDING (partial)

Whole files completed: **2 of the pre-registered list.**

- `silesia_dickens` (<!-- src: nat_silesia_dickens / dataset_bytes = 10192446 --> B):
  RQ-A yes (<!-- src: nat_silesia_dickens / n_relations = 25 --> relations), RQ-B **no**
  (container <!-- src: nat_silesia_dickens / container_bytes = 9197882 --> B ≫
  `raw_best` <!-- src: nat_silesia_dickens / raw_best_bytes = 2799520 --> B), RQ-C **no**
  (`G_abs` <!-- src: nat_silesia_dickens / composition_gap_bytes = -2645016 --> B,
  `G_pct` −0.94). Round-trip and composed round-trip ok; independently verified
  (`verify_container` on the 10 MB container: `sha256_ok`, `accounting_ok`).
- `silesia_mozilla` whole-file: re-running cleanly (an earlier record from a
  stale background process was discarded — see `docs/audit.md` correction C1).

Dev-machine feasibility slices (256 KiB prefixes, `results/natural_slice/`, **not
the pre-registered answer**): 20/20 round-trip ok, **0 meaningful positives**;
GF(2) finds constant-bit-plane / ASCII-high-bit relations (RQ-A) but RQ-B and
RQ-C fail on every one; Silesia binaries fall to passthrough.

## 16. Negative results (layered)

Read from the ledger per `docs/statistics.md` §5. For the natural corpora
measured so far:

| layer | finding |
| --- | --- |
| L1 structure exists at a tried width | **frequently yes** — a zero high bit-plane on mostly-ASCII data, etc. |
| L2 discoverable & verified every row | **yes when L1 holds** (or the codec raises) |
| L3 reduces representation vs raw | **no** — description + container overhead exceeds the recovered bits; container is *larger* than `raw_best` |
| L4 survives metadata | **no** (accounting is inside `\|D(x)\|`) |
| L5 survives composition | **no**, usually large-negative |
| L6 strong mixer does not absorb planted gap | **holds** (paq8l/paq8px) — so a natural-data negative is about the data, not a weak baseline |

The redundancy the detector finds in natural data is real but trivial and is
already captured by stock compressors from the raw byte layout. This is the
scientifically useful content of the negative — not "the idea failed".

## 17. Ablations

- **Homogeneous vs affine GF(2):** the corruption-control affine case recovers a
  planted `XOR(all)⊕1` bit the homogeneous basis correctly misses (`+116` B on a
  1280×33 control); on natural slices neither variant reaches RQ-B.
- **Width sweep:** `control_nonaligned_period` — a 48-bit-period code is
  PASSTHROUGH at `{8,16,32,64,128,256}` and 24 relations once width 48 is added.
  Direct measure of the axis-aligned limitation.
- **CRC on/off (accounting):** removing the 32 CRC bits changes `|D(x)|` by 4 B
  and does not flip RQ-B/RQ-C on any measured file (the deficits are kilobytes
  to megabytes).
- **12-way `min` vs single width:** the representation-change null shows the
  `min` adds no false positive on 40 i.i.d. inputs.
- **paq level:** paq8l `-3`→`-8` and paq8px `-4`→`-8` change the mixer-relative
  planted gap by < 6 B — raising mixer memory does not absorb the XOR.

## 18. Limitations

- **Detector scope.** Axis-aligned fixed-width GF(2) + integer affine only. A
  negative is about these families; §17 shows structure at other periods is
  missed by construction.
- **Baseline ceiling.** cmix / nncp not run. The planted control bounds — but
  does not eliminate — "a stronger mixer would absorb it".
- **Whole-file sweep incomplete.** 2 of the pre-registered corpora run; the rest
  need ≥ 32 GiB RAM. Until then the natural-corpus result is INCONCLUSIVE by the
  pre-registration.
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

**Standing verdict:** controls and mechanism complete and passing; whole-file
natural sweep partial → **INCONCLUSIVE by the pre-registration**
(`docs/preregistration.md` §4). The most likely completed outcome, on the
partial evidence, is **B — a scoped negative-results paper** with the single
named follow-up (a non-axis-aligned detector); a positive would require a file
clearing 5 % and independent reproduction.

## 22. Conclusion

We built a rigorously accounted, independently verified, pre-registered test of
whether blind axis-aligned exact-relation discovery helps lossless compression
after composition. The mechanism works exactly as designed on planted linear
codes and is not absorbed by the strongest mixers we could run. On the natural
data measured so far it fails at the "reduces representation" layer and every
layer after it, finding only redundancy stock compressors already capture. The
whole-file sweep must complete on adequate hardware before the pre-registered
hypothesis verdict is issued.

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
python -m pytest -q                              # 90+ tests incl. equivalence, properties, independent verify
python verification/independent_verify.py --self-test

# controls (fast; any machine)
python experiments/controls/run.py               # exit 0 == all gates pass

# natural corpora
python experiments/natural/run.py --mode slice   # dev-machine provenance only
python experiments/natural/run.py --mode whole   # >= 32 GiB machine; the pre-registered answer
python experiments/natural/run.py --mode whole --only silesia_xml   # one corpus at a time

# ledger + paper tables + checks
python scripts/build_ledger.py
python scripts/regen_tables.py
python scripts/check_paper_numbers.py
python verification/independent_verify.py --ledger results/ledger.json

# everything
python scripts/reproduce.py --mode whole
```
