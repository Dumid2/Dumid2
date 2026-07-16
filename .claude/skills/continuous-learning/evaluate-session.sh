#!/bin/bash
# Continuous Learning - Session Evaluator
# Runs as a Stop hook (wired in .claude/settings.json). On the first Stop
# attempt of a session with enough messages, blocks the stop once (exit 2)
# so Claude evaluates the session for extractable grant-writing patterns
# and saves them per the continuous-learning skill. A marker file prevents
# blocking again on the same session's later Stop attempts.
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

if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  MIN_SESSION_LENGTH=$(jq -r '.min_session_length // 10' "$CONFIG_FILE")
  relative_path=$(jq -r '.learned_skills_path // ".claude/skills/learned/"' "$CONFIG_FILE")
  LEARNED_SKILLS_PATH="$PROJECT_DIR/${relative_path#./}"
fi

mkdir -p "$LEARNED_SKILLS_PATH"

transcript_path="${CLAUDE_TRANSCRIPT_PATH:-}"

if [ -z "$transcript_path" ] || [ ! -f "$transcript_path" ]; then
  exit 0
fi

message_count=$(grep -c '"type":"user"' "$transcript_path" 2>/dev/null || echo "0")

if [ "$message_count" -lt "$MIN_SESSION_LENGTH" ]; then
  exit 0
fi

# Only nudge once per session: mark this transcript as already handled.
marker_dir="${TMPDIR:-/tmp}/claude-continuous-learning"
mkdir -p "$marker_dir"
marker_file="$marker_dir/$(basename "$transcript_path").nudged"

if [ -f "$marker_file" ]; then
  exit 0
fi
touch "$marker_file"

echo "[ContinuousLearning] Session has $message_count messages. Before stopping:" >&2
echo "[ContinuousLearning] review it for funder preferences, voice corrections," >&2
echo "[ContinuousLearning] successful framing, reviewer feedback, or process" >&2
echo "[ContinuousLearning] workarounds worth remembering. Save any found (auto_approve" >&2
echo "[ContinuousLearning] is on) to $LEARNED_SKILLS_PATH per the continuous-learning skill," >&2
echo "[ContinuousLearning] then finish." >&2
exit 2
