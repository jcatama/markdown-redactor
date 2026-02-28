#!/usr/bin/env bash
set -euo pipefail

markdown-redactor README.md -o /tmp/README.redacted.md --stats
cat README.md | markdown-redactor -
