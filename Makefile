PYTHON := .venv/bin/python
FILE ?= -
OUT ?= -
MASK ?= [REDACTED]
REDACT_FLAGS ?=

.PHONY: lint type test check redact

lint:
	PYTHONPATH=src $(PYTHON) -m ruff check src tests

type:
	PYTHONPATH=src $(PYTHON) -m mypy src

test:
	PYTHONPATH=src $(PYTHON) -m pytest

check: lint type test

redact:
	PYTHONPATH=src $(PYTHON) -m markdown_redactor.cli "$(FILE)" -o "$(OUT)" --mask "$(MASK)" $(REDACT_FLAGS)
