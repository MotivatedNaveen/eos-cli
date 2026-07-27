"""`python -m eos_cli` — the same command as the `eos` executable.

A two-line shim so the implementation lives in an ordinary importable module. Running a
package's `__main__.py` directly gives it no parent package, which is why the frozen binary
enters through `eos_launcher.py` and this file rather than the other way round.
"""

from .cli import main

raise SystemExit(main())
