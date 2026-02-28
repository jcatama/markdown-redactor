# Documentation index

Welcome to the `markdown-redactor` documentation hub.

## Quick start

- Validate everything:

```bash
make check
```

- Redact a file:

```bash
make redact FILE=input.md OUT=output.md
```

- Redact from stdin:

```bash
cat input.md | make redact FILE=- OUT=-
```

## Codebase map

Top-level:

- `src/markdown_redactor/`: library source
- `tests/`: unit tests
- `examples/`: runnable examples
- `.github/workflows/`: CI + release automation
- `docs/`: architecture and maintainer guides

Core modules:

- `types.py`: config/context/result models + rule protocol
- `registry.py`: plugin registration and ordering
- `markdown.py`: markdown segmentation with code-span/block controls
- `engine.py`: orchestration, rule execution, and stats
- `rules.py`: default enterprise-oriented redaction rules
- `cli.py`: `markdown-redactor` command implementation
- `factory.py`: default engine constructor

## Daily dev flow

Setup:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov ruff mypy
```

Checks:

```bash
make lint
make type
make test
make check
```

Build package artifacts:

```bash
.venv/bin/python -m pip install build twine
.venv/bin/python -m build
.venv/bin/python -m twine check dist/*
```

## Release and publish

- [03_RELEASE_AND_PUBLISH.md](03_RELEASE_AND_PUBLISH.md): practical release checklist
- [RELEASING.md](RELEASING.md): maintainer release playbook
- [FIRST_RELEASE_CLICK_BY_CLICK.md](FIRST_RELEASE_CLICK_BY_CLICK.md): beginner click-by-click release guide

Release automation:

- `.github/workflows/release.yml`: tag-driven PyPI publish with trusted publishing
- `.github/workflows/github-release.yml`: GitHub Release + signed provenance attestations

## What has been implemented

- Pluggable markdown redaction engine with strict typing
- Markdown-aware segmentation to avoid breaking code examples by default
- Built-in rules for common sensitive patterns (email, phone, IPs, keys, tokens, private keys, cards)
- CLI command with stdin/stdout and stats support
- CI + release workflows for enterprise-grade delivery
- Comprehensive tests and contributor documentation

## Reference docs

- [ARCHITECTURE.md](ARCHITECTURE.md): design and data flow
- [FAQ.md](FAQ.md): common questions

## Root-level operational docs

- [../README.md](../README.md): user-facing package documentation
- [../CONTRIBUTING.md](../CONTRIBUTING.md): contribution workflow
- [../SECURITY.md](../SECURITY.md): vulnerability reporting policy
- [../SUPPORT.md](../SUPPORT.md): support expectations and issue guidance
- [../CHANGELOG.md](../CHANGELOG.md): release history
