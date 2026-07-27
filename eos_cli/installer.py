"""Install the EOS engineering standard into an existing repository (ADR-0014, ADR-0016).

Minimal and non-invasive: the `.engos` structured state, the taxonomy skeleton, the
discovery layer, the AI instructions (CLAUDE.md), and the protocol version. Nothing
product-specific. Idempotent-safe: refuses to overwrite an existing install.

(Footprint note — provisional: this v0 installs the layout EOS already reads
[`docs/` + `.engos/` + `discovery/`]. The definitive `.engos` footprint is a spec
question, to be forced by a repo with its own conventions.)
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

ENGOS_VERSION = "0.1"

# The standard-stamp: bumped whenever the EOS-owned artifacts (CLAUDE.md template,
# hook wiring) change. Connected repos compare it at every publish event and
# self-upgrade when behind — updates ride commits; nobody runs an updater.
#
# Deliberately NOT bumped for changes to the seed template below. `upgrade_standard`
# refreshes CLAUDE.md and the hook and nothing else — it never rewrites `.engos/` state,
# `docs/` or `discovery/`, because a tool that silently edits authored files during a commit
# is a tool people stop trusting. A seed-only change therefore has nothing to apply to an
# already-seeded repository, and bumping for it would run a no-op upgrade everywhere.
STANDARD_STAMP = "2026-07-27.1"


class InstallError(RuntimeError):
    """The target repo is missing or already has the standard installed."""


def _write(root: Path, rel: str, content: str) -> str:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return rel


def _claude_md(name: str) -> str:
    return f"""# {name} — engineering agent instructions

This repository is **Engineering OS–native**. Its engineering knowledge lives in a
canonical `.engos` layer that Engineering OS reads and projects (Workspace, Library,
Dashboard). **You maintain that layer as you build.** Engineering OS reasons about
nothing and never writes here — *you* are the author; EOS validates and projects.

## The layers

- `.engos/manifest.yaml` — identity + protocol version (do not hand-edit `engos_version`).
- `.engos/project.yaml` — the product's current status and focus. `current_focus` is
  **one sentence** — what's in flight right now. History belongs in the journal,
  plans in the roadmap and docs; never append to the focus, replace it.
- `.engos/roadmap.yaml` — milestones (identity only; status is derived from capabilities).
- `.engos/capabilities.yaml` — what the product does: `id`, `title`, `module`, `milestone`,
  `maturity` (planned→available→released→deprecated), `delivery` (pre-release), and
  `evidence` (links to the ADRs/journals that realize it).
- `docs/` — the settled-knowledge taxonomy: `constitution/`, `decisions/` (ADRs),
  `standards/`, `knowledge/`, `journal/`.
- `discovery/observations/` — unsettled learnings (the discovery layer).

## How to work

1. **Build the software** — and, in the same change, **update the engineering model**:
   add/adjust the capability, write an ADR for any real decision, add a journal entry for
   the slice. Your writes carry provenance `ai-authored` until a human confirms them.
2. **Decisions are gated.** Record a decision as a `proposed` ADR in `docs/decisions/`.
   A human accepts it. You never accept your own ADRs, and you never self-implement a
   change to the standard.
3. **When you notice a gap** (in the product, or in Engineering OS itself), record an
   **Observation** in `discovery/observations/YYYY-MM-DD-slug.md` with a `Target`,
   `Category`, and `Provenance`. Humans triage it (accept / refine / decline / dismiss).
4. **Keep `.engos` accurate.** It is the contract EOS projects — if the code changes, the
   engineering model changes with it.
5. **Commit your work.** The commit is the engineering event: on a connected repo
   (`eos connect`), a post-commit hook publishes engineering-layer changes to EOS
   automatically — you never run a publish command or a watcher. End every session by
   committing, so EOS reflects reality. (Explicit fallback: `eos publish`.)

