# FAQ

## Is this a complete DLP solution?

No. It is a fast, pluggable redaction layer for markdown before LLM use.

## Why are code blocks not redacted by default?

To avoid breaking technical examples and snippets. You can enable redaction in code with CLI flags or config.

## Can I add organization-specific rules?

Yes. Register custom rules through `RuleRegistry` and pass it to `RedactionEngine`.

## Does order of rules matter?

Yes. Rules run in registration order.

## Can I process very large files?

Yes, but benchmark with your workload and rule set. Complexity is `O(n * r)`.
