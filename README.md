# mdoutline

**Markdown chapters → one print-quality PDF with exact outline bookmarks.**

Point it at a folder of `*.md` chapter files. It stitches them into a styled
HTML document (cover, clickable table of contents, page headers/footers),
prints it to PDF with a Chromium engine, and writes the PDF outline so every
heading shows up in the bookmarks panel of your PDF viewer — at the right
page, by construction.

## Why this exists

Chromium's print-to-PDF drops the document outline: the resulting PDF has no
bookmarks. Existing workarounds guess heading pages back from font sizes,
which breaks as soon as pagination drifts.

mdoutline takes another route: the rendered table of contents consists of
internal hyperlinks, and Chromium resolves each link to a concrete page while
printing. The bookmark step reads those GoTo link annotations back out of the
PDF — the target page of every heading is already stored in the file, so
bookmark positions are exact and immune to font/pagination changes. Only
headings that never made it into the TOC fall back to a font-size heuristic.

The default theme is CJK-friendly out of the box (serif body, sans headings,
print-oriented tables and code blocks), and works equally well for plain
Latin documents.

## Install

Requires Python 3.10+.

```bash
pip install mdoutline            # from source: pip install -e .
playwright install chromium      # one-time browser download (~170 MB)
```

To use an existing Chrome/Chromium/Edge instead of the bundled browser:

```bash
export MDOUTLINE_BROWSER="/path/to/chrome"
```

## Quickstart

```bash
mdoutline make examples/demo -o demo.pdf
```

A "book" is a directory of chapters ordered by filename, plus an optional
`book.toml`:

```
mybook/
  book.toml
  chapters/
    01-intro.md
    02-methods.md
    03-results.md
```

Run `mdoutline make mybook/chapters -o mybook.pdf` (or from `mybook/`, simply
`mdoutline make chapters`). One command runs all three stages atomically:
re-rendering can never leave you with a bookmark-less PDF.

## Configuration (book.toml)

All keys live under `[book]`; every one is optional.

| Key | Default | Meaning |
|---|---|---|
| `title` | directory name | cover + page-header title |
| `subtitle` | — | cover subtitle, header right side |
| `authors` | — | cover meta table |
| `date` | today | cover meta table |
| `summary` | — | cover summary paragraph |
| `lang` | `"zh-CN"` | `<html lang>` of the document |
| `cover` | `true` | render a cover page |
| `toc_title` | `"Contents"` | TOC page title |
| `header_left` / `header_right` | `"{title}"` / `"{subtitle}"` | running header; supports `{title}`, `{subtitle}` |
| `footer_format` | `"{page} / {pages}"` | running footer; supports `{page}`, `{pages}` |
| `page_format` | `"A4"` | any Chromium page format (`A4`, `Letter`, ...) |
| `margin_top_mm` ... `margin_right_mm` | 18/16/16/16 | page margins in mm |
| `css` | — | extra CSS file appended after the theme |
| `browser_path` | — | Chromium executable (env `MDOUTLINE_BROWSER` wins) |
| `settle_ms` | `500` | wait after fonts load; raise if pagination looks unstable |

## Commands

```
mdoutline make SRC [-o OUT.pdf] [--config book.toml] [--keep-html]
    build + render + bookmarks in one atomic run

mdoutline build SRC [-o OUT.html] [--config book.toml]
    chapters -> styled HTML (cover, TOC, section ids)

mdoutline render IN.html [-o OUT.pdf] [--config book.toml]
    HTML -> PDF (no bookmarks written)

mdoutline bookmarks IN.pdf --html IN.html
    write outline bookmarks into an existing PDF
```

## How heading ids work

Numeric headings keep readable anchors: `# 7 Title` → `sec-7`, `## 7.9 Sub`
→ `sec-7-9`, so cross-links like `[see 7.9](#sec-7-9)` work. Any other
heading gets a slug id. If two headings would produce the same id (a repeated
section number, say), the second gets a `-2` suffix and a warning on stderr —
a duplicated number degrades to a nudge instead of silently hijacking both
TOC links.

## Dependencies and licensing

mdoutline itself is MIT-licensed and contains no third-party code. It has four
runtime dependencies, each pulled from PyPI at install time:

| Package | License | Role |
|---|---|---|
| markdown | BSD-3-Clause | Markdown -> HTML |
| pymdown-extensions | MIT | `~~deletion~~` markup |
| playwright | Apache-2.0 | drives the Chromium print engine |
| pymupdf | **AGPL-3.0** | reads TOC link annotations, writes the outline |

PyMuPDF is the one to be aware of: it is AGPL-3.0 (Artifex sells a commercial
license). Running mdoutline locally to build your own PDFs distributes nothing
and triggers no AGPL obligations. If you redistribute mdoutline **bundled with
its dependencies** (container image, frozen app), the AGPL terms apply to that
distribution as far as PyMuPDF is concerned, and network services built on such
a bundle fall under AGPL's source-disclosure clause. A permissively-licensed
PDF backend would remove this caveat entirely — contributions welcome.

## Development

```bash
pip install -e .
python tests/test_smoke.py    # end-to-end: builds the demo book, checks every bookmark lands
```

## License

[MIT](LICENSE)
