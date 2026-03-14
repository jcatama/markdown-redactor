from __future__ import annotations

import pytest

from markdown_redactor import NERRule, RedactionConfig, RuleMetadata
from markdown_redactor.types import RuleContext


def test_ner_rule_instantiates_without_spacy() -> None:
    rule = NERRule()

    assert rule.name == "ner"
    assert rule.model == "en_core_web_sm"
    assert "PERSON" in rule.entity_labels
    assert "ORG" in rule.entity_labels
    assert "GPE" in rule.entity_labels
    assert "LOC" in rule.entity_labels
    assert rule.metadata is None


def test_ner_rule_custom_params() -> None:
    rule = NERRule(
        name="names",
        model="en_core_web_md",
        entity_labels=frozenset({"PERSON"}),
        metadata=RuleMetadata(category="pii", risk_level="high", description="Person names"),
    )

    assert rule.name == "names"
    assert rule.model == "en_core_web_md"
    assert rule.entity_labels == frozenset({"PERSON"})
    assert rule.metadata is not None
    assert rule.metadata.risk_level == "high"


@pytest.fixture(scope="module")
def nlp_available() -> None:
    spacy = pytest.importorskip("spacy")
    try:
        spacy.load("en_core_web_sm")
    except OSError:
        pytest.skip("en_core_web_sm not installed; run: python -m spacy download en_core_web_sm")


def test_ner_redacts_person_name(nlp_available: None) -> None:
    rule = NERRule()
    content = "Barack Obama spoke at the event."

    updated, count = rule.redact(content, RedactionConfig(), RuleContext())

    assert count >= 1
    assert "Barack Obama" not in updated
    assert "[REDACTED]" in updated


def test_ner_redacts_organisation(nlp_available: None) -> None:
    rule = NERRule()
    content = "She joined Google last year."

    updated, count = rule.redact(content, RedactionConfig(), RuleContext())

    assert count >= 1
    assert "Google" not in updated


def test_ner_no_entities_returns_unchanged(nlp_available: None) -> None:
    rule = NERRule()
    content = "The weather is nice today."

    updated, count = rule.redact(content, RedactionConfig(), RuleContext())

    assert count == 0
    assert updated == content


def test_ner_entity_label_filter_person_only(nlp_available: None) -> None:
    rule = NERRule(entity_labels=frozenset({"PERSON"}))
    content = "Barack Obama founded no company."

    updated, count = rule.redact(content, RedactionConfig(), RuleContext())

    assert "Barack Obama" not in updated


def test_ner_audit_log_records_entries(nlp_available: None) -> None:
    rule = NERRule()
    entries: list = []
    context = RuleContext(audit_entries=entries)
    content = "Barack Obama visited the United Nations."

    rule.redact(content, RedactionConfig(collect_audit_log=True), context)

    ner_entries = [e for e in entries if e.rule_name == "ner"]
    assert len(ner_entries) >= 1
    for entry in ner_entries:
        assert content[entry.start : entry.end] in content
        assert len(entry.original_hash) == 16
        assert entry.replacement == "[REDACTED]"


def test_ner_audit_log_positions_match_original(nlp_available: None) -> None:
    rule = NERRule(entity_labels=frozenset({"PERSON"}))
    entries: list = []
    context = RuleContext(audit_entries=entries)
    content = "Contact Barack Obama directly."

    rule.redact(content, RedactionConfig(collect_audit_log=True), context)

    person_entries = [e for e in entries if e.rule_name == "ner"]
    for entry in person_entries:
        assert content[entry.start : entry.end] == "Barack Obama"
