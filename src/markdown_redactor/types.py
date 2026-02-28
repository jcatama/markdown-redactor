from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RedactionConfig:
    mask: str = "[REDACTED]"
    skip_fenced_code_blocks: bool = True
    skip_inline_code: bool = True


@dataclass(frozen=True, slots=True)
class RuleContext:
    file_path: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)


class RedactionRule(Protocol):
    name: str

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
