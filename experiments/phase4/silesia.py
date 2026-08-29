"""Phase 4: Silesia prefixes (dumps not committed).

Public compression corpus mix: English text, XML, 16-bit medical, Windows DLL.
General GF(2) on byte prefixes; not a format parser. Dumps stay gitignored.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT / "experiments") not in sys.path:
    sys.path.insert(0, str(ROOT / "experiments"))

from common import persist, print_record, run_codec_experiment  # noqa: E402
from deductive.codecs.gf2_codec import encode_bytes_best_gf2  # noqa: E402
from deductive.datasets.corpora import (  # noqa: E402
    load_silesia_member_prefix,
    try_download_silesia_member,
    try_download_silesia_zip,
)

MEMBERS = (
    ("dickens", "English ASCII novels"),
    ("xml", "concatenated XML (tar)"),
    ("x-ray", "16-bit grayscale DICOM"),
    ("ooffice", "Windows DLL"),
)
PREFIX = 512_000
HYPOTHESIS = (
    "Silesia prefixes are ordinary bytes, not planted linear codes. "
    "Composed GF(2) gap vs xz/brotli is expected negative."
)


def _gf2(data: bytes):
    widths = (8, 16, 32, 64) if len(data) > 80_000 else (8, 16, 32, 64, 128)
    return lambda d=data, w=widths: encode_bytes_best_gf2(d, widths=w)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    only = set(argv) if argv else None
    zip_status = try_download_silesia_zip(timeout=180)
    print(f"silesia zip: {zip_status}")
    if "download failed" in zip_status:
        for member, _desc in MEMBERS:
            print(f"silesia member {member}: {try_download_silesia_member(member, timeout=90)}")

    ran = 0
    for member, desc in MEMBERS:
        if only and member not in only:
            continue
        data, note = load_silesia_member_prefix(member, PREFIX)
        if data is None:
            print(f"skip {member}: {note}")
            continue
        rec = run_codec_experiment(
            phase="phase4_silesia",
            experiment_id=f"phase4_silesia_{member}_p{len(data)}",
            dataset_id=f"silesia_{member}_prefix_{len(data)}",
            data=data,
            seed=None,
            config={
                "codec": "gf2_best",
                "category": "silesia",
                "member": member,
                "n_bytes": len(data),
                "label": "public_corpus_prefix",
            },
            encode_fn=_gf2(data),
            hypothesis=HYPOTHESIS,
            notes=f"{desc}; {note}; dump not committed",
            skip_slow_baselines=len(data) > 2_000_000,
        )
        persist(rec, "phase4_silesia")
        print_record(rec)
        ran += 1
    if ran == 0:
        print("silesia: no members loaded; continuing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
