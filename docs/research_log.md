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

### Accounting
Every JSON file includes payload, relation description, header, framing, CRC, leftover. Round-trip required. Never-worse passthrough when GF(2) is not strictly smaller.

### Theory discipline
No claim that autoregressive models cannot represent parity. See `docs/theory.md`.
