# Project Instructions

Always follow the `verification-before-completion` skill before claiming any code change is complete, fixed, working, or passing: run the actual command that proves the claim, read its output, then state the result — never assert success without fresh evidence.

The other Superpowers skills in `.claude/skills/` (brainstorming, TDD, etc.) are available on-demand but not mandatory before every response.

## External research for grants (funders, portals, eligibility)

`WebFetch` is unreliable in this environment for arbitrary external sites — this is a network policy limitation of the environment itself, confirmed by testing, not a per-site issue. Do not rely on it for funder or portal research.

- Use `WebSearch` and `Exa` (`web_search_exa` / `web_fetch_exa`) for funder/portal research instead. Cross-check anything that will drive a go/no-go decision or get written into a submitted document against at least two independent sources.
- Every factual claim about a funder (eligibility, deadline, contact, cap, process) that appears in a grant narrative, portal answer, or qualification note must trace to an actual tool call made in that session. If it is not verified, label it `UNVERIFIED` rather than stating it as fact.
- A no-go recommendation requires a confirmed, sourced disqualifying fact. "Could not verify" is never grounds for no-go — if verification is genuinely blocked, flag it as an `OPEN ITEM` for a human to confirm (phone, email, direct check), not a silent no-go and not a guess.
