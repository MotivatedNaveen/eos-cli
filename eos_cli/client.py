"""Client-side publish: package this repo's `.engos` protocol and send it.

Stdlib plus PyYAML — the manifest is YAML and writing a YAML parser to avoid one
dependency would be trading a packaging problem for a correctness one.
"""

from __future__ import annotations

import json
import unicodedata
import urllib.request
from pathlib import Path

import yaml

from .payload import Payload

_ENGINEERING_DIRS = (".engos", "docs", "discovery")


class PublishClientError(RuntimeError):
    pass


def package_protocol(repo_root: Path) -> Payload:
    """Read the engineering layer (.engos/ + docs/ + discovery/) into a publish payload. Not code."""
    root = Path(repo_root)
    manifest = root / ".engos" / "manifest.yaml"
    if not manifest.is_file():
        raise PublishClientError(
            "Not an EOS-native repo (.engos/manifest.yaml missing). Run `install` first.")
    data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
    project = data.get("project")
    engos_version = str(data.get("engos_version", ""))
    if not project:
        raise PublishClientError("Manifest has no `project`.")

    files: dict[str, str] = {}
    skipped: list[str] = []
    for d in _ENGINEERING_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.name != ".gitkeep":
                try:
                    content = p.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    # The protocol is text (markdown + YAML). A stray binary or unreadable
                    # file is skipped — one bad file must never block the whole publish —
                    # but it is reported, not dropped in silence (publish-protocol §5).
                    skipped.append(p.relative_to(root).as_posix())
                    continue
                # Path normalization (publish-protocol §6.2). NFC because macOS stores
                # filenames decomposed: without this the same file publishes under two
                # different keys depending on which platform published it.
                rel = unicodedata.normalize("NFC", p.relative_to(root).as_posix())
                # Content normalization (§6.1). `read_text` already translated CRLF to LF via
                # universal newlines; the BOM is stripped here so a Windows-authored file and
                # a Linux-authored one produce identical content for the same commit.
                files[rel] = content.lstrip("﻿") if content.startswith("﻿") else content
    return Payload(project=project, engos_version=engos_version, files=files,
                   skipped=tuple(sorted(skipped)))


def send(server: str, key: str, payload: Payload) -> dict:
    """POST the protocol to <server>/api/publish. Raises urllib.error.HTTPError on rejection."""
    url = server.rstrip("/") + "/api/publish"
    body = json.dumps(payload.wire()).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "X-Publish-Key": key},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (server URL is user-supplied)
        return json.loads(resp.read().decode("utf-8"))
