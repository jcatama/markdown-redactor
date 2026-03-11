# markdown-redactor

Rule-based PII and secret redaction for Markdown documents — audit log, risk-level filtering, LLM pipeline ready

## Quick start

```bash
pip install markdown-redactor
printf "Contact me at jane@example.com\n" | markdown-redactor -
```

Expected output:

```text
Contact me at [REDACTED]
```

See [docs/GUIDE.md](docs/GUIDE.md) for the full API and CLI usage guide.

## Table of contents

- [Who is this for](#who-is-this-for)
- [Key features](#key-features)
- [Built-in redaction rules](#built-in-redaction-rules)
- [How redaction works](#how-redaction-works)
- [Performance](#performance)
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

## Built-in redaction rules

Default engine includes 24 rules:

- `email`, `phone`
- `ipv4`, `ipv6`
- `us_ssn`, `us_ein`
- `uk_nino`
- `in_pan`, `in_aadhaar`, `in_gstin`
- `br_cpf`, `br_cnpj`
- `iban`, `swift_bic`, `eu_vat`
- `labeled_sensitive_id` (tax ID, driver license, passport, national ID labels)
- `secret_assignment` (password/api_key/token style assignments)
- `credential_uri` (connection-string credentials)
- `aws_access_key`, `generic_token`, `google_api_key`, `jwt`, `private_key`
- `credit_card` (Luhn-validated to reduce false positives)

## How redaction works

1. Markdown text is segmented.
2. Based on config, non-redactable segments (like fenced code) can be preserved.
3. Each redactable segment is processed by registered rules in order.
4. Output and stats are returned.

This makes behavior explicit and easy to extend.

## Performance

Runs in $O(n \cdot r)$ time where $n$ is input length and $r$ is active rule count. No network I/O, no AST parsing, no heavy dependencies.

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

- Full usage guide: [docs/GUIDE.md](docs/GUIDE.md)
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
