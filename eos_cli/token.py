"""The connection token — one paste, everything needed to connect (ADR-0019 §1).

    eostk_<base64url( {"v":1,"s":"https://eos.example","k":"eospk_…"} )>

A token is an *invitation to a specific project on a specific server*. Carrying the
destination is what lets the CLI stop asking for a server URL without pretending there is only
one EOS deployment. Every deployment is self-hosted by someone, so the single-server premise
was never true and compiling a URL in would mean one binary per deployment.

The token holds no lifecycle of its own. It wraps a publish key that already has `expires_at`,
`revoked_at` and an audit trail; revoking the key invalidates every token carrying it. A second
expiry would be a second thing to reason about and a second thing to get wrong.

Bare `eospk_…` keys are still accepted and fall back to the default server, so every existing
connection keeps working.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass

TOKEN_PREFIX = "eostk_"
KEY_PREFIX = "eospk_"
TOKEN_VERSION = 1


class TokenError(ValueError):
    """The pasted value is not a usable connection token. The message is shown to a human
    who just pasted something, so it says what to do, not what failed internally."""


@dataclass(frozen=True)
class Connection:
    server: str
    key: str
    version: int = TOKEN_VERSION


def _b64url_decode(raw: str) -> bytes:
    # Padding is stripped on encode so the token survives URLs and shell quoting; restore it.
    return base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))


def encode(server: str, key: str) -> str:
    """Build a token. The server mints these; the CLI only ever decodes."""
    payload = json.dumps(
        {"v": TOKEN_VERSION, "s": server.rstrip("/"), "k": key},
        separators=(",", ":"), sort_keys=True,
    ).encode("utf-8")
    return TOKEN_PREFIX + base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def decode(pasted: str, *, default_server: str = "") -> Connection:
    """Turn what the user pasted into a destination and a credential.

    Accepts a full token, or a bare publish key when a default server is configured — an
    older key pasted into a newer CLI should connect, not lecture.
    """
    value = (pasted or "").strip()
    if not value:
        raise TokenError("No connection token was entered.")

    if value.startswith(KEY_PREFIX):
        if not default_server:
            raise TokenError(
                "That looks like a publish key rather than a connection token, and this CLI "
                "has no default server. Paste the connection token from EOS, or pass --server."
            )
        return Connection(server=default_server.rstrip("/"), key=value)

    if not value.startswith(TOKEN_PREFIX):
        raise TokenError(
            f"That does not look like an EOS connection token (expected it to start with "
            f"'{TOKEN_PREFIX}'). Copy the whole token from EOS and paste it again."
        )

    try:
        data = json.loads(_b64url_decode(value[len(TOKEN_PREFIX):]))
    except Exception as e:  # noqa: BLE001 — every decode failure is the same user-facing problem
        raise TokenError(
            "That connection token is damaged - it may have been truncated when copied. "
            "Copy the whole token and paste it again."
        ) from e

    if not isinstance(data, dict):
        raise TokenError("That connection token is damaged. Copy the whole token and retry.")

    version = data.get("v")
    if version != TOKEN_VERSION:
        # Forward compatibility is the point of carrying a version: a newer token in an older
        # CLI must say "upgrade", not fail with a decode error.
        raise TokenError(
            f"This connection token is version {version}, which this CLI does not understand. "
            "Update the EOS CLI and try again."
        )

    server, key = data.get("s"), data.get("k")
    if not isinstance(server, str) or not isinstance(key, str) or not server or not key:
        raise TokenError("That connection token is incomplete. Copy the whole token and retry.")
    if not server.startswith(("https://", "http://")):
        raise TokenError("That connection token names an invalid server address.")
    if server.startswith("http://") and not _is_local(server):
        # Plain http would send the publish key in clear. Allowed only against a local
        # deployment, where there is no network to intercept.
        raise TokenError(
            "That token points at an insecure (http) server. EOS refuses to send a publish "
            "key over plain http except to localhost."
        )
    return Connection(server=server.rstrip("/"), key=key, version=version)


def _is_local(server: str) -> bool:
    host = server.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
    return host in {"localhost", "127.0.0.1", "::1", "[::1]"}


def redact(token: str) -> str:
    """A token safe to print in logs or errors — enough to identify, not enough to use."""
    value = (token or "").strip()
    return f"{value[:12]}..." if len(value) > 12 else "..."


# --- the connection file ------------------------------------------------------
#
# The same project-scoped credential, in the form a human downloads. Not a second credential
# type: the compact token above is for CI and environment variables, this is for people, and
# both carry one key whose hash is all the server keeps.
#
# It additionally carries `project` and `display_name`, which is what makes the protocol's
# identity rule (publish-protocol §4) hold by construction: the CLI seeds the manifest from
# here, so `manifest.project` and the platform's identifier cannot disagree.

DESCRIPTOR_VERSION = 1
DESCRIPTOR_FILENAME = "eos-project.json"


@dataclass(frozen=True)
class ProjectConnection:
    server: str
    project: str
    key: str
    display_name: str = ""
    version: int = DESCRIPTOR_VERSION


def descriptor(server: str, project: str, key: str, display_name: str = "") -> dict:
    """Build the downloadable connection file. The server mints these; the CLI reads them."""
    return {
        "version": DESCRIPTOR_VERSION,
        "server": server.rstrip("/"),
        "project": project,
        "display_name": display_name or project,
        "publish_key": key,
    }


def from_descriptor(data: object) -> ProjectConnection:
    """Validate a connection file. Every failure message is written for a person who has just
    downloaded a file and is halfway through setting up."""
    if not isinstance(data, dict):
        raise TokenError("That connection file is not valid JSON.")

    version = data.get("version")
    if version != DESCRIPTOR_VERSION:
        raise TokenError(
            f"This connection file is version {version}, which this CLI does not understand. "
            "Update the EOS CLI and try again."
        )

    server = data.get("server")
    project = data.get("project")
    key = data.get("publish_key")
    if not all(isinstance(v, str) and v for v in (server, project, key)):
        raise TokenError("That connection file is incomplete. Download a new one from EOS.")
    if not server.startswith(("https://", "http://")):
        raise TokenError("That connection file names an invalid server address.")
    if server.startswith("http://") and not _is_local(server):
        raise TokenError(
            "That connection file points at an insecure (http) server. EOS refuses to send a "
            "publish key over plain http except to localhost."
        )

    display = data.get("display_name")
    return ProjectConnection(
        server=server.rstrip("/"), project=project, key=key,
        display_name=display if isinstance(display, str) and display else project,
    )
