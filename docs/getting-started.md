# Getting started

From nothing to a connected repository. Ten minutes, most of it reading.

## Before you start

**You need an AI coding assistant for this to be worth doing.** Claude Code, Codex, Cursor,
Gemini CLI, or similar. EOS exists to give that assistant memory across sessions. Without one,
you are installing a discipline with no reader.

You also need:

- **git**, and a repository to connect. It does not need to be empty, old, documented, or
  tidy. An existing project is the normal case.
- **An account** on an EOS deployment — [eos.manaaki.in](https://eos.manaaki.in), or your own
  (see [self-hosting](./self-hosting.md)).

## 1. Install the CLI

Open **[Releases](https://github.com/MotivatedNaveen/eos-cli/releases/latest)**, download the
one file for your machine, and put it on your `PATH`. A single file — no runtime, no package
manager, nothing else installed.

The per-platform commands, the macOS quarantine step, and checksum verification are in
**[Installing](../README.md#installing)**.

Check it before going further:

```sh
eos --help
```

If that prints usage, you are ready. If your terminal says *command not found*, the binary is
not on your `PATH` — the README covers that, and also how to skip `PATH` entirely.

## 2. Create an account and a project

Sign up, verify your email address, and you land in your own organization — nobody has to
approve you or set anything up.

Create a project. You type **one thing**: a name. EOS derives the identifier from it, creates
the project, and mints its first publish key.

You are then offered a **connection file**, `eos-project.json`, to download. It looks like
this:

```json
{
  "version": 1,
  "server": "https://eos.manaaki.in",
  "project": "hospitality-management",
  "display_name": "Hospitality Management",
  "publish_key": "eospk_..."
}
```

**Download it now.** It is shown once and cannot be shown again: the server stores only a hash
of the key, so there is nothing to re-serve. If you lose it, generate another connection and
revoke the old one — keys are cheap.

Treat it like a password. It is a credential that can replace one project's engineering
memory.

## 3. Open a terminal and go to your repository

**This step decides which repository gets connected.** `eos` acts on the directory you are
standing in — it does not ask you which project you mean, because you are already in it.

```sh
cd /path/to/your/repository
```

Confirm you are in the right place. Both of these should describe the project you mean:

```sh
pwd            # the path you expect
git status     # "On branch main", and your files
```

If `git status` says *"not a git repository"*, you are in the wrong directory — `cd` again.
EOS publishes on commit, so it needs the repository itself, not a folder beside it.

## 4. Connect

```sh
eos connect
```

It finds the downloaded file — in the current directory, the repository root, or your
Downloads folder — and shows you what it is about to do:

```
  Repository    Hospitality Management
                /home/dana/work/hospitality-management
  Organization  Dana Rivera
  Project       hospitality-management
  Publishes to  https://eos.manaaki.in
  Publishes on  main
  From          /home/dana/Downloads/eos-project.json

Connect this repository? [Y/n]
```

Everything above the prompt was discovered or read from the file. Nothing has been written to
your repository yet. If any line is wrong, say no — nothing is changed.

Then:

```
Setting up the engineering layer ...
  12 files created
  connection stored in .eos/ (gitignored - the key is never committed)
  commit hook installed - commits on 'main' publish automatically
Publishing ...
  OK: published 12 files for 'hospitality-management'
  connection file used and deleted (eos-project.json - it held the key)

Connected. hospitality-management publishes to https://eos.manaaki.in on every commit to 'main'.

  Read       1,284 commits since 2019-03-04 - 7 contributors, last change 2026-07-26
  Found      23 documents under docs/, 11 of them decision-shaped
  Left alone ARCHITECTURE.md, documentation/ (4 documents)
             (EOS reads docs/, .engos/ and discovery/ only)
  Published  27 files

EOS is now publishing engineering memory this repository already had.
  https://eos.manaaki.in/hospitality-management
```

## 5. Read what it wrote

Two things are worth opening.

**`docs/journal/<today>-eos-connected.md`** — a record of what EOS found in your repository on
the day it arrived. Its history, its shape, the documentation you already had, what was left
alone, and a section titled *"What EOS still does not know"* listing the things no tool can
derive: why anything is the way it is, what the product does, what is in flight, where it is
going.

That section is the honest one. Those files exist and are empty, and they are empty on
purpose — a plausible roadmap nobody wrote is worse than no roadmap, because you would have to
find out it was fiction.

**`CLAUDE.md`** — instructions for your AI assistant, generated from the standard. It explains
the layers, how to record a decision, and that decisions are gated: an assistant proposes, a
human accepts.

If you use something other than Claude Code, this file is still the right content — EOS just
does not yet write it to your tool's own instruction path. Point your assistant at it, and see
[AI adapters](./ai-adapters.md) for why, and for what "support" means.

## 6. Commit

```sh
git add -A
git commit -m "Connect to Engineering OS"
```

That commit publishes itself. So does every commit after it that changes `.engos/`, `docs/` or
`discovery/`. A commit that only touches code sends nothing — the hook compares a digest and
exits.

You will not run `eos` again.

## 7. Write the first thing only you know

Open `docs/constitution/charter.md` and answer one question: **why does this exist?**

Then, next time you make a real decision — a rejected approach, a constraint that forced an
awkward design — write it as an ADR in `docs/decisions/`. Or let your assistant write it and
accept it yourself.

That is the whole loop. Everything else compounds from there: each publish makes the next
session better informed, because the thing your assistant reads at the start of it is larger
and truer than it was.

## What to do if something goes wrong

| Symptom | Cause |
|---|---|
| `That connection file names project 'x', but its key publishes to 'y'` | The file was edited, or two downloads crossed. Download a fresh one. |
| `This repository already publishes as 'x'` | You are connecting a repository that belongs to another project. Nothing was changed. |
| `Found more than one eos-project.json` | Name the one you mean: `eos connect path/to/file.json`. |
| `git was not found on this machine` | EOS publishes on commit, so it needs git. |
| `This is not a git repository` | You are not in the repository. `cd` into it and check `git status`. |
| `No connection file at …` | The download did not land where you are looking. Pass the path: `eos connect ~/Downloads/eos-project.json`. |
| The commit hook prints an error | Publishing failed; your commit succeeded. Run `eos publish` to see the full message. |
| `Connected, but the first publish did not go through` | The connection is stored and the hook will retry on your next commit. |

More in the [FAQ](./faq.md).

## What it should look like afterwards

[`docs/example/`](./example/) is a real engineering layer, copied from an actual `eos connect`
run — including the empty files, which are empty on purpose.
