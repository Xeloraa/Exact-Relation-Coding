# Research log

## 2026-08-29 — Phase 0–3 first measured loop

Empty repo → prototype → tests (27 passed) → phases 0–3.

### Hypothesis 1
Exact GF(2) parity bits are omitted more cheaply than gzip/zstd/xz/brotli can encode them, after relation-description cost.

**Result: confirmed on synthetic planted codes**, including composition. 1 MiB 64+64 code: DEDC 524850 vs best baseline 1048581; composed gap +523726. Description 4224 bits.

### Hypothesis 2
Discovery without planted masks still finds a basis.

**Result: confirmed** (phase2 sparse 24+24, 24 relations, composed gap +24464).

### Hypothesis 3
Null data and broken relations must not produce a net win.

**Result: confirmed.** iid bits, shuffle, near-flip, non-affine product: passthrough or full rank; no useful relations. Product composed +168 is xz(header||raw) luck, not deduction.

### Hypothesis 4
Ordinary text has a GF(2) composed gap.

**Result: falsified on this repo's source/docs** (116597 B → DEDC 114857, best_stat 26135, composed gap -43830). Two relations found; statistical codecs still dominate.

### Hypothesis 5
Integer affine derived columns yield a composed win.

**Result: confirmed, labeled prior art.** 32k-row affine table composed gap +149936. Do not claim novelty (Corra, patents, Wolpe 2026 FD pre-pass).

### Hypothesis 6
Tiny SQLite/JSON/C fixtures demonstrate a general corpus gap.

**Result: rejected.** SQLite GF(2) shrinks zeros (8192→3104) and still loses to xz (145 B). Format/sparsity.

### Hypothesis 7
Per-record CRC32 is a GF(2) (affine) relation that gzip/xz will not invert.

**Result: confirmed, labeled format-aware checksum.** Homogeneous 31 relations, DEDC 17067, composed gap +15701. Affine GF(2) (ones column first) 32 relations, DEDC 16559, composed gap +16209. Not novelty.

### Decision
Do not kill. Synthetic mechanism is real. General-text gap is not. CRC and FD wins are real and pre-occupied. Affine GF(2) is implemented and still a checksum when it hits CRC32. Continue only with experiments that distinguish “planted linear code / FD table / checksum” from “arbitrary bytes.” Next: local enwik8 if available; never commit copyrighted dumps.

## 2026-08-29 — Phase 4 natural / formats / scaling

### Hypothesis 8
A 1 MB enwik8 prefix, local CPython stdlib `.py`, or the running interpreter prefix has a GF(2) composed gap.

**Result: falsified.** enwik8 prefix: passthrough, brotli 281012 vs DEDC 1000018, composed −80 (header). Stdlib: one 8-bit-plane relation (ASCII high bit), DEDC 350037 vs brotli 74546, composed −65177. PE stub: passthrough, composed −24.

### Hypothesis 9
Whole-file GF(2) inverts PNG/ZIP CRC32 or yields a composed gap on a larger SQLite FD file.

**Result: rejected.** PNG/ZIP/SQLite 4000-row: `n_relations==0`, passthrough, negative composed gaps of header size or xz/brotli dominance. General bit-matrix is not a format parser.

### Hypothesis 10
JSON/log text with an exact derived field, or CSV `c=a+b` as *bytes*, shows a composed GF(2) gap.

**Result: falsified for GF(2) on text** (JSON composed −11194; logs −5152; CSV text −21753). **Confirmed for parsed int64 CSV**, composed +15560, **labeled FD elimination / prior art.**

### Hypothesis 11
Planted GF(2) composed gap scales with rows; relation description does not.

**Result: confirmed.** 1 KiB → 256 KiB, description 1088 bits, composed +343 … +127829.

### Hypothesis 12
Homogeneous GF(2) misses `XOR(all) XOR 1`; affine recovers it.

**Result: confirmed** on 1280×33 (homogeneous passthrough; affine 1 relation, composed +116). Control, not a corpus claim.

### Hypothesis 13
xz/brotli on packed independent bits beats the accounted GF(2) container.

**Result: rejected.** 10 KiB: packed 5120 → best 5124; payload+description 5295 vs DEDC 5291. 100 KiB: 51200 → 51204; 51375 vs 51371. Pivots are incompressible; packing is not an extra win.

### Hypothesis 14
Silesia prefixes have a GF(2) composed gap.

**Result: falsified.** All twelve 512000-byte prefixes, all `roundtrip_ok`. Every composed gap is negative.

- dickens: GF2, 1 relation, composed −114679.
- xml: GF2, 1 relation, composed −24245.
- x-ray: GF2, 4 relations, composed −75917.
- ooffice: passthrough, composed −20 (header).
- mozilla: passthrough, composed −149 (header).
- mr: passthrough, composed −78 (header).
- nci: GF2, 1 relation (ASCII plane), DEDC 448037 vs bz2 29853, composed −17833.
- sao: passthrough, composed −20 (header).
- osdb: passthrough, composed −67 (header).
- reymont: GF2, 1 relation, DEDC 448037 vs bz2 98623, composed −38291.
- samba: passthrough, composed −133 (header).
- webster: GF2, 1 relation, DEDC 448037 vs bz2 110460, composed −59085.

Negative composed gaps are falsification, not a near-miss. Do not claim novelty. Dumps not committed.

### Hypothesis 15
paq8l absorbs planted GF(2) XOR, so the gzip/xz gap is a weak-baseline artifact.

**Result: rejected at paq8l -3** on 10 KiB (seed 902). paq(raw)=10299 vs DEDC 5291 vs paq(DEDC)=5331. Mixer-relative gap +4968, same order as gzip/xz +4949.

### Hypothesis 16
paq8l `-8` (~1.6 GB) absorbs the same planted XOR.

**Result: rejected.** paq(raw)=10321 vs DEDC 5291 vs paq(DEDC)=5347. Mixer-relative gap +4974. Higher memory does not invert the parity bits. Not paq8px or cmix.

### Decision
Do not kill. Do not claim a real-corpus success. Planted GF(2) remains the only large composed gap among measured byte strings that are not FD tables or checksums. paq8l `-3` and `-8` do not absorb it. All twelve Silesia prefixes lose on composition. Never commit dumps.

### Accounting
Every JSON file includes payload, relation description, header, framing, CRC, leftover. Round-trip required. Never-worse passthrough when GF(2) is not strictly smaller.

### Theory discipline
No claim that autoregressive models cannot represent parity. See `docs/theory.md`.
