"""`eos connect` — import a connection file, then EOS disappears (ADR-0019).

EOS is the control plane: it owns organizations, projects and credentials. This command owns
none of them. It connects a repository that already exists to a project that already exists,
and it is the only EOS command most developers ever run.

So it asks for as little as possible and derives the rest:

    connection file  -> server + project + credential   (downloaded from EOS)
    server           -> organization, standard template (fetched)
    cwd              -> repository, branch, author      (discovered)

Order matters more than it looks. Nothing touches the repository until the file has been
validated, the server has confirmed the credential, and the user has confirmed the project —
so a wrong file leaves the working tree exactly as it was.
"""

from __future__ import annotations

import getpass
import json
from datetime import date
from pathlib import Path

import yaml

from .connect_client import ConnectError, fetch_context, fetch_template
from .local import save_connection, save_standard_version, save_stamp
from .publisher import Publisher
from .token import (
    DESCRIPTOR_FILENAME,
    ProjectConnection,
    TokenError,
    decode,
    from_descriptor,
)
from . import firstlook, gitinfo
from .client import package_protocol
from .hooks import HookError, install_post_commit
from .inventory import survey
from .installer import STANDARD_STAMP, render_template

PROMPT = "Paste your EOS connection token: "


class ConnectAborted(RuntimeError):
    """The user declined, or a prerequisite is missing. Never a traceback — this runs in
    front of someone who is thirty seconds into trying EOS for the first time."""


# --- finding the connection file ---------------------------------------------


def candidate_paths(repo: Path, cwd: Path | None = None) -> list[Path]:
    """Where a just-downloaded connection file plausibly is.

    A browser saves it to Downloads; the developer is standing in their repository. Searching
    both is the difference between "run one command" and "work out the path to a file you did
    not choose the name of". Whatever is found is shown before anything happens, so discovery
    can surprise but never act unseen.
    """
    here = Path(cwd) if cwd else Path.cwd()
    found: list[Path] = []
    for base in (here, Path(repo), Path.home() / "Downloads"):
        try:
            path = (base / DESCRIPTOR_FILENAME).resolve()
        except OSError:
            continue
        if path.is_file() and path not in found:
            found.append(path)
    return found


