"""What the repository can be asked about itself, without reading anyone's prose.

Everything here is a directory walk or a file that exists. Nothing is parsed for meaning, no
code is analysed, and no document is interpreted — the point is to say things that are
checkable by the person reading them, because a tool that guesses and is occasionally right
is worse than one that observes and is always right.

The one exception proves the rule: a package manifest's `name` and `description` are quoted,
attributed to the file they came from. That is not derivation, it is *citation* — a human
already wrote down what this project is, and repeating it is honest where inventing it would
not be.

Runs client-side, always. EOS never reads repositories (ADR-0014); this is the machine that
has one, describing it to itself.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# The published roots (publish-protocol §5). Everything else in the repository is a thing EOS
# will not take, and saying so is the difference between a tool that quietly took a subset
# and a tool that told you where its boundary is.
PUBLISHED_ROOTS = (".engos", "docs", "discovery")

# Never walked. Vendor directories are somebody else's repository and dwarf the real one.
_SKIP_DIRS = {
    ".git", ".hg", ".svn", ".eos", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", "out", "target", "bin", "obj", ".next", ".nuxt", ".idea", ".vscode",
    ".pytest_cache", ".ruff_cache", ".mypy_cache", "vendor", "Pods", ".gradle", ".tox",
}

_LANGUAGES = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript", ".js": "JavaScript",
    ".jsx": "JavaScript", ".cs": "C#", ".java": "Java", ".kt": "Kotlin", ".go": "Go",
    ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".scala": "Scala",
    ".c": "C", ".h": "C", ".cpp": "C++", ".hpp": "C++", ".cc": "C++", ".m": "Objective-C",
    ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell", ".ex": "Elixir", ".dart": "Dart",
    ".vue": "Vue", ".svelte": "Svelte", ".r": "R", ".lua": "Lua", ".pl": "Perl",
}

# Directories whose name says "engineering knowledge lives here" but which the protocol does
# not take. Naming them is the whole value of the exclusion report — a developer who wrote
# their architecture notes in `documentation/` should learn that on day one, not in a support
# thread three weeks later.
_DOC_LIKE = {"documentation", "doc", "wiki", "adr", "adrs", "architecture", "design",
             "rfc", "rfcs", "decisions", "notes", "handbook", "guides"}

# ADRs are recognised by convention and **counted, never parsed**. Reading someone's decision
# records into our model would be inventing engineering memory rather than projecting it.
_DECISION_NAME = re.compile(r"^(adr[-_ ]?\d+|\d{3,4}[-_].+)\.mdx?$", re.IGNORECASE)
_DECISION_DIRS = {"decisions", "adr", "adrs"}
# `2026-07-06-something.md` matches the `NNNN-title.md` ADR convention and is a dated journal
# entry. Counting a team's journal as their decision record would overstate exactly the thing
# this number exists to report honestly.
_DATED_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}[-_]")

_CI_MARKERS = (".github/workflows", ".gitlab-ci.yml", "azure-pipelines.yml", "Jenkinsfile",
               ".circleci/config.yml", ".travis.yml", "bitbucket-pipelines.yml")
_TEST_DIRS = {"tests", "test", "spec", "specs", "__tests__"}


@dataclass(frozen=True)
class Inventory:
    """Shape. Never intent."""

    top_level: tuple[str, ...] = ()
    languages: tuple[tuple[str, int], ...] = ()      # (language, file count), largest first
    readme: str = ""                                 # the README's first heading, if any
    stated_name: str = ""                            # from a package manifest
    stated_purpose: str = ""                         # from a package manifest
    stated_by: str = ""                              # which file said so
    has_license: bool = False
    has_ci: bool = False
    has_container: bool = False
    has_tests: bool = False
    docs_total: int = 0
    docs_by_area: tuple[tuple[str, int], ...] = ()
    decision_like: int = 0
    engos_present: bool = False
    excluded: tuple[str, ...] = field(default_factory=tuple)   # engineering-looking, not taken

    @property
    def has_engineering_docs(self) -> bool:
        return self.docs_total > 0


def survey(repo: Path) -> Inventory:
    """Walk the repository once. Never raises — an unreadable corner is not worth failing."""
    root = Path(repo)
    try:
        entries = sorted(p for p in root.iterdir() if not p.name.startswith("."))
    except OSError:
        return Inventory()

    top_level = tuple(p.name for p in entries if p.is_dir() and p.name not in _SKIP_DIRS)
    languages = _languages(root)
    name, purpose, source = _stated_identity(root)
    docs_total, docs_by_area, decisions = _docs(root)

    return Inventory(
        top_level=top_level,
        languages=languages,
        readme=_readme_heading(root),
        stated_name=name,
        stated_purpose=purpose,
        stated_by=source,
        has_license=any((root / n).exists()
                        for n in ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")),
        has_ci=any((root / m).exists() for m in _CI_MARKERS),
        has_container=any((root / n).exists()
                          for n in ("Dockerfile", "docker-compose.yml", "compose.yaml")),
        has_tests=any((root / d).is_dir() for d in _TEST_DIRS) or bool(languages and _has_tests(root)),
        docs_total=docs_total,
        docs_by_area=docs_by_area,
        decision_like=decisions,
        engos_present=(root / ".engos" / "manifest.yaml").is_file(),
        excluded=_excluded(root),
    )


def _walk(root: Path, base: Path):
    """Every file under `base`, skipping vendor and build directories."""
    if not base.is_dir():
        return
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if entry.name in _SKIP_DIRS:
                    continue
                if entry.is_dir():
                    stack.append(entry)
                elif entry.is_file():
                    yield entry
        except OSError:
            continue


def _languages(root: Path) -> tuple[tuple[str, int], ...]:
    counts: dict[str, int] = {}
    for path in _walk(root, root):
        language = _LANGUAGES.get(path.suffix.lower())
        if language:
            counts[language] = counts.get(language, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return tuple(ranked[:4])


def _has_tests(root: Path) -> bool:
    for path in _walk(root, root):
        name = path.name.lower()
        if name.startswith("test_") or name.endswith(("_test.py", ".test.ts", ".spec.ts",
                                                      "_test.go", "Test.java", "Tests.cs")):
            return True
    return False


def _readme_heading(root: Path) -> str:
    for name in ("README.md", "README.markdown", "README.rst", "README.txt", "README"):
        path = root / name
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
                stripped = line.strip().lstrip("#").strip()
                if stripped and not stripped.startswith(("!", "[", "<", "=", "-")):
                    return stripped[:120]
        except OSError:
            return ""
        return ""
    return ""


def _stated_identity(root: Path) -> tuple[str, str, str]:
    """Name and description a human already wrote into a package manifest.

    Quoted and attributed, never paraphrased. This is the only place EOS can learn what a
    project *is* without being told, and only because someone already typed it.
    """
    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                name = str(data.get("name") or "")
                desc = str(data.get("description") or "")
                if name or desc:
                    return name[:80], desc[:300], "package.json"
        except (OSError, ValueError):
            pass

    # Deliberately regex, not a TOML parser: this must work on a Python older than 3.11's
    # tomllib and must never fail a connect because a manifest has an exotic table.
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            text = pyproject.read_text(encoding="utf-8")
            name = _toml_value(text, "name")
            desc = _toml_value(text, "description")
            if name or desc:
                return name[:80], desc[:300], "pyproject.toml"
        except OSError:
            pass

    for manifest, pattern, label in (
        ("go.mod", r"^module\s+(\S+)", "go.mod"),
        ("Cargo.toml", r'^\s*name\s*=\s*"([^"]+)"', "Cargo.toml"),
    ):
        path = root / manifest
        if path.is_file():
            try:
                match = re.search(pattern, path.read_text(encoding="utf-8"), re.MULTILINE)
            except OSError:
                continue
            if match:
                return match.group(1)[:80], "", label
    return "", "", ""


def _toml_value(text: str, key: str) -> str:
    match = re.search(rf'^\s*{key}\s*=\s*"([^"]*)"', text, re.MULTILINE)
    return match.group(1) if match else ""


def _docs(root: Path) -> tuple[int, tuple[tuple[str, int], ...], int]:
    """What is already under `docs/` — the memory a repository brings with it."""
    docs = root / "docs"
    if not docs.is_dir():
        return 0, (), 0

    by_area: dict[str, int] = {}
    total = decisions = 0
    for path in _walk(root, docs):
        if path.suffix.lower() not in (".md", ".mdx", ".markdown") or path.name == ".gitkeep":
            continue
        total += 1
        relative = path.relative_to(docs)
        area = relative.parts[0] if len(relative.parts) > 1 else "(top level)"
        by_area[area] = by_area.get(area, 0) + 1
        in_decision_dir = any(part.lower() in _DECISION_DIRS for part in relative.parts[:-1])
        named_like_one = _DECISION_NAME.match(path.name) and not _DATED_NAME.match(path.name)
        if in_decision_dir or named_like_one:
            decisions += 1

    ranked = sorted(by_area.items(), key=lambda kv: (-kv[1], kv[0]))
    return total, tuple(ranked[:6]), decisions


def _excluded(root: Path) -> tuple[str, ...]:
    """Engineering-looking content the protocol will not take.

    Only things that plausibly *are* engineering knowledge: markdown at the repository root
    and directories whose name announces documentation. Listing every untaken file would be
    listing the entire codebase, which reports nothing.
    """
    found: list[str] = []
    try:
        for entry in sorted(root.iterdir()):
            if entry.name.startswith(".") or entry.name in _SKIP_DIRS:
                continue
            if entry.is_dir():
                if entry.name in PUBLISHED_ROOTS:
                    continue
                if entry.name.lower() in _DOC_LIKE:
                    count = sum(1 for p in _walk(root, entry)
                                if p.suffix.lower() in (".md", ".mdx", ".markdown", ".rst"))
                    if count:
                        found.append(f"{entry.name}/ ({count} document"
                                     f"{'s' if count != 1 else ''})")
            elif entry.suffix.lower() in (".md", ".markdown"):
                # README and CLAUDE.md are excluded by design and by every convention; saying
                # so would be noise in a report meant to surface surprises.
                if entry.stem.upper() in ("README", "CLAUDE", "LICENSE", "CHANGELOG",
                                          "CONTRIBUTING", "CODE_OF_CONDUCT", "SECURITY"):
                    continue
                found.append(entry.name)
    except OSError:
        return ()
    return tuple(found[:8])
