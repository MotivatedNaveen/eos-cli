"""Local git discovery — what the CLI knows that the server cannot (ADR-0019 §2).

EOS never knows repositories: no credentials, no clone, no path. So the repository, its
branch, and a sensible display name are all discovered here, on the machine that has them.
Everything degrades to None rather than raising — a missing git is a message to the user,
not a traceback.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


def _git(args: list[str], cwd: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def git_available(cwd: Path | None = None) -> bool:
    return _git(["--version"], cwd or Path.cwd()) is not None


def repo_root(start: Path | None = None) -> Path | None:
    """The git root containing `start` (default: the working directory).

    This is the whole of "repository discovery". The user is standing in the repository they
    mean; asking them to type its path would be asking for something already known.
    """
    cwd = Path(start or Path.cwd()).resolve()
    top = _git(["rev-parse", "--show-toplevel"], cwd)
    return Path(top).resolve() if top else None


def current_branch(repo: Path) -> str | None:
    """The checked-out branch, or None on a detached HEAD or an empty repository."""
    name = _git(["rev-parse", "--abbrev-ref", "HEAD"], Path(repo))
    return None if name in (None, "HEAD") else name


def default_branch(repo: Path) -> str | None:
    """The remote's default branch, when the remote advertises one.

    Preferred over the current branch as the publishing branch: what is on the default branch
    is what the team has agreed is true, which is exactly what engineering memory should show.
    """
    ref = _git(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], Path(repo))
    return ref.rsplit("/", 1)[-1] if ref else None


def user_name(repo: Path) -> str | None:
    return _git(["config", "user.name"], Path(repo))


def suggest_display_name(repo: Path) -> str:
    """A human name for the project, seeded from the directory.

    The platform cannot supply this — a project's name is substance, derived from its own
    store (ADR-0018 §0) — and asking for it would be asking for something the repository
    already implies. The repository owns it from the moment it is written.
    """
    return Path(repo).name or "Project"


def symbolic_branch(repo: Path) -> str | None:
    """The branch HEAD points at, even before the first commit exists.

    `rev-parse --abbrev-ref HEAD` fails outright on a repository with no commits, which is
    how a freshly-`git init`ed project ended up connecting with no recorded branch — and a
    connection with no branch does not filter, so it publishes from *every* branch, which is
    exactly what ADR-0019 §4 exists to prevent.
    """
    return _git(["symbolic-ref", "--short", "HEAD"], Path(repo))


# --- what the history can be asked, and nothing more --------------------------
#
# Shape, not intent. How old, how active, how many people, where the work happens. Every fact
# here is checkable by the developer reading it, which is the property that makes it safe to
# state without hedging. Why any of it is the way it is remains unknowable from here, and is
# what Engineering Memory is for.

@dataclass(frozen=True)
class History:
    commits: int = 0
    first_date: str = ""            # ISO date of the oldest commit
    last_date: str = ""             # ISO date of the newest
    authors: int = 0
    recent_authors: tuple[str, ...] = ()
    busiest: tuple[tuple[str, int], ...] = ()   # (top-level directory, changed files)

    @property
    def empty(self) -> bool:
        return self.commits == 0


# Reading every filename of every commit is unbounded work on an old repository, and this
# runs while someone waits at a terminal. The most recent slice answers "where does the work
# happen *now*", which is the only useful reading of it anyway.
_RECENT_COMMITS = 300


def history(repo: Path) -> History:
    """Everything derivable from the commit log, in two git calls.

    Never raises and never returns None: a repository with no commits is a legitimate state
    with an honest answer, not an error.
    """
    root = Path(repo)
    # One pass. The log is newest-first, so the first line is the last commit and the last
    # line is the first — no second `--reverse` walk, which is the expensive one.
    log = _git(["log", "--format=%aI%x09%aN"], root)
    if not log:
        return History()

    lines = [line for line in log.splitlines() if "\t" in line]
    if not lines:
        return History()

    dates, names = zip(*(line.split("\t", 1) for line in lines), strict=False)
    seen: list[str] = []
    for name in names:
        if name and name not in seen:
            seen.append(name)

    # min/max, not first/last of the log. `git log` orders by commit graph, and author dates
    # legitimately run out of order after a rebase, a cherry-pick, or an imported history —
    # which would otherwise produce "9 commits since 2026, last change 2025".
    days = sorted(d[:10] for d in dates if d)
    return History(
        commits=len(lines),
        first_date=days[0] if days else "",
        last_date=days[-1] if days else "",
        authors=len(seen),
        recent_authors=tuple(seen[:3]),   # `seen` is newest-first, so these are the active ones
        busiest=_busiest(root),
    )


def _busiest(repo: Path) -> tuple[tuple[str, int], ...]:
    """Top-level directories by files touched in recent history."""
    out = _git(["log", "--name-only", "--format=", f"-n{_RECENT_COMMITS}"], repo)
    if not out:
        return ()
    counts: dict[str, int] = {}
    for line in out.splitlines():
        path = line.strip()
        if not path:
            continue
        head = path.split("/", 1)[0] if "/" in path else "(root)"
        counts[head] = counts.get(head, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return tuple(ranked[:4])
