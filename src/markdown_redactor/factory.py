from __future__ import annotations

from collections.abc import Iterable

from .engine import RedactionEngine
from .registry import RuleRegistry
from .rules import default_rules
from .types import RedactionRule


def create_default_engine() -> RedactionEngine:
    registry = RuleRegistry()
    registry.extend(default_rules())
    return RedactionEngine(registry=registry)


def create_tenant_engine(
    tenant_rules: Iterable[RedactionRule],
    *,
    include_default_rules: bool = True,
    tenant_rules_first: bool = False,
) -> RedactionEngine:
    registry = RuleRegistry()

    if include_default_rules and not tenant_rules_first:
        registry.extend(default_rules())

    registry.extend(tenant_rules)

    if include_default_rules and tenant_rules_first:
        registry.extend(default_rules())

    return RedactionEngine(registry=registry)
