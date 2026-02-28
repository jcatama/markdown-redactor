from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .factory import create_default_engine
from .types import RedactionConfig


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="markdown-redactor")
    parser.add_argument("input", nargs="?", default="-", help="Input markdown file or - for stdin")
    parser.add_argument("-o", "--output", default="-", help="Output file or - for stdout")
    parser.add_argument("--mask", default="[REDACTED]", help="Replacement mask")
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
            skip_fenced_code_blocks=not args.redact_fenced_code_blocks,
            skip_inline_code=not args.redact_inline_code,
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
    except OSError as exc:
        sys.stderr.write(f"markdown-redactor: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
