# Journal: EOS connected to Hospitality Management

> **Date:** 2026-07-27 · **Status:** recorded (immutable) · **Provenance:** derived by `eos connect` — observed, not confirmed

## What EOS found

> Booking, housekeeping and billing for independent hotels.

*— quoted from `package.json`, the one place someone had already written down what this is.*

- **History:** 9 commits between 2025-02-15 and 2026-07-27, 2 contributors — most recently Sam Okafor, Dana Rivera.
- **Languages:** TypeScript (6 files).
- **Where the work happens:** `src`, `docs`, `(root)`, `documentation` (by files changed in recent commits).
- **Also present:** tests, CI, containers, a licence.

## Engineering memory

- **7 documents already under `docs/`** — published to EOS as they are, from now on. Anything in a taxonomy section it recognises (`decisions`, `standards`, `knowledge`, `journal`, `constitution`) also gets a place in the Library.
  `decisions` (4), `guides` (2), `constitution` (1)
- 4 files look like decision records (counted by convention, never parsed — your ADRs stay yours).

## What EOS did not take

EOS publishes `.engos/`, `docs/` and `discovery/` and nothing else. These were left where they are:
- `ARCHITECTURE.md`
- `documentation/ (2 documents)`

Nothing was moved or changed. If any of it is engineering knowledge you want EOS to hold, move it under `docs/` and commit.

## What EOS still does not know

Everything above is *shape* — how big, how old, how active, how it is laid out. Only
people know *intent*, and none of it can be derived from a repository:

- **Why** anything is the way it is → decisions, in `docs/decisions/`
- **What this product does**, and how mature each part is → `.engos/capabilities.yaml`
- **What is in flight right now** → `current_focus` in `.engos/project.yaml`
- **Where it is going** → milestones in `.engos/roadmap.yaml`
- **What is true but written nowhere** → `docs/knowledge/`, `docs/standards/`

Those files exist and are empty. They are empty because EOS refuses to guess: a
plausible roadmap nobody wrote is worse than no roadmap, because you would have to
find out it was fiction.

## What happens now

Every commit to this repository that changes `.engos/`, `docs/` or `discovery/`
publishes itself to EOS. Nothing to run, no daemon. This entry is a record of one
day and is not regenerated — edit it, or leave it and write the next one.

