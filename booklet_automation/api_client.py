#!/usr/bin/env python3
"""Minimal stdlib-only client for the class-story booklet automation API.

No third-party deps (no `requests`) so it runs in a bare Python environment
with nothing pre-installed beyond the standard library.
"""
import json
import mimetypes
import urllib.error
import urllib.request
import uuid

BASE_URL = "https://class-story.higgsfield.app"


def fetch_requests(secret: str) -> dict:
    req = urllib.request.Request(
        f"{BASE_URL}/api/automation/booklets",
        headers={"Authorization": f"Bearer {secret}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def upload_pdf(secret: str, request_id: str, stage: str, pdf_path: str, manifest_json: str | None = None) -> dict:
    """stage must be 'draft' or 'final'. `manifest_json` (a JSON string) is only
    meaningful for stage='draft' -- it's persisted so a later run (for the
    'final' stage, with zero memory of this one) can reuse the exact
    manifest the owner reviewed and approved, instead of re-writing it."""
    boundary = uuid.uuid4().hex
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    def text_field(name: str, value: str) -> bytes:
        return (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'
        ).encode("utf-8")

    parts = [
        text_field("requestId", request_id),
        text_field("stage", stage),
    ]
    if manifest_json is not None:
        parts.append(text_field("manifest", manifest_json))
    parts.append(
        (
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="output.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8")
        + pdf_bytes
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(parts)

    req = urllib.request.Request(
        f"{BASE_URL}/api/automation/booklets",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upload_pdf failed: HTTP {e.code}: {body_text}") from e


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: api_client.py <secret> [upload <requestId> <draft|final> <pdf_path>]")
        sys.exit(1)
    secret = sys.argv[1]
    if len(sys.argv) == 2:
        print(json.dumps(fetch_requests(secret), ensure_ascii=False, indent=2))
    elif sys.argv[2] == "upload":
        _, _, request_id, stage, pdf_path = sys.argv[1:6]
        print(json.dumps(upload_pdf(secret, request_id, stage, pdf_path), ensure_ascii=False))
