"""The first thing EOS writes about a repository, and the first thing it says out loud.

Two renderings of one observation: a journal entry that stays in the repository, and six
lines in the terminal. The journal entry is the artifact — dated, committed, published,
editable, and part of the engineering memory from the first minute. The terminal output is a
view of it that scrolls away.

Every sentence here is something that was *observed*. Not "this project is well documented" —
"23 documents under docs/, 11 decision-shaped". The first is a judgement that is wrong for
somebody and unfalsifiable for everybody; the second is checkable by the person reading it,
which is what makes it safe to state without hedging.

What EOS cannot derive is named as absent, never filled in. An empty product is a legitimate
state and the job is to show it accurately (ADR-0015: a validator, not a gatekeeper).
"""

from __future__ import annotations

from pathlib import Path

from . import gitinfo
from .inventory import Inventory

# Dated, so it sorts with the rest of the journal and reads as what it is: a record of one
# day. Never regenerated — journal entries are recorded and immutable, and the self-upgrade
# machinery that keeps CLAUDE.md current must not come near this.
FILENAME = "docs/journal/{today}-eos-connected.md"


def _plural(n: int, word: str, suffix: str = "s") -> str:
    return f"{n} {word}{'' if n == 1 else suffix}"


def _shape(history: gitinfo.History, inv: Inventory) -> list[str]:
    """The facts, ordered by how much they tell a stranger about the repository."""
    lines: list[str] = []

    if history.empty:
        lines.append("- **No commits yet.** EOS publishes on your first commit.")
    else:
        span = (f"{_plural(history.commits, 'commit')} between {history.first_date} "
                f"and {history.last_date}")
        who = _plural(history.authors, "contributor")
        if history.recent_authors:
            who += f" — most recently {', '.join(history.recent_authors)}"
        lines.append(f"- **History:** {span}, {who}.")

    if inv.languages:
        lines.append("- **Languages:** " + ", ".join(
            f"{name} ({_plural(count, 'file')})" for name, count in inv.languages) + ".")

    if history.busiest:
        lines.append("- **Where the work happens:** " + ", ".join(
            f"`{name}`" for name, _ in history.busiest)
            + " (by files changed in recent commits).")

    marks = [label for present, label in (
        (inv.has_tests, "tests"), (inv.has_ci, "CI"), (inv.has_container, "containers"),
        (inv.has_license, "a licence")) if present]
    if marks:
        lines.append("- **Also present:** " + ", ".join(marks) + ".")

    return lines


def _memory(inv: Inventory) -> list[str]:
    """What the repository already carries that EOS is now projecting."""
    if not inv.has_engineering_docs:
        return ["- Nothing under `docs/` yet. The taxonomy has been created and is empty."]

    lines = [f"- **{_plural(inv.docs_total, 'document')} already under `docs/`** — "
             "published to EOS as they are, from now on. Anything in a taxonomy section it "
             "recognises (`decisions`, `standards`, `knowledge`, `journal`, `constitution`) "
             "also gets a place in the Library."]
    if inv.docs_by_area:
        lines.append("  " + ", ".join(f"`{area}` ({count})" for area, count in inv.docs_by_area))
    if inv.decision_like:
        lines.append(f"- {_plural(inv.decision_like, 'file')} look like decision records "
                     "(counted by convention, never parsed — your ADRs stay yours).")
    return lines


def _excluded(inv: Inventory, skipped: tuple[str, ...]) -> list[str]:
    """What EOS did not take, and why. The most disproportionate paragraph available."""
    if not inv.excluded and not skipped:
        return []

    lines = ["EOS publishes `.engos/`, `docs/` and `discovery/` and nothing else. "
             "These were left where they are:"]
    lines += [f"- `{name}`" for name in inv.excluded]
    if skipped:
        lines.append(f"- {_plural(len(skipped), 'file')} inside those directories could not be "
                     "read as UTF-8 text and were not sent: "
                     + ", ".join(f"`{name}`" for name in skipped[:5]))
    lines.append("")
    lines.append("Nothing was moved or changed. If any of it is engineering knowledge you "
                 "want EOS to hold, move it under `docs/` and commit.")
    return lines


