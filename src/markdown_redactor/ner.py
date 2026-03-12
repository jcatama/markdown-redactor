from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from spacy.language import Language

from .rules import _replacement_value
from .types import AuditEntry, RedactionConfig, RuleContext, RuleMetadata, _hash_value

_NLP_CACHE: dict[str, Language] = {}


def _get_nlp(model: str) -> Language:
    if model not in _NLP_CACHE:
        try:
            import spacy
        except ImportError as exc:
            raise ImportError(
                "spacy is required for NERRule.\n"
                "Install it with: pip install 'markdown-redactor[ner]'\n"
                "Then download a model: python -m spacy download en_core_web_sm"
            ) from exc
        _NLP_CACHE[model] = spacy.load(model)
    return _NLP_CACHE[model]


@dataclass(frozen=True, slots=True)
class NERRule:
    name: str = "ner"
    model: str = "en_core_web_sm"
    entity_labels: frozenset[str] = frozenset({"PERSON", "ORG", "GPE", "LOC"})
    metadata: RuleMetadata | None = None

    def redact(
        self,
        content: str,
        config: RedactionConfig,
        context: RuleContext,
    ) -> tuple[str, int]:
        nlp = _get_nlp(self.model)
        doc = nlp(content)
        matches = [
            (ent.start_char, ent.end_char, ent.text)
            for ent in doc.ents
            if ent.label_ in self.entity_labels
        ]
        if not matches:
            return content, 0

        replacements = [
            (start, end, orig, _replacement_value(orig, config))
            for start, end, orig in matches
        ]
        if context.audit_entries is not None:
            for start, end, orig, repl in replacements:
                context.audit_entries.append(
                    AuditEntry(
                        rule_name=self.name,
                        start=context.segment_start + start,
                        end=context.segment_start + end,
                        original_hash=_hash_value(orig),
                        replacement=repl,
                    )
                )
        result = content
        for start, end, _orig, repl in sorted(replacements, key=lambda x: x[0], reverse=True):
            result = result[:start] + repl + result[end:]
        return result, len(replacements)