Protocol version: `{ENGOS_VERSION}`.
"""


# The placeholder set that crosses the wire. Deliberately tiny and fixed: no template
# language travels, and the client performs four substitutions (ADR-0019 §3).
PLACEHOLDERS = ("project_slug", "project_name", "owner", "today")


def standard_template() -> tuple[dict[str, str], list[str]]:
    """The Engineering Layer as data — path -> content, placeholders unsubstituted.

    This is the single definition of the standard. `install_standard` renders it locally and
    `GET /api/connect/template` serves it verbatim, so a server-seeded repository and a
    locally-installed one are byte-identical. Two definitions would drift, and the drift would
    stay invisible until two projects disagreed about what the standard is.
    """
    manifest = (
        "schema_version: 1\n"
        f"engos_version: '{ENGOS_VERSION}'\n"
        "project: {{project_slug}}\n"
        "display_name: '{{project_name}}'\n"
        "provenance: installed by the Engineering OS Factory\n"
    )
    # Empty but named. A file that says `capabilities: []` is a labelled slot the developer
    # can fill; a file that says "Founding — the standard is installed" is EOS talking about
    # itself in the one place a new user is guaranteed to look. What EOS cannot derive, it
    # leaves blank — pre-filling it with something plausible would make the one thing only a
    # human knows look like something the tool already worked out.
    project = (
        "# `current_focus` is one sentence: what is in flight right now. Replace it, never\n"
        "# append — history belongs in the journal and plans in the roadmap.\n"
        "schema_version: 1\n"
        "status: active\n"
        "current_focus: ''\n"
        "owners:\n"
        "  - role: Founding Engineer\n"
        "    holder: '{{owner}}'\n"
        "updated: '{{today}}'\n"
    )
    roadmap = (
        "# Milestones are authored as the product is planned; status derives from\n"
        "# capabilities, never from this file.\n"
        "schema_version: 1\n"
        "milestones: []\n"
        "updated: '{{today}}'\n"
    )
    capabilities = (
        "# Capabilities are authored as the product is built.\n"
        "schema_version: 1\n"
        "capabilities: []\n"
        "updated: '{{today}}'\n"
    )
    charter = (
        "# {{project_name}} — Charter\n\n"
        "> **Status:** Active · **Owner:** Founding Engineer · **Layer:** Universal\n\n"
        "## Mission\n\n"
        "_Why this exists, in a sentence or two. Nothing in the repository can tell EOS this;\n"
        "it is the first thing worth writing down._\n\n"
        "## Foundation\n\n"
        "This product is built on the Engineering OS standard — its taxonomy, lifecycle, and "
        "principles. Its own decisions, standards, and knowledge accumulate here as it grows.\n"
    )
    return {
        ".engos/manifest.yaml": manifest,
        ".engos/project.yaml": project,
        ".engos/roadmap.yaml": roadmap,
        ".engos/capabilities.yaml": capabilities,
        "docs/constitution/charter.md": charter,
        "docs/decisions/.gitkeep": "",
        "docs/standards/.gitkeep": "",
        "docs/knowledge/.gitkeep": "",
        # The first journal entry is not a template. It is written by `connect`, from what was
        # actually found in the repository (`eos_cli/firstlook.py`) — a dated record of the day
        # EOS arrived, rather than a paragraph about EOS installing itself.
        "docs/journal/.gitkeep": "",
        "discovery/observations/.gitkeep": "",
        "CLAUDE.md": _claude_md("{{project_name}}"),
    }, list(PLACEHOLDERS)


def render_template(files: dict[str, str], values: dict[str, str]) -> dict[str, str]:
    """Substitute the fixed placeholder set, in paths as well as contents."""
    def sub(text: str) -> str:
        for name in PLACEHOLDERS:
            text = text.replace("{{" + name + "}}", values.get(name, ""))
        return text

    return {sub(path): sub(content) for path, content in files.items()}


def install_standard(
    target_root: Path | str,
    name: str,
    slug: str,
    owner: str = "Founding Engineer",
    today: str | None = None,
) -> list[str]:
    """Install the standard into an existing repo. Returns the list of files written."""
    root = Path(target_root)
    today = today or date.today().isoformat()
    if not root.is_dir():
        raise InstallError(f"Target repository does not exist: {root}")
    if (root / ".engos" / "manifest.yaml").exists():
        raise InstallError("The EOS standard is already installed (.engos/manifest.yaml exists).")

    files, _ = standard_template()
    rendered = render_template(files, {
        "project_slug": slug, "project_name": name, "owner": owner, "today": today,
    })
    return [_write(root, path, content) for path, content in sorted(rendered.items())]


def upgrade_standard(root: Path | str) -> list[str]:
    """Refresh what the Factory owns in an ALREADY-installed repo, without ever
    touching authored content (.engos state, docs, discovery are the project's).

    EOS-owned and safely refreshable: the generated CLAUDE.md (previous content is
    backed up if it diverged — it may carry local customizations) and, when the repo
    is connected, the post-commit hook. Returns human-readable actions taken.
    """
    import yaml

    root = Path(root)
    manifest_path = root / ".engos" / "manifest.yaml"
    if not manifest_path.is_file():
        raise InstallError(f"{root} is not EOS-native (.engos/manifest.yaml missing). Run install first.")
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        manifest = {}
    name = str(manifest.get("display_name") or manifest.get("project") or root.name)
    actions: list[str] = []

    # 1. The AI instructions — regenerate from the current template.
    fresh = _claude_md(name)
    cm = root / "CLAUDE.md"
    current = cm.read_text(encoding="utf-8") if cm.is_file() else None
    if current == fresh:
        actions.append("CLAUDE.md already current")
    else:
        if current is not None:
            (root / "CLAUDE.md.bak").write_text(current, encoding="utf-8")
            actions.append("CLAUDE.md refreshed (previous saved to CLAUDE.md.bak)")
        else:
            actions.append("CLAUDE.md written")
        cm.write_text(fresh, encoding="utf-8")

    # 2. The publishing event wiring — refresh only if this repo is connected.
    from .hooks import HookError, install_post_commit
    from .local import ensure_gitignored, load_connection

    server, key = load_connection(root)
    if server and key:
        ensure_gitignored(root)
        try:
            install_post_commit(root)
            actions.append("post-commit hook refreshed")
        except HookError as e:
            actions.append(f"hook not refreshed: {e}")
    else:
        actions.append("not connected yet — run `connect` once to enable event-driven publishing")

    # 3. Protocol version — report, never silently rewrite identity.
    repo_version = str(manifest.get("engos_version", "")) or "unknown"
    if repo_version == ENGOS_VERSION:
        actions.append(f"protocol v{repo_version} — current")
    else:
        actions.append(f"protocol v{repo_version} (server speaks v{ENGOS_VERSION}) — "
                       "migration will be a spec-versioned step, not a silent rewrite")
    return actions


def maybe_self_upgrade(root: Path | str, log=print) -> bool:
    """The permanent update loop: at every publish event, if this repo's stamped
    standard is older than the one this Factory carries, refresh it in place.
    Safe by construction (upgrade_standard touches only EOS-owned artifacts) and
    quiet by default — returns True when an upgrade ran."""
    from .local import load_stamp, save_stamp

    root = Path(root)
    if load_stamp(root) == STANDARD_STAMP:
        return False
    try:
        actions = upgrade_standard(root)
    except InstallError:
        return False  # not an installed repo — nothing to keep current
    save_stamp(root, STANDARD_STAMP)
    quiet_markers = ("already current", "not connected", "— current")
    changed = [a for a in actions if not any(m in a for m in quiet_markers)]
    if changed:
        log(f"· EOS standard self-upgraded to {STANDARD_STAMP}: " + "; ".join(changed))
    return True
