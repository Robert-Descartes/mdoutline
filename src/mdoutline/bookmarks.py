# -*- coding: utf-8 -*-
"""Write the PDF outline from the document's own clickable TOC.

Every entry of the generated TOC is a GoTo link annotation, so the target page
of each heading is already stored in the PDF. Reading those links is exact and
immune to font-size or pagination changes; no text/size heuristics are needed.
Headings absent from the TOC fall back to a size-based search.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf


def _norm(s: str) -> str:
    return re.sub(r"[\s`*_~]", "", s)


def add_bookmarks(pdf_path: Path, headings) -> dict:
    """headings: [(level, title)] in document order. Returns a stats dict."""
    doc = pymupdf.open(pdf_path)
    want = {_norm(t): (lvl, t) for lvl, t in headings}

    # 1) target pages straight from the TOC hyperlinks
    found: dict[str, int] = {}
    for pno in range(len(doc)):
        page = doc[pno]
        for link in page.get_links():
            if link.get("kind") not in (pymupdf.LINK_GOTO, pymupdf.LINK_NAMED):
                continue
            if "page" not in link:
                continue
            rect = pymupdf.Rect(link["from"])
            text = page.get_text("text", clip=rect).strip()
            key = _norm(text)
            if key in want and key not in found:
                found[key] = link["page"] + 1
    from_toc = len(found)

    # 2) size-based fallback for headings missing from the TOC
    missing = [t for _, t in headings if _norm(t) not in found]
    if missing:
        sizes = []
        for pno in range(len(doc)):
            for blk in doc[pno].get_text("dict")["blocks"]:
                for ln in blk.get("lines", []):
                    if ln["spans"]:
                        sizes.append(ln["spans"][0]["size"])
        sizes.sort()
        threshold = sizes[len(sizes) // 2] * 1.25
        for pno in range(len(doc)):
            for blk in doc[pno].get_text("dict")["blocks"]:
                for ln in blk.get("lines", []):
                    text = "".join(s["text"] for s in ln["spans"]).strip()
                    size = max((s["size"] for s in ln["spans"]), default=0)
                    if size < threshold or not text:
                        continue
                    key = _norm(text)
                    if key in want and key not in found:
                        found[key] = pno + 1

    outline, missing_final, last = [], [], 1
    for lvl, title in headings:
        page = found.get(_norm(title))
        if page is None:
            missing_final.append(title)
            page = last
        last = page
        outline.append([lvl, title, page])

    doc.set_toc(outline)
    tmp = pdf_path.with_suffix(".tmp.pdf")
    doc.save(tmp, garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf_path)

    if missing_final:
        print("mdoutline: warning: not located (attached to previous page):",
              missing_final[:8], file=sys.stderr)
    return {
        "headings": len(headings),
        "from_toc": from_toc,
        "total": len(outline),
        "fallback_missing": len(missing_final),
    }
