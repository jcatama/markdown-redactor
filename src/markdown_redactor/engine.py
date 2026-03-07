from __future__ import annotations

import time
from collections import defaultdict

from .markdown import segment_markdown
from .registry import RuleRegistry
from .types import RedactionConfig, RedactionResult, RedactionRule, RedactionStats, RuleContext


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
        active_rules = self._active_rules(active_config)

        for segment in segment_markdown(
            content,
            skip_fenced_code_blocks=active_config.skip_fenced_code_blocks,
            skip_inline_code=active_config.skip_inline_code,
        ):
            if not segment.redactable:
                output.append(segment.text)
                continue

            updated, placeholders = self._protect_allowlist(segment.text, active_config)
            for rule in active_rules:
                updated, count = rule.redact(updated, active_config, active_context)
                if count:
                    rule_counts[rule.name] += count
            updated = self._restore_allowlist(updated, placeholders)
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

    def _active_rules(self, config: RedactionConfig) -> tuple[RedactionRule, ...]:
        rules = self._registry.list_rules()
        enabled = set(config.enabled_rule_names) if config.enabled_rule_names is not None else None
        disabled = set(config.disabled_rule_names)

        return tuple(
            rule
            for rule in rules
            if (enabled is None or rule.name in enabled) and rule.name not in disabled
        )

    def _protect_allowlist(
        self,
        content: str,
        config: RedactionConfig,
    ) -> tuple[str, dict[str, str]]:
        if not config.allowlist:
            return content, {}

        placeholders: dict[str, str] = {}
        updated = content
        for index, value in enumerate(sorted(set(config.allowlist), key=len, reverse=True)):
            if not value or value not in updated:
                continue
            placeholder = f"\x00MR_ALLOWLIST_{index}\x00"
            updated = updated.replace(value, placeholder)
            placeholders[placeholder] = value
        return updated, placeholders

    def _restore_allowlist(self, content: str, placeholders: dict[str, str]) -> str:
        updated = content
        for placeholder, value in placeholders.items():
            updated = updated.replace(placeholder, value)
        return updated
