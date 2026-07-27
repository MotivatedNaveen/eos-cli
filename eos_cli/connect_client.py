"""The client half of onboarding: ask the server who this key belongs to (ADR-0019).

Stdlib only, like the rest of the publisher — a client that needs dependencies is a client
that needs a package manager, which is the problem we are removing.

The one piece of real defensive code here is `safe_paths`. The server is trusted enough to
hold your engineering memory, but a response is still a response: a template that named
`../../.ssh/authorized_keys` would otherwise be written wherever the CLI was run. Validating
paths is not distrust of the server, it is refusing to make a trust decision at all.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

CONNECT_TIMEOUT = 20

# Where a template may write. Anything else is refused, whatever the server says.
ALLOWED_ROOTS = (".engos/", "docs/", "discovery/")
ALLOWED_FILES = ("CLAUDE.md",)


class ConnectError(RuntimeError):
    """Something went wrong reaching or trusting the server. The message is shown to a
    human mid-setup, so it says what happened and what to do next."""


@dataclass(frozen=True)
class ProjectContext:
    organization_slug: str
    organization_name: str
    project_slug: str
    protocol_version: str
    standard_version: str


def _get(server: str, path: str, key: str) -> dict:
    url = server.rstrip("/") + path
    req = urllib.request.Request(url, headers={"X-Publish-Key": key}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise ConnectError(
                "EOS rejected that connection token. It may have been revoked or replaced - "
                "ask for a new one."
            ) from e
        if e.code == 429:
            raise ConnectError("Too many attempts. Wait a moment and try again.") from e
        raise ConnectError(f"EOS refused the request ({e.code}). Try again shortly.") from e
    except urllib.error.URLError as e:
        raise ConnectError(
            f"Could not reach EOS at {server} - {e.reason}. Check the connection and retry; "
            "nothing has been changed in this repository."
        ) from e
    except (ValueError, TimeoutError) as e:
        raise ConnectError(f"EOS returned an unreadable response: {e}") from e


def fetch_context(server: str, key: str) -> ProjectContext:
    data = _get(server, "/api/connect/context", key)
    try:
        return ProjectContext(
            organization_slug=data["organization"]["slug"],
            organization_name=data["organization"]["name"],
            project_slug=data["project"]["slug"],
            protocol_version=str(data.get("protocol_version", "")),
            standard_version=str(data.get("standard_version", "")),
        )
    except (KeyError, TypeError) as e:
        raise ConnectError("EOS returned an unexpected response. Update the CLI.") from e


def fetch_template(server: str, key: str) -> tuple[dict[str, str], str]:
    """(files, standard_version) with every path validated before the caller writes anything."""
    data = _get(server, "/api/connect/template", key)
    files = data.get("files")
    if not isinstance(files, dict):
        raise ConnectError("EOS returned an unexpected template. Update the CLI.")
    return safe_paths(files), str(data.get("standard_version", ""))


def safe_paths(files: dict) -> dict[str, str]:
    """Keep only paths this client is willing to write. Refuses absolute paths, traversal,
    drive letters, and anything outside the engineering layer."""
    clean: dict[str, str] = {}
    for path, content in files.items():
        if not isinstance(path, str) or not isinstance(content, str):
            raise ConnectError("EOS returned a malformed template entry.")
        norm = path.replace("\\", "/").strip()
        if (
            not norm
            or norm.startswith("/")
            or ".." in norm.split("/")
            or ":" in norm
            or not (norm.startswith(ALLOWED_ROOTS) or norm in ALLOWED_FILES)
        ):
            raise ConnectError(
                f"EOS returned a template path this CLI will not write: {path!r}. "
                "Nothing has been changed in this repository."
            )
        clean[norm] = content
    return clean
