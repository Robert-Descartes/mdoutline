# -*- coding: utf-8 -*-
"""Render the stitched HTML to PDF via playwright-driven Chromium."""
from __future__ import annotations

import os
from pathlib import Path


def _browser_executable(cfg) -> str | None:
    env = os.environ.get("MDOUTLINE_BROWSER")
    return env or (cfg.browser_path or None)


def render_pdf(html_path: Path, pdf_path: Path, cfg) -> Path:
    from playwright.sync_api import sync_playwright

    header, footer = cfg.header_footer_templates()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=_browser_executable(cfg),
            args=["--no-sandbox", "--disable-gpu", "--font-render-hinting=none"],
        )
        try:
            page = browser.new_page()
            page.goto(html_path.resolve().as_uri())
            # Let fonts and layout settle so pagination is reproducible.
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(cfg.settle_ms)
            page.pdf(
                path=str(pdf_path),
                format=cfg.page_format,
                print_background=True,
                display_header_footer=True,
                header_template=header,
                footer_template=footer,
                margin=cfg.margins(),
            )
        finally:
            browser.close()
    return pdf_path
