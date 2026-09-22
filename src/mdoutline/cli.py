# -*- coding: utf-8 -*-
"""mdoutline command line: build/render/bookmarks, plus atomic `make`."""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import __version__
from .bookmarks import add_bookmarks
from .config import fill_defaults, load_config
from .htmlbuild import build_html, headings_from_html
from .render import render_pdf


def _resolve_src(src: Path) -> Path:
    """Accept either the chapters dir itself or a book dir containing chapters/."""
    if src.is_dir() and not list(src.glob("*.md")) and (src / "chapters").is_dir():
        return src / "chapters"
    return src


def _cmd_make(args) -> int:
    book_dir = Path(args.src).resolve()
    src = _resolve_src(book_dir)
    cfg = fill_defaults(load_config(book_dir if book_dir != src else src,
                                    args.config and Path(args.config)), book_dir)
    pdf = Path(args.out).resolve() if args.out else book_dir / f"{book_dir.name}.pdf"
    pdf.parent.mkdir(parents=True, exist_ok=True)

    if args.keep_html:
        html_path = pdf.with_suffix(".html")
        build_html(src, html_path, cfg)
        render_pdf(html_path, pdf, cfg)
        headings = headings_from_html(html_path)
    else:
        with tempfile.TemporaryDirectory(prefix="mdoutline-") as td:
            html_path = Path(td) / "book.html"
            build_html(src, html_path, cfg)
            render_pdf(html_path, pdf, cfg)
            headings = headings_from_html(html_path)
    stats = add_bookmarks(pdf, headings)
    print(f"mdoutline: {stats['total']} bookmarks ({stats['from_toc']} exact from TOC links) "
          f"-> {pdf}")
    return 0


def _cmd_build(args) -> int:
    book_dir = Path(args.src).resolve()
    src = _resolve_src(book_dir)
    cfg = fill_defaults(load_config(book_dir if book_dir != src else src,
                                    args.config and Path(args.config)), book_dir)
    out = Path(args.out).resolve() if args.out else book_dir / f"{book_dir.name}.html"
    build_html(src, out, cfg)
    print(f"mdoutline: html written -> {out}")
    return 0


def _cmd_render(args) -> int:
    html_path = Path(args.html).resolve()
    cfg = fill_defaults(load_config(html_path.parent, args.config and Path(args.config)),
                        html_path.parent)
    pdf = Path(args.out).resolve() if args.out else html_path.with_suffix(".pdf")
    render_pdf(html_path, pdf, cfg)
    print(f"mdoutline: pdf written -> {pdf} (bookmarks not written; use `make` or `bookmarks`)")
    return 0


def _cmd_bookmarks(args) -> int:
    pdf = Path(args.pdf).resolve()
    if not args.html:
        print("mdoutline: --html is required (heading levels come from the generated html)",
              file=sys.stderr)
        return 2
    headings = headings_from_html(Path(args.html))
    stats = add_bookmarks(pdf, headings)
    print(f"mdoutline: {stats['total']} bookmarks ({stats['from_toc']} exact from TOC links) "
          f"-> {pdf}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="mdoutline",
        description="Markdown chapters -> one PDF with cover, TOC and exact outline bookmarks.",
    )
    ap.add_argument("--version", action="version", version=f"mdoutline {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("make", help="build + render + bookmarks in one atomic run")
    p.add_argument("src", help="directory containing *.md chapters (and optional book.toml)")
    p.add_argument("-o", "--out", help="output pdf path (default: <src-name>.pdf next to src)")
    p.add_argument("--config", help="path to book.toml (default: <src>/book.toml)")
    p.add_argument("--keep-html", action="store_true",
                   help="keep the intermediate html next to the pdf")
    p.set_defaults(fn=_cmd_make)

    p = sub.add_parser("build", help="chapters -> styled html")
    p.add_argument("src")
    p.add_argument("-o", "--out")
    p.add_argument("--config")
    p.set_defaults(fn=_cmd_build)

    p = sub.add_parser("render", help="html -> pdf (no bookmarks)")
    p.add_argument("html")
    p.add_argument("-o", "--out")
    p.add_argument("--config")
    p.set_defaults(fn=_cmd_render)

    p = sub.add_parser("bookmarks", help="write outline bookmarks into a rendered pdf")
    p.add_argument("pdf")
    p.add_argument("--html", required=True, help="generated html (heading source)")
    p.set_defaults(fn=_cmd_bookmarks)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
