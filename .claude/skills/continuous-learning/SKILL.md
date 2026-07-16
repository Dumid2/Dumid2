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
3. **Confirm with the user** — never save a learned pattern silently. Show the draft skill file and ask before writing it.
4. **Skill Extraction**: Save confirmed patterns to `.claude/skills/learned/`.

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
3. Draft the skill file.
4. **Show the user the draft and ask before saving.** `auto_approve` is off by default — see `config.json`.
5. Save to `.claude/skills/learned/[pattern-name]/SKILL.md`.

## Manual Trigger

Run `/learn` at any point in a session — see `.claude/commands/learn.md`.

## Automatic Trigger (opt-in, not enabled by default)

The original repo wires this to a Stop hook so it fires automatically at session end. That's **not enabled here** — it would mean every session silently runs a script and nudges pattern-extraction on close, which is a standing behavior change worth an explicit yes. `evaluate-session.sh` is included for reference; to enable it, add it to a `Stop` hook in `.claude/settings.json` and confirm with the team first, since it affects every session in this shared repo.
