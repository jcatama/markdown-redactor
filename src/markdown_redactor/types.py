from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class RuleMetadata:
    category: Literal["pii", "credential", "financial", "network"]
    risk_level: Literal["high", "medium", "low"]
    description: str


_RISK_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}


@dataclass(frozen=True, slots=True)
class RedactionConfig:
    mask: str = "[REDACTED]"
    replacement_mode: Literal["full", "preserve_last4", "preserve_format"] = "full"
    skip_fenced_code_blocks: bool = True
    skip_inline_code: bool = True
    allowlist: tuple[str, ...] = ()
    enabled_rule_names: tuple[str, ...] | None = None
    disabled_rule_names: tuple[str, ...] = ()
    min_risk_level: Literal["high", "medium", "low"] | None = None


@dataclass(frozen=True, slots=True)
class RuleContext:
    file_path: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


class RedactionRule(Protocol):
    name: str
    metadata: RuleMetadata | None

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        ...


@dataclass(frozen=True, slots=True)
class RedactionStats:
    total_matches: int
    rule_matches: Mapping[str, int]
    elapsed_ms: float
    source_bytes: int
    output_bytes: int


@dataclass(frozen=True, slots=True)
class RedactionResult:
    content: str
    stats: RedactionStats
