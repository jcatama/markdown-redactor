from __future__ import annotations

from dataclasses import dataclass

from markdown_redactor import RedactionConfig, RedactionEngine, RuleContext, RuleRegistry


@dataclass(frozen=True, slots=True)
class DemoRule:
    name: str = "demo"

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        updated = content.replace("SECRET", config.mask)
        count = content.count("SECRET")
        return updated, count


def test_registry_custom_rule() -> None:
    registry = RuleRegistry()
    registry.register(DemoRule())
    engine = RedactionEngine(registry=registry)

    result = engine.redact("SECRET and SECRET")

    assert result.content == "[REDACTED] and [REDACTED]"
    assert result.stats.rule_matches["demo"] == 2
