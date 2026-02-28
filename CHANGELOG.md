# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.

## [0.1.0] - 2026-02-28

### Added

- Core pluggable redaction engine for Markdown content
- Markdown segmentation with configurable fenced/inline code handling
- Built-in rules: email, phone, IPv4/IPv6, AWS keys, generic tokens, private keys, credit cards (Luhn-validated)
- Type-safe Python API (`RedactionEngine`, `RuleRegistry`, `RedactionConfig`, `RuleContext`)
- CLI entrypoint (`markdown-redactor`) with file/stdin support and stats output
- Makefile targets for lint/type/test/check/redact
- Unit tests for engine, registry, and CLI behavior
- Comprehensive README and contribution docs
