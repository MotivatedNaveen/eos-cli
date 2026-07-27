"""What a publish sends (publish-protocol §3).

A dataclass rather than the server's pydantic model, for one reason that matters: pydantic
was the only non-stdlib dependency in the client path besides PyYAML, and a CLI that drags a
validation framework in to build a three-field dictionary is a CLI that is hard to package
and slow to start.

Validation still happens — at the server's router boundary, which is where a payload arriving
over a network has to be checked anyway. Validating it a second time on the machine that just
constructed it protects nobody.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Payload:
    """A project's complete engineering protocol — relative path → file content.

    `files` is the whole engineering layer (`.engos/`, `docs/`, `discovery/`), never code,
    and a publish replaces the stored protocol wholesale: what is absent here is deleted
    there (publish-protocol §7).
    """

    project: str
    engos_version: str
    files: dict[str, str] = field(default_factory=dict)

    # Files inside the published roots that were read but not sent — unreadable bytes, or not
    # valid UTF-8 (publish-protocol §6.1). Client-local: never serialised, never sent. The
    # protocol says a client SHOULD report what it excluded rather than dropping it silently,
    # and a file that vanishes without a word is the kind of thing found months later.
    skipped: tuple[str, ...] = ()

    def wire(self) -> dict:
        """The JSON body, exactly as the protocol defines it.

        One place builds this, so the digest and the request can never disagree about what
        was sent — which is the failure that would make a repository look unchanged while
        publishing something different.
        """
        return {
            "project": self.project,
            "engos_version": self.engos_version,
            "files": self.files,
        }
