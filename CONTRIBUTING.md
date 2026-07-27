# Contributing

## Read this first: where the code lives

`eos_cli/`, `pyproject.toml`, `eos.spec` and `eos_launcher.py` are **mirrored verbatim** from
the Engineering OS repository, which is private and holds the test suite. This repository
builds and releases the binaries.

That has a practical consequence: **a pull request changing `eos_cli/` cannot be merged here
directly.** It has to be applied upstream, tested against the suite, and mirrored back. That
is not a formality — the CLI has invariants (it imports no server package, has exactly one
third-party dependency, installs a hook that names an absolute path) that are enforced by
tests living upstream.

So the most useful contributions here, roughly in order:

| | |
|---|---|
| **Issues** | A bug with a reproduction is worth more than a patch, because the patch has to be re-derived upstream anyway. |
| **Documentation** | Everything outside `eos_cli/` lives here and is edited here. Corrections welcome directly. |
| **Protocol feedback** | If the specification is ambiguous, that is a real defect. See below. |
| **Another implementation** | The specification's acceptance criterion is untested. See below. |
| **An assistant's instruction mechanism** | If `docs/ai-adapters.md` names the wrong file for your tool, correcting it is most of the work of the adapter. |
| **Code patches** | Welcome, but open an issue first so the change can be applied upstream where the tests are. |

Mirrored files are marked in this list; if you are unsure, check whether the path starts with
`eos_cli/`.

## Reporting a bug

Include:

- what you ran, and the full output — the CLI is written to print actionable messages, and if
  yours was not actionable that is itself the bug
- your OS and Python version, or the binary you downloaded
- what the repository looked like: had it been connected before, did it already have `docs/`,
  did it have commits

Anything that produced a **traceback** is a bug regardless of the cause. The CLI runs in front
of someone thirty seconds into trying EOS for the first time, and a stack trace is never the
right answer.

## Ambiguity in the protocol is a defect

[`docs/protocol.md`](docs/protocol.md) is meant to be sufficient on its own: a minimal client
implementable from it alone, without reading any EOS code, interoperating with the same
deployment as this one.

If you tried and had to guess — or had to read `eos_cli/` to work something out — the
specification is wrong, not you. Open an issue saying what you had to guess. That is the most
valuable feedback this repository can receive, because the failure mode of a specification is
that the code becomes the real answer and nobody notices.

## Writing another client

Encouraged. This CLI is the reference implementation, not a privileged one — the wire contract
is one endpoint, one header, three JSON fields.

If you build one, open an issue saying so. The specification requires that two independent
implementations produce equivalent results against the same deployment, and that has not been
tested against a second implementation.

## Development

Python is the **contributor** path. Users download a binary and never install a runtime — if
you find yourself writing a document that tells a user to `pip install`, that is a bug in the
document.

```sh
git clone https://github.com/MotivatedNaveen/eos-cli.git
cd eos-cli
pip install -e .
eos --help
```

Build a binary for your platform:

```sh
pip install pyinstaller
pyinstaller --clean --noconfirm eos.spec
./dist/eos --help
```

The tests are upstream. What you *can* check locally:

```sh
python -c "import sys; sys.modules['pydantic'] = None; import eos_cli.cli"
```

That must pass. The CLI's only third-party dependency is PyYAML, and anything else creeping
into the import graph is the beginning of a package nobody can install.

## Style

Match what is there. Concretely, the two things that are not obvious:

**Comments explain *why*, and only where the reasoning is easy to undo by accident.** A comment
restating the code is noise; a comment recording why the obvious approach was rejected is the
most valuable line in the file. Much of `eos_cli/` is annotated that way, and the annotations
exist because each one marks something that was got wrong first.

**Console output is ASCII.** Windows consoles default to cp1252 and git hook output is piped;
an em-dash or a checkmark arrives as a replacement glyph, so a first run looks broken before
it has said anything. There is an upstream test enforcing this.

## Code of conduct

[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Security

Do not open a public issue for anything exploitable — [SECURITY.md](SECURITY.md).

## Licence

Undecided, and that affects you: until a licence exists there is no grant of rights, so a
contribution cannot be licensed to anyone. If you want to contribute code, say so in an issue
— a real contributor waiting is the best reason to settle it. See [LICENSE](LICENSE).
