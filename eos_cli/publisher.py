"""The event-driven publisher — one idempotent engine, many triggers.

Any engineering event fires the same cheap call: a git commit (post-commit hook),
an AI session ending in a commit, an explicit `factory publish`, or the optional
watcher. The digest persists in `.eos/state.json`, so a code-only commit costs a
hash comparison and sends nothing. Failures are explained, never raised — the
triggering event (a commit, a session) must never be blocked by publishing.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
from collections.abc import Callable
from pathlib import Path

from .client import PublishClientError, package_protocol, send
from .local import load_last_digest, save_last_digest
from .payload import Payload


def content_digest(payload: Payload) -> str:
    """Stable digest of the packaged protocol — the idempotence key."""
    canon = json.dumps(
        {"project": payload.project, "v": payload.engos_version, "files": payload.files},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class Publisher:
    """Package → digest-compare → send → remember. Safe to fire from any event."""

    def __init__(
        self,
        repo: Path,
        server: str,
        key: str,
        *,
        log: Callable[[str], None] = print,
        send_fn: Callable[[str, str, Payload], dict] = send,
    ) -> None:
        self._repo = Path(repo)
        self._server = server
        self._key = key
        self._log = log
        self._send = send_fn

    def publish_if_changed(self, payload: Payload | None = None) -> str:
        """Returns 'published' | 'unchanged' | 'error'. Never raises — the event
        that triggered us (a commit, a session end) must complete regardless.

        A caller that already packaged the protocol passes it in. `connect` does, because it
        needs the file count for its report, and walking the engineering layer twice is a
        cost paid at the exact moment a first-time user is watching.
        """
        try:
            payload = payload if payload is not None else package_protocol(self._repo)
        except PublishClientError as e:
            self._log(f"x cannot package: {e}")
            return "error"
        digest = content_digest(payload)
        if digest == load_last_digest(self._repo):
            self._log("- no engineering change, nothing to publish")
            return "unchanged"
        try:
            result = self._send(self._server, self._key, payload)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
            self._log(f"x publish rejected ({e.code}): {detail.strip() or e.reason}")
            return "error"
        except Exception as e:  # noqa: BLE001 — any transport failure, explained
            self._log(f"x could not reach {self._server}: {e} - will retry on the next event")
            return "error"
        save_last_digest(self._repo, digest)  # only after success — failures retry
        self._log(f"OK: published {len(payload.files)} files for '{payload.project}' "
                  f"- {result.get('message', 'ok')}")
        return "published"
