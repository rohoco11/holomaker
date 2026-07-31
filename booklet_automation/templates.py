#!/usr/bin/env python3
"""Builds the HTML for a class-story booklet (draft or final stage).

This is deliberately a single adaptable design (four color/typography
presets keyed off the teacher's chosen booklet_style) rather than four
fully bespoke hand-art-directed themes -- a good-enough v1 for unattended
generation. It intentionally does NOT try to replicate the full
hand-crafted visual richness of the interactive booklet-restyler skill
(which hand-writes a unique image prompt and pull-quote per student and
iterates on layout conversationally); revisit with real output in hand.

manifest shape (a plain dict, JSON-serializable):
{
  "school_name": str,
  "class_name": str,
  "teacher_letter": str,
  "booklet_style": str,          # one of BOOKLET_STYLE presets, or custom text
  "font_family": str,            # CSS font-family value, discovered at runtime
  "students": [
    {"name": str, "gender": str|None, "story": str, "image_path": str|None}
  ],
}
"""
import html

PAGE_WIDTH_MM = 148
PAGE_HEIGHT_MM = 210

PRESET_MAGAZINE = "매거진"
PRESET_NEWSPAPER = "신문"
PRESET_RETRO_FB = "레트로 페이스북"
PRESET_COMIC = "만화"


def _theme_for(booklet_style: str) -> dict:
    style = booklet_style or ""
    if PRESET_NEWSPAPER in style:
        return {
            "bg": "#f5f3ee",
            "ink": "#1a1a1a",
            "accent": "#8a1f1f",
            "headline_font": "Georgia, 'Nanum Myeongjo', serif",
            "rule": "2px solid #1a1a1a",
        }
    if PRESET_RETRO_FB in style:
        return {
            "bg": "#eef2f7",
            "ink": "#1c2b3a",
            "accent": "#3b5998",
            "headline_font": "'Trebuchet MS', sans-serif",
            "rule": "1px solid #c8d3e0",
        }
    if PRESET_COMIC in style:
        return {
            "bg": "#fff7e0",
            "ink": "#20140a",
            "accent": "#e0562f",
            "headline_font": "'Comic Sans MS', 'Nanum Pen Script', sans-serif",
            "rule": "3px solid #20140a",
        }
    # Default / magazine / unrecognized custom description.
    return {
        "bg": "#faf6ef",
        "ink": "#241f1a",
        "accent": "#b8862f",
        "headline_font": "Georgia, serif",
        "rule": "1px solid #d8cdb8",
    }


def _page_css(font_family: str, theme: dict) -> str:
    return f"""
    @page {{ size: {PAGE_WIDTH_MM}mm {PAGE_HEIGHT_MM}mm; margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: {font_family}; color: {theme['ink']}; }}
    .page {{
      width: {PAGE_WIDTH_MM}mm; height: {PAGE_HEIGHT_MM}mm;
      background: {theme['bg']}; padding: 14mm 12mm;
      page-break-after: always; break-after: page;
      display: flex; flex-direction: column;
      overflow: hidden;
    }}
    .page:last-child {{ page-break-after: auto; break-after: auto; }}
    h1.cover-title {{ font-family: {theme['headline_font']}; font-size: 26pt; margin: auto 0 4mm 0; }}
    h2.class-name {{ font-family: {theme['headline_font']}; font-size: 15pt; color: {theme['accent']}; margin: 0; }}
    .rule {{ border: none; border-top: {theme['rule']}; margin: 6mm 0; }}
    .letter-body {{ font-size: 11pt; line-height: 1.9; white-space: pre-wrap; }}
    .student-name {{ font-family: {theme['headline_font']}; font-size: 18pt; color: {theme['accent']}; margin: 0 0 6mm 0; }}
    .student-story {{ font-size: 10.5pt; line-height: 1.85; white-space: pre-wrap; }}
    .photo-slot {{
      margin-top: auto; width: 100%; height: 70mm;
      border: 2px dashed {theme['accent']}; border-radius: 4mm;
      display: flex; align-items: center; justify-content: center;
      color: {theme['accent']}; font-size: 10pt;
    }}
    .photo-slot img {{ width: 100%; height: 100%; object-fit: cover; border-radius: 4mm; border: none; }}
    .closing {{ margin: auto; text-align: center; font-family: {theme['headline_font']}; font-size: 16pt; }}
    """


def _esc(text: str) -> str:
    return html.escape(text or "")


def _cover_page(manifest: dict, theme: dict) -> str:
    return f"""
    <div class="page">
      <div>
        <h2 class="class-name">{_esc(manifest.get('school_name', ''))}</h2>
        <h1 class="cover-title">{_esc(manifest.get('class_name', ''))}</h1>
      </div>
    </div>
    """


def _letter_page(manifest: dict, theme: dict) -> str:
    letter = manifest.get("teacher_letter") or "아직 편지를 작성하지 않았어요."
    return f"""
    <div class="page">
      <h2 class="class-name">선생님의 편지</h2>
      <hr class="rule" />
      <div class="letter-body">{_esc(letter)}</div>
    </div>
    """


def _student_pages(student: dict, theme: dict, include_image: bool) -> str:
    name = _esc(student.get("name", ""))
    story = _esc(student.get("story", ""))
    image_path = student.get("image_path") if include_image else None
    if image_path:
        slot = f'<div class="photo-slot"><img src="file://{image_path}" /></div>'
    else:
        slot = '<div class="photo-slot">사진 자리</div>'
    return f"""
    <div class="page">
      <h2 class="student-name">{name}</h2>
      <div class="student-story">{story}</div>
    </div>
    <div class="page">
      {slot}
    </div>
    """


def _closing_page(manifest: dict, theme: dict) -> str:
    return f"""
    <div class="page">
      <div class="closing">{_esc(manifest.get('class_name', ''))}, 안녕.<br/>모두 반짝반짝 빛나는 미래를 향해.</div>
    </div>
    """


def _build(manifest: dict, include_images: bool) -> str:
    theme = _theme_for(manifest.get("booklet_style", ""))
    font_family = manifest.get("font_family") or "'Noto Sans KR', 'Malgun Gothic', sans-serif"
    css = _page_css(font_family, theme)
    body_parts = [_cover_page(manifest, theme), _letter_page(manifest, theme)]
    for student in manifest.get("students", []):
        body_parts.append(_student_pages(student, theme, include_images))
    body_parts.append(_closing_page(manifest, theme))
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8" /><style>{css}</style></head>
<body>{''.join(body_parts)}</body></html>"""


def build_draft_html(manifest: dict) -> str:
    """Story pages only, no images -- the owner-review artifact."""
    return _build(manifest, include_images=False)


def build_final_html(manifest: dict) -> str:
    """Full themed pages with each student's generated image."""
    return _build(manifest, include_images=True)


if __name__ == "__main__":
    import json
    import sys

    manifest = json.load(open(sys.argv[1], "r", encoding="utf-8"))
    out_html = sys.argv[2]
    stage = sys.argv[3] if len(sys.argv) > 3 else "draft"
    html_out = build_final_html(manifest) if stage == "final" else build_draft_html(manifest)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"OK: wrote {out_html}")
