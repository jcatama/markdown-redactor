from __future__ import annotations

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


def main() -> None:
    registry = RuleRegistry()
    registry.register(TicketRule())
    engine = RedactionEngine(registry=registry)

    content = "Escalation ticket: TICKET-123456"
    result = engine.redact(content)

    print(result.content)
    print(result.stats)


if __name__ == "__main__":
    main()
