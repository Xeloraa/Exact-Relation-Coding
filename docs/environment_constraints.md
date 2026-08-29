# Environment constraints and their effect on the campaign

Recorded 2026-08-29 on the development machine so the paper's Limitations section
is grounded in measured facts, not vague hedging.

## 1. Development machine

| property | value | how measured |
| --- | --- | --- |
| OS | Windows 11 Home 10.0.22631 | `platform.platform()` |
| CPU | 4 logical cores | `os.cpu_count()` |
| RAM total | 8025 MiB | `GlobalMemoryStatusEx.ullTotalPhys` |
| RAM available (idle) | ~500–580 MiB (93% load) | two samples, `ullAvailPhys` |
| Disk free | 7.8 GiB of 120 GiB (94% full) | `shutil.disk_usage` |
| Python | 3.13.6, MSC v.1944 64-bit | `sys.version` |
| numpy / zstandard / brotli | 2.2.6 / 0.25.0 / 1.2.0 | import |
| C/C++ toolchain | **none** (`gcc`, `g++`, `make`, `cmake`, `clang`, `cl` all absent) | `command -v` |
| WSL | present (`wsl.exe`) but shares the 8 GiB ceiling | `command -v wsl` |
| network | outbound HTTPS works (Silesia mirror returned 200) | `curl -sI` |

## 2. Consequence for whole-file corpora

A whole Silesia member as an `n_rows × w` GF(2) bit matrix costs `8·|file|`
bytes as `uint8`, plus a working copy for Gaussian elimination, plus each
baseline's own buffers. `xz -9` alone requests ~700 MiB. Measured earlier in the
project: `xz -9` raised `MemoryError` on a **1 MiB** enwik8 prefix on this
machine after GF(2) discovery.

Therefore, on this machine (measured, not estimated):

- Feasible: inputs up to ~256 KiB (feasibility slices, controls, synthetic);
  and, foreground with a long timeout, **one** whole Silesia member up to
  ~10 MiB — `silesia_dickens` (10 192 446 B) completes discovery + all six
  baselines + composed round-trip in a few minutes and is independently
  verified.
- **Not feasible:** the 12-width `encode_bytes_best_gf2` sweep on a 5.3 MiB file
  (`silesia_xml`) did not finish in 120 s on 4 cores; `silesia_mozilla`
  (51 MiB) did not complete a clean whole-file run (OOM / time). So whole
  Silesia members above ~10 MiB, `enwik8` whole, whole SDRBench fields
  (11.5 MiB each), and UCI household power whole (~127 MiB) are deferred to the
  ≥ 32 GiB machine. Background long-runs on this OS proved unreliable to kill
  (a zombie corrupted one record — `docs/audit.md` C1); whole-file runs are now
  foreground only.

The whole-file sweep is **deferred to a higher-memory machine** (target: ≥ 32
GiB RAM) and is driven by `scripts/reproduce.py` with no code changes. Every
row produced on the development machine that used a prefix is labelled
`prefix=<bytes>` / `prefix_reason=MemoryError` in its result JSON. Prefixes are
never presented as whole-file results.

### Cheapest legitimate path to the missing compute — investigated 2026-08-29

- **This machine, foreground, longer budget:** works up to ~10 MiB per Silesia
  member (`xml` 5.3 MB → 1m54s; `mr`/`osdb` 10 MB → ~4 min). **Done for 8 of 12
  Silesia members** (`dickens, xml, ooffice, reymont, sao, x-ray, mr, osdb`).
- **A cloud routine (claude.ai RemoteTrigger):** four create attempts, each
  rejected by an undocumented nested schema (`session_request` / `job_config`
  → requires a `ccr`-shaped object not exposed to this session). Abandoned:
  further blind schema-guessing bills the user per request, and a claude.ai
  code container's RAM is not guaranteed to exceed this box's anyway. A user
  with a ≥ 32 GiB machine runs the identical sweep via
  `python scripts/reproduce.py --mode whole` (or
  `python experiments/natural/run.py --mode whole --only silesia_mozilla`, one
  file at a time). No code, threshold, or corpus change is needed.
- **Remaining gap:** `samba` (21 MB), `nci` (34 MB), `webster` (41 MB),
  `mozilla` (51 MB); `enwik8` whole (100 MB); the 6 SDRBench fields whole
  (11.5 MB each); UCI whole (127 MB). These need a machine with > 8 GiB RAM
  that this environment does not provide. The paper reports exactly which files
  are whole and which are ≥ 256 KiB prefixes, and scopes the verdict
  accordingly (`docs/preregistration.md` §4: coverage is "enough for a scoped
  NEGATIVE" — 8/12 whole + every member as a slice + the offset extension — but
  a top-venue reviewer would want the 4 giants; see `docs/venue_assessment.md`).

## 3. Consequence for context-mixing baselines

| compressor | requirement | status on this machine | decision |
| --- | --- | --- | --- |
| `paq8l` | ~59 MiB (`-3`) … 1.6 GiB (`-8`) | binary present under `data/downloads/paq8l/`; `-3` runs; `-8` runs slowly | **kept** for the planted-GF(2) control (already measured) |
| `paq8px v216` | ~660 MiB (`-4`) … 2.4 GiB (`-8`) | binary present; runs on ~10 KiB inputs | **kept** for the planted-GF(2) control (already measured) |
| `cmix` | allocates a fixed ~20–32 GiB model regardless of input size; no memory-level flag | **cannot run** (8 GiB machine, ~0.5 GiB free); no toolchain to build | **not run.** Documented as a limitation. |
| `nncp` | GPU (CUDA) strongly assumed; large model; very slow on CPU | **cannot run** (no CUDA GPU) | **not run.** Documented as a limitation. |
| `zpaq`, `bsc` | C/C++ build | no toolchain | not run |

**Wording rule for the paper.** The natural-corpus baseline is exactly
`{gzip9, zlib9, bz2_9, xz9, zstd19, brotli11}`. The planted-GF(2) control adds
`{paq8l -3, paq8l -8, paq8px v216 -4, paq8px v216 -8}`. Nothing is described as
"the strongest context mixers" — the honest phrase is "the strongest
context-mixing compressors we could run (paq8l, paq8px v216); cmix and nncp were
out of reach on available hardware". If cmix / nncp are later run on adequate
hardware, this file and the claim are updated together.

## 4. What this does NOT excuse

- It does not weaken the metric, the accounting, or the never-worse guard.
- It does not permit dropping a corpus for being inconvenient — only for a
  documented technical reason (licence, unreadable format, or a size that no
  available machine can process), logged in `docs/protocol.md` §4.
- A NEGATIVE result still requires the full pre-registered corpus list to have
  been run **somewhere** (this machine for small cases, a bigger machine for the
  rest) before it is reported. Until then the status is INCONCLUSIVE by
  `docs/preregistration.md` §4.
