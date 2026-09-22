# 1 What mdoutline does

mdoutline turns a folder of Markdown chapters into one print-quality PDF with a
cover, a clickable table of contents, page headers/footers, and -- its reason
to exist -- **exact PDF outline bookmarks**.

## 1.1 Why another Markdown-to-PDF tool

Chromium's print-to-PDF drops the document outline: the PDF has no bookmarks
panel. Most pipelines either ship without bookmarks or guess heading pages
back from font sizes, which breaks whenever pagination drifts.

mdoutline takes a third route. The table of contents it renders is made of
internal hyperlinks, and Chromium resolves every one of them to a concrete
page when printing. The bookmark step simply reads those link annotations
back out of the PDF -- the target page of each heading is already stored in
the file, so bookmark positions are exact by construction.

## 1.2 What you write

A directory of `*.md` files, ordered by filename:

    chapters/
      01-intro.md
      02-tables.md
      ...

plus an optional `book.toml` for the title, cover, headers and page setup.
Numeric headings like `# 1` / `## 1.1` keep stable ids (`sec-1`, `sec-1-1`);
any other heading gets a slug id. Duplicated ids are uniquified and warned
about on stderr.

## 1.3 What you get

One command, three stages, no way to forget the bookmark step:

    mdoutline make chapters -o book.pdf

`make` is atomic: it stitches the HTML, prints it, and writes the outline in a
single run, so a re-render can never leave you with a bookmark-less PDF.
