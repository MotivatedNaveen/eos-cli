"""The local connection — where a repo remembers how to reach EOS Cloud.

Lives in `<repo>/.eos/` — OUTSIDE the engineering layer, so it is never packaged
into a publish payload (the key must never travel) and never triggers the watcher.
`connect` gitignores the whole directory. Reads degrade gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

_DIR = ".eos"
_CONN_FILE = "publish.yaml"
_STATE_FILE = "state.json"

# Everything EOS puts in a repository that must never be committed. Both entries hold the
# publish key: `.eos/` is where it lives, `eos-project.json` is how it arrived.
_GITIGNORE_ENTRIES = (".eos/", "eos-project.json")


def _dir(repo: Path) -> Path:
    return Path(repo) / _DIR


def save_connection(repo: Path, server: str, key: str, branch: str | None = None) -> Path:
    """Store where this repo publishes, with what, and from which branch.

    `branch` is the single branch that publishes (ADR-0019 §4). One, not a list: "which state
    is EOS showing?" must have exactly one answer, and any set larger than one reintroduces
    last-writer-wins between its members.
    """
    d = _dir(repo)
    d.mkdir(parents=True, exist_ok=True)
    path = d / _CONN_FILE
    conn: dict = {"server": server, "key": key}
    if branch:
        conn["branch"] = branch
    path.write_text(
        "# EOS connection — LOCAL ONLY (gitignored). The publish key must never be committed.\n"
        + yaml.safe_dump(conn, sort_keys=False),
        encoding="utf-8",
    )
    ensure_gitignored(repo)
    return path


def load_branch(repo: Path) -> str | None:
    """The branch this repo publishes from, or None when unset (an older connection)."""
    path = _dir(repo) / _CONN_FILE
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    branch = data.get("branch") if isinstance(data, dict) else None
    return branch if isinstance(branch, str) and branch else None


def load_standard_version(repo: Path) -> str | None:
    value = _load_state(repo).get("standard_version")
    return value if isinstance(value, str) else None


def save_standard_version(repo: Path, version: str) -> None:
    """The standard the server seeded this repo with. Later publishes compare and REPORT a
    newer one rather than applying it — a tool that silently rewrites files in your repository
    during a commit is a tool people stop trusting."""
    _save_state(repo, standard_version=version)


def load_connection(repo: Path) -> tuple[str | None, str | None]:
    path = _dir(repo) / _CONN_FILE
    if not path.is_file():
        return None, None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None, None
    if not isinstance(data, dict):
        return None, None
    server = data.get("server")
    key = data.get("key")
    return (server if isinstance(server, str) else None,
            key if isinstance(key, str) else None)


def _load_state(repo: Path) -> dict:
    path = _dir(repo) / _STATE_FILE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_state(repo: Path, **updates: str) -> None:
    """Best-effort merge — losing state only costs one redundant idempotent action."""
    try:
        d = _dir(repo)
        d.mkdir(parents=True, exist_ok=True)
        state = {**_load_state(repo), **updates}
        (d / _STATE_FILE).write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        return
    ensure_gitignored(repo)  # whoever creates .eos/ keeps it out of git


def load_stamp(repo: Path) -> str | None:
    stamp = _load_state(repo).get("standard_stamp")
    return stamp if isinstance(stamp, str) else None


def save_stamp(repo: Path, stamp: str) -> None:
    _save_state(repo, standard_stamp=stamp)


def load_last_digest(repo: Path) -> str | None:
    digest = _load_state(repo).get("last_digest")
    return digest if isinstance(digest, str) else None


def save_last_digest(repo: Path, digest: str) -> None:
    """Best-effort — losing the state only costs one redundant (idempotent) publish."""
    _save_state(repo, last_digest=digest)


def ensure_gitignored(repo: Path) -> None:
    """Make sure nothing holding the publish key can reach git.

    Appends only what is missing, so running this twice adds nothing and an entry the
    developer deleted on purpose comes back only if EOS still needs it.
    """
    gi = Path(repo) / ".gitignore"
    try:
        text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
        present = set(text.splitlines())
        missing = [e for e in _GITIGNORE_ENTRIES if e not in present]
        if not missing:
            return
        sep = "" if (not text or text.endswith("\n")) else "\n"
        gi.write_text(
            text + f"{sep}# EOS — these hold the publish key and must never be committed\n"
            + "".join(f"{e}\n" for e in missing),
            encoding="utf-8",
        )
    except OSError:
        pass
