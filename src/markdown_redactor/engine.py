from __future__ import annotations

import time
from collections import defaultdict

from .markdown import segment_markdown
from .registry import RuleRegistry
from .types import RedactionConfig, RedactionResult, RedactionStats, RuleContext


class RedactionEngine:
    def __init__(self, registry: RuleRegistry | None = None) -> None:
        self._registry = registry if registry is not None else RuleRegistry()

    @property
    def registry(self) -> RuleRegistry:
        return self._registry

    def redact(
        self,
        content: str,
        *,
        config: RedactionConfig | None = None,
        context: RuleContext | None = None,
    ) -> RedactionResult:
        active_config = config if config is not None else RedactionConfig()
        active_context = context if context is not None else RuleContext()

        start = time.perf_counter()
        rule_counts: defaultdict[str, int] = defaultdict(int)
        output: list[str] = []

        for segment in segment_markdown(
            content,
            skip_fenced_code_blocks=active_config.skip_fenced_code_blocks,
            skip_inline_code=active_config.skip_inline_code,
        ):
            if not segment.redactable:
                output.append(segment.text)
                continue

            updated = segment.text
            for rule in self._registry.list_rules():
                updated, count = rule.redact(updated, active_config, active_context)
                if count:
                    rule_counts[rule.name] += count
            output.append(updated)

        redacted_content = "".join(output)
        elapsed_ms = (time.perf_counter() - start) * 1000
        total_matches = sum(rule_counts.values())

        return RedactionResult(
            content=redacted_content,
            stats=RedactionStats(
                total_matches=total_matches,
                rule_matches=dict(rule_counts),
                elapsed_ms=elapsed_ms,
                source_bytes=len(content.encode("utf-8")),
                output_bytes=len(redacted_content.encode("utf-8")),
            ),
        )
