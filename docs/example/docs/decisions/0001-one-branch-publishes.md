# ADR-0001: Exactly one branch publishes engineering memory

> **Status:** accepted
> **Date:** 2026-07-28 · **Owner:** Dana Rivera · **Layer:** Opinionated

## Context

Our `post-commit` hook fired on every branch. Publishing replaces a project's engineering
memory wholesale, so a commit on a feature branch overwrote what was published from `main` —
and the next commit on `main` overwrote that back.

Nobody noticed for a week. It is not a merge conflict; it is the projection flickering between
two realities with the last committer winning, which looks like flakiness rather than a bug.

## Decision

**One branch publishes, recorded when the repository is connected. The hook exits silently on
every other branch.**

Not a configurable set of branches. "Which state is EOS showing?" must have exactly one answer,
and any set larger than one reintroduces last-writer-wins between its members — less often, and
therefore more confusingly.

## Alternatives considered

- **Publish from every branch, last write wins.** Rejected: this is the bug, not a design.
- **A set of publishing branches.** Rejected: same incoherence, rarer, harder to diagnose.
- **Merge published states.** Rejected: engineering memory on a feature branch has not been
  agreed yet. Merging it would publish proposals as though they were decisions.

## Consequences

- **Positive:** what EOS shows is what the team has agreed is true, because that is what is on
  the publishing branch. Feature-branch churn is invisible, correctly.
- **Negative:** a decision written on a long-lived branch is not visible in EOS until it
  merges. We accept that — it is not decided until it merges either.
- **Note:** the branch lives in `.eos/publish.yaml` and is local, so a teammate who connects
  the same repository chooses again. Publishing from CI instead makes it one answer for
  everyone.
