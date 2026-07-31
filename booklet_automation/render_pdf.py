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
    """Render a PNG of the first page. Kept for interactive/manual debugging
    only -- NOT used by the automated routine (see verify_rendering()),
    because visually inspecting it requires reading the image back with a
    vision-capable tool, which has been observed to hang indefinitely in the
    unattended cloud routine sandbox."""
    abs_path = os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page(viewport={"width": width_px, "height": height_px})
        page.goto(f"file://{abs_path}")
        page.screenshot(path=png_path)
        browser.close()


HANGUL_RANGES = ((0xAC00, 0xD7A3), (0x1100, 0x11FF), (0x3130, 0x318F))


def _hangul_count(text: str) -> int:
    return sum(1 for ch in text if any(lo <= ord(ch) <= hi for lo, hi in HANGUL_RANGES))


def verify_rendering(html_path: str, font_family: str, expected_snippets: list[str], min_hangul_chars: int = 20) -> dict:
    """Non-visual QA check to replace the old screenshot()+Read self-check.

    Loads the HTML in the same Playwright/Chromium used for the real render
    and checks, without ever looking at pixels:
      1. font_ok -- the browser actually resolved a font for the primary
         family named in `font_family` (catches the case where fc-list found
         a Korean font at the OS level but the CSS family name doesn't match
         what got installed, which fc-list alone can't catch).
      2. hangul_ok -- the rendered page's visible text contains at least
         `min_hangul_chars` Hangul characters (catches an empty/broken
         template rendering no CJK text at all).
      3. content_ok -- every string in `expected_snippets` (e.g. the class
         name, a chunk of the teacher letter, each student's name) shows up
         verbatim in the rendered text (catches escaping/truncation/mangling
         bugs that a font check alone would miss).

    Returns {"ok": bool, "font_ok": bool, "hangul_ok": bool, "content_ok": bool,
    "missing_snippets": [...], "hangul_count": int, "detail": str}.
    """
    abs_path = os.path.abspath(html_path)
    primary_font = font_family.split(",")[0].strip().strip("'\"")
    with sync_playwright() as p:
        browser = launch_browser(p)
        page = browser.new_page()
        page.goto(f"file://{abs_path}")
        page.evaluate("document.fonts.ready")
        font_ok = bool(page.evaluate(f"document.fonts.check(\"16px '{primary_font}'\")"))
        text = page.inner_text("body")
        browser.close()

    hangul_count = _hangul_count(text)
    hangul_ok = hangul_count >= min_hangul_chars
    missing = [s for s in expected_snippets if s and s not in text]
    content_ok = not missing

    ok = font_ok and hangul_ok and content_ok
    detail_parts = [
        f"font '{primary_font}' resolved" if font_ok else f"font '{primary_font}' NOT resolved by browser",
        f"{hangul_count} Hangul chars found" if hangul_ok else f"only {hangul_count} Hangul chars found (need {min_hangul_chars})",
        "all expected content present" if content_ok else f"missing snippets: {missing}",
    ]
    return {
        "ok": ok,
        "font_ok": font_ok,
        "hangul_ok": hangul_ok,
        "content_ok": content_ok,
        "missing_snippets": missing,
        "hangul_count": hangul_count,
        "detail": "; ".join(detail_parts),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_html")
    parser.add_argument("output_pdf")
    parser.add_argument("--width-mm", type=float, default=148)
    parser.add_argument("--height-mm", type=float, default=210)
    parser.add_argument("--screenshot", help="Optional PNG path to also render, for manual/interactive visual QA only")
    args = parser.parse_args()

    render(args.input_html, args.output_pdf, args.width_mm, args.height_mm)
    print(f"OK: wrote {args.output_pdf}")
    if args.screenshot:
        screenshot(args.input_html, args.screenshot)
        print(f"OK: wrote {args.screenshot}")
