# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.

## [0.1.3] - 2026-03-10

### Fixed

- US SSN pattern now requires a separator (`-` or space) — bare 9-digit numbers (order IDs, version codes) no longer match
- SWIFT/BIC pattern now requires at least one digit in the location/branch code — common all-caps English words (`REQUIRED`, `CRITICAL`, `ACCEPTED`, etc.) no longer match
- IBAN pattern now restricts the country prefix to 85 valid ISO 3166-1 country codes — arbitrary two-letter-prefixed identifiers no longer match
- Closing backtick delimiter in `_split_inline_code` is now correctly marked non-redactable
- `UnicodeDecodeError` in CLI is now caught and reported as `markdown-redactor: ...` with exit code 2 (was an unhandled traceback)
- `create_tenant_engine(tenant_rules_first=True)` no longer double-registers default rules that collide with a tenant rule name

### Added

- `AuditEntry` frozen dataclass with `rule_name`, `start`, `end`, `original_hash`, and `replacement` fields
- `collect_audit_log: bool` field on `RedactionConfig` — opt-in audit log collection (default `False`)
- `audit_log: tuple[AuditEntry, ...]` field on `RedactionResult` — tuple of all redactions made during a `redact()` call
- `AuditEntry` exported from package root
- `RuleMetadata` type with `category`, `risk_level`, and `description` fields on every built-in rule
- `min_risk_level` field on `RedactionConfig` — filters active rules to `high`, `medium`, or `low` and above
- `--min-risk-level` CLI flag to apply risk-level filtering from the command line
- `RuleRegistry.register()` now raises `ValueError` on duplicate rule name
- Rule classes (`RegexRule`, `CreditCardRule`, `PhoneRule`, `LabelValueRule`, `SecretAssignmentRule`, `CredentialUriRule`) exported from package root
- `RuleMetadata` exported from package root
- `__version__` attribute on package root

### Improved

- All 24 default-rule regex patterns moved to module-level constants (compiled once per process, not once per engine instantiation)
- Extended near-miss test matrix with bare SSN digits, all-caps word, and invalid-country IBAN cases
- Added `test_registry_raises_on_duplicate_rule_name`, `test_min_risk_level_high_excludes_medium_and_low_rules`, `test_min_risk_level_medium_includes_medium_excludes_low`, `test_all_default_rules_have_metadata`, and audit-log test suite tests
- README updated with risk-level filtering guide, metadata inspection example, `--min-risk-level` CLI flag, and audit log usage section

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
