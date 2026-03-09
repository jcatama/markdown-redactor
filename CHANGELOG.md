# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.

## [0.1.2] - 2026-03-09

### Added

- Allowlist support to preserve exact values during redaction
- Per-rule toggles via `enabled_rule_names` and `disabled_rule_names`
- File helper APIs: `redact_file()` and `redact_to_file()`
- Replacement modes: `full`, `preserve_last4`, and `preserve_format`
- CLI support for `--replacement-mode`, `--allowlist`, `--enable-rule`, and `--disable-rule`

### Improved

- Expanded false-positive regression coverage for links, hostnames, prose, and URI edge cases
- Added tests for file helpers, replacement modes, allowlists, and rule toggles
- Updated README examples and configuration guidance for the new redaction controls

## [0.1.1] - 2026-02-28

### Added

- Core pluggable redaction engine for Markdown content
- Markdown segmentation with configurable fenced/inline code handling
- Built-in rules: email, phone, IPv4/IPv6, AWS keys, generic tokens, private keys, credit cards (Luhn-validated)
- Type-safe Python API (`RedactionEngine`, `RuleRegistry`, `RedactionConfig`, `RuleContext`)
- CLI entrypoint (`markdown-redactor`) with file/stdin support and stats output
- Makefile targets for lint/type/test/check/redact
- Unit tests for engine, registry, and CLI behavior
- Comprehensive README and contribution docs
