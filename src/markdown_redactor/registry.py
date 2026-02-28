from __future__ import annotations

from collections.abc import Iterable

from .types import RedactionRule


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: list[RedactionRule] = []

    def register(self, rule: RedactionRule) -> None:
        self._rules.append(rule)

    def extend(self, rules: Iterable[RedactionRule]) -> None:
        self._rules.extend(rules)

    def list_rules(self) -> tuple[RedactionRule, ...]:
        return tuple(self._rules)
