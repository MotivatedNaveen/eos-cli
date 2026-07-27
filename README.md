# eos

The command-line client for **Engineering OS** — an Engineering Memory platform for
AI-assisted software engineering.

```sh
eos connect
```

One command connects a repository. After that, your engineering memory publishes itself on
every commit, and there is nothing to run.

> **Status: pre-release.** The CLI works end to end and is used daily against a live
> deployment. Binaries and a PyPI package are **not published yet** — see
> [Installing](#installing).

---

## Who this is for

**Developers who work with AI coding assistants** — Claude Code, Codex, Cursor, Gemini CLI,
Copilot, or anything else that reads your repository and writes code with you.

If you do not use an AI assistant, **EOS will probably not help you.** It is not a wiki, not a
documentation site, and not a knowledge base for humans to browse. It exists because
AI-assisted engineering has a specific, structural problem, and everything in it is shaped by
that problem. Saying so plainly is more useful than selling you something you do not need.

## The problem it addresses

An AI assistant starts every session knowing nothing about your project.

It reads your code, so it can see *what* the code does. It cannot see why. It does not know
which approach you already tried and rejected, which constraint made you pick the awkward
design, what is in flight this week, or which parts of the system are load-bearing. That
context lives in closed pull requests, in Slack, in someone's head, and in the last session's
conversation — none of which the next session can reach.

So the same explanations get retyped, the same rejected approach gets proposed again, and the
assistant confidently contradicts a decision you made two months ago because nothing recorded
it in a form it could read.

**Engineering Memory is that context, written down where both you and your assistant can read
it, in your repository, in plain text.**

## What Engineering Memory is

Not documentation. Documentation describes how to use software. Engineering Memory records
the reasoning that produced it, in a small, fixed taxonomy:

| | |
|---|---|
| **Decisions** | Why something is the way it is, and what was rejected. Architecture Decision Records. |
| **Constitution** | The rules that hold across the whole project. Its charter, its principles. |
| **Standards** | How things are done here — conventions that outlive any one decision. |
| **Knowledge** | Things that are true and written nowhere else. |
| **Journal** | Dated, immutable records of what happened and when. |
| **Observations** | Things noticed but not yet settled — the queue before a decision exists. |
| **Capabilities** | What the product actually does, and how mature each part is. |
| **Roadmap** | Where it is going. |

All of it is markdown and YAML, in your repository, committed to your git history. **Your
repository is the canonical store.** EOS holds a copy so it can project it — a hosted
deployment could vanish tomorrow and your engineering memory would be untouched, because it
never lived there.

That is the point of the split, and it is deliberate: a memory you cannot take with you is a
memory you cannot trust.

## What EOS does and does not upload

**Only the engineering layer. Never source code.**

Three directories are read and published, and nothing else:

```
.engos/        structured engineering state (YAML)
docs/          the taxonomy — constitution, decisions, standards, knowledge, journal
discovery/     observations
```

Your source code is never read, never packaged, and never sent. Neither is anything outside
those three roots — not your README, not your CI config, not `CLAUDE.md`. And `eos connect`
tells you what it left alone, rather than quietly taking a subset:

```
  Left alone ARCHITECTURE.md, documentation/ (2 documents)
             (EOS reads docs/, .engos/ and discovery/ only)
```

If a file's bytes are not valid UTF-8, it is reported rather than dropped in silence.

## What `.engos/` is

A small directory of YAML holding the parts of engineering memory that are *structured* rather
than prose — the parts a tool can reason about:

```
.engos/
├── manifest.yaml       project identity and protocol version
├── project.yaml        status, current focus, owners
├── capabilities.yaml   what the product does, with maturity and evidence
└── roadmap.yaml        milestones
```

`docs/` holds the prose; `.engos/` holds the model. Together they are the contract EOS reads
and projects. You author both — EOS validates and displays, and never writes into them.

## What happens during `eos connect`

You create a project in EOS and download a one-time connection file (`eos-project.json`). Then,
in your repository:

```sh
eos connect
```

In order, and nothing touches your working tree until the last four steps:

1. **Finds the connection file** — in the current directory, the repository root, or Downloads.
2. **Validates it** and asks the server which project the credential authorises. If the file
   and the credential disagree, it stops.
3. **Checks your repository** — if `.engos/manifest.yaml` already names a different project, it
   stops and says both names, rather than storing a connection that could never publish.
4. **Shows you what it is about to do** — repository, organization, project, server, branch —
   and waits for you to confirm.
5. **Sets up the engineering layer**, if there isn't one. Existing memory is left alone.
6. **Writes a first journal entry** describing what it found in *your* repository: how long it
   has existed, how many contributors, what languages, what documentation you already had,
   what it left alone, and — explicitly — what it cannot know.
7. **Stores the credential** in `.eos/` and gitignores it. The key is never committed.
8. **Installs a `post-commit` hook** and **publishes once**.

From then on, every commit that changes `.engos/`, `docs/` or `discovery/` publishes itself. No
daemon, no scheduled job, nothing to remember. A commit that only touches code sends nothing.

The connection file is deleted once it has been used — it holds a credential and has exactly
one use.

## AI adapters

Every assistant reads a different instructions file. Claude Code reads `CLAUDE.md`; other
tools read their own. The **adapter** idea is that EOS generates the file *your* assistant
already looks for, from one definition of the standard — so the assistant learns how to
maintain engineering memory as it works, without you writing those instructions yourself.

The generated file tells your assistant to record a decision when it makes one, add a journal
entry for a slice of work, keep the capability model honest, and file an observation when it
notices a gap. Decisions stay gated: an assistant proposes, a human accepts.

**Today the CLI writes `CLAUDE.md` and only `CLAUDE.md`.** Adapters for other assistants are
planned and not built. When they exist they will be listed here; until then, if you use a
different tool, the generated file is still readable and you can point your assistant at it.

## Installing

**Binaries: coming soon.** The release workflow builds single-file executables for Linux,
macOS and Windows with checksums, and no download has been published yet. When one is, it will
appear under [Releases](https://github.com/MotivatedNaveen/eos-cli/releases) and this section
will say so.

**PyPI: coming soon.** `eos-cli` is not on PyPI yet.

Until then, with Python 3.11 or newer:

```sh
git clone https://github.com/MotivatedNaveen/eos-cli.git
cd eos-cli
pip install .
eos --help
```

The only runtime dependency is PyYAML.

## Commands

| Command | What it does |
|---|---|
| `eos connect [file]` | Connect this repository to a project. Finds `eos-project.json` if you don't name it. |
| `eos publish` | Publish now. `--if-changed` skips when the engineering layer is unchanged — what the commit hook uses. |
| `eos upgrade` | Refresh the EOS-owned artifacts (the assistant instructions, the commit hook). Never touches what you authored. |
| `eos watch` | Watch and publish when the engineering layer settles. A fallback for non-git workflows. |
| `eos install` | Write the engineering standard into a repository offline, without connecting. |

`eos <command> --help` for full arguments.

## What it will not do

- **It never creates a project.** Projects and credentials are created in EOS. A CLI that could
  create one would make "which repository is this project?" a question with two answers, and
  move provisioning outside the audit log.
- **It never sends a publish key over plain HTTP**, except to `localhost`, where there is no
  network to intercept.
- **It never rewrites what you authored.** `upgrade` refreshes the assistant instructions and
  the commit hook. Your `.engos/`, `docs/` and `discovery/` are yours.
- **It never invents engineering memory.** What it cannot derive from a repository it leaves
  empty and says so. A plausible roadmap nobody wrote is worse than no roadmap, because you
  would have to find out it was fiction.
- **A failed publish never fails your commit.** The hook always exits 0.

## The publish protocol

This CLI is the **reference implementation of the EOS publish protocol**, not a privileged
insider. The wire contract is specified, and a client in any language can implement it from
[`docs/protocol.md`](docs/protocol.md) alone:

```http
POST {server}/api/publish
Content-Type: application/json
X-Publish-Key: {key}

{"project": "acme-web", "engos_version": "0.1", "files": {"docs/decisions/0001-x.md": "..."}}
```

A publish is a **complete snapshot**: files absent from it are deleted server-side. That makes
it idempotent and safe to retry after a timeout, and it is why exactly one branch publishes.

Anything this client does that the specification does not require is client behaviour, and is
documented as such.

## Documentation

| | |
|---|---|
| [Getting started](docs/getting-started.md) | From nothing to a connected repository |
| [Engineering Memory](docs/engineering-memory.md) | What it is, what belongs in it, and what does not |
| [The publish protocol](docs/protocol.md) | The wire contract, in full |
| [Self-hosting](docs/self-hosting.md) | Running your own deployment |
| [FAQ](docs/faq.md) | Including the honest answers |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Note that `eos_cli/` is mirrored from the Engineering
OS repository, which holds the test suite — so issues and discussion are more useful here than
patches. Security reports: [SECURITY.md](SECURITY.md).

## Licence

Not yet chosen. See [LICENSE](LICENSE) — please read it before depending on this.