def entry(repo: Path, *, project: str, display_name: str, today: str,
          history: gitinfo.History, inv: Inventory,
          skipped: tuple[str, ...] = ()) -> str:
    """The first journal entry: what was found on the day EOS arrived."""
    known = _shape(history, inv)
    memory = _memory(inv)
    excluded = _excluded(inv, skipped)

    parts = [
        f"# Journal: EOS connected to {display_name}",
        "",
        f"> **Date:** {today} · **Status:** recorded (immutable) · "
        f"**Provenance:** derived by `eos connect` — observed, not confirmed",
        "",
        "## What EOS found",
        "",
    ]

    if inv.stated_purpose or inv.stated_name:
        stated = inv.stated_purpose or inv.stated_name
        parts += [f"> {stated}", "",
                  f"*— quoted from `{inv.stated_by}`, the one place someone had already "
                  f"written down what this is.*", ""]
    elif inv.readme:
        parts += [f"> {inv.readme}", "", "*— the first heading in `README.md`.*", ""]

    parts += known
    parts += ["", "## Engineering memory", ""]
    parts += memory

    if excluded:
        parts += ["", "## What EOS did not take", ""]
        parts += excluded

    parts += [
        "",
        "## What EOS still does not know",
        "",
        "Everything above is *shape* — how big, how old, how active, how it is laid out. Only",
        "people know *intent*, and none of it can be derived from a repository:",
        "",
        "- **Why** anything is the way it is → decisions, in `docs/decisions/`",
        "- **What this product does**, and how mature each part is → `.engos/capabilities.yaml`",
        "- **What is in flight right now** → `current_focus` in `.engos/project.yaml`",
        "- **Where it is going** → milestones in `.engos/roadmap.yaml`",
        "- **What is true but written nowhere** → `docs/knowledge/`, `docs/standards/`",
        "",
        "Those files exist and are empty. They are empty because EOS refuses to guess: a",
        "plausible roadmap nobody wrote is worse than no roadmap, because you would have to",
        "find out it was fiction.",
        "",
        "## What happens now",
        "",
        f"Every commit to this repository that changes `.engos/`, `docs/` or `discovery/`",
        f"publishes itself to EOS. Nothing to run, no daemon. This entry is a record of one",
        f"day and is not regenerated — edit it, or leave it and write the next one.",
        "",
    ]
    return "\n".join(parts) + "\n"


def report(*, project: str, server: str, branch: str | None, url: str,
           history: gitinfo.History, inv: Inventory, published: int,
           skipped: tuple[str, ...] = ()) -> list[str]:
    """The terminal's six lines. Says one true thing they did not type, then hands off.

    Deliberately not a summary of the journal entry. A forty-line report is a report nobody
    reads even once, and the browser already derives health, an attention queue and a single
    recommended next step from what was just published.
    """
    lines: list[str] = []

    if history.empty:
        read = "no commits yet - EOS publishes on your first"
    else:
        read = (f"{_plural(history.commits, 'commit')} since {history.first_date} - "
                f"{_plural(history.authors, 'contributor')}, "
                f"last change {history.last_date}")
    lines.append(f"  Read       {read}")

    if inv.docs_total:
        found = f"{_plural(inv.docs_total, 'document')} under docs/"
        if inv.decision_like:
            found += f", {inv.decision_like} of them decision-shaped"
    elif inv.languages:
        found = ", ".join(f"{name}" for name, _ in inv.languages[:3]) + " - no docs/ yet"
    else:
        found = "an empty repository"
    lines.append(f"  Found      {found}")

    if inv.excluded or skipped:
        left = ", ".join(inv.excluded[:2]) if inv.excluded else ""
        if skipped:
            left = (left + ", " if left else "") + f"{_plural(len(skipped), 'unreadable file')}"
        lines.append(f"  Left alone {left}")
        lines.append("             (EOS reads docs/, .engos/ and discovery/ only)")

    lines.append(f"  Published  {_plural(published, 'file')}")
    lines.append("")

    if inv.docs_total:
        lines.append("EOS is now publishing engineering memory this repository already had.")
    else:
        lines.append("EOS knows the shape of this project. It does not yet know what it does,")
        lines.append("or why - that part is yours to write, and it starts here:")
    lines.append(f"  {url}")
    return lines
