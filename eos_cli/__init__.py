"""The EOS command-line client — a protocol client, distributable on its own.

This package is the thing a developer installs. It connects a repository to a project EOS
already provisioned, keeps the local connection, and publishes the engineering layer on every
commit. It is the reference implementation of the publish protocol
(`docs/standards/universal/publish-protocol.md`), not a privileged insider: everything it
does, another client could do from that specification alone.

**It imports nothing from `app`.** That is the property that makes it shippable, and
`tests/test_cli_packaging.py` fails the build if it is ever violated. The dependency runs one
way — the server imports `eos_cli.token` and `eos_cli.installer`, because the connection
format and the engineering standard are one definition each and must not exist twice.

Third-party dependencies: **PyYAML, and nothing else.** A CLI that needs a web framework to
run is a CLI nobody can package.
"""

__all__ = ["__version__"]

# Tracks the CLI's own releases. Deliberately not `engos_version` (the content schema) or
# `STANDARD_STAMP` (the artifacts the Factory installs) — three version numbers that answer
# three different questions, and conflating any two of them is how a client ends up claiming
# compatibility it does not have.
__version__ = "0.1.0"
