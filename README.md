# markdown-redactor

A lightweight, pluggable Python library that redacts sensitive information from Markdown before content is sent to LLMs.

It is designed for teams that need practical safety controls without adding heavy dependencies or complex infrastructure.

## First 60 seconds

If you want a fast smoke test:

```bash
pip install markdown-redactor
printf "Contact me at jane@example.com\n" | markdown-redactor -
```

Expected output:

```text
Contact me at [REDACTED]
```

From this point, move to the [Quickstart (5 minutes)](#quickstart-5-minutes) for API and CLI examples.

## Table of contents

- [First 60 seconds](#first-60-seconds)
- [Who is this for](#who-is-this-for)
- [Key features](#key-features)
- [Quickstart (5 minutes)](#quickstart-5-minutes)
- [Python API guide](#python-api-guide)
- [CLI guide](#cli-guide)
- [Makefile shortcuts](#makefile-shortcuts)
- [How redaction works](#how-redaction-works)
- [Built-in redaction rules](#built-in-redaction-rules)
- [Writing custom rules (plugin model)](#writing-custom-rules-plugin-model)
- [Performance and Big-O](#performance-and-big-o)
- [Security and compliance notes](#security-and-compliance-notes)
- [Troubleshooting](#troubleshooting)
- [Additional resources](#additional-resources)
- [Development and contribution](#development-and-contribution)
- [Release process](#release-process)

## Who is this for

- Teams feeding Markdown documents into LLMs (RAG, agents, chat pipelines)
- Security-conscious teams that need deterministic redaction before inference
- Developers who want a small codebase with extensible rules

## Key features

- **Pluggable architecture**: register custom redaction rules without touching core engine
- **Markdown-aware behavior**: by default, skips fenced code blocks and inline code spans
- **Lightweight runtime**: zero runtime dependencies
- **Typed API**: strict typing-friendly design
- **Operational visibility**: per-rule match counters and timing stats

## Quickstart (5 minutes)

### 1) Install

Install from package index:

```bash
pip install markdown-redactor
```

Or install from source:

```bash
pipp install -e .
```

### 2) Redact text in Python

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()

markdown = """
Contact: jane@example.com
Server IP: 10.0.0.1
Token: ghp_ABCDEF1234567890
"""

result = engine.redact(markdown)

print(result.content)
print(result.stats.total_matches)
print(result.stats.rule_matches)
```

### 3) Redact from CLI

```bash
markdown-redactor input.md -o output.md --stats
```

## Python API guide

### Create the default engine

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()
```

### Basic redaction

```python
result = engine.redact("Email me at jane@example.com")
print(result.content)
```

### Configure masking and markdown behavior

```python
from markdown_redactor import RedactionConfig

config = RedactionConfig(
    mask="<redacted>",
    skip_fenced_code_blocks=True,
    skip_inline_code=True,
)

result = engine.redact(content, config=config)
```

### Add context metadata (optional)

```python
from markdown_redactor import RuleContext

context = RuleContext(file_path="docs/customer.md", metadata={"source": "crm"})
result = engine.redact(content, context=context)
```

### Understand returned stats

`result.stats` includes:

- `total_matches`: total number of replacements
- `rule_matches`: replacements grouped by rule name
- `elapsed_ms`: execution time for this call
- `source_bytes` and `output_bytes`: input/output size in bytes

## CLI guide

### Input and output

Redact a file to stdout:

```bash
markdown-redactor input.md
```

Read from stdin and write to stdout:

```bash
cat input.md | markdown-redactor -
```

Write to a file:

```bash
markdown-redactor input.md -o output.md
```

### Useful flags

- `--mask "<secret>"`: custom replacement value
- `--redact-inline-code`: redact inside inline code spans (default is skip)
- `--redact-fenced-code-blocks`: redact inside fenced blocks (default is skip)
- `--stats`: print stats as JSON to stderr

Example:

```bash
markdown-redactor input.md -o output.md --mask "<secret>" --stats
```

## Makefile shortcuts

This repository includes convenient local commands:

- `make lint`
- `make type`
- `make test`
- `make check` (runs lint + type + test)
- `make redact FILE=input.md OUT=output.md`

Redact with additional CLI flags:

```bash
make redact FILE=input.md OUT=output.md REDACT_FLAGS="--redact-inline-code --redact-fenced-code-blocks"
```

Redact from stdin:

```bash
cat input.md | make redact FILE=- OUT=-
```

## Copy/paste recipes

Use these examples as starting points for common LLM workflows.

### 1) RAG ingest preprocessor (single file)

Redact first, then pass clean text to your embedding/indexing pipeline.

```python
from pathlib import Path

from markdown_redactor import create_default_engine

engine = create_default_engine()

source_path = Path("docs/customer-notes.md")
clean_path = Path("docs/customer-notes.redacted.md")

source_text = source_path.read_text(encoding="utf-8")
result = engine.redact(source_text)

clean_path.write_text(result.content, encoding="utf-8")
print(result.stats.rule_matches)
```

### 2) Chat app pre-send filter

Apply redaction before sending user-provided markdown to an LLM.

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()


def prepare_prompt(user_markdown: str) -> str:
    result = engine.redact(user_markdown)
    return result.content
```

### 3) Keep code examples unchanged (default behavior)

By default, fenced code blocks and inline code are skipped.

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()
result = engine.redact("""
My email is jane@example.com
```python
API_KEY = \"ghp_ABCDEF1234567890\"
```
Inline token: `ghp_ABCDEF1234567890`
""")
```

### 4) Strict mode for high-risk exports

If required by policy, redact inside inline and fenced code too.

```bash
markdown-redactor input.md -o output.md --redact-inline-code --redact-fenced-code-blocks
```

### 5) Batch process a folder with shell

Redact every markdown file into a sibling output folder.

```bash
mkdir -p redacted
for file in docs/*.md; do
  markdown-redactor "$file" -o "redacted/$(basename "$file")"
done
```

### 6) Batch process with Python

Useful when you need richer reporting or custom naming.

```python
from pathlib import Path

from markdown_redactor import create_default_engine

engine = create_default_engine()
input_dir = Path("docs")
output_dir = Path("redacted")
output_dir.mkdir(exist_ok=True)

for path in input_dir.glob("*.md"):
    content = path.read_text(encoding="utf-8")
    result = engine.redact(content)
    destination = output_dir / path.name
    destination.write_text(result.content, encoding="utf-8")
    print(path.name, result.stats.total_matches)
```

### 7) Custom company identifier rule

Add a simple plugin for org-specific IDs.

```python
import re
from dataclasses import dataclass

from markdown_redactor import RedactionConfig, RedactionEngine, RuleContext, RuleRegistry


@dataclass(frozen=True, slots=True)
class TicketRule:
    name: str = "ticket_id"
    pattern: re.Pattern[str] = re.compile(r"\bTICKET-\d{6}\b")

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        updated, count = self.pattern.subn(config.mask, content)
        return updated, count


registry = RuleRegistry()
registry.register(TicketRule())
engine = RedactionEngine(registry=registry)
```

### 8) CI check to prevent raw secrets in generated artifacts

Example step to redact docs before publishing snapshots.

```bash
make redact FILE=README.md OUT=/tmp/README.redacted.md
```

## How redaction works

1. Markdown text is segmented.
2. Based on config, non-redactable segments (like fenced code) can be preserved.
3. Each redactable segment is processed by registered rules in order.
4. Output and stats are returned.

This makes behavior explicit and easy to extend.

## Built-in redaction rules

Default engine includes:

- `email`
- `us_ssn`
- `us_ein`
- `uk_nino`
- `in_pan`
- `in_aadhaar`
- `in_gstin`
- `br_cpf`
- `br_cnpj`
- `iban`
- `swift_bic`
- `eu_vat`
- `labeled_sensitive_id` (tax ID, driver license, passport, national ID labels)
- `secret_assignment` (password/api_key/token style assignments)
- `credential_uri` (connection-string credentials)
- `phone`
- `ipv4`
- `ipv6`
- `aws_access_key`
- `generic_token`
- `google_api_key`
- `jwt`
- `private_key`
- `credit_card` (Luhn-validated to reduce false positives)

## Writing custom rules (plugin model)

Rules implement a simple contract:

- `name`: string identifier
- `redact(content, config, context) -> (updated_content, match_count)`

Example custom rule:

```python
from dataclasses import dataclass

from markdown_redactor import RedactionConfig, RedactionEngine, RuleContext, RuleRegistry


@dataclass(frozen=True, slots=True)
class EmployeeIdRule:
    name: str = "employee_id"

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        updated = content.replace("EMP-", config.mask + "-")
        count = content.count("EMP-")
        return updated, count


registry = RuleRegistry()
registry.register(EmployeeIdRule())

engine = RedactionEngine(registry=registry)
result = engine.redact("Employee: EMP-001")
```

### Rule design tips

- Keep rules deterministic and side-effect free
- Precompile regex at module load time
- Return accurate match counts for observability
- Avoid very broad patterns that over-redact business content

### Tenant-specific layering (recommended)

For enterprise deployments, keep the global baseline and layer tenant rules on top.

```python
from dataclasses import dataclass

from markdown_redactor import (
    RedactionConfig,
    RuleContext,
    create_tenant_engine,
)


@dataclass(frozen=True, slots=True)
class CustomerTicketRule:
    name: str = "customer_ticket"

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        updated = content.replace("TICKET-", f"{config.mask}-")
        count = content.count("TICKET-")
        return updated, count


engine = create_tenant_engine(
    [CustomerTicketRule()],
    include_default_rules=True,
)
```

You can disable default rules for tenant-only behavior:

```python
engine = create_tenant_engine([CustomerTicketRule()], include_default_rules=False)
```

## Performance and Big-O

Let:

- $n$ = input length
- $r$ = number of active rules

Complexity:

- Time: $O(n \cdot r)$
- Memory: $O(n)$

Why this stays lightweight:

- Precompiled regex patterns in built-in rules
- No Markdown AST parsing dependency
- No network I/O, no external services, no heavy runtime libs

## Security and compliance notes

- This is **best-effort pattern redaction**, not formal DLP certification
- Always validate on your real data and threat model
- Combine with downstream controls (access controls, logging, policy engines)
- Add organization-specific rules for identifiers, ticket IDs, or internal secrets

## Troubleshooting

### Nothing is being redacted

- Verify you are using `create_default_engine()` or registering custom rules
- Check whether content is inside fenced/inline code that is skipped by default

### Too much is being redacted

- Tighten custom regex patterns
- Keep `--redact-inline-code` / `--redact-fenced-code-blocks` disabled unless required

### CLI command not found

- Ensure package is installed in active environment
- Try module mode: `python -m markdown_redactor.cli input.md`

## Additional resources

- Architecture guide: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- FAQ: [docs/FAQ.md](docs/FAQ.md)
- Support process: [SUPPORT.md](SUPPORT.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Releasing guide: [docs/RELEASING.md](docs/RELEASING.md)
- Guided onboarding docs: [docs/README.md](docs/README.md)
- Runnable examples:
    - [examples/basic_api.py](examples/basic_api.py)
    - [examples/custom_rule.py](examples/custom_rule.py)
    - [examples/cli_usage.sh](examples/cli_usage.sh)

## Development and contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and quality checks.

Primary local quality command:

```bash
PYTHONPATH=src .venv/bin/python -m ruff check src tests && \
PYTHONPATH=src .venv/bin/python -m mypy src && \
PYTHONPATH=src .venv/bin/python -m pytest
```

## Release process

Maintainers can follow [docs/RELEASING.md](docs/RELEASING.md).

Publishing is automated via [.github/workflows/release.yml](.github/workflows/release.yml) on tags matching `v*`.
GitHub Release notes and signed provenance attestations are generated via [.github/workflows/github-release.yml](.github/workflows/github-release.yml).
