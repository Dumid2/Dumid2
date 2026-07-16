---
name: security-review
description: Use when adding authentication, handling user/uploaded input, creating or changing FastAPI endpoints, working with secrets, or before deploying app/ anywhere reachable over a network. Checklist tuned to this repo's actual stack (FastAPI, Pydantic, SQLite, python-dotenv, Anthropic API).
---

# Security Review Skill

> **Rewritten from [worldflowai/everything-claude-code](https://github.com/worldflowai/everything-claude-code)'s `security-review` (MIT).** The original is a Next.js/Supabase/Solana checklist (JWT-in-cookies, Row Level Security, wallet-signature verification) — none of which applies to this repo's plain FastAPI + SQLite + Anthropic-API stack. Rewritten against `app/main.py`, `app/schemas.py`, and `app/db.py` directly instead of vendored as-is.

This skill ensures `app/` follows security practices appropriate to a small internal FastAPI service that handles nonprofit financial/compliance data and calls the Anthropic API.

## When to Activate

- Adding or changing a FastAPI endpoint in `app/main.py`
- Handling user input, form fields, or file uploads (`UploadFile`)
- Working with `ANTHROPIC_API_KEY` or any other secret
- Before deploying this app anywhere reachable outside localhost

## Checklist

### 1. Secrets Management

- [ ] No hardcoded API keys — `ANTHROPIC_API_KEY` loads via `python-dotenv`/`os.environ`, never a literal string
- [ ] `.env` is in `.gitignore` (confirmed: it is) — only `.env.example` is committed, and it must stay empty of real values
- [ ] No secrets in git history (`git log -p -- .env` should show nothing)
- [ ] Production secrets set via the hosting platform's env var mechanism, not baked into an image

### 2. Input Validation

- [x] **Already good**: every endpoint takes a Pydantic model (`GrantDraftRequest`, etc.) — FastAPI rejects malformed JSON automatically. Keep new endpoints on this pattern; don't accept raw `dict`/`Any`.
- [ ] New fields should have real types/constraints (e.g. `requested_amount: float | None`, not `str`), so bad input fails at the schema boundary, not deep in `grant_agent.py`

### 3. File Upload Validation

- [x] **Already good**: `_read_pdf()` in `app/main.py` checks `content_type == "application/pdf"` and enforces `MAX_PDF_SIZE` (32MB) before reading.
- [ ] Content-type is client-supplied and spoofable — for anything beyond internal use, verify the PDF magic bytes (`%PDF-`) rather than trusting `file.content_type` alone
- [ ] `supporting_documents` has no cap on file *count* — a request with hundreds of files each just under 32MB isn't blocked by the current check

### 4. SQL Injection

- [x] **Already good**: `app/db.py` uses parameterized `?` placeholders throughout (`conn.execute("... WHERE id = ?", (draft_id,))`). Keep it that way — never f-string or `.format()` a value into a SQL string.

### 5. Authentication & Authorization

- [ ] **Current gap**: every endpoint in `app/main.py` — including `/grants/drafts` (list) and `/grants/drafts/{id}` (read) — is unauthenticated. Anyone who can reach this service can read every saved draft (which includes budget figures and funder strategy) and create new ones.
- [ ] If this ever runs anywhere beyond localhost/a trusted network, add at minimum an API key or basic auth dependency on the router before exposing it.
- [ ] No role/ownership model exists — there's only one implicit "org," so this may be acceptable for a single-tenant internal tool, but it should be a conscious decision, not an oversight.

### 6. Rate Limiting / Cost Control

- [ ] **Current gap**: `/grants/draft` and `/grants/draft/upload` call the Anthropic API with no rate limit. An unauthenticated, unthrottled endpoint that spends API budget per request is a real cost-abuse vector if this is ever network-reachable.
- [ ] If deployed beyond localhost, add per-IP or per-key rate limiting (e.g. `slowapi`) on the two drafting endpoints specifically.

### 7. Error / Exception Handling

- [ ] **Current gap**: `draft_grant` and `draft_grant_with_documents` both do `raise HTTPException(status_code=502, detail=str(exc))` — this returns the raw Python exception message (which can include internal file paths, library stack detail, or Anthropic API error internals) directly to the client.
- [ ] Prefer logging the full exception server-side and returning a generic `detail` to the caller, e.g. `detail="Draft generation failed; check server logs."`

### 8. Sensitive Data in Logs

- [ ] Don't log full `GrantDraftRequest` bodies or PDF contents at INFO level in production — they contain nonprofit budget/strategy data
- [ ] If logging is added, redact or omit `request_json` and `draft` fields

### 9. Dependency Security

- [ ] Run `pip list --outdated` / `pip-audit` periodically — `requirements.txt` pins lower bounds (`>=`) only, so nothing prevents pulling a newer, potentially vulnerable transitive dependency
- [ ] Consider pinning exact versions (or a lockfile) once this moves toward production use, for reproducible installs

## Pre-Deployment Checklist

Before running this anywhere beyond localhost:

- [ ] Secrets: confirmed via env vars only, `.env` not committed
- [ ] Auth: added if the service is reachable outside a trusted network
- [ ] Rate limiting: added on `/grants/draft` and `/grants/draft/upload`
- [ ] Error handling: exception details no longer returned raw to clients
- [ ] File upload: PDF magic-byte check added if untrusted users can upload
- [ ] Dependencies: `pip-audit` clean

## Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security docs](https://fastapi.tiangolo.com/tutorial/security/)
