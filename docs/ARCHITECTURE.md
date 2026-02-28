# Architecture

## Overview

`markdown-redactor` is built around a small core:

- `RedactionEngine`: orchestrates markdown segmentation and rule execution
- `RuleRegistry`: stores active rules in execution order
- `RedactionRule` protocol: contract for custom plugins
- `RedactionConfig` and `RuleContext`: runtime behavior and optional metadata

## Data flow

1. Input markdown is segmented into redactable and non-redactable segments.
2. Non-redactable segments are copied as-is.
3. Redactable segments are passed through all registered rules in order.
4. Output segments are joined and stats are returned.

## Key design choices

- Keep runtime lightweight (no external runtime dependencies)
- Keep behavior deterministic and easy to reason about
- Keep extension model explicit via protocol + registry
- Keep processing cost linear over input and rules

## Extension model

A rule plugin must:

- expose `name`
- implement `redact(content, config, context) -> (content, count)`

Rules should be pure and side-effect free where possible.

## Performance model

Let:

- `n` = input size
- `r` = number of active rules

Complexity:

- time: `O(n * r)`
- memory: `O(n)`

## Operational observability

Engine results include:

- total match count
- per-rule match counts
- elapsed time in milliseconds
- source/output size in bytes
