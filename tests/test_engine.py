from __future__ import annotations

from pathlib import Path

import pytest

from markdown_redactor import (
    RedactionConfig,
    RedactionEngine,
    RuleRegistry,
    create_default_engine,
    default_rules,
)


def test_redacts_sensitive_values() -> None:
    engine = create_default_engine()
    content = "Contact me at jane@example.com from ip 192.168.1.1"

    result = engine.redact(content)

    assert result.stats.total_matches >= 2
    assert "jane@example.com" not in result.content
    assert "192.168.1.1" not in result.content


def test_skips_fenced_code_block_by_default() -> None:
    engine = create_default_engine()
    content = """Outside email jane@example.com
```python
SECRET = 'jane@example.com'
```
"""

    result = engine.redact(content)

    assert "Outside email [REDACTED]" in result.content
    assert "SECRET = 'jane@example.com'" in result.content


def test_inline_code_behavior_configurable() -> None:
    engine = create_default_engine()
    content = "Token `ghp_ABCDEF1234567890` and token ghp_ABCDEF1234567890"

    keep_inline = engine.redact(content)
    redact_inline = engine.redact(content, config=RedactionConfig(skip_inline_code=False))

    assert "`ghp_ABCDEF1234567890`" in keep_inline.content
    assert redact_inline.content.count("[REDACTED]") >= 2


def test_credit_card_luhn_guard() -> None:
    engine = create_default_engine()
    content = "Invalid: 1234 5678 9012 3456; Valid: 4111 1111 1111 1111"

    result = engine.redact(content)

    assert "1234 5678 9012 3456" in result.content
    assert "4111 1111 1111 1111" not in result.content


def test_custom_mask() -> None:
    engine = create_default_engine()
    content = "mail: jane@example.com"

    result = engine.redact(content, config=RedactionConfig(mask="<secret>"))

    assert "<secret>" in result.content


def test_allowlist_preserves_exact_values() -> None:
    engine = create_default_engine()
    content = "email jane@example.com ip 10.0.0.1"

    result = engine.redact(content, config=RedactionConfig(allowlist=("jane@example.com",)))

    assert "jane@example.com" in result.content
    assert "10.0.0.1" not in result.content
    assert result.stats.rule_matches.get("email", 0) == 0
    assert result.stats.rule_matches.get("ipv4", 0) == 1


def test_redact_file_reads_source_and_sets_file_context(tmp_path: Path) -> None:
    engine = create_default_engine()
    input_file = tmp_path / "sample.md"
    input_file.write_text("email jane@example.com", encoding="utf-8")

    result = engine.redact_file(input_file)

    assert "jane@example.com" not in result.content
    assert result.stats.rule_matches.get("email", 0) == 1


def test_redact_to_file_writes_output(tmp_path: Path) -> None:
    engine = create_default_engine()
    input_file = tmp_path / "in.md"
    output_file = tmp_path / "out.md"
    input_file.write_text("ip 10.0.0.1", encoding="utf-8")

    result = engine.redact_to_file(input_file, output_file)

    assert result.stats.rule_matches.get("ipv4", 0) == 1
    assert "10.0.0.1" not in output_file.read_text(encoding="utf-8")


def test_disabled_rule_names_skip_specific_default_rules() -> None:
    engine = create_default_engine()
    content = "email jane@example.com ip 10.0.0.1"

    result = engine.redact(content, config=RedactionConfig(disabled_rule_names=("email",)))

    assert "jane@example.com" in result.content
    assert "10.0.0.1" not in result.content
    assert result.stats.rule_matches.get("email", 0) == 0


def test_enabled_rule_names_limit_active_rules() -> None:
    engine = create_default_engine()
    content = "email jane@example.com ip 10.0.0.1"

    result = engine.redact(content, config=RedactionConfig(enabled_rule_names=("email",)))

    assert "jane@example.com" not in result.content
    assert "10.0.0.1" in result.content
    assert result.stats.rule_matches == {"email": 1}


def test_preserve_last4_replacement_mode_keeps_last_four_characters() -> None:
    engine = create_default_engine()

    result = engine.redact(
        "Card 4111 1111 1111 1111",
        config=RedactionConfig(replacement_mode="preserve_last4"),
    )

    assert "1111" in result.content
    assert "4111 1111 1111 1111" not in result.content
    assert "XXXX" in result.content


def test_preserve_format_replacement_mode_keeps_separators() -> None:
    engine = create_default_engine()

    result = engine.redact(
        "Phone +1 (415) 555-2671",
        config=RedactionConfig(replacement_mode="preserve_format"),
    )

    assert "+X (XXX) XXX-XXXX" in result.content


@pytest.mark.parametrize(
    "content",
    [
        "Hostname: db.internal.local",
        "Markdown link: [docs](https://example.com/docs)",
        "password policy enabled for all users",
        "Database URI without credentials postgres://admin@db.internal:5432/app",
    ],
)
def test_false_positive_regressions_are_not_redacted(content: str) -> None:
    engine = create_default_engine()

    result = engine.redact(content)

    assert result.content == content
    assert result.stats.total_matches == 0


