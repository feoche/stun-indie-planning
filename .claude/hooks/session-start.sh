#!/bin/bash
set -euo pipefail

# Uniquement dans les sessions cloud (Claude Code web / mobile)
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/../..}"
pip install -q -r requirements.txt
