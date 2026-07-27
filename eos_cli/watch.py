"""Watch mode — the OPTIONAL fallback publisher, not the primary experience.

The primary experience is event-driven (`factory connect` + the post-commit hook +
explicit `factory publish`): publishing rides real engineering events, and nobody
keeps a terminal running. The watcher remains for the cases events can't cover —
live demos, uncommitted work-in-progress dashboards, non-git workflows.

Design: stdlib-only polling (no filesystem-watcher dependency) and a settle window
so a burst of edits becomes one publish. The actual publishing is the shared
event-driven `Publisher` — same digest idempotence, same honest failures.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from .client import send
from .payload import Payload
from .publisher import Publisher, content_digest

_WATCH_DIRS = (".engos", "docs", "discovery")

__all__ = ["Watcher", "content_digest", "snapshot"]


def snapshot(root: Path) -> dict[str, tuple[float, int]]:
    """Cheap change detector: path → (mtime, size) across the engineering layer.
    Size is included because filesystem mtime granularity can report two quick
    writes as identical — size catches what the clock misses."""
    out: dict[str, tuple[float, int]] = {}
    for d in _WATCH_DIRS:
        base = root / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if p.is_file() and p.name != ".gitkeep":
                try:
                    st = p.stat()
                    out[p.relative_to(root).as_posix()] = (st.st_mtime, st.st_size)
                except OSError:
                    continue  # a vanished/locked file is a change signal, not a crash
    return out


class Watcher:
    """Watch one repo's engineering layer and keep EOS Cloud current.

    Publishing delegates to the shared event-driven Publisher; the watcher only adds
    the notice-and-settle loop. Collaborators are injectable so the loop is testable.
    """

    def __init__(
        self,
        repo: Path,
        server: str,
        key: str,
        *,
        poll: float = 1.0,
        settle: float = 2.0,
        log: Callable[[str], None] = print,
        send_fn: Callable[[str, str, Payload], dict] = send,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._repo = Path(repo)
        self._server = server
        self._settle = settle
        self._poll = poll
        self._log = log
        self._clock = clock
        self._sleep = sleep
        self._publisher = Publisher(repo, server, key, log=log, send_fn=send_fn)

    def publish_if_changed(self) -> str:
        return self._publisher.publish_if_changed()

    # --- the loop: notice → settle → publish ----------------------------------
    def run(self, max_cycles: int | None = None) -> None:
        self._log(f"Watching {self._repo} → {self._server} "
                  f"(publish after {self._settle:.0f}s of quiet). Ctrl-C to stop.")
        self.publish_if_changed()  # catch up on start — the dashboard begins current
        last_seen = snapshot(self._repo)
        dirty_since: float | None = None
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            cycles += 1
            self._sleep(self._poll)
            current = snapshot(self._repo)
            if current != last_seen:
                last_seen = current
                dirty_since = self._clock()  # edits still landing — restart the settle window
            elif dirty_since is not None and self._clock() - dirty_since >= self._settle:
                dirty_since = None
                self.publish_if_changed()