def test_empty_registry_leaves_content_unchanged() -> None:
    engine = RedactionEngine(registry=RuleRegistry())
    content = "No secret data here"

    result = engine.redact(content)

    assert result.content == content
    assert result.stats.total_matches == 0
    assert result.stats.rule_matches == {}


def test_fenced_code_redaction_can_be_enabled() -> None:
    engine = create_default_engine()
    content = """```text
jane@example.com
```
"""

    result = engine.redact(content, config=RedactionConfig(skip_fenced_code_blocks=False))

    assert "jane@example.com" not in result.content
    assert "[REDACTED]" in result.content


def test_ipv4_count_tracks_ipv4_rule() -> None:
    engine = create_default_engine()
    content = "IPs: 10.0.0.1 and 172.16.0.2"

    result = engine.redact(content)

    assert result.stats.rule_matches.get("ipv4") == 2
    assert result.stats.rule_matches.get("phone", 0) == 0


@pytest.mark.parametrize(
    ("content", "rule_name"),
    [
        ("Email: jane@example.com", "email"),
        ("SSN: 123-45-6789", "us_ssn"),
        ("EIN: 12-3456789", "us_ein"),
        ("NINO: AB123456C", "uk_nino"),
        ("PAN: ABCDE1234F", "in_pan"),
        ("Aadhaar: 1234 5678 9123", "in_aadhaar"),
        ("GSTIN: 27ABCDE1234F1Z5", "in_gstin"),
        ("CPF: 123.456.789-01", "br_cpf"),
        ("CNPJ: 12.345.678/0001-95", "br_cnpj"),
        ("IBAN: DE89370400440532013000", "iban"),
        ("SWIFT: DEUTDEFF500", "swift_bic"),
        ("VAT: DE123456789", "eu_vat"),
        ("Driver License: D123-4567-8901", "labeled_sensitive_id"),
        ("Tax ID: ZZ-991-ABC-7781", "labeled_sensitive_id"),
        ("api_key=supersecretvalue123", "secret_assignment"),
        ("DB: postgres://admin:secretpass@db.internal:5432/app", "credential_uri"),
        ("Phone: +1 (415) 555-2671", "phone"),
        ("IPv4: 10.0.0.1", "ipv4"),
        ("IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334", "ipv6"),
        ("AWS: AKIAABCDEFGHIJKLMNOP", "aws_access_key"),
        ("Google key: AIzaSyAaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "google_api_key"),
        (
            "JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4iLCJpYXQiOjE1MTYyMzkwMjJ9."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "jwt",
        ),
        ("Token: ghp_ABCDEF1234567890", "generic_token"),
        (
            "-----BEGIN PRIVATE KEY-----abc-----END PRIVATE KEY-----",
            "private_key",
        ),
    ],
)
def test_default_rules_matrix_redacts(content: str, rule_name: str) -> None:
    engine = create_default_engine()

    result = engine.redact(content)

    assert "[REDACTED]" in result.content
    assert result.stats.rule_matches.get(rule_name, 0) >= 1


@pytest.mark.parametrize(
    "content",
    [
        "Invalid email: jane@example",
        "Near miss AWS: AKIAABCDEF",
        "Invalid IPv4 token: 999x999x999x999",
        "Random token: ghp_short",
        "Plain 9-digit number: 123456789",
        "All-caps word: REQUIRED",
        "Unknown country IBAN: XX89370400440532013000",
    ],
)
def test_default_rules_matrix_ignores_near_miss_patterns(content: str) -> None:
    engine = create_default_engine()

    result = engine.redact(content)

    assert result.content == content
    assert result.stats.total_matches == 0


def test_redaction_scaling_is_reasonable_for_large_input() -> None:
    engine = create_default_engine()
    line = "Contact jane@example.com token ghp_ABCDEF1234567890 ip 10.0.0.1\n"
    small_content = line * 1_500
    large_content = line * 3_000

    small = engine.redact(small_content)
    large = engine.redact(large_content)

    assert large.stats.total_matches == small.stats.total_matches * 2
    baseline_ms = max(small.stats.elapsed_ms, 0.01)
    scaling_ratio = large.stats.elapsed_ms / baseline_ms
    assert scaling_ratio < 8
    assert large.stats.elapsed_ms < 3000


def test_min_risk_level_high_excludes_medium_and_low_rules() -> None:
    engine = create_default_engine()
    content = "ssn 123-45-6789 email jane@example.com ip 10.0.0.1"

    result = engine.redact(content, config=RedactionConfig(min_risk_level="high"))

    assert "123-45-6789" not in result.content
    assert "jane@example.com" in result.content
    assert "10.0.0.1" in result.content


def test_min_risk_level_medium_includes_medium_excludes_low() -> None:
    engine = create_default_engine()
    content = "email jane@example.com ip 10.0.0.1"

    result = engine.redact(content, config=RedactionConfig(min_risk_level="medium"))

    assert "jane@example.com" not in result.content
    assert "10.0.0.1" in result.content


def test_all_default_rules_have_metadata() -> None:
    for rule in default_rules():
        assert rule.metadata is not None, f"Rule {rule.name!r} is missing metadata"
