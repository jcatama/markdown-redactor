from __future__ import annotations

from markdown_redactor import create_default_engine


def main() -> None:
    engine = create_default_engine()
    content = """
Customer email: jane@example.com
Server: 10.0.0.1
Card: 4111 1111 1111 1111
"""
    result = engine.redact(content)
    print(result.content)
    print(result.stats)


if __name__ == "__main__":
    main()
