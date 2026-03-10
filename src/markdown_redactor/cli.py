from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .factory import create_default_engine
from .types import RedactionConfig


def _expand_multi_values(values: Sequence[str] | None) -> tuple[str, ...]:
    if not values:
        return ()

    expanded: list[str] = []
    for value in values:
        parts = [part.strip() for part in value.split(",")]
        expanded.extend(part for part in parts if part)
    return tuple(expanded)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="markdown-redactor")
    parser.add_argument("input", nargs="?", default="-", help="Input markdown file or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="Output file or - for stdout")
    parser.add_argument("--mask", default="[REDACTED]", help="Replacement mask")
    parser.add_argument(
        "--replacement-mode",
        choices=("full", "preserve_last4", "preserve_format"),
        default="full",
        help="How redacted values should be rendered",
    )
    parser.add_argument(
        "--redact-fenced-code-blocks",
        action="store_true",
        help="Redact fenced code blocks",
    )
    parser.add_argument(
        "--redact-inline-code",
        action="store_true",
        help="Redact inline code spans",
    )
    parser.add_argument(
        "--allowlist",
        action="append",
        help="Exact value to preserve; repeat or use comma-separated values",
    )
    parser.add_argument(
        "--enable-rule",
        action="append",
        help="Only run these rule names; repeat or use comma-separated values",
    )
    parser.add_argument(
        "--disable-rule",
        action="append",
        help="Skip these rule names; repeat or use comma-separated values",
    )
    parser.add_argument("--stats", action="store_true", help="Print stats as JSON to stderr")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    try:
        if args.input == "-":
            source = sys.stdin.read()
        else:
            source = Path(args.input).read_text(encoding="utf-8")

        engine = create_default_engine()
        config = RedactionConfig(
            mask=args.mask,
            replacement_mode=args.replacement_mode,
            skip_fenced_code_blocks=not args.redact_fenced_code_blocks,
            skip_inline_code=not args.redact_inline_code,
            allowlist=_expand_multi_values(args.allowlist),
            enabled_rule_names=(
                _expand_multi_values(args.enable_rule) if args.enable_rule is not None else None
            ),
            disabled_rule_names=_expand_multi_values(args.disable_rule),
        )
        result = engine.redact(source, config=config)

        if args.output == "-":
            sys.stdout.write(result.content)
        else:
            Path(args.output).write_text(result.content, encoding="utf-8")

        if args.stats:
            payload = {
                "total_matches": result.stats.total_matches,
                "rule_matches": result.stats.rule_matches,
                "elapsed_ms": result.stats.elapsed_ms,
                "source_bytes": result.stats.source_bytes,
                "output_bytes": result.stats.output_bytes,
            }
            sys.stderr.write(json.dumps(payload, separators=(",", ":")) + "\n")

        return 0
    except (OSError, ValueError) as exc:
        sys.stderr.write(f"markdown-redactor: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
