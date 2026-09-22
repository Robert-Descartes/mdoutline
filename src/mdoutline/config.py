# -*- coding: utf-8 -*-
"""Book-level configuration: a small dataclass loaded from an optional book.toml."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from pathlib import Path

try:  # tomllib is stdlib on 3.11+; 3.10 needs the backport
    from tomllib import load as _toml_load  # noqa: F811
except ImportError:  # pragma: no cover
    from tomli import load as _toml_load  # type: ignore


@dataclass
class BookConfig:
    """All rendering knobs. Every field can be set in book.toml under [book]."""

    title: str = ""
    subtitle: str = ""
    authors: str = ""
    date: str = ""
    summary: str = ""
    lang: str = "zh-CN"
    cover: bool = True
    toc_title: str = "Contents"
    header_left: str = "{title}"
    header_right: str = "{subtitle}"
    footer_format: str = "{page} / {pages}"
    page_format: str = "A4"
    margin_top_mm: float = 18.0
    margin_bottom_mm: float = 16.0
    margin_left_mm: float = 16.0
    margin_right_mm: float = 16.0
    css: str = ""          # extra css file appended after the built-in theme
    browser_path: str = "" # chromium executable; MDOUTLINE_BROWSER env overrides
    settle_ms: int = 500   # extra wait after fonts.ready, keeps pagination stable

    def header_footer_templates(self):
        """Chromium header/footer templates; {page}/{pages} become span hooks."""
        subs = {
            "title": self.title,
            "subtitle": self.subtitle,
            "page": '<span class="pageNumber"></span>',
            "pages": '<span class="totalPages"></span>',
        }
        left = _esc(self.header_left).format(**subs)
        right = _esc(self.header_right).format(**subs)
        foot = _esc(self.footer_format).format(**subs)
        header = (
            '<div style="width:100%;font-size:7.5px;color:#7f8c8d;padding:0 12mm;'
            'display:flex;justify-content:space-between;">'
            f"<span>{left}</span><span>{right}</span></div>"
        )
        footer = (
            '<div style="width:100%;font-size:7.5px;color:#7f8c8d;text-align:center;">'
            f"{foot}</div>"
        )
        return header, footer

    def margins(self) -> dict:
        return {
            "top": f"{self.margin_top_mm}mm",
            "bottom": f"{self.margin_bottom_mm}mm",
            "left": f"{self.margin_left_mm}mm",
            "right": f"{self.margin_right_mm}mm",
        }


def _esc(text: str) -> str:
    import html

    return html.escape(text, quote=False)


def load_config(src: Path, explicit: Path | None = None) -> BookConfig:
    """BookConfig from explicit book.toml, else <src>/book.toml if present, else defaults.

    The [book] table is used directly; a bare top-level table is accepted too.
    """
    path = explicit or (src / "book.toml")
    cfg = BookConfig()
    if not path.is_file():
        return cfg
    with path.open("rb") as f:
        data = _toml_load(f)
    table = data.get("book", data)
    from typing import get_type_hints

    hints = get_type_hints(BookConfig)
    for key, val in table.items():
        if key not in hints:
            raise SystemExit(f"book.toml: unknown key '{key}' (in {path})")
        if not isinstance(val, hints[key]):
            raise SystemExit(f"book.toml: '{key}' expects {hints[key].__name__}, "
                             f"got {type(val).__name__}")
        setattr(cfg, key, val)
    if cfg.css and not Path(cfg.css).is_absolute():
        cfg.css = str((path.parent / cfg.css).resolve())
    return cfg


def fill_defaults(cfg: BookConfig, src: Path) -> BookConfig:
    if not cfg.title:
        cfg.title = src.resolve().name.replace("-", " ").replace("_", " ").strip().title() or "Book"
    if not cfg.date:
        cfg.date = _dt.date.today().isoformat()
    return cfg
