# A real engineering layer

What `eos connect` leaves in a repository, and what it looks like once someone has used it.

The `.engos/` files, `charter.md` and the journal entry here were **copied verbatim from an
actual `eos connect` run** (only the project name was changed), so they cannot drift from what
the tool produces. The decision and the observation were then authored by hand, because that is
the half no tool can generate.

```
.engos/
├── manifest.yaml       project identity and protocol version
├── project.yaml        status, current focus, owners
├── capabilities.yaml   what the product does — empty until authored
└── roadmap.yaml        milestones — empty until authored
docs/
├── constitution/charter.md              why this exists — a prompt, not an answer
├── decisions/0001-one-branch-publishes.md
└── journal/2026-07-27-eos-connected.md  what EOS found on the day it arrived
discovery/
└── observations/2026-07-28-onboarding-loses-context.md
```

## What to notice

**The generated files are empty where they should be.** `capabilities.yaml` says
`capabilities: []`. `roadmap.yaml` says `milestones: []`. `current_focus` is `''`. The charter
asks a question instead of answering it.

That is not an unfinished install. Nothing in a repository can tell EOS what a product *does*,
what is in flight, or where it is going, so those files ship as labelled slots rather than as
plausible fiction. A roadmap nobody wrote would be worse than no roadmap, because you would have
to discover it was invented.

**The journal entry is entirely derived, and says so.** Its header carries
`Provenance: derived by eos connect — observed, not confirmed`. Every claim in it is checkable:
commit counts, contributor names, languages by file extension, what was already under `docs/`,
and — explicitly — what was left alone and why. It ends with a section titled *"What EOS still
does not know"*.

It is written once and never regenerated. Edit it, or leave it and write the next one.

**The decision records what was rejected.** That is the half people skip and the half that is
worth the most: "we chose one publishing branch" tells your assistant almost nothing, while
"we rejected a configurable set because it reintroduces last-writer-wins less often and
therefore more confusingly" tells it what to do the next time someone proposes exactly that.

**The observation is not a decision.** It records something noticed, including what is *not*
yet known, so it can be triaged rather than lost. Its "What is not yet known" section is the
point — a system that forces every observation to arrive as a conclusion produces conclusions
nobody checked.

## What is not here

Source code. This is the entire engineering layer of a repository that also contains a
TypeScript application, and none of that application appears — nothing outside `.engos/`,
`docs/` and `discovery/` is read or published.

## Trying it

You do not need an EOS account to see this shape in your own repository:

```sh
eos install --into /path/to/a/scratch/repo --name "Scratch" --slug scratch
```

That writes the standard offline, without connecting or publishing anything.
