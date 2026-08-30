"""Render paper/exact-relation-coding.md to a submission-ready PDF.

Pipeline: manuscript Markdown -> substitute ledger source-markers with their
rendered values -> Markdown to HTML (python-markdown, tables + fenced code) ->
wrap in an academic print stylesheet, inline the SVG figures -> headless
Chromium/Edge --print-to-pdf.

    python scripts/build_ledger.py && python scripts/regen_tables.py
    python scripts/make_figures.py
    python scripts/check_paper_numbers.py      # markers must already verify
    python scripts/build_pdf.py

Outputs paper/exact-relation-coding.pdf (and .html alongside, self-contained).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
MD = ROOT / "paper" / "exact-relation-coding.md"
TABLES_MD = ROOT / "paper" / "results_tables.md"
FIG_DIR = ROOT / "paper" / "figures"
HTML_OUT = ROOT / "paper" / "exact-relation-coding.html"
PDF_OUT = ROOT / "paper" / "exact-relation-coding.pdf"

MARKER = re.compile(r"<!--\s*src:\s*([A-Za-z0-9_./-]+)\s*/\s*([A-Za-z0-9_]+)\s*=\s*(.+?)\s*-->")


def _render_value(field: str, raw: str) -> str:
    raw = raw.strip()
    try:
        f = float(raw)
    except ValueError:
        return raw
    if "pct" in field:
        s = f"{f * 100:+.2f}\u00a0%"
        return s.replace("-", "\u2212")
    if f == int(f):
        s = f"{int(f):,}"
        return s.replace("-", "\u2212")
    return raw


def substitute_markers(text: str) -> str:
    # keep the marker as an HTML comment too, so the source stays auditable in the HTML
    return MARKER.sub(lambda m: f"{_render_value(m.group(2), m.group(3))}"
                                f"<!-- {m.group(1)}/{m.group(2)} -->", text)


CSS = """
@page { size: A4; margin: 20mm 18mm 22mm 18mm;
        @bottom-center { content: counter(page) " / " counter(pages); font-size: 9px; color:#666; } }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Georgia","Times New Roman",serif; font-size: 10.2pt; line-height: 1.42;
       color:#111; max-width: 46em; margin: 0 auto; }
h1 { font-size: 17pt; line-height:1.25; margin: 0 0 .3em; text-align:center; font-family:"Helvetica Neue",Arial,sans-serif; }
h2 { font-size: 12.5pt; margin: 1.4em 0 .4em; padding-bottom:2px; border-bottom:1px solid #ccc;
     font-family:"Helvetica Neue",Arial,sans-serif; }
h3 { font-size: 10.8pt; margin: 1.1em 0 .3em; font-family:"Helvetica Neue",Arial,sans-serif; }
h2, h3 { page-break-after: avoid; }
p { margin: .45em 0; text-align: justify; hyphens: auto; }
code, pre { font-family: "SFMono-Regular","Consolas","Menlo",monospace; font-size: 8.8pt; }
pre { background:#f6f6f6; border:1px solid #e2e2e2; border-radius:4px; padding:.6em .8em;
      white-space: pre-wrap; word-wrap: break-word; page-break-inside: avoid; }
code { background:#f2f2f2; padding: 0 2px; border-radius:2px; }
pre code { background: none; padding: 0; }
a { color:#0b3d91; text-decoration: none; }
table { border-collapse: collapse; width: 100%; margin: .8em 0; font-size: 8.4pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #bbb; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background:#eee; font-family:"Helvetica Neue",Arial,sans-serif; }
td:not(:first-child), th:not(:first-child) { text-align: right; }
img, svg { max-width: 100%; height: auto; display:block; margin: .6em auto; page-break-inside: avoid; }
figure { margin: 1em 0; page-break-inside: avoid; }
figcaption { font-size: 8.6pt; color:#333; text-align:center; margin-top:.3em; }
hr { border:0; border-top:1px solid #ccc; margin: 1.6em 0; }
.title-block { text-align:center; margin-bottom: 1.4em; }
.title-block .meta { font-size: 8.8pt; color:#444; margin-top:.5em; }
blockquote { border-left:3px solid #ccc; margin:.6em 0; padding:.2em .9em; color:#333; }
ul, ol { margin:.4em 0 .4em 1.3em; padding:0; }
li { margin:.15em 0; }
.appendix h2 { page-break-before: always; }
""".strip()


def _svg(name: str) -> str:
    p = FIG_DIR / f"{name}.svg"
    if not p.is_file():
        return f"<em>[missing figure: {name}]</em>"
    content = p.read_text(encoding="utf-8")
    content = re.sub(r"<\?xml[^>]*\?>", "", content)
    content = re.sub(r"<!DOCTYPE[^>]*>", "", content)
    return content


def inline_figures_md(md_text: str) -> str:
    """Replace a standalone `FIGURE::name` line with an <svg> figure block."""
    def repl(m):
        return f'<figure>{_svg(m.group(1))}</figure>'
    return re.sub(r"^FIGURE::([A-Za-z0-9_]+)\s*$", repl, md_text, flags=re.M)


def build_html() -> str:
    text = substitute_markers(MD.read_text(encoding="utf-8"))
    text = inline_figures_md(text)

    lines = text.splitlines()
    h1 = next((l[2:].strip() for l in lines if l.startswith("# ")), "Exact-Relation Coding")
    body_md = "\n".join(l for l in lines if not l.startswith("# "))

    html_body = markdown.markdown(
        body_md,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{h1}</title>
<style>{CSS}</style>
</head><body>
<div class="title-block">
  <h1>{h1}</h1>
  <div class="meta">Preregistered empirical study &nbsp;&middot;&nbsp;
  inconclusive for the full corpus, clean negative within the achieved coverage<br>
  frozen experiment state: git tag <code>v1.1-final</code> &nbsp;&middot;&nbsp;
  repository: https://github.com/Xeloraa/Exact-Relation-Coding<br>
  every quantity traceable to <code>results/ledger.json</code></div>
</div>
{html_body}
</body></html>
"""


def find_browser() -> str | None:
    for name in ("chrome", "chromium", "chromium-browser", "google-chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    cands = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in cands:
        if Path(c).is_file():
            return c
    return None


def main() -> int:
    html = build_html()
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"wrote {HTML_OUT} ({len(html):,} bytes)")

    browser = find_browser()
    if not browser:
        print("ERROR: no Chromium/Edge found for --print-to-pdf", file=sys.stderr)
        return 2

    PDF_OUT.unlink(missing_ok=True)
    cmd = [
        browser, "--headless", "--disable-gpu", "--no-sandbox",
        "--no-pdf-header-footer",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=10000",
        f"--print-to-pdf={PDF_OUT}",
        HTML_OUT.as_uri(),
    ]
    print("$", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not PDF_OUT.is_file() or PDF_OUT.stat().st_size < 20_000:
        print(r.stdout[-2000:]); print(r.stderr[-2000:], file=sys.stderr)
        print("ERROR: PDF not produced or too small", file=sys.stderr)
        return 3
    print(f"wrote {PDF_OUT} ({PDF_OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
