# FAQ

Including the answers that are not flattering.

## Is this useful without an AI coding assistant?

**Probably not.** You could use it as a disciplined place to record decisions, and some teams
would get value from that alone — but you would be adopting a workflow whose payoff is
designed to arrive somewhere else.

Everything here is shaped by one problem: an assistant starts each session knowing what your
code does and nothing about why. If you do not have that problem, most of the design will look
like overhead, because for you it is.

## Does EOS upload my source code?

No. Three directories are read and published:

```
.engos/        docs/        discovery/
```

Nothing else is read, packaged or sent. Not your source, not your README, not your CI config,
not `CLAUDE.md`. `eos connect` prints what it left alone rather than quietly taking a subset,
and the server rejects any path outside those roots.

You can verify this yourself: `eos_cli/client.py` is 75 lines and the directory list is a
constant on line 18.

## What exactly can the publish key do?

Replace one project's engineering memory, in one organization. That is all.

It grants no read access, no administrative capability, and nothing outside its project. The
server stores only a SHA-256 of it, so a database leak exposes no working credential. Several
keys can be live at once — that overlap is how rotation stays zero-downtime.

If a key leaks, revoke it in EOS. Anything publishing with it stops immediately.

## Is anything sent when I commit code?

No. The hook packages the engineering layer, compares a digest with the last publish, and
sends nothing when it is unchanged. A commit that only touches source code costs a hash
comparison.

## Will a failed publish break my commit?

No. The hook always exits 0, and the publisher explains failures rather than raising. A commit
that triggered a publish completes regardless — the next commit retries.

## What if my repository already has ADRs and documentation?

Then you are the case this is built for. `eos connect` leaves an existing engineering layer
alone, publishes what is already under `docs/`, and tells you what it found:

```
  Found      23 documents under docs/, 11 of them decision-shaped
```

Decision-shaped files are recognised by convention and **counted, never parsed**. Your ADRs
keep whatever format they have; EOS does not rewrite them into its own.

## What if my documentation is not in `docs/`?

It is not published, and `eos connect` says so by name:

```
  Left alone ARCHITECTURE.md, documentation/ (4 documents)
```

Move it under `docs/` and commit if you want EOS to hold it. Nothing is moved for you.

## Which branch publishes?

Exactly one, recorded when you connect, defaulting to the repository's default branch. The
hook exits silently on any other.

Not a list. "Which state is EOS showing?" must have one answer, and any set larger than one
reintroduces last-writer-wins between its members. Something on a feature branch has not been
decided yet; what is on the publishing branch is what the team agreed is true. Change it in
`.eos/publish.yaml`.

## Can I use this from CI instead of a commit hook?

Yes, and for a team you probably should — a commit hook lives in one clone, so every developer
would need their own. Set the publish key as a CI secret and run `eos publish` in the
pipeline.

## What happens if two people publish at once?

Last write wins. There is no ordering guarantee and no concurrency control, and the protocol
says so explicitly rather than implying safety it does not provide.

Publish from one place — one branch, or CI rather than developer machines — if you need a
single coherent published state.

## Does EOS have access to my GitHub account?

No. There is no OAuth, no GitHub App, no repository access, and no webhook. EOS never learns
which repository published — it cannot enumerate, clone or read anything of yours.

The only thing that crosses the wire is a payload your machine constructed, authenticated by a
key you can revoke.

## Can I self-host?

Yes. See [self-hosting](./self-hosting.md).

## Why is there no licence?

Because choosing one is easy to do and hard to undo, and it has not been decided. The
[LICENSE](../LICENSE) file says exactly what that means for you. If you need certainty before
depending on this, open an issue — a licence question from a real user is the fastest route to
getting one chosen.

## Why is the CLI written in Python?

Because the server is, and one definition of the engineering standard is better than two.

It should not matter to you: the intended distribution is a single-file binary with no runtime
to install, and most adopters will be working in .NET, Node, Java or Go and should never learn
what language EOS is written in. Until those binaries are published, the Python requirement is
a real cost and is marked as such in the README.

## Can I write my own client?

Yes, and the specification exists for that reason. [`docs/protocol.md`](./protocol.md) is
written so that a minimal client can be implemented from it alone, without reading any EOS
code. This CLI is the reference implementation, not a privileged one.

If you write one, an issue saying so would be genuinely useful — the specification's own
acceptance criterion is that two independent implementations interoperate.

## What does EOS do with my engineering memory?

Projects it: a dashboard, a library, capability and roadmap views, freshness. It does not
train on it, does not aggregate across tenants, and does not read it into any model.

## Is this production-ready?

The CLI works end to end and is used daily against a live deployment. It is version 0.1.0, no
binary has been published, and the licence is undecided. Judge accordingly.

## How do I disconnect?

Delete `.eos/` and `.git/hooks/post-commit`, and revoke the key in EOS. Your engineering
memory stays where it always was — in your repository.
