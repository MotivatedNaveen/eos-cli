# eos

**Engineering Memory for AI-assisted software engineering.**

Your AI coding assistant starts every session knowing what your code does and nothing about
why. `eos` fixes that by keeping the *why* in your repository, in plain text, where both you
and your assistant can read it.

```sh
cd /path/to/your/repository
eos connect
```

That is the only command most people ever run. After it, your engineering memory publishes
itself on every commit.

**It never uploads your source code.** Three directories — `.engos/`, `docs/`, `discovery/` —
and nothing else. [What gets published](#what-gets-published-and-what-does-not).

<!-- RELEASE-PENDING: delete this block when v0.1.0 is tagged. -->
> **Status: pre-release (v0.1.0).** The CLI works end to end and is used daily against a live
> deployment. The first binary release is being prepared — see [Installing](#installing).

---

## Contents

| | |
|---|---|
| [Who this is for](#who-this-is-for) | and who it is not for |
| [The problem](#the-problem-it-addresses) | why this exists |
| [What Engineering Memory is](#what-engineering-memory-is) | and how it differs from documentation |
| [What gets published](#what-gets-published-and-what-does-not) | source code never leaves your machine |
| [Installing](#installing) | one file, no runtime, three platforms |
| [Connecting a repository](#connecting-a-repository) | the complete workflow, step by step |
| [AI assistants](#ai-assistants) | Claude Code today; the adapter model for the rest |
| [What it will not do](#what-it-will-not-do) | deliberate absences |
| [The publish protocol](#the-publish-protocol) | this CLI is the reference implementation |

---

## Who this is for

**Developers who work with an AI coding assistant.** Claude Code, Codex, Cursor, Gemini CLI,
GitHub Copilot — anything that reads your repository and writes code with you.

**If you do not use an AI assistant, EOS will probably not help you.** It is not a wiki, not a
documentation site, and not a knowledge base for humans to browse. It exists because
AI-assisted engineering has one specific structural problem, and every design decision in it
is shaped by that problem. Saying so plainly is more useful than selling you something you do
not need.

## The problem it addresses

An AI assistant starts every session knowing nothing about your project.

It reads your code, so it can see *what* the code does. It cannot see **why**. It does not
know which approach you already tried and rejected, which constraint forced the awkward
design, what is in flight this week, or which parts of the system are load-bearing. That
context lives in closed pull requests, in Slack, in someone's head, and in the last session's
conversation — none of which the next session can reach.

So the same explanations get retyped. The rejected approach gets proposed again. The assistant
confidently contradicts a decision you made two months ago, because nothing recorded it in a
form anything could read.

This is not a model capability problem. A larger context window does not fix it and a better
model does not fix it. **The information does not exist in a form anything can read.**

## What Engineering Memory is

**Documentation describes how to use software. Engineering Memory records the reasoning that
produced it.** Different audience, different lifetime, different content.

| | Documentation | Engineering Memory |
|---|---|---|
| Answers | *How do I use this?* | *Why is it like this?* |
| Written for | users of the software | whoever changes it next — increasingly, an AI assistant |
| Goes stale when | the interface changes | never — a decision is a record of a moment |
| Example | "Call `publish()` with a payload" | "We chose wholesale replace over diffing, because a partial sync leaves a state nobody can reason about" |

It lives in a small, fixed taxonomy:

| | |
|---|---|
| **Decisions** — `docs/decisions/` | Why something is the way it is, and what was rejected |
| **Constitution** — `docs/constitution/` | What holds across the whole project: charter, principles |
| **Standards** — `docs/standards/` | How things are done here — conventions that outlive one decision |
| **Knowledge** — `docs/knowledge/` | Things that are true and written nowhere else |
| **Journal** — `docs/journal/` | Dated, immutable records of what happened |
| **Observations** — `discovery/` | Noticed but not yet settled — the queue before a decision exists |
| **Capabilities** — `.engos/capabilities.yaml` | What the product does, and how mature each part is |
| **Roadmap** — `.engos/roadmap.yaml` | Where it is going |

All of it is markdown and YAML, committed to your git history. See a real one in
[`docs/example/`](docs/example/), and the full explanation in
[Engineering Memory](docs/engineering-memory.md).

### Your repository is the canonical source

EOS holds a *copy* so it can project it. It never owns it.

If every EOS deployment vanished tomorrow, your engineering memory would be untouched, because
it never lived there. That is not a fallback — it is the design. A memory you cannot take with
you is a memory you cannot trust, and something you do not trust, you do not invest in.

## What gets published, and what does not

**Three directories are read and sent. Nothing else is even opened.**

```
.engos/        structured engineering state (YAML)
docs/          the taxonomy — constitution, decisions, standards, knowledge, journal
discovery/     observations
```

Your source code is never read, never packaged, and never transmitted. Neither is anything
outside those three roots — not your README, not your CI configuration, not your assistant's
instruction file.

And `eos connect` tells you what it left alone, rather than quietly taking a subset:

```
  Left alone ARCHITECTURE.md, documentation/ (2 documents)
             (EOS reads docs/, .engos/ and discovery/ only)
```

You do not have to take that on trust. The code that decides what gets sent is 75 lines, and
the directory list is a constant at the top of it —
[`eos_cli/client.py`](eos_cli/client.py), line 18.

## Installing

**Download one file and run it.** No runtime, no package manager, no toolchain — nothing else
gets installed on your machine.

### 1. Download

### &nbsp;&nbsp;&nbsp;&nbsp;[⬇&nbsp; Download the latest release](https://github.com/MotivatedNaveen/eos-cli/releases/latest)

Under **Assets** on that page, pick the one file for your machine:

| Your machine | Download |
|---|---|
| **Windows** | `eos-windows-x64.exe` |
| **Mac** — Apple silicon (M1, M2, M3, M4) | `eos-macos-arm64` |
| **Mac** — Intel | `eos-macos-x64` |
| **Linux** — x64 | `eos-linux-x64` |

*Not sure which Mac you have?* Apple menu → About This Mac. "Apple M‑something" is Apple
silicon; "Intel" is Intel. From a terminal, `uname -m` prints `arm64` or `x86_64`.

The file is named by platform so the release page is unambiguous. **You will rename it to
`eos`** — that is part of the one command below, not an extra step.

### 2. Install it

<details open>
<summary><b>Windows</b></summary>

Open PowerShell in the folder you downloaded to, then:

```powershell
$dir = "$env:LOCALAPPDATA\Programs\eos"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Move-Item -Force .\eos-windows-x64.exe "$dir\eos.exe"

# put it on your PATH, once
[Environment]::SetEnvironmentVariable(
  "Path", "$([Environment]::GetEnvironmentVariable('Path','User'));$dir", "User")
```

**Open a new terminal** — `PATH` changes only apply to terminals opened afterwards.

Windows may warn that the file is unrecognised, because the binary is not code-signed. That is
a reputation check, not a detection; [verify the checksum](#verify-what-you-downloaded) if you
want certainty about what you have.

</details>

<details open>
<summary><b>macOS</b></summary>

```sh
chmod +x ~/Downloads/eos-macos-arm64          # or eos-macos-x64 on an Intel Mac
xattr -d com.apple.quarantine ~/Downloads/eos-macos-arm64
sudo mv ~/Downloads/eos-macos-arm64 /usr/local/bin/eos
```

**The `xattr` line is not optional after a browser download.** macOS flags anything a browser
saved, and refuses to run it — *"cannot be opened because the developer cannot be verified"* —
because the binary is not signed by an Apple developer account. That command clears the flag.
(Downloading with `curl` instead never sets it; see below.)

</details>

<details open>
<summary><b>Linux</b></summary>

```sh
chmod +x ~/Downloads/eos-linux-x64
sudo mv ~/Downloads/eos-linux-x64 /usr/local/bin/eos
```

</details>

### 3. Check it worked

```sh
eos --help
```

If that prints usage, you are done. Next: [connect a repository](#connecting-a-repository).

---

<details>
<summary><b>Prefer the terminal?</b> — one command, no browser</summary>

`latest` always resolves to the newest release, so these do not go stale. On macOS this is also
the tidier route: `curl` does not set the quarantine flag a browser does, so there is no
`xattr` step.

```sh
# set FILE for your platform: eos-macos-arm64 | eos-macos-x64 | eos-linux-x64
FILE=eos-macos-arm64

curl -fL -o eos "https://github.com/MotivatedNaveen/eos-cli/releases/latest/download/$FILE"
chmod +x eos
sudo mv eos /usr/local/bin/eos
eos --help
```

```powershell
$dir = "$env:LOCALAPPDATA\Programs\eos"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
Invoke-WebRequest -Uri "https://github.com/MotivatedNaveen/eos-cli/releases/latest/download/eos-windows-x64.exe" -OutFile "$dir\eos.exe"
```

</details>

<details>
<summary><b>Don't want to touch <code>PATH</code>?</b> — you don't have to</summary>

`eos` works from wherever it sits. Run it with a path:

```sh
~/Downloads/eos connect          # .\eos.exe connect on Windows
```

The commit hook it installs records the **absolute path** to the binary, so publishing keeps
working afterwards without `eos` ever being on your `PATH`.

The one catch: move or delete the binary later and that repository stops publishing. Putting it
on `PATH` is the version that survives housekeeping.

</details>

<details>
<summary id="verify-what-you-downloaded"><b>Verify what you downloaded</b> — recommended</summary>

Every release ships `SHA256SUMS` beside the binaries. Running an unsigned binary from the
internet without checking it is a habit worth not having:

```sh
curl -fLO "https://github.com/MotivatedNaveen/eos-cli/releases/latest/download/SHA256SUMS"
shasum -a 256 -c SHA256SUMS --ignore-missing
```

```powershell
(Get-FileHash .\eos.exe -Algorithm SHA256).Hash    # compare against SHA256SUMS
```

</details>

<details>
<summary><b>Build it yourself</b> — contributors</summary>

[CONTRIBUTING.md](CONTRIBUTING.md#building-a-binary) has the four commands. You do not need
this to use EOS.

</details>

<!-- RELEASE-PENDING: delete this block when v0.1.0 is tagged. -->
> **The first release has not been tagged yet**, so the Releases page is empty and the download
> above has nothing behind it. Until it lands, building it yourself is the only route —
> [CONTRIBUTING.md](CONTRIBUTING.md#building-a-binary). This is the only place in the repository
> that fact is recorded.

## Connecting a repository

The complete workflow. Steps 1–3 happen in a browser, steps 4–6 in a terminal.

**1. Create an account** on an EOS deployment — [eos.manaaki.in](https://eos.manaaki.in), or
your own ([self-hosting](docs/self-hosting.md)). Verify your email address. You land in your
own organization; nobody has to approve you.

**2. Create a project.** You type one thing: a name. EOS derives the identifier and mints the
project's first publish key.

**3. Download the connection file** you are offered — `eos-project.json`. It carries the
server address, the project identifier and the credential, so nothing else has to be told to
you.

> It is shown **once**. The server keeps only a hash of the key, so there is nothing to
> re-serve. Lost it? Generate another connection and revoke the old one. Treat it like a
> password.

**4. Open a terminal.**

**5. Change into the repository you want to connect.** `eos` acts on the directory you are
standing in, so this step decides which repository gets connected:

```sh
cd /path/to/your/repository
```

You can confirm you are in the right place — `git status` should describe the project you mean.

**6. Run `eos connect`.**

```sh
eos connect
```

It finds the file you downloaded — in the current directory, the repository root, or your
Downloads folder — and shows you exactly what it is about to do before touching anything:

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

Everything above that prompt was discovered or read from the file. Nothing has been written
yet. If any line is wrong, answer `n` and nothing changes.

After you confirm, it sets up the engineering layer if there is none, writes a first journal
entry describing what it actually found in your repository, stores the credential in `.eos/`
(gitignored — the key is never committed), installs a `post-commit` hook, publishes once, and
deletes the connection file it just spent.

**That is the last time you run `eos`.** From then on, every commit that changes `.engos/`,
`docs/` or `discovery/` publishes itself. A commit that only touches code sends nothing.

Full walkthrough with output and troubleshooting: [Getting started](docs/getting-started.md).

## AI assistants

**Today EOS generates `CLAUDE.md`, and only `CLAUDE.md`.** If you use Claude Code, the
integration is complete. If you use anything else, read on — the honest answer takes a
paragraph.

`.engos/` is the **Engineering Standard**: the structure and rules of engineering memory,
identical for every project and every assistant. An assistant instruction file is an
**adapter** — a translation of that one standard into the mechanism a particular tool reads.
The standard does not change per assistant; only the file it is delivered in does.

That is why adding Codex, Cursor, Gemini CLI or Copilot is a new adapter rather than a new
model of engineering memory — and why, until each adapter is written, EOS declines to claim
support it does not have.

**Your assistant is not blocked meanwhile.** The generated `CLAUDE.md` is plain markdown that
describes the standard; pointing any assistant at it works, it is simply not automatic.

The architecture, what "support" means, and per-tool considerations:
[AI adapters](docs/ai-adapters.md).

## What it will not do

- **It never creates a project.** Projects and credentials are created in EOS. A CLI that could
  create one would make "which repository is this project?" a question with two answers, and
  move provisioning outside the audit log.
- **It never sends a publish key over plain HTTP**, except to `localhost`, where there is no
  network to intercept.
- **It never rewrites what you authored.** `eos upgrade` refreshes the assistant instructions
  and the commit hook. Your `.engos/`, `docs/` and `discovery/` are yours.
- **It never invents engineering memory.** What it cannot derive from a repository, it leaves
  empty and says so. A plausible roadmap nobody wrote is worse than no roadmap, because you
  would have to find out it was fiction.
- **A failed publish never fails your commit.** The hook always exits 0.

## Commands

| Command | What it does |
|---|---|
| `eos connect [file]` | Connect this repository to a project. Finds `eos-project.json` if you don't name it. |
| `eos publish` | Publish now. `--if-changed` skips when the engineering layer is unchanged — what the commit hook uses. |
| `eos upgrade` | Refresh the EOS-owned artifacts. Never touches what you authored. |
| `eos watch` | Watch and publish when the engineering layer settles. A fallback for non-git workflows. |
| `eos install` | Write the engineering standard into a repository offline, without connecting. |

`eos <command> --help` for full arguments.

## The publish protocol

This CLI is the **reference implementation** of the EOS publish protocol, not a privileged
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
| [Engineering Memory](docs/engineering-memory.md) | What it is, what belongs in it, what does not |
| [AI adapters](docs/ai-adapters.md) | Why Claude Code works today and what support means |
| [Example](docs/example/) | A real engineering layer, as generated |
| [The publish protocol](docs/protocol.md) | The wire contract, in full |
| [Self-hosting](docs/self-hosting.md) | Running your own deployment |
| [FAQ](docs/faq.md) | Including the unflattering answers |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). `eos_cli/` is mirrored from the Engineering OS
repository, which holds the test suite, so issues and discussion are more useful here than
patches. Security reports: [SECURITY.md](SECURITY.md).

## Licence

**Not yet chosen.** [LICENSE](LICENSE) says exactly what that means for you — please read it
before depending on this.
