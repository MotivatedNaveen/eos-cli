# Security

## Reporting a vulnerability

Email **motivated.naveen.sharma@gmail.com** with `EOS-CLI SECURITY` in the subject.

Please do not open a public issue for anything exploitable. Include what you found, how to
reproduce it, and what you think the impact is. You will get an acknowledgement within a few
days; there is no bounty programme.

If you are unsure whether something counts, report it. A false alarm costs an email.

## What an attacker gets from a publish key

Stating the blast radius plainly is more useful than a policy.

A publish key authorizes **exactly one action**: replacing one project's engineering memory,
in one organization. It grants no read access, no administrative capability, and nothing
outside its project. It cannot enumerate tenants, cannot reach your repository, and cannot be
escalated.

Someone holding a leaked key can overwrite that project's published memory with anything.
They cannot read your source, and they cannot damage the canonical copy — which is in your git
history, not on the server.

**If a key leaks:** revoke it in EOS. Anything publishing with it stops immediately. Mint a
replacement first if you want zero downtime; overlapping keys are supported for exactly that.

## Where credentials live

| | |
|---|---|
| `.eos/publish.yaml` | the key, in your repository, **gitignored by `connect`** |
| `eos-project.json` | the connection file — **deleted once used** |
| Server-side | a SHA-256 of the key. The raw key is shown once and never stored. |

The connection file is deleted rather than merely gitignored, because gitignoring addresses
the smaller risk: a spent credential sitting in a Downloads folder is the larger one.

## What the CLI will not do

These are enforced in code, not by convention:

- **Never sends a publish key over plain HTTP**, except to `localhost`. A connection file
  naming an `http://` server is refused outright.
- **Never writes a server-supplied path it has not validated.** Template responses are checked
  for absolute paths, `..` traversal, drive letters and anything outside `.engos/`, `docs/`,
  `discovery/` and `CLAUDE.md`. A trusted server is still a server; validating a response is
  not distrust, it is declining to make a trust decision at all.
- **Never echoes a credential.** The interactive path reads through `getpass`; `--token` exists
  for automation and warns that it has entered shell history.
- **Never reads or transmits source code.** Three directories, and nothing else.

## What is *your* responsibility

EOS publishes what is in `.engos/`, `docs/` and `discovery/`. It does not scan for secrets on
your behalf. **If you write a credential into a decision record, it is published.**

Use a secret scanner in CI. That is not a gap this tool intends to close, because a tool that
sometimes catches secrets is worse than one you know does not.

## Supported versions

Pre-release. Only the latest commit on `main` is supported; there are no released versions to
patch yet.
