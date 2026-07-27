## What this changes

<!-- One or two sentences. What is different afterwards? -->

## Why

<!-- The reasoning, not the diff. If it fixes a bug, what was the bug? If it was a judgement
     call, what did you rule out? That is the part a reviewer cannot reconstruct. -->

## Type of change

- [ ] Documentation, or something else outside `eos_cli/` — mergeable here
- [ ] A change to `eos_cli/`, `pyproject.toml`, `eos.spec` or `eos_launcher.py`

> **If you ticked the second box:** those files are mirrored verbatim from the Engineering OS
> repository, which holds the test suite. The change has to be applied and tested upstream,
> then mirrored back — so this PR will be used as the description of the change rather than
> merged. That is not a rejection; please do open it. See
> [CONTRIBUTING.md](../CONTRIBUTING.md).

## Checked

- [ ] `pip install -e . && eos --help` runs
- [ ] `python -c "import sys; sys.modules['pydantic'] = None; import eos_cli.cli"` passes
      (no new third-party dependency has entered the import graph)
- [ ] Any console output added is ASCII — a cp1252 terminal must not render it as `?`
- [ ] No credential, path from your machine, or private hostname is in the diff

## Related

<!-- Issue number, or "none". -->
