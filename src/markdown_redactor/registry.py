from __future__ import annotations

from collections.abc import Iterable

from .types import RedactionRule


class RuleRegistry:
    def __init__(self) -> None:
        self._rules: list[RedactionRule] = []

    def register(self, rule: RedactionRule) -> None:
        if any(r.name == rule.name for r in self._rules):
            raise ValueError(f"Rule {rule.name!r} is already registered")
        self._rules.append(rule)

    def extend(self, rules: Iterable[RedactionRule]) -> None:
        for rule in rules:
            self.register(rule)

    def list_rules(self) -> tuple[RedactionRule, ...]:
        return tuple(self._rules)
