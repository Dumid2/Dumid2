---
name: continuous-learning
description: Extract reusable patterns from grant-writing sessions — funder preferences, voice corrections, framing that worked, reviewer feedback — and save them as learned skills for future drafts. Use at the end of a substantial drafting session, or when asked to "remember" a funder preference or writing correction.
---

# Continuous Learning Skill

> **Adapted from [worldflowai/everything-claude-code](https://github.com/worldflowai/everything-claude-code) (MIT).** The original targets software-debugging sessions (error resolution, workarounds) and writes to a per-user global path (`~/.claude/skills/learned/`). Retargeted here for grant-writing work, and pointed at a repo-local path so learned patterns are committed to git and shared with the team — a per-user home-directory path wouldn't survive this repo's ephemeral session containers anyway.

Evaluates a session for extractable, reusable patterns about how GOODProjects grant writing actually works in practice, and saves them as small skill files future sessions can draw on automatically.

## How It Works

1. **Session Evaluation**: At the end of a substantial drafting session (10+ user messages), or on manual `/learn`, review what happened.
2. **Pattern Detection**: Look for the pattern types below.
3. **Skill Extraction**: Save patterns to `.claude/skills/learned/` (`auto_approve` is on — see below).
4. **Report what was saved** — even with auto-save on, always summarize what got written after the fact, so nothing is silent.

## Pattern Types

| Pattern | Description | Example |
|---|---|---|
| `funder_preferences` | What a specific funder values, avoids, or requires that isn't already in `gp-grant-writer` | "TD Bank sponsorship LOIs want community visibility framed first, budget detail second" |
| `voice_corrections` | Edits the user made to bring a draft in line with GOODProjects house style | "Replace 'many families' with the specific percentage from `08-crime-data-and-community-need.md`" |
| `successful_framing` | An argument or angle that the user confirmed worked well | "Framing field trips as workforce-readiness exposure landed better than pure enrichment framing" |
| `reviewer_feedback_patterns` | Recurring notes from human review of drafts (QA gate misses, repeated asks) | "Reviewer keeps asking for named cost drivers in budget narratives, not just totals" |
| `process_workarounds` | Repo/tooling quirks discovered while drafting (file locations, template gaps) | "DC government template expects a separate 2-page attachment for org chart" |

**Ignore:** one-off typos, single-session API/tooling errors, anything already documented in `gp-grant-writer` or the org profile.

## Output Format

Create a skill file at `.claude/skills/learned/[pattern-name]/SKILL.md`:

```markdown
---
name: learned-[pattern-name]
description: [When this should trigger — be specific about the funder/situation]
---

# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Pattern
[The preference/correction/framing — stated as a rule, not a story]

## Example
[The concrete instance this came from]

## Source
[Which draft/conversation this was extracted from, if worth noting]
```

## Process

1. Review the session (or the specific thing the user just told you to remember).
2. Check it isn't redundant with `gp-grant-writer`, `grants`, or an existing `learned/` skill — if it's a funder-specific fact, prefer updating that funder's section in `gp-grant-writer`'s canon over creating a new tiny skill.
3. Draft the skill file and save it directly to `.claude/skills/learned/[pattern-name]/SKILL.md` (`auto_approve: true` in `config.json` — no confirmation gate).
4. Tell the user what was saved, briefly, so it's never silent even though it wasn't asked for first.

## Manual Trigger

Run `/learn` at any point in a session — see `.claude/commands/learn.md`.

## Automatic Trigger (enabled)

Wired as a `Stop` hook in `.claude/settings.json`, running `evaluate-session.sh`. On the first stop attempt of a session with 10+ user messages, the hook blocks the stop once and signals this skill to evaluate the session and save anything worth keeping; a per-session marker file (in `$TMPDIR/claude-continuous-learning/`) stops it from blocking on every subsequent stop attempt in the same session. Short sessions and sessions with no new patterns pass through untouched.
