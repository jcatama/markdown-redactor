from __future__ import annotations

from dataclasses import dataclass

from markdown_redactor import RedactionConfig, RuleContext, create_tenant_engine


@dataclass(frozen=True, slots=True)
class TicketRule:
    name: str = "ticket_id"

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        updated = content.replace("TICKET-", f"{config.mask}-")
        count = content.count("TICKET-")
        return updated, count


def test_create_tenant_engine_with_defaults() -> None:
    engine = create_tenant_engine([TicketRule()])
    content = "email jane@example.com ticket TICKET-123"

    result = engine.redact(content)

    assert "jane@example.com" not in result.content
    assert "TICKET-123" not in result.content
    assert result.stats.rule_matches.get("email", 0) == 1
    assert result.stats.rule_matches.get("ticket_id", 0) == 1


def test_create_tenant_engine_without_defaults() -> None:
    engine = create_tenant_engine([TicketRule()], include_default_rules=False)
    content = "email jane@example.com ticket TICKET-123"

    result = engine.redact(content)

    assert "jane@example.com" in result.content
    assert "TICKET-123" not in result.content
    assert result.stats.rule_matches.get("email", 0) == 0
    assert result.stats.rule_matches.get("ticket_id", 0) == 1
