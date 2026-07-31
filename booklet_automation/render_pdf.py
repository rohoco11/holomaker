#!/usr/bin/env python3
"""Render an HTML file to a PDF using Playwright.

Usage:
    python3 render_pdf.py <input.html> <output.pdf> [--width-mm 148] [--height-mm 210]

Falls back to a pre-installed Chromium at /opt/pw-browsers/chromium when
Playwright's own browser auto-download is blocked by outbound network
policy (confirmed in the Higgsfield cloud routine sandbox: the default
`playwright install chromium` download to cdn.playwright.dev is rejected
by the sandbox's proxy, but a Chromium build is already present on disk).
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

FALLBACK_CHROMIUM = "/opt/pw-browsers/chromium"


def launch_browser(p):
    try:
        return p.chromium.launch(headless=True)
    except Exception:
        if os.path.exists(FALLBACK_CHROMIUM):
            return p.chromium.launch(headless=True, executable_path=FALLBACK_CHROMIUM)
        raise


def render(html_path: str, pdf_path: str, width_mm: float, height_mm: float) -> None:
    abs_path = os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        page.goto(f"file://{abs_path}")
        page.pdf(
            path=pdf_path,
            width=f"{width_mm}mm",
            height=f"{height_mm}mm",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"},
        )
        browser.close()


def screenshot(html_path: str, png_path: str, width_px: int = 900, height_px: int = 1273) -> None:
    """Render a PNG of the first page, used to visually sanity-check text
    rendering (e.g. Korean glyphs not showing as tofu boxes) before trusting
    a full batch run."""
    abs_path = os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": width_px, "height": height_px})
        page.goto(f"file://{abs_path}")
        page.screenshot(path=png_path)
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_html")
    parser.add_argument("output_pdf")
    parser.add_argument("--width-mm", type=float, default=148)
    parser.add_argument("--height-mm", type=float, default=210)
    parser.add_argument("--screenshot", help="Optional PNG path to also render for visual QA")
    args = parser.parse_args()

    render(args.input_html, args.output_pdf, args.width_mm, args.height_mm)
    print(f"OK: wrote {args.output_pdf}")
    if args.screenshot:
        screenshot(args.input_html, args.screenshot)
        print(f"OK: wrote {args.screenshot}")
