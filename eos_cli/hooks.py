"""Git hook installation — publishing rides the commit, the natural engineering event.

`connect` installs a post-commit hook so every commit that changed the engineering layer
publishes itself. It always exits 0: publishing must never make a commit fail or feel slow
to retry. It is clearly marked, so we can recognise and refresh our own hook without
clobbering someone else's.

**The hook names an absolute path to the `eos` it was installed by.** Git runs hooks in a
minimal shell whose PATH is not the one the developer sees — most visibly on Windows, where
a hook that said `eos publish` would work when tested by hand and silently do nothing on
every real commit. The absolute path is resolved once, at install; a PATH lookup is kept as
the fallback for the case where the executable later moves, because a hook that finds the
wrong `eos` is still better than one that finds none.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

_MARKER = "# EOS post-commit hook"


class HookError(RuntimeError):
    pass


def eos_command() -> str:
    """The absolute path to this installation's `eos`, or the bare name as a last resort.

    Three cases, in the order they are likely: a frozen binary (the executable *is* `eos`),
    a console script beside the running interpreter, and a source checkout — where there is
    no `eos` on disk at all and the hook has to re-enter through the interpreter.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).as_posix()

    exe = "eos.exe" if os.name == "nt" else "eos"
    beside = Path(sys.executable).parent / exe
    if beside.is_file():
        return beside.as_posix()

    found = shutil.which("eos")
    if found:
        return Path(found).as_posix()

    # Not installed — running from a checkout. Name the interpreter and the module, so a
    # contributor's own repositories keep publishing without a pip install.
    return f'"{Path(sys.executable).as_posix()}" -m eos_cli'


def _hook_script(repo: Path) -> str:
    command = eos_command()
    if not command.startswith('"') and " " in command:
        command = f'"{command}"'
    return (
        "#!/bin/sh\n"
        f"{_MARKER} - publish the engineering protocol when it changed.\n"
        "# Reads the connection from <repo>/.eos/publish.yaml. Always exits 0:\n"
        "# publishing must never make a commit fail or feel slow to retry.\n"
        f'{command} publish --repo "{Path(repo).as_posix()}" --if-changed --quiet\n'
        "exit 0\n"
    )


def install_post_commit(repo: Path) -> Path:
    """Install (or refresh) our post-commit hook. Refuses to clobber a foreign hook."""
    hooks_dir = Path(repo) / ".git" / "hooks"
    if not hooks_dir.is_dir():
        raise HookError(f"{repo} is not a git repository (no .git/hooks).")
    path = hooks_dir / "post-commit"
    if path.exists() and _MARKER not in path.read_text(encoding="utf-8", errors="replace"):
        raise HookError(
            f"A post-commit hook already exists at {path} and it isn't EOS's. "
            "Add this line to it yourself:\n  "
            + _hook_script(repo).splitlines()[-2]
        )
    path.write_text(_hook_script(repo), encoding="utf-8", newline="\n")
    try:
        path.chmod(0o755)  # no-op on Windows, required on POSIX
    except OSError:
        pass
    return path
