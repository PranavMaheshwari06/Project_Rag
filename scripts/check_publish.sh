#!/usr/bin/env bash
# Publish rule check: run before every commit. Fails if a staged change would publish
# build-only material or text that must not be public. See CLAUDE.md, "Publish rule".
set -u
cd "$(git rev-parse --show-toplevel)"
bad=0

# 1. build-only paths
paths=$(git diff --cached --name-only --diff-filter=AM | grep -E '(^docs/working/|(^|/)STATUS\.md$|(^|/)CLAUDE\.md$|WORKSHEET|audit_sheet|Audit_sheet|^graphify-out/|^\.claude/|^\.env$)')
if [ -n "$paths" ]; then echo "build-only paths staged:"; echo "$paths"; bad=1; fi

# 2. phrases that mark working papers or AI attribution (added lines only)
hits=$(git diff --cached -U0 -- . ':!scripts/check_publish.sh' | grep -E '^\+[^+]' | grep -n -i -E 'you answer|Co-Authored-By|Generated with|Claude Code' || true)
if [ -n "$hits" ]; then echo "staged text matches a blocked phrase:"; echo "$hits"; bad=1; fi

[ "$bad" -eq 0 ] && echo "publish check: ok"
exit "$bad"
