# markdown-redactor Guide

Detailed usage guide for the Python API, CLI, Makefile shortcuts, copy/paste recipes, and custom rules.

## Table of contents

- [Quickstart (5 minutes)](#quickstart-5-minutes)
- [Python API guide](#python-api-guide)
  - [Named-entity redaction (NER)](#named-entity-redaction-ner)
- [CLI guide](#cli-guide)
- [Makefile shortcuts](#makefile-shortcuts)
- [Copy/paste recipes](#copypaste-recipes)
- [Writing custom rules (plugin model)](#writing-custom-rules-plugin-model)

## Quickstart (5 minutes)

### 1) Install

Install from package index:

```bash
pip install markdown-redactor
```

Or install from source:

```bash
pip install -e .
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
    replacement_mode="full",
    skip_fenced_code_blocks=True,
    skip_inline_code=True,
)

result = engine.redact(content, config=config)
```

### Replacement modes

Available modes:

- `full`: replace the whole match with `mask`
- `preserve_last4`: keep the last 4 alphanumeric characters
- `preserve_format`: keep separators like `-`, `.`, `(`, `)` while masking characters

```python
config = RedactionConfig(replacement_mode="preserve_last4")
```

### File helpers

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()

result = engine.redact_file("input.md")
result = engine.redact_to_file("input.md", "output.md")
```

### Allowlist specific values

```python
config = RedactionConfig(
    allowlist=("jane@example.com", "10.0.0.1"),
)
```

### Enable or disable specific rules

Only enable chosen rules:

```python
config = RedactionConfig(enabled_rule_names=("email", "jwt"))
```

Disable specific rules:

```python
config = RedactionConfig(disabled_rule_names=("phone", "swift_bic"))
```

### Filter rules by risk level

```python
config = RedactionConfig(min_risk_level="high")
```

Risk levels across the 24 built-in rules:

| Level | Rules |
|-------|-------|
| `high` | SSN, NINO, PAN, Aadhaar, GSTIN, CPF, CNPJ, EIN, IBAN, labeled IDs, secrets, credentials, AWS keys, tokens, JWTs, private keys, credit cards |
| `medium` | email, phone, SWIFT/BIC, EU VAT |
| `low` | IPv4, IPv6 |

### Inspect rule metadata

```python
for rule in engine.registry.list_rules():
    m = rule.metadata
    if m:
        print(f"{rule.name:20s}  {m.category:12s}  {m.risk_level:6s}  {m.description}")
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

### Audit log

```python
from markdown_redactor import RedactionConfig, create_default_engine

engine = create_default_engine()
result = engine.redact(
    "Contact jane@example.com or call +1 (555) 123-4567",
    config=RedactionConfig(collect_audit_log=True),
)

for entry in result.audit_log:
    print(entry.rule_name, entry.start, entry.end, entry.original_hash, entry.replacement)
# email  8  24  a3f1b2c4d5e6f789  [REDACTED]
# phone  32  50  7c8d9e0f1a2b3c4d  [REDACTED]
```

Each `AuditEntry` is a frozen dataclass with:

| Field | Type | Description |
|---|---|---|
| `rule_name` | `str` | Name of the rule that triggered the redaction |
| `start` | `int` | 0-based start offset in the original input string |
| `end` | `int` | 0-based exclusive end offset in the original input string |
| `original_hash` | `str` | First 16 hex chars of SHA-256 of the matched text |
| `replacement` | `str` | Replacement string that was written to the output |

> **Note:** `collect_audit_log` is `False` by default. Offsets are relative to the original input text. When an allowlist is configured, character positions for matches that appear after allowlisted values may be slightly shifted due to placeholder substitution during processing.

### Named-entity redaction (NER)

`NERRule` detects and redacts named entities using a spaCy pipeline. It is an **opt-in dependency** — install the extra and a model before use:

```bash
pip install 'markdown-redactor[ner]'
python -m spacy download en_core_web_sm
```

```python
from markdown_redactor import NERRule, create_default_engine

engine = create_default_engine()
engine.registry.register(NERRule())

result = engine.redact("Send the report to Alice Johnson at Acme Corp.")
print(result.content)
# Send the report to [REDACTED] at [REDACTED].
```

**Default entity labels** detected: `PERSON`, `ORG`, `GPE` (geopolitical entity), `LOC`. Use `entity_labels` to narrow the scope:

```python
NERRule(entity_labels=frozenset({"PERSON"}))  # people only
```

**Choosing a model** — any spaCy pipeline with an NER component works:

| Model | Size | Notes |
|---|---|---|
| `en_core_web_sm` | ~12 MB | Default · fast |
| `en_core_web_md` | ~43 MB | Better accuracy |
| `en_core_web_trf` | ~400 MB | Transformer-based · highest accuracy |

> `NERRule` loads the model lazily on the first `redact()` call and caches it for the lifetime of the process. Constructing `NERRule()` without spaCy installed is safe — the `ImportError` is only raised when `redact()` is called.

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
- `--replacement-mode preserve_last4`: control redaction rendering
- `--min-risk-level high`: only run rules at or above this risk level (`high`, `medium`, `low`)
- `--allowlist jane@example.com`: preserve exact values
- `--enable-rule email,jwt`: only run selected rules
- `--disable-rule phone,swift_bic`: skip selected rules
- `--redact-inline-code`: redact inside inline code spans (default is skip)
- `--redact-fenced-code-blocks`: redact inside fenced blocks (default is skip)
- `--stats`: print stats as JSON to stderr

Examples:

```bash
markdown-redactor input.md -o output.md --mask "<secret>" --stats
markdown-redactor input.md --allowlist jane@example.com --disable-rule phone
markdown-redactor input.md --enable-rule email,jwt
```

## Makefile shortcuts

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

### 1) RAG ingest preprocessor (single file)

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

```python
from markdown_redactor import create_default_engine

engine = create_default_engine()


def prepare_prompt(user_markdown: str) -> str:
    result = engine.redact(user_markdown)
    return result.content
```

### 3) Keep code examples unchanged (default behavior)

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

```bash
markdown-redactor input.md -o output.md --redact-inline-code --redact-fenced-code-blocks
```

### 5) Batch process a folder with shell

```bash
mkdir -p redacted
for file in docs/*.md; do
  markdown-redactor "$file" -o "redacted/$(basename "$file")"
done
```

### 6) Batch process with Python

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

```bash
make redact FILE=README.md OUT=/tmp/README.redacted.md
```

## Writing custom rules (plugin model)

Rules implement a simple contract:

- `name`: string identifier
- `redact(content, config, context) -> (updated_content, match_count)`

Example:

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

### Tenant-specific layering

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

Disable default rules for tenant-only behavior:

```python
engine = create_tenant_engine([CustomerTicketRule()], include_default_rules=False)
```