def load_descriptor(path: Path) -> ProjectConnection:
    """Read and validate a connection file, with messages written for a person mid-setup."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ConnectAborted(f"No connection file at {path}.") from e
    except (OSError, UnicodeDecodeError) as e:
        raise ConnectAborted(f"Could not read {path}: {e}") from e
    except ValueError as e:
        raise ConnectAborted(
            f"{path} is not valid JSON. Download the connection file from EOS again."
        ) from e
    try:
        return from_descriptor(data)
    except TokenError as e:
        raise ConnectAborted(str(e)) from e


def dispose(path: Path, repo: Path, *, log=print) -> None:
    """Delete the connection file once the repository holds the credential.

    It is a secret with exactly one use, and it is now spent. Leaving it behind means a
    publish key sitting in Downloads — so it is removed rather than merely gitignored.
    Failing to delete is reported, never fatal: the repository is connected either way, and
    the developer is the one who can act on it.
    """
    path = Path(path)
    try:
        path.unlink()
    except OSError as e:
        log(f"! could not delete the connection file at {path}: {e}")
        log("  It holds your publish key - delete it yourself."
            + (" It is gitignored, so it will not be committed."
               if _is_inside(path, repo) else ""))
        return
    log(f"  connection file used and deleted ({path.name} - it held the key)")


def _is_inside(path: Path, repo: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(repo).resolve())
    except (ValueError, OSError):
        return False
    return True


# --- what the repository already says -----------------------------------------


def manifest_project(repo: Path) -> str | None:
    """The project this repository already publishes as, or None if it is not EOS-native.

    Read before anything is written, because a mismatch here is the one failure a developer
    would otherwise never see: the connection would store happily, and every future publish
    would be rejected 403 by a silent commit hook (publish-protocol §4).
    """
    path = Path(repo) / ".engos" / "manifest.yaml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None
    project = data.get("project") if isinstance(data, dict) else None
    return project if isinstance(project, str) and project else None


def read_token(provided: str | None, *, prompt=getpass.getpass, log=print) -> str:
    """Read a connection token without echoing it.

    A token carries a publish credential, so it must not reach shell history, a process
    listing, or a CI log. `--token` exists for automation and says so out loud when used.
    """
    if provided:
        log("! --token was passed on the command line, so it is now in your shell history.\n"
            "  For interactive use, run `connect` with no arguments and paste when asked.")
        return provided.strip()
    try:
        return (prompt(PROMPT) or "").strip()
    except (EOFError, KeyboardInterrupt):
        raise ConnectAborted("Cancelled.") from None


def confirm(context, repo: Path, display_name: str, branch: str | None, server: str, *,
            source: Path | None = None, ask=input, log=print) -> bool:
    """Show what the connection means before changing anything.

    This is not asking the user for information — it is showing them what they have. A
    credential for one project used in another repository would otherwise connect happily and
    start publishing the wrong engineering memory under the wrong name.

    The server is shown because it is the one fact nobody typed: it came out of the file, and
    "which EOS am I publishing to?" must never be answered by assumption.
    """
    log("")
    log(f"  Repository    {display_name}")
    log(f"                {repo}")
    log(f"  Organization  {context.organization_name}")
    log(f"  Project       {context.project_slug}")
    log(f"  Publishes to  {server}")
    log(f"  Publishes on  {branch or '(current branch)'}")
    if source is not None:
        log(f"  From          {source}")
    log("")
    try:
        answer = (ask("Connect this repository? [Y/n] ") or "").strip().lower()
    except (EOFError, KeyboardInterrupt):
        # Ctrl-C, or no terminal at all (a pipe, a CI shell). Both mean "not confirmed" —
        # and neither is a traceback, which is the one thing this command must never print.
        log("")
        return False
    return answer in ("", "y", "yes")


def run_connect(
    descriptor_path: str | None = None,
    token_value: str | None = None,
    repo_hint: str | None = None,
    *,
    default_server: str = "",
    assume_yes: bool = False,
    log=print,
    prompt=getpass.getpass,
    ask=input,
    cwd: Path | None = None,
) -> int:
    # --- prerequisites, before anything else -------------------------------
    if not gitinfo.git_available():
        raise ConnectAborted(
            "git was not found on this machine. EOS publishes on commit, so it needs git.")

    repo = gitinfo.repo_root(Path(repo_hint) if repo_hint else None)
    if repo is None:
        raise ConnectAborted(
            "This is not a git repository. Run `connect` inside the repository you want to "
            "connect, or pass --repo.")

    # --- where the credential comes from ------------------------------------
    #
    # The connection file is the path EOS hands people. A pasted token is the same credential
    # in the form that fits a CI secret, and stays supported because a repository connected
    # that way must keep working.
    source: Path | None = None
    descriptor: ProjectConnection | None = None
    if descriptor_path:
        source = Path(descriptor_path).expanduser()
    elif not token_value:
        found = candidate_paths(repo, cwd)
        if len(found) == 1:
            source = found[0]
        elif len(found) > 1:
            raise ConnectAborted(
                f"Found more than one {DESCRIPTOR_FILENAME}:\n"
                + "\n".join(f"  {p}" for p in found)
                + f"\nRun `connect <path>` with the one you mean.")

    if source is not None:
        descriptor = load_descriptor(source)
        server, key = descriptor.server, descriptor.key
    else:
        try:
            connection = decode(read_token(token_value, prompt=prompt, log=log),
                                default_server=default_server)
        except TokenError as e:
            raise ConnectAborted(str(e)) from e
        server, key = connection.server, connection.key

    # --- ask the server who this credential belongs to ----------------------
    log(f"Connecting to {server} ...")
    try:
        context = fetch_context(server, key)
    except ConnectError as e:
        raise ConnectAborted(str(e)) from e

    if descriptor is not None and context.project_slug != descriptor.project:
        # The file and the credential disagree — it was edited, or two downloads were crossed.
        # Either way the project it names is not the project it can publish to.
        raise ConnectAborted(
            f"That connection file names project '{descriptor.project}', but its key "
            f"publishes to '{context.project_slug}'. Download a fresh connection file "
            f"from EOS.")

    # Two separate questions, deliberately not one. "Is there a layer?" decides whether to
    # seed; "what does it publish as?" decides whether this connection can work. Collapsing
    # them means an unreadable manifest reads as "no layer" and the template overwrites a
    # repository's authored engineering memory.
    has_layer = (repo / ".engos" / "manifest.yaml").is_file()
    existing = manifest_project(repo)

    if has_layer and existing is None:
        raise ConnectAborted(
            "This repository has an engineering layer, but .engos/manifest.yaml does not name "
            "a project. It may be damaged or hand-edited. Nothing was changed.\n"
            "Add `project: " + context.project_slug + "` to it and run `connect` again; "
            "publishing is rejected without it.")

    if existing is not None and existing != context.project_slug:
        # Protocol §4: a publish is rejected unless the manifest's project and the key's
        # project are the same string. Caught here, while it is still a sentence someone can
        # read — not later, as a 403 from a silent post-commit hook.
        raise ConnectAborted(
            f"This repository already publishes as '{existing}', but that connection is for "
            f"'{context.project_slug}'. Nothing was changed.\n"
            f"Connect the repository that belongs to '{context.project_slug}', or change "
            f"`project:` in .engos/manifest.yaml if this repository really did move.")

    display_name = ((descriptor.display_name if descriptor else "")
                    or gitinfo.suggest_display_name(repo))
    # `symbolic_branch` is the third fallback and the one that matters: a repository with no
    # commits yet answers neither of the first two, and a connection with no recorded branch
    # does not filter — so it would publish from every branch, which is what ADR-0019 §4
    # exists to prevent.
    branch = (gitinfo.default_branch(repo) or gitinfo.current_branch(repo)
              or gitinfo.symbolic_branch(repo))

    if not assume_yes and not confirm(context, repo, display_name, branch, server,
                                      source=source, ask=ask, log=log):
        raise ConnectAborted("Cancelled - nothing was changed.")

    # --- look at the repository before changing it --------------------------
    #
    # Read now, so the first journal entry describes what was here when EOS arrived rather
    # than what EOS just created. Both halves are local: git and a directory walk. EOS never
    # reads repositories (ADR-0014) — this is the machine that has one, describing it.
    story = gitinfo.history(repo)
    inv = survey(repo)

    # --- seed the engineering layer, only if there is none ------------------
    standard_version = STANDARD_STAMP
    today = date.today().isoformat()
    if not has_layer:
        log("Setting up the engineering layer ...")
        try:
            files, standard_version = fetch_template(server, key)
        except ConnectError as e:
            # Fail before writing anything. A half-created engineering layer is worse than
            # none: the next publish would send an incoherent protocol.
            raise ConnectAborted(str(e)) from e
        rendered = render_template(files, {
            # The slug comes from the server, never from the repository — which is what makes
            # the protocol's identity rule hold by construction rather than by luck.
            "project_slug": context.project_slug,
            "project_name": display_name,
            "owner": gitinfo.user_name(repo) or "Founding Engineer",
            "today": today,
        })
        for rel, content in sorted(rendered.items()):
            path = repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        # The first entry, written from what was found rather than from a template. Only when
        # seeding: a repository that already has an engineering layer keeps the one it has,
        # and writing into it would break the promise that `connect` leaves it alone.
        first = repo / firstlook.FILENAME.format(today=today)
        if not first.exists():
            first.parent.mkdir(parents=True, exist_ok=True)
            first.write_text(
                firstlook.entry(repo, project=context.project_slug, display_name=display_name,
                                today=today, history=story, inv=inv),
                encoding="utf-8")
        log(f"  {len(rendered) + 1} files created")
    else:
        log("Engineering layer already present - leaving it alone.")

    # --- record the connection and wire the commit hook ---------------------
    save_connection(repo, server, key, branch)
    save_standard_version(repo, standard_version)
    save_stamp(repo, STANDARD_STAMP)
    log("  connection stored in .eos/ (gitignored - the key is never committed)")

    try:
        install_post_commit(repo)
        log(f"  commit hook installed - commits on '{branch}' publish automatically")
    except HookError as e:
        log(f"! could not install the git hook: {e}")
        log("  Publishing still works with `publish`.")

    # --- publish once, now --------------------------------------------------
    #
    # Without this the developer finishes setup and EOS shows them an empty project until
    # they happen to commit. Seeing your engineering memory is the point of connecting.
    log("Publishing ...")
    sent = package_protocol(repo)
    outcome = Publisher(repo, server, key,
                        log=lambda m: log(f"  {m}")).publish_if_changed(sent)

    if source is not None:
        dispose(source, repo, log=log)

    log("")
    if outcome == "error":
        # The connection is stored and the hook is installed, so this retries by itself. But
        # the closing line must not claim a success the developer can see did not happen —
        # they would go looking for memory that is not there and conclude EOS is broken.
        log(f"Connected, but the first publish did not go through. {context.project_slug}")
        log(f"will publish to {server} on the next commit to '{branch}'.")
        return 0

    # --- say one true thing they did not type, then hand off ----------------
    #
    # Not a summary of the journal entry that was just written: a forty-line report is a
    # report nobody reads even once, and the browser already derives health, an attention
    # queue and a single recommended next step from what was published.
    log(f"Connected. {context.project_slug} publishes to {server} on every commit to "
        f"'{branch}'.")
    log("")
    for line in firstlook.report(
        project=context.project_slug, server=server, branch=branch,
        url=f"{server}/{context.project_slug}", history=story, inv=inv,
        published=len(sent.files), skipped=sent.skipped,
    ):
        log(line)
    return 0
