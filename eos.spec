# PyInstaller spec for the `eos` command.
#
#     pip install pyinstaller && pyinstaller --clean --noconfirm eos.spec
#
# Produces `dist/eos` (`dist/eos.exe` on Windows): one file, no Python required on the target
# machine. That is the point — ADR-0019's context rejects making adopters install a Python
# toolchain to use EOS, and most of them will be .NET, Node, Java or Go engineers who should
# never learn what language EOS is written in.
#
# It also removes the last way a repository can interfere with the CLI: a frozen binary
# resolves imports from its own bundle, so a project containing `app.py` cannot shadow
# anything of ours. See the observation from 2026-07-26.
#
# Built per platform — a binary is not cross-compiled. The release workflow runs this on a
# Linux, a macOS and a Windows runner.

block_cipher = None

analysis = Analysis(
    ["eos_launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    # PyYAML is the only runtime dependency and is found by import tracing. Named here so a
    # build that silently loses it fails loudly instead of shipping a binary that dies on the
    # first manifest it reads.
    hiddenimports=["yaml"],
    hookspath=[],
    runtime_hooks=[],
    # The server half of this checkout must never be pulled in by an accidental import. If
    # one appears, the build fails rather than quietly producing a 40 MB binary carrying a
    # web framework and an ORM. `tests/test_cli_packaging.py` is the fast check; this is the
    # one that cannot be argued with.
    excludes=[
        "app", "fastapi", "starlette", "pydantic", "pydantic_settings", "pydantic_core",
        "sqlalchemy", "alembic", "argon2", "uvicorn", "httpx", "pytest",
        "tkinter", "unittest", "email.mime.audio", "email.mime.image",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    [],
    name="eos",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # compression buys a few MB and costs antivirus false positives
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # it is a command-line tool; a windowed build would hide every message
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
