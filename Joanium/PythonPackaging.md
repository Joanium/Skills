---
name: Python Packaging & Project Setup
trigger: python package, setup.py, pyproject.toml, poetry, uv, hatch, pip install -e, publish to pypi, python project structure, virtual environment, dependency management python, python library, pip package, twine upload, python build
description: Set up, structure, and publish Python packages and libraries using modern tooling (uv, Poetry, Hatch, pyproject.toml). Use this skill when the user wants to create a Python library or package, configure pyproject.toml, set up a virtual environment, manage dependencies, or publish to PyPI. Covers project layout, dependency locking, versioning, and CI publishing.
---

# ROLE
You are a Python packaging expert. You know the modern toolchain (uv, pyproject.toml, hatch) and the classic one (pip, setup.py). You help teams ship clean, installable Python packages.

# MODERN PROJECT SETUP (2024)

## Using uv (Fastest — Recommended)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create new project
uv init mypackage
cd mypackage

# Add dependencies
uv add requests httpx
uv add --dev pytest ruff mypy

# Install in dev mode
uv sync

# Run with managed venv
uv run python -m mypackage
uv run pytest
```

## Using Poetry
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Create new project
poetry new mypackage
cd mypackage

# Add dependencies
poetry add requests httpx
poetry add --group dev pytest ruff mypy

# Install in dev mode (creates .venv)
poetry install

# Run commands
poetry run pytest
poetry shell  # activate venv
```

# PYPROJECT.TOML — THE ONLY CONFIG FILE YOU NEED

```toml
# pyproject.toml — complete example
[build-system]
requires = ["hatchling"]        # or "flit-core", "setuptools>=61"
build-backend = "hatchling.build"

[project]
name = "mypackage"
version = "0.1.0"
description = "A short description of what this does"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.9"
authors = [{ name = "Alice", email = "alice@example.com" }]
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "License :: OSI Approved :: MIT License",
    "Intended Audience :: Developers",
]

# Runtime dependencies (installed with the package)
dependencies = [
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
]

# Optional dependencies (extras)
[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1.0", "mypy>=1.0"]
cli = ["click>=8.0"]

# Console scripts (CLI entry points)
[project.scripts]
mypackage = "mypackage.cli:main"

[project.urls]
Homepage = "https://github.com/alice/mypackage"
Documentation = "https://mypackage.readthedocs.io"
Changelog = "https://github.com/alice/mypackage/blob/main/CHANGELOG.md"

# Tool configurations (ruff, mypy, pytest — all in one file)
[tool.ruff]
target-version = "py39"
line-length = 100
[tool.ruff.lint]
select = ["E", "W", "F", "I", "UP", "B", "S"]

[tool.mypy]
python_version = "3.9"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src/mypackage"]
omit = ["tests/*"]
```

# PROJECT STRUCTURE

```
mypackage/
├── src/
│   └── mypackage/           # src layout (recommended — prevents import confusion)
│       ├── __init__.py
│       ├── core.py
│       ├── utils.py
│       └── cli.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_core.py
├── docs/
│   └── index.md
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE

# Why src layout?
# Without it: `import mypackage` might import the local folder (not installed package)
# With src/: Python must install the package to import it → catches packaging bugs early
```

## __init__.py — Public API
```python
# src/mypackage/__init__.py
# Expose the public API — what users should import
from mypackage.core import Client, Config
from mypackage.exceptions import MyPackageError, AuthError

__version__ = "0.1.0"
__all__ = ["Client", "Config", "MyPackageError", "AuthError"]

# Users can now: from mypackage import Client
```

# VERSIONING

```toml
# Option 1: Static version in pyproject.toml
[project]
version = "1.2.3"

# Option 2: Dynamic version from git tags (hatchling)
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"   # uses git tags: git tag v1.2.3 && git push --tags
```

```python
# Option 3: Single source of truth in __init__.py
# pyproject.toml:
# dynamic = ["version"]
# [tool.hatch.version]
# path = "src/mypackage/__init__.py"

# src/mypackage/__init__.py:
__version__ = "1.2.3"
```

## Semantic Versioning Rules
```
MAJOR.MINOR.PATCH

PATCH: bug fixes, no API changes (1.2.3 → 1.2.4)
MINOR: new features, backwards compatible (1.2.3 → 1.3.0)
MAJOR: breaking changes (1.2.3 → 2.0.0)

Pre-release: 1.0.0-alpha.1, 1.0.0-beta.2, 1.0.0-rc.1
```

# BUILDING AND PUBLISHING

```bash
# Build distribution files (wheel + sdist)
python -m build        # pip install build
# Or with uv:
uv build
# Creates: dist/mypackage-0.1.0.tar.gz
#          dist/mypackage-0.1.0-py3-none-any.whl

# Upload to TestPyPI first (always test before real PyPI)
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ mypackage

# Upload to PyPI (production)
python -m twine upload dist/*
# Or with uv:
uv publish

# Get PyPI API token: pypi.org → Account Settings → API tokens
# Store as PYPI_TOKEN in GitHub Secrets (never hardcode)
```

## GitHub Actions — Publish on Tag
```yaml
# .github/workflows/publish.yml
name: Publish to PyPI

on:
  push:
    tags: ["v*"]           # triggers on: git tag v1.2.3 && git push --tags

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi       # requires manual approval in GitHub
    permissions:
      id-token: write       # for trusted publishing (no API token needed!)

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: Build
        run: uv build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        # Trusted publishing: no API token needed — configured on PyPI website
```

# VIRTUAL ENVIRONMENTS (PLAIN PYTHON)

```bash
# Create venv
python -m venv .venv

# Activate
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate.bat       # Windows cmd
.venv\Scripts\Activate.ps1       # Windows PowerShell

# Deactivate
deactivate

# Install package in editable/dev mode
pip install -e ".[dev]"

# Freeze dependencies
pip freeze > requirements.txt
pip install -r requirements.txt

# Always gitignore:
# .venv/
# __pycache__/
# *.pyc
# dist/
# *.egg-info/
```

# DEPENDENCY BEST PRACTICES

```toml
# In libraries: use ranges (don't constrain consumers unnecessarily)
dependencies = [
    "httpx>=0.24.0,<1.0.0",   # allows minor updates
    "pydantic>=2.0.0",         # allows any 2.x
]

# In applications: pin exact versions for reproducibility
# Use uv.lock or poetry.lock — commit these to git for apps, gitignore for libraries

# Separate runtime vs dev vs optional:
[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
docs = ["mkdocs", "mkdocs-material"]
```

# CHECKLIST
```
[ ] pyproject.toml with [build-system], [project], [project.optional-dependencies]
[ ] src/ layout to prevent import confusion
[ ] __init__.py exposes clean public API with __all__
[ ] Semantic versioning with single source of truth
[ ] Tests run with: uv run pytest  or  poetry run pytest
[ ] .gitignore includes .venv, dist/, *.egg-info, __pycache__
[ ] CI runs tests on Python 3.9, 3.10, 3.11, 3.12
[ ] TestPyPI tested before real publish
[ ] PyPI trusted publishing configured (no stored API tokens)
```
