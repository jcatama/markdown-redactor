from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Segment:
    text: str
    redactable: bool


def segment_markdown(
    content: str,
    *,
    skip_fenced_code_blocks: bool,
    skip_inline_code: bool,
) -> Iterator[Segment]:
    in_fence = False
    fence_marker = ""
    buffer: list[str] = []
    buffer_redactable = True

    def flush_buffer() -> Iterator[Segment]:
        nonlocal buffer
        if not buffer:
            return
        segment = "".join(buffer)
        buffer = []
        yield Segment(text=segment, redactable=buffer_redactable)

    lines = content.splitlines(keepends=True)

    for line in lines:
        stripped = line.lstrip()
        fence = stripped.startswith("```") or stripped.startswith("~~~")

        if skip_fenced_code_blocks and fence:
            current_marker = stripped[:3]
            if not in_fence:
                yield from flush_buffer()
                in_fence = True
                fence_marker = current_marker
                buffer_redactable = False
                buffer.append(line)
                continue

            if in_fence and current_marker == fence_marker:
                buffer.append(line)
                yield from flush_buffer()
                in_fence = False
                fence_marker = ""
                buffer_redactable = True
                continue

        if in_fence and skip_fenced_code_blocks:
            buffer.append(line)
            continue

        if skip_inline_code:
            yield from flush_buffer()
            yield from _split_inline_code(line)
            continue

        if not buffer:
            buffer_redactable = True
        buffer.append(line)

    yield from flush_buffer()


def _split_inline_code(line: str) -> Iterator[Segment]:
    start = 0
    in_code = False
    i = 0

    while i < len(line):
        if line[i] == "`":
            if i > start:
                yield Segment(text=line[start:i], redactable=not in_code)
            in_code = not in_code
            start = i
            i += 1
            while i < len(line) and line[i] == "`":
                i += 1
            yield Segment(text=line[start:i], redactable=not in_code)
            start = i
            continue
        i += 1

    if start < len(line):
        yield Segment(text=line[start:], redactable=not in_code)
