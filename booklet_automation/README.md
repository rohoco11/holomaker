# Booklet automation pipeline scripts

Helper scripts for the class-story hourly cloud routine. Not used
interactively -- these exist so the routine doesn't have to reconstruct
Playwright/font/API boilerplate from scratch every run.

## Files

- `api_client.py` -- stdlib-only HTTP client for
  `https://class-story.higgsfield.app/api/automation/booklets`.
  - `fetch_requests(secret) -> dict` -- GET the work queue (pending +
    approved booklet_requests, each with full class + submissions data).
  - `upload_pdf(secret, request_id, stage, pdf_path) -> dict` -- POST a
    finished PDF. `stage` is `"draft"` (moves request to
    `awaiting_review`) or `"final"` (moves it to `done`).
  - The bearer secret itself is NOT stored here -- fetch it at runtime via
    the Higgsfield `website_secrets` MCP tool
    (`website_id=447af952-36ce-426b-8e55-9f5a85a6db39`,
    `operation=list`, key `BOOKLET_AUTOMATION_SECRET`).

- `templates.py` -- turns a manifest dict into a full HTML document (one
  A5 page per `<div class="page">`, `page-break-after` between them).
  - `build_draft_html(manifest)` -- story pages only, no images. Used for
    the owner-review draft.
  - `build_final_html(manifest)` -- same structure, with each student's
    generated image dropped into their photo slot. Used for the final PDF
    after owner approval.
  - Four built-in color/typography presets keyed off `booklet_style`
    matching one of the site's preset labels (매거진/신문/레트로
    페이스북/만화); anything else (custom teacher description) falls back
    to the magazine preset. This is a deliberately simple v1 -- not a
    replacement for hand-art-directed themes.

- `render_pdf.py` -- Playwright HTML-to-PDF, CLI or importable
  (`render(html_path, pdf_path, width_mm, height_mm)`). Falls back to the
  pre-installed Chromium at `/opt/pw-browsers/chromium` if Playwright's
  own browser download is blocked (confirmed blocked in this sandbox --
  `cdn.playwright.dev` is not on the outbound allowlist).
  - `verify_rendering(html_path, font_family, expected_snippets)` -- the
    automated QA check the routine actually uses. Loads the HTML in
    Playwright and checks, without looking at any pixels: (1) the browser
    resolved a real font for the primary family in `font_family` (via
    `document.fonts.check(...)`), (2) the rendered body text contains a
    reasonable number of Hangul characters, (3) every string in
    `expected_snippets` (e.g. class name, a chunk of the teacher letter,
    each student's name) appears verbatim in the rendered text. Returns a
    dict with an overall `ok` bool plus per-check detail -- see the
    docstring for the full shape.
  - `screenshot(html_path, png_path)` -- renders a PNG of the first page.
    Kept only for interactive/manual debugging (a human opening the PNG
    themselves). **Do not use this in the unattended routine and do not
    `Read` the PNG from the routine's own reasoning** -- doing so was
    observed to hang the routine indefinitely (15+ minutes, no further
    tool calls, no error) on 2026-07-31, reproduced on a second manual
    trigger of the same run. Use `verify_rendering()` instead, which
    covers the same "did Korean actually render, not tofu boxes" concern
    without ever needing a vision read-back.

## Manifest shape

```json
{
  "school_name": "부산초등학교",
  "class_name": "6학년 2반",
  "teacher_letter": "...",
  "booklet_style": "매거진 (잡지 스타일)",
  "font_family": "'Noto Sans KR', sans-serif",
  "students": [
    {"name": "김하은", "gender": "여자", "story": "...", "image_path": "/abs/path/to/generated.png"}
  ]
}
```

`font_family` should be discovered at runtime, not hardcoded: run
`fc-list :lang=ko` first; if nothing Korean is installed, install one
(`apt-get install -y fonts-noto-cjk`, sandbox permitting) before rendering
anything real, and confirm with `render_pdf.verify_rendering()` before
trusting a batch. `image_path` is only needed for `build_final_html` --
omit or leave `None` for the draft stage.

## Not included here (by design)

Writing the actual story text per student, writing each student's image
prompt, and picking/adjusting the theme are creative judgment calls made
by the routine's own reasoning each run (see the routine's own prompt) --
they are not scripted here, since that's exactly the part that most needs
a model's judgment rather than a fixed template.
