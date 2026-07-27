"""The `eos` command.

    eos connect [path/to/eos-project.json] [--repo /path/to/repo]
    eos publish [--repo /path/to/repo] [--if-changed] [--quiet]
    eos upgrade [--repo /path/to/repo]
    eos watch   [--repo /path/to/repo]
    eos install --into /path/to/repo --name "BusOS" --slug busos [--owner NAME] [--commit]

`connect` is the one command a developer runs: it imports the connection file EOS produced
when the project was created, seeds the engineering layer, stores the connection locally
(gitignored - the key never travels), installs a post-commit hook, and publishes once. From
then on publishing is EVENT-DRIVEN - every commit that changed the engineering layer
publishes itself, and nobody keeps a terminal running.

No command here creates a project. EOS is the control plane and provisions projects and
credentials; this CLI connects a repository to one that already exists (ADR-0019).

`install` writes the standard into a repository offline. `publish` is the explicit action
(server/key resolve from args, then env, then the stored connection); `watch` is the optional
fallback for live demos and non-git workflows.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import urllib.error
from pathlib import Path

from .token import DESCRIPTOR_FILENAME
from . import gitinfo
from .installer import (
    ENGOS_VERSION,
    InstallError,
    install_standard,
    maybe_self_upgrade,
    upgrade_standard,
)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


def _resolve_connection(args: argparse.Namespace, repo: Path) -> tuple[str | None, str | None]:
    """args → env → the stored local connection (.eos/publish.yaml)."""
    from .local import load_connection

    stored_server, stored_key = load_connection(repo)
    server = args.server or os.environ.get("EOS_SERVER") or stored_server
    key = args.key or os.environ.get("EOS_PUBLISH_KEY") or stored_key
    return server, key


def _publish(args: argparse.Namespace) -> int:
    from .publisher import Publisher

    repo = Path(args.repo).expanduser().resolve()
    server, key = _resolve_connection(args, repo)
    if not server or not key:
        print("error: no connection - run `eos connect` once, or pass --server/--key "
              "(or set EOS_SERVER/EOS_PUBLISH_KEY)", file=sys.stderr)
        return 1

    log = (lambda _msg: None) if args.quiet else print
    if args.if_changed:
        # Branch policy (ADR-0019 section 4). Event-driven publishing respects it; an explicit
        # `publish` does not, because the user asked. Silent on a mismatch: a message on every
        # feature-branch commit would be noise the developer learns to ignore.
        from .local import load_branch

        configured = load_branch(repo)
        current = gitinfo.current_branch(repo)
        if configured and current and configured != current:
            return 0

    publisher = Publisher(repo, server, key, log=log)
    if args.if_changed:
        outcome = publisher.publish_if_changed()
        # The permanent update loop: every publish event also keeps the repo's
        # EOS standard current with the Factory running it. Never blocks the event.
        try:
            maybe_self_upgrade(repo, log=log)
        except Exception:  # noqa: BLE001 — self-upgrade must never break publishing
            pass
        return 0 if outcome != "error" else 1
    # Explicit publish ignores the digest — the user asked, so send.
    from .local import save_last_digest
    from .client import PublishClientError, package_protocol, send
    from .publisher import content_digest

    try:
        payload = package_protocol(repo)
    except PublishClientError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    log(f"Publishing {len(payload.files)} protocol files for '{payload.project}' "
        f"(v{payload.engos_version}) to {server} ...")
    try:
        result = send(server, key, payload)
    except urllib.error.HTTPError as e:
        print(f"error: publish rejected ({e.code}): {e.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 — surface any transport error to the user
        print(f"error: could not reach {server}: {e}", file=sys.stderr)
        return 1
    save_last_digest(repo, content_digest(payload))
    log(f"OK: {result.get('message')} ({result.get('files_written')} files)")
    return 0


def _watch(args: argparse.Namespace) -> int:
    from .watch import Watcher

    repo = Path(args.repo).expanduser().resolve()
    server, key = _resolve_connection(args, repo)
    if not server or not key:
        print("error: no connection - run `eos connect` once, or pass --server/--key "
              "(or set EOS_SERVER/EOS_PUBLISH_KEY)", file=sys.stderr)
        return 1
    watcher = Watcher(repo, server, key, poll=args.poll, settle=args.settle)
    try:
        watcher.run()
    except KeyboardInterrupt:
        print("\nStopped watching.")
    return 0


def main(argv: list[str] | None = None) -> int:
    # Console safety: glyphs in output (checkmarks etc.) must never crash a cp1252
    # console or a piped git hook — degrade characters, don't die.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (OSError, ValueError):
                pass
    parser = argparse.ArgumentParser(prog="eos", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inst = sub.add_parser("install", help="Install the EOS standard into an existing repo.")
    inst.add_argument("--into", required=True, help="Path to the existing target repository")
    inst.add_argument("--name", required=True, help="Product display name")
    inst.add_argument("--slug", required=True, help="Product slug (lowercase, hyphens)")
    inst.add_argument("--owner", default="Founding Engineer")
    inst.add_argument("--commit", action="store_true", help="git add + commit the install")

    conn = sub.add_parser("connect", help="Connect this repository to a project EOS already has. Import one file; everything else is derived.")
    conn.add_argument("descriptor", nargs="?", default=None,
                      help=f"Path to the connection file downloaded from EOS "
                           f"(default: {DESCRIPTOR_FILENAME}, found in this directory, the "
                           f"repository root, or Downloads)")
    conn.add_argument("--repo", default=None, help="Repository to connect (default: discovered from the working directory)")
    conn.add_argument("--token", default=None, help="Connection token instead of a file (AUTOMATION ONLY - lands in shell history)")
    conn.add_argument("--yes", action="store_true", dest="assume_yes", help="Skip the confirmation (for automation)")
    conn.add_argument("--server", default=None, help="Fallback server when a bare publish key is used")

    pub = sub.add_parser("publish", help="Publish this repo's .engos protocol to EOS Cloud (explicit action).")
    pub.add_argument("--repo", default=".", help="Path to the EOS-native repo (default: cwd)")
    pub.add_argument("--server", default=None, help="EOS server base URL (or $EOS_SERVER, or the stored connection)")
    pub.add_argument("--key", default=None, help="Project publish key (or $EOS_PUBLISH_KEY, or the stored connection)")
    pub.add_argument("--if-changed", action="store_true", dest="if_changed",
                     help="Skip when the engineering layer is unchanged (what event triggers use)")
    pub.add_argument("--quiet", action="store_true", help="Only errors (for hooks)")

    upg = sub.add_parser("upgrade", help="Refresh EOS-stamped artifacts (CLAUDE.md, hook) in an already-installed repo. Never touches authored content.")
    upg.add_argument("--repo", default=".", help="Path to the EOS-native repo (default: cwd)")

    watch = sub.add_parser("watch", help="Watch the repo and publish automatically when the engineering layer settles.")
    watch.add_argument("--repo", default=".", help="Path to the EOS-native repo (default: cwd)")
    watch.add_argument("--server", default=None, help="EOS server base URL (or $EOS_SERVER)")
    watch.add_argument("--key", default=None, help="Project publish key (or $EOS_PUBLISH_KEY)")
    watch.add_argument("--settle", type=float, default=2.0, help="Seconds of quiet before publishing (default 2)")
    watch.add_argument("--poll", type=float, default=1.0, help="Seconds between change checks (default 1)")

    args = parser.parse_args(argv)
    if args.command == "publish":
        return _publish(args)
    if args.command == "connect":
        from .connect import ConnectAborted, run_connect

        default = args.server or os.environ.get("EOS_SERVER", "")
        try:
            return run_connect(args.descriptor, args.token, args.repo,
                               default_server=default, assume_yes=args.assume_yes)
        except ConnectAborted as e:
            print(f"{e}", file=sys.stderr)
            return 1
    if args.command == "upgrade":
        repo = Path(args.repo).expanduser().resolve()
        try:
            actions = upgrade_standard(repo)
        except InstallError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        from .local import save_stamp
        from .installer import STANDARD_STAMP
        save_stamp(repo, STANDARD_STAMP)
        print(f"Upgraded the EOS standard in {repo}:")
        for a in actions:
            print(f"  - {a}")
        return 0
    if args.command == "watch":
        return _watch(args)
    if args.command != "install":
        parser.print_help()
        return 2

    root = Path(args.into).expanduser().resolve()
    try:
        written = install_standard(root, name=args.name, slug=args.slug, owner=args.owner)
    except InstallError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"Installed the EOS standard (protocol v{ENGOS_VERSION}) into {root}:")
    for rel in written:
        print(f"  + {rel}")
    if args.commit:
        _git(root, "add", "-A")
        _git(root, "-c", "user.name=EOS Factory", "-c", "user.email=factory@eos.local",
             "commit", "-m", f"Install Engineering OS standard (protocol v{ENGOS_VERSION})")
        print("Committed the install.")
    print(f"\n{args.name} is now Engineering OS-native. Register it in EOS to project it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
