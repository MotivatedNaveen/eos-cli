# Changelog

Notable changes to the EOS CLI. Format follows [Keep a Changelog](https://keepachangelog.com/);
versioning follows [Semantic Versioning](https://semver.org/).

Three version numbers exist in EOS and are easy to confuse. This file tracks only the first:

| Version | Versions what |
|---|---|
| **This CLI** (`0.1.0`) | the client's own releases |
| `engos_version` (`0.1`) | the `.engos` **content schema**, in the manifest and every payload |
| standard stamp (`2026-07-27.1`) | the artifacts the CLI installs — assistant instructions, commit hook |

## [0.1.0] — 2026-07-27

### First public release

The first tagged release. Single-file executables for Linux, macOS (Apple silicon) and Windows,
with SHA-256 checksums, from the Releases page. No runtime to install.

**Added**

- `eos connect` — imports a one-time connection file, seeds the engineering layer if the
  repository has none, stores the credential locally (gitignored), installs a `post-commit`
  hook, and publishes once. Finds `eos-project.json` in the working directory, the repository
  root, or Downloads without being told where it is.
- A first journal entry derived from the repository itself: history, contributors, languages,
  what documentation already existed, what was left alone, and an explicit account of what
  cannot be derived. Written once and never regenerated.
- Exclusion reporting. `connect` names engineering-looking content outside the published roots
  (`documentation/`, root-level markdown) and any file inside them that is not valid UTF-8,
  rather than dropping it silently — publish-protocol §5.
- `eos publish` — explicit publish. `--if-changed` compares a content digest and sends nothing
  when the engineering layer is unchanged; this is what the commit hook runs.
- `eos upgrade` — refreshes only what the CLI owns (assistant instructions, commit hook).
  Never writes to `.engos/`, `docs/` or `discovery/`.
- `eos watch` — a polling fallback for non-git workflows.
- `eos install` — writes the engineering standard into a repository offline.
- Single-file binaries for Linux, macOS (Apple silicon) and Windows, built per platform with
  SHA-256 checksums. **No Intel Mac build** — the `macos-13` runner label no longer allocates,
  and a matrix job that never starts would block every release. Build from source meanwhile. A `v*` tag attaches them to a GitHub Release.
  The binaries are unsigned: macOS quarantines a browser-downloaded copy and Windows
  SmartScreen may warn. Both are documented in the README rather than left to be discovered.
- `docs/ai-adapters.md` — what "supported" means, why Claude Code works today, and what an
  adapter for another assistant has to do.
- `docs/example/` — a real engineering layer, copied from an actual `eos connect` run.

**Security**

- A publish key is never sent over plain HTTP except to `localhost`.
- The connection file is deleted once used — a spent credential, and `eos-project.json` is
  added to `.gitignore` meanwhile.
- `--token` warns that it has entered shell history; the interactive path reads through
  `getpass` and does not echo.
- Server-supplied template paths are validated before anything is written: no absolute paths,
  no traversal, nothing outside the engineering roots.

**Notes on what this deliberately does not do**

- It never creates a project. Projects and credentials are created in EOS.
- It never invents engineering memory. What it cannot derive it leaves empty and says so.
- A failed publish never fails a commit — the hook always exits 0.
