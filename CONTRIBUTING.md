# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest pytest-cov ruff mypy
```

## Local quality checks

Run the same command used in CI-style local validation:

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src tests && \
PYTHONPATH=src .venv/bin/python -m mypy src && \
PYTHONPATH=src .venv/bin/python -m pytest
```

## Contribution guidelines

- Keep changes minimal and focused
- Preserve strict typing (`mypy --strict`)
- Add or update tests for behavior changes
- Keep runtime dependency footprint lightweight
- Ensure markdown-aware redaction behavior is not regressed

## Pull request checklist

- [ ] Lint passes
- [ ] Type checks pass
- [ ] Tests pass
- [ ] Docs updated (`README.md` if behavior/API changed)

## Maintainer release flow

For version bumps and publishing, follow [docs/RELEASING.md](docs/RELEASING.md).
