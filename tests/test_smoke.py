# -*- coding: utf-8 -*-
"""End-to-end smoke test: build the demo book and verify bookmark landing.

Run:  python tests/test_smoke.py
Needs: pip install -e . && playwright install chromium  (or set MDOUTLINE_BROWSER)
"""
import re
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

import pymupdf  # noqa: E402
from mdoutline.bookmarks import _norm  # noqa: E402
from mdoutline.cli import main  # noqa: E402

DEMO = REPO / "examples" / "demo"


def check_duplicate_ids(tmp: Path) -> None:
    """Two identical numeric headings must get distinct ids + a warning."""
    src = tmp / "dup"
    src.mkdir()
    (src / "a.md").write_text("# 1 One\n\n## 1.1 Same\n\ntext\n", encoding="utf-8")
    (src / "b.md").write_text("# 2 Two\n\n## 1.1 Same number again\n\ntext\n", encoding="utf-8")
    from mdoutline.htmlbuild import build_html
    from mdoutline.config import BookConfig
    out = tmp / "dup.html"
    build_html(src, out, BookConfig(title="dup"))
    html = out.read_text(encoding="utf-8")
    assert html.count('id="sec-1-1"') == 1, "first sec-1-1 should keep the plain id"
    assert 'id="sec-1-1-2"' in html, "duplicate heading should get a suffixed id"
    print("PASS duplicate-id handling")


def check_e2e(tmp: Path) -> None:
    pdf = tmp / "demo.pdf"
    rc = main(["make", str(DEMO), "-o", str(pdf)])
    assert rc == 0, "mdoutline make exited nonzero"
    assert pdf.is_file() and pdf.stat().st_size > 10_000, "pdf missing or suspiciously small"

    doc = pymupdf.open(pdf)
    try:
        toc = doc.get_toc()
        assert len(toc) >= 12, f"expected >=12 bookmarks, got {len(toc)}"

        missed = []
        for lvl, title, page in toc:
            text = _norm(doc[page - 1].get_text())
            probe = _norm(title)
            probe = probe[-8:] if len(probe) > 8 else probe
            if probe not in text:
                missed.append((title, page))
        assert not missed, f"bookmarks not landing on their heading page: {missed}"

        full = "".join(doc[i].get_text() for i in range(len(doc)))
        pages = len(doc)
    finally:
        doc.close()
    for probe in ("mdoutline Demo Book", "Contents", "中文排版验证", "Deletion marks"):
        assert probe in full, f"expected content missing from pdf: {probe!r}"
    print(f"PASS e2e: {pages} pages, {len(toc)} bookmarks, all landing exactly")


def check_single_file(tmp: Path) -> None:
    """Bare invocation (no subcommand) on one file with multi-level headings."""
    pdf = tmp / "cjk.pdf"
    rc = main([str(DEMO / "chapters" / "03-cjk.md"), "-o", str(pdf)])
    assert rc == 0, "bare mdoutline <file.md> exited nonzero"
    assert pdf.is_file() and pdf.stat().st_size > 10_000, "single-file pdf missing or tiny"

    doc = pymupdf.open(pdf)
    try:
        toc = doc.get_toc()
        assert len(toc) >= 4, f"expected >=4 bookmarks for the single file, got {len(toc)}"
        missed = []
        for lvl, title, page in toc:
            text = _norm(doc[page - 1].get_text())
            probe = _norm(title)
            probe = probe[-8:] if len(probe) > 8 else probe
            if probe not in text:
                missed.append((title, page))
        assert not missed, f"single-file bookmarks not landing: {missed}"
    finally:
        doc.close()
    print("PASS single-file bare invocation")


def main_test() -> None:
    with tempfile.TemporaryDirectory(prefix="mdoutline-test-") as td:
        tmp = Path(td)
        check_duplicate_ids(tmp)
        check_e2e(tmp)
        check_single_file(tmp)
    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main_test()
