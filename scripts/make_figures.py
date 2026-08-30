"""Generate paper figures from results/ledger.json. No hand-placed data points.

    python scripts/build_ledger.py && python scripts/make_figures.py

Writes:
  paper/figures/fig_natural_gpct.svg   per-file composed G_pct, natural corpus
  paper/figures/fig_planted_scaling.svg  planted GF(2): |G_abs| vs input bytes
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "results" / "ledger.json"
OUTDIR = ROOT / "paper" / "figures"
THRESH = 0.05


def load():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def fig_natural(rows):
    nat = [r for r in rows if r["phase"] in ("natural", "natural_slice", "offset")]
    # one bar per (dataset, phase); prefer whole over slice for the same base id
    seen = {}
    for r in nat:
        base = (r["dataset_id"] or "").split("@")[0]
        tag = {"natural": "whole", "natural_slice": "slice", "offset": "offset"}[r["phase"]]
        g = r.get("composition_gap_pct")
        if g is None:
            continue
        seen.setdefault(base, {})[tag] = g
    if not seen:
        return
    bases = sorted(seen)
    fig, ax = plt.subplots(figsize=(6.6, max(3, 0.30 * len(bases))))
    y = range(len(bases))
    for tag, color in (("whole", "#1f77b4"), ("slice", "#9ecae1"), ("offset", "#d62728")):
        pts = [(i, seen[b].get(tag)) for i, b in enumerate(bases) if seen[b].get(tag) is not None]
        if pts:
            ax.scatter([v for _, v in pts], [i for i, _ in pts], s=24, label=tag, color=color, zorder=3)
    ax.axvline(0, color="k", lw=0.8)
    ax.axvline(THRESH, color="green", ls="--", lw=1, label=f"threshold +{THRESH:.0%}")
    ax.set_yticks(list(y))
    ax.set_yticklabels(bases, fontsize=6.5)
    ax.set_xlabel("composed gain  G_pct", fontsize=8)
    ax.tick_params(axis="x", labelsize=7)
    ax.set_title("Natural corpus: composed gain per file", fontsize=9)
    ax.legend(fontsize=7, loc="lower left", framealpha=0.9)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTDIR / "fig_natural_gpct.svg", bbox_inches="tight")
    plt.close(fig)


def fig_planted(rows):
    pts = []
    for r in rows:
        if r["codec_kind"] != "GF2":
            continue
        did = r["dataset_id"] or ""
        if not (did.startswith("gf2_n") or "gf2_n" in did) or r["phase"] not in ("phase1", "phase4", "phase0", "controls"):
            continue
        g = r.get("composition_gap_bytes")
        b = r.get("dataset_bytes")
        if g is None or b is None or g <= 0:
            continue
        pts.append((b, g))
    if len(pts) < 2:
        return
    pts.sort()
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.loglog([b for b, _ in pts], [g for _, g in pts], "o-", color="#1f77b4")
    ax.set_xlabel("input size (bytes)", fontsize=8)
    ax.set_ylabel("composed gain  G  (bytes)", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.set_title("Planted GF(2): composed gain vs input size", fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTDIR / "fig_planted_scaling.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    rows = load()
    fig_natural(rows)
    fig_planted(rows)
    print(f"wrote figures to {OUTDIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
