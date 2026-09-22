# -*- coding: utf-8 -*-
"""mdoutline command line: bare `mdoutline SRC` runs make; build/render/bookmarks stay as stages."""
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


def _prepare(src_arg: str) -> tuple[Path, Path, Path]:
    """Resolve SRC into (chapters, book_dir, default_out).

    SRC is a single markdown file, a chapters directory, or a book
    directory containing chapters/. default_out's stem is also the config
    title fallback: file stem for a file, dir name for a directory.
    """
    arg = Path(src_arg).resolve()
    if arg.is_file():
        if arg.suffix.lower() != ".md":
            raise SystemExit(f"mdoutline: not a markdown file: {arg}")
        return arg, arg.parent, arg.with_suffix(".pdf")
    chapters = _resolve_src(arg)
    return chapters, arg, arg / f"{arg.name}.pdf"


def _cmd_make(args) -> int:
    src, book_dir, default_out = _prepare(args.src)
    cfg = fill_defaults(load_config(book_dir, args.config and Path(args.config)),
                        default_out.with_suffix(""))
    pdf = Path(args.out).resolve() if args.out else default_out
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
    src, book_dir, default_out = _prepare(args.src)
    cfg = fill_defaults(load_config(book_dir, args.config and Path(args.config)),
                        default_out.with_suffix(""))
    out = Path(args.out).resolve() if args.out else default_out.with_suffix(".html")
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


_SUBCOMMANDS = ("make", "build", "render", "bookmarks")


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)
    if not argv:
        argv = ["--help"]
    elif argv[0] not in _SUBCOMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "make")
    ap = argparse.ArgumentParser(
        prog="mdoutline",
        description="Markdown file or chapter directory -> one PDF with cover, "
                    "TOC and exact outline bookmarks.",
    )
    ap.add_argument("--version", action="version", version=f"mdoutline {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("make", help="build + render + bookmarks in one atomic run (default)")
    p.add_argument("src", help="markdown file, or directory of *.md chapters (book.toml optional)")
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
