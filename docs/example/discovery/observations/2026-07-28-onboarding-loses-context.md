# Observation: new joiners re-ask questions our decisions already answer

> **Date:** 2026-07-28 · **Observer:** Sam Okafor · **Status:** open
> **Target:** hospitality-management · **Category:** process
> **Provenance:** human-authored

## What was noticed

Three of the last four new engineers asked why billing runs nightly rather than on checkout.
The answer is in a decision record from 2024. None of them found it; two were told a
half-remembered version by someone who was not there.

The AI assistant does the same thing — it proposes moving billing to checkout roughly once a
month, because the reasoning is in a file it was never pointed at.

## Why it might matter

We have the decision. It is written down, correctly, in the right place. The failure is
entirely in retrieval, which suggests the problem is not "write more down" but "make what is
written reachable at the moment someone is about to contradict it".

## What is not yet known

Whether this is a discoverability problem (nobody searches `docs/decisions/`) or a linking
problem (the decision is not referenced from the code or the capability it governs). Those
have different fixes and we should not guess.

---

*An observation is not a decision. It records something noticed, so it can be triaged rather
than lost — accepted into a decision, folded into a standard, or declined with a reason.*
