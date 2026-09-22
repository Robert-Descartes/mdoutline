# 4 Stressing the outline

This chapter exists to give the bookmark machinery more entries to land and to
exercise duplicate-id handling.

## 4.1 Many small sections

Each `##` here becomes one outline level-2 entry; all of them must land on the
correct page after printing.

## 4.2 Another section

With short chapters several sections share a page -- exact targeting still
matters, and the TOC-link method delivers it.

## 4.3 A note on duplicate numbers

If a book accidentally repeats a section number, mdoutline keeps both TOC
entries working (the second id gets a suffix) and prints a warning on stderr
instead of silently pointing both links at the first heading.

## 4.4 End

That's the demo book. Toss `examples/demo/chapters` and write your own.
