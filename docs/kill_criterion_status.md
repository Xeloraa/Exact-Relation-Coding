# Kill-criterion status

`docs/preregistration.md` §7 (git-locked) freezes the research direction if
**all three** hold. This file tracks each; it does not modify the locked
criterion.

| # | condition | status (2026-08-29) |
| --- | --- | --- |
| 1 | **NEGATIVE on the full pre-registered corpus list.** | **Partly met.** NEGATIVE for the coverage achieved — 8/12 Silesia members whole, all 12 + enwik8 + 6 SDRBench float32 fields + UCI telemetry as ≥ 256 KiB prefixes; 0 files clear the threshold; validity gates pass. **Not met for the full list**: `samba`/`nci`/`webster`/`mozilla` (21–51 MB) and whole enwik8 / SDRBench / UCI were not runnable on 8 GiB (`docs/environment_constraints.md`). By `docs/preregistration.md` §4 the formal outcome is INCONCLUSIVE-for-the-full-list until those run. |
| 2 | **One bounded detector-broadening attempt moves no pre-registered natural file above the threshold.** | **MET.** The bit-phase-offset extension (`experiments/offset/run.py`, paper §8.4): for each width, reshape at every bit phase `0..w-1` (coarse for `w ∈ {128,256}`), carrying skipped bits as a counted `prefix` field. Verified to recover a phase-shifted planted code. Run on every pre-registered natural file (whole where feasible, else ≥ 256 KiB prefix): **0 files cross the 0.05 threshold**, and the offset search does not beat the phase-0 container by more than header perturbation on any file (`results/offset/verdicts.json`). The negative is robust to bit phase, not a framing artifact. |
| 3 | **The strongest context-mixing baseline actually executed does not absorb the planted-GF(2) composed gap.** | **MET for paq8l / paq8px v216.** `results/phase4_paq/`: paq8l `-3/-8` and paq8px v216 `-4/-8` on the 10 KiB planted code leave the parity gap intact (mixer-relative gap +4 968…+4 974 B ≈ the gzip/xz gap +4 949 B). cmix / nncp not run (hardware). |

## Consequence

- If condition 1 is completed on adequate hardware and stays NEGATIVE (expected,
  given 8/12 whole + 20 slices + the offset extension all negative), **all three
  hold** → the pre-registration says: freeze Exact-Relation Coding as a
  general-purpose compression research direction.
- Until then, per `docs/preregistration.md` §7's fallback clause ("If only the
  first holds → *negative, detector-scoped*"), and given condition 2 is now met,
  the accurate statement is: **the negative is established for the axis-aligned
  GF(2)/affine family at any bit phase, on the corpora covered; the one bounded
  broadening attempt did not rescue it.** The remaining open direction is a
  *materially* different relation family (non-axis-aligned linear via a
  searched/learned column permutation; low-degree polynomial) — named as the
  single follow-up, out of scope for this paper.
