# 2 Tables, code and marks

## 2.1 Tables

Tables get zebra-free print styling, repeat their header on page breaks, and
never split a row across pages:

| Stage | Command | Output |
|---|---|---|
| stitch | `mdoutline build chapters` | `chapters.html` |
| print | `mdoutline render chapters.html` | `chapters.pdf` |
| outline | `mdoutline bookmarks chapters.pdf --html chapters.html` | bookmarks written in place |

Escape a literal pipe inside a cell as `\|`, especially for absolute-value
notation like `\|x\| < 360` -- an unescaped pipe silently splits the cell.

## 2.2 Code blocks

Fenced code blocks keep their line breaks and never split across pages:

```text
$ mdoutline make examples/demo -o demo.pdf
mdoutline: 9 bookmarks (9 exact from TOC links) -> demo.pdf
```

## 2.3 Deletion marks

~~Wrong statements~~ can be struck through with `~~double tildes~~` and render
in a muted color.

## 2.4 Cross-links

Sections link to each other, e.g. [1.1](#sec-1-1) explains the bookmark trick
and [3.1](#sec-3-1) shows CJK typesetting. In the PDF these are clickable.
