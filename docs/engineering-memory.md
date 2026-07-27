# Engineering Memory

What it is, what belongs in it, and — more usefully — what does not.

## The problem, stated precisely

An AI coding assistant reads your repository at the start of every session and knows, with
complete accuracy, **what the code does**. It has no access at all to **why**.

Why is not in the code. It is in a closed pull request from eighteen months ago, in a Slack
thread, in the head of someone who left, and in the last session's conversation — which the
next session cannot reach. So the assistant:

- proposes the approach you already tried and rejected, because nothing recorded the rejection
- contradicts a decision you made in March, confidently, because nothing recorded it
- asks you to re-explain the same constraint every session
- writes code that is locally reasonable and globally wrong, because the global reasoning was
  never written down

None of that is a model capability problem. More context window does not fix it, and a better
model does not fix it. **The information does not exist in a form anything can read.**

Engineering Memory is that information, written down, in your repository, in plain text.

## Why it lives in your repository

Because the alternative fails the only test that matters.

If your engineering memory lives in a platform, then the platform's availability is your
memory's availability, its export format is your exit cost, and its shutdown is your amnesia.
A memory you cannot take with you is a memory you cannot trust — and something you do not
trust, you do not invest in.

So the split is: **your repository is the canonical store; EOS holds a copy so it can project
it.** Markdown and YAML, committed to your git history, readable with `cat`. If EOS
disappeared tomorrow, you would lose a set of views and nothing else.

That is also why publishing is a complete snapshot rather than a sync: there is one direction
of truth, and it points away from the platform.

## The taxonomy

Small and fixed, because a taxonomy that grows is a taxonomy nobody can file into.

### Decisions — `docs/decisions/`

Architecture Decision Records. **Why something is the way it is, and what was rejected.**

The rejected options are the valuable half and the half people skip. "We chose Postgres" tells
your assistant almost nothing. "We chose Postgres over DynamoDB because the reporting queries
are relational and we were not willing to maintain two data models" tells it what to do the
next time someone suggests DynamoDB.

A decision has a status. `proposed` means someone wrote it down; `accepted` means a human
agreed. Assistants may write decisions and may not accept their own — that gate is the point.

### Constitution — `docs/constitution/`

What holds across the whole project regardless of any single decision. The charter (why this
exists), principles, ownership. Short, and changed rarely.

### Standards — `docs/standards/`

How things are done here. Conventions that outlive the decision that introduced them: error
handling, testing approach, API shape.

The distinction from a decision is tense. A decision records a moment — *we chose X, on this
date, over Y*. A standard records an ongoing rule — *this is how we do it*.

### Knowledge — `docs/knowledge/`

Things that are true and written nowhere else. The undocumented behaviour of a dependency, the
reason a workaround exists, the operational fact that only bites at 3am.

If you have ever thought "someone should write that down" — this is where it goes.

### Journal — `docs/journal/`

Dated, immutable records of what happened. Not a changelog of commits: a record of *slices of
work* and what was learned in them.

Immutable matters. A journal you edit is a journal that tells you what you now believe, not
what you believed then — and the difference between those two is often the most valuable thing
in the file.

### Observations — `discovery/observations/`

Things noticed but not settled. The gap before a decision exists.

This is the queue that stops the decision log filling with half-thoughts. An assistant that
notices something wrong files an observation; a human triages it into a decision, a standard,
or nothing.

### Capabilities — `.engos/capabilities.yaml`

What the product actually does, as a structured model: an id, a title, the module it belongs
to, its maturity (`planned` → `available` → `released` → `deprecated`), and **evidence** —
links to the decisions and journal entries that realise it.

The evidence link is what makes the model honest. A capability claiming to be `released` with
nothing supporting it is visible as exactly that.

### Roadmap — `.engos/roadmap.yaml`

Milestones. Identity only — status is derived from the capabilities assigned to them, never
declared. A milestone cannot claim to be done while the capabilities under it are `planned`.

## Prose and model: `docs/` and `.engos/`

`docs/` holds what people write. `.engos/` holds what tools reason about:

```
.engos/
├── manifest.yaml       project identity and protocol version
├── project.yaml        status, current focus, owners
├── capabilities.yaml   what the product does
└── roadmap.yaml        where it is going
```

`current_focus` in `project.yaml` is one sentence: what is in flight *right now*. Replace it,
never append — history belongs in the journal.

You author both halves. EOS reads, validates and projects, and never writes into them.

## What does not belong

Being clear about this matters more than the taxonomy, because the failure mode of a knowledge
system is that it fills with things nobody needed.

- **API documentation and how-to guides.** Documentation describes how to use software.
  Engineering memory records the reasoning that produced it. Different audience, different
  lifetime. Keep your docs site.
- **Meeting notes.** Unless a decision came out of one, in which case write the decision.
- **Status updates.** The capability model and the journal cover this, structurally.
- **Anything secret.** Publish keys, credentials, customer data. EOS reads three directories
  and publishes what is in them — if you put a secret there, it is published. Nothing scans
  for that on your behalf.
- **Source code.** Never read, never sent.
- **Speculation, at decision status.** Write it as an observation.

## How it accumulates

You do not sit down and write engineering memory. The economics do not work and nobody ever
finishes.

It accumulates as a by-product of work you were doing anyway:

1. You and your assistant build something.
2. In the same change, the engineering model changes with it — the capability is updated, a
   decision is written for anything genuinely decided, a journal entry records the slice.
3. You commit. The commit publishes.
4. The next session starts with all of it.

The generated assistant instructions (`CLAUDE.md`) tell your assistant to do step 2 without
being asked. Its writes are marked as AI-authored until a human confirms them, and it cannot
accept its own decisions.

The compounding is the product: every publish makes the next session better informed than the
last, because what the assistant reads at the start of it is larger and truer than it was.

## The two tests

Two questions worth asking of the whole arrangement, because they are the ones that decide
whether it is worth your discipline:

**The Engineering Recovery Test.** If every EOS deployment vanished, could your repositories
fully restore your engineering knowledge? Yes, by construction — it never left them.

**The Platform Recovery Test.** If your repositories vanished, could EOS restore them? **No,
and deliberately so.** EOS is not a backup, does not host your repository, and holds no
credentials to reach it. It holds a projection of what you published.

If those two answers were ever the other way round, something would have gone badly wrong.
