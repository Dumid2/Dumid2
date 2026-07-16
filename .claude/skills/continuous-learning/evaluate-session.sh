#!/bin/bash
# Continuous Learning - Session Evaluator
# Reference script for a Stop hook that nudges pattern-extraction at session end.
# NOT wired into .claude/settings.json by default — see SKILL.md "Automatic Trigger".
#
# Why Stop hook instead of UserPromptSubmit:
# - Stop runs once at session end (lightweight)
# - UserPromptSubmit runs every message (heavy, adds latency)
#
# To enable (after confirming with the team):
# {
#   "hooks": {
#     "Stop": [{
#       "matcher": "*",
#       "hooks": [{
#         "type": "command",
#         "command": "$CLAUDE_PROJECT_DIR/.claude/skills/continuous-learning/evaluate-session.sh"
#       }]
#     }]
#   }
# }
#
# Patterns to detect: funder_preferences, voice_corrections, successful_framing,
#                      reviewer_feedback_patterns, process_workarounds
# Patterns to ignore: simple_typos, one_time_fixes, external_api_issues
# Extracted skills saved to: .claude/skills/learned/ (repo-local, git-tracked)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config.json"
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
LEARNED_SKILLS_PATH="$PROJECT_DIR/.claude/skills/learned"
MIN_SESSION_LENGTH=10

# Load config if exists
if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  MIN_SESSION_LENGTH=$(jq -r '.min_session_length // 10' "$CONFIG_FILE")
  relative_path=$(jq -r '.learned_skills_path // ".claude/skills/learned/"' "$CONFIG_FILE")
  LEARNED_SKILLS_PATH="$PROJECT_DIR/${relative_path#./}"
fi

# Ensure learned skills directory exists
mkdir -p "$LEARNED_SKILLS_PATH"

# Get transcript path from environment (set by Claude Code)
transcript_path="${CLAUDE_TRANSCRIPT_PATH:-}"

if [ -z "$transcript_path" ] || [ ! -f "$transcript_path" ]; then
  exit 0
fi

# Count messages in session
message_count=$(grep -c '"type":"user"' "$transcript_path" 2>/dev/null || echo "0")

# Skip short sessions
if [ "$message_count" -lt "$MIN_SESSION_LENGTH" ]; then
  echo "[ContinuousLearning] Session too short ($message_count messages), skipping" >&2
  exit 0
fi

# Signal to Claude that session should be evaluated for extractable patterns
echo "[ContinuousLearning] Session has $message_count messages - evaluate for extractable grant-writing patterns" >&2
echo "[ContinuousLearning] Save learned skills to: $LEARNED_SKILLS_PATH" >&2
