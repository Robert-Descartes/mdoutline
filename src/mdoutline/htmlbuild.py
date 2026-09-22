# -*- coding: utf-8 -*-
"""Stitch chapter markdown files into one styled HTML document.

Numeric headings keep readable ids ("# 7 ..." -> sec-7, "## 7.9 ..." -> sec-7-9);
any other heading gets a slug id. Duplicate ids are uniquified with a -2/-3
suffix and reported on stderr, so a duplicated section number degrades to a
warning instead of silently hijacking TOC links.
"""
from __future__ import annotations

import html as _html
import re
import sys
from pathlib import Path

import markdown

THEME_DIR = Path(__file__).parent / "theme"

_MD = markdown.Markdown(
    extensions=["tables", "fenced_code", "sane_lists", "pymdownx.tilde"],
    output_format="html5",
)

_num = re.compile(r"^\s*(\d+)(?:\.(\d+))?(?![\d.])")  # "7", "7.9" but not "7.9.1"
_tag = re.compile(r"<(h1|h2)>(.*?)</\1>", re.DOTALL)
_inline = re.compile(r"<[^>]+>")


def slugify(title: str) -> str:
    """ascii alnum + CJK kept, everything else collapsed to single '-'."""
    s = title.strip().lower()
    out, prev_dash = [], False
    for ch in s:
        if ch.isalnum() and (ch.isascii() or ord(ch) > 0x2E7F):
            out.append(ch)
            prev_dash = False
        elif not prev_dash:
            out.append("-")
            prev_dash = True
    return "".join(out).strip("-") or "h"


def strip_inline(text: str) -> str:
    """Plain text of a rendered heading (drop <code> etc. tags)."""
    return _inline.sub("", text).strip()


class _IdGen:
    def __init__(self) -> None:
        self.used: set[str] = set()

    def __call__(self, title: str, warn_where: str) -> str:
        m = _num.match(title)
        hid = f"sec-{m.group(1)}" + (f"-{m.group(2)}" if m.group(2) else "") if m else slugify(title)
        if hid in self.used:
            print(f"mdoutline: warning: duplicate heading id '{hid}' ({warn_where}: {title!r}); "
                  f"appending suffix", file=sys.stderr)
            n = 2
            while f"{hid}-{n}" in self.used:
                n += 1
            hid = f"{hid}-{n}"
        self.used.add(hid)
        return hid


def render_chapters(src: Path):
    """[(h1_title, h1_id, [(h2_title, h2_id)], body_html)] in filename order.

    src is a directory of *.md chapters or a single markdown file; in the
    latter case every h1 in the file acts as one chapter.
    """
    files = [src] if src.is_file() else sorted(src.glob("*.md"))
    if not files:
        raise SystemExit(f"no .md chapters found in {src}")
    ids = _IdGen()
    chapters = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        _MD.reset()
        body = _MD.convert(text)

        def add_ids(m: re.Match) -> str:
            tag, inner = m.group(1), m.group(2)
            hid = ids(strip_inline(inner), path.name)
            return f'<{tag} id="{hid}">{inner}</{tag}>'

        body = _tag.sub(add_ids, body)

        h1m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.DOTALL)
        title = strip_inline(h1m.group(1)) if h1m else path.stem
        cid = re.search(r'<h1[^>]*id="([^"]+)"', body).group(1) if h1m else ""
        subs = [
            (strip_inline(m.group(2)), m.group(1))
            for m in re.finditer(r'<h2[^>]*id="([^"]+)">(.*?)</h2>', body, re.DOTALL)
        ]
        chapters.append((title, cid, subs, body))
    return chapters


def _toc_html(chapters, toc_title: str) -> str:
    parts = [f'<nav id="toc"><h1 class="toc-title">{_html.escape(toc_title)}</h1><ol class="toc-chapters">']
    for title, cid, subs, _ in chapters:
        parts.append(f'<li><a href="#{cid}">{_html.escape(title)}</a>')
        if subs:
            parts.append('<ul class="toc-sub">')
            for text, sid in subs:
                parts.append(f'<li><a href="#{sid}">{_html.escape(text)}</a></li>')
            parts.append("</ul>")
        parts.append("</li>")
    parts.append("</ol></nav>")
    return "\n".join(parts)


def _cover_html(cfg) -> str:
    if not cfg.cover:
        return ""
    meta_rows = ""
    for label, value in (("Authors", cfg.authors), ("Date", cfg.date)):
        if value:
            meta_rows += (
                f"<tr><td><strong>{_html.escape(label)}</strong></td>"
                f"<td>{_html.escape(value)}</td></tr>"
            )
    summary = f'<div class="cover-summary">{_html.escape(cfg.summary)}</div>' if cfg.summary else ""
    return f"""<section class="cover">
  <div class="cover-band">
    <h1>{_html.escape(cfg.title)}</h1>
    {f'<div class="sub">{_html.escape(cfg.subtitle)}</div>' if cfg.subtitle else ''}
  </div>
  {summary}
  <div class="cover-meta"><table>{meta_rows}</table></div>
  <div class="cover-foot">{_html.escape(cfg.title)}</div>
</section>"""


def build_html(src: Path, out: Path, cfg) -> Path:
    chapters = render_chapters(src)
    css = (THEME_DIR / "default.css").read_text(encoding="utf-8")
    if cfg.css:
        css += "\n/* ---- user css ---- */\n" + Path(cfg.css).read_text(encoding="utf-8")
    doc = f"""<!DOCTYPE html>
<html lang="{_html.escape(cfg.lang)}">
<head>
<meta charset="utf-8">
<title>{_html.escape(cfg.title)}</title>
<style>{css}</style>
</head>
<body>
{_cover_html(cfg)}
{_toc_html(chapters, cfg.toc_title)}
{chr(10).join(f'<section class="chapter">{body}</section>' for _, _, _, body in chapters)}
</body>
</html>
"""
    out.write_text(doc, encoding="utf-8")
    return out


def headings_from_html(html_path: Path):
    """[(level, plain_title)] for h1/h2 in document order -- input for bookmarks."""
    text = html_path.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"<(h1|h2)[^>]*id=[\"']([^\"']+)[\"'][^>]*>(.*?)</\1>", text, re.DOTALL):
        out.append((1 if m.group(1) == "h1" else 2, _html.unescape(strip_inline(m.group(3)))))
    return out
