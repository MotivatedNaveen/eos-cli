"""The frozen binary's entry point.

PyInstaller runs a *script*, not a module, and a script has no parent package — so pointing
it at `eos_cli/__main__.py` makes every relative import inside the package fail. Importing
through the package from a one-line launcher is what keeps `eos_cli` a normal package with
normal imports, rather than one contorted to survive being frozen.
"""

from eos_cli.cli import main

raise SystemExit(main())
