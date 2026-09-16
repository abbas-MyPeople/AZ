# AZ growth engine + analytics dashboard — build plan (reuse-first)

**Goal (owner's words):** a guarded `/analytics` dashboard on Hugging Face to see how the AZ site is
performing (where people go, what's happening), **plus** a daily agent loop that analyzes what's working
and why, proposes site changes, **emails a brief**, and — on an emailed **approval or reply-with-
instructions** — actions the change. Full working loop, nothing breaks.

**Strategy:** this is the same system already **built and running for the restaurant** — the
`analytics/` dashboard (guarded, on HF) and `seo_engine/` (the closed loop with email send + IMAP
reply-ingestion). We **port and retarget** it to the AZ site. Almost every credential is reused.

---

## Architecture (mirrors the restaurant, retargeted to AZ)

- **Dashboard** → **Hugging Face Space** (Docker, private, Basic-auth). Reads **GA4** for the AZ property
  (`G-3GEL1D477G`) + optional Search Console. Auto-deployed from this repo's `analytics/` folder by a
  GitHub Action (mirror of `sync-hf-space.yml`). *(No Clover for AZ — AZ has no POS; MEASURE = web analytics.)*
- **Growth loop** → **GitHub Actions cron in THIS repo** (`abbas-MyPeople/AZ`). Because the AZ site
  *is* this repo (GitHub Pages serves root on `main`), the engine commits approved changes straight to
  `main` → Pages redeploys. Same-repo = uses the built-in `GITHUB_TOKEN`; **no PAT needed.**
- **Email loop** → the existing engine Gmail (`WK_ENGINE_EMAIL`/`WK_ENGINE_APP_PASSWORD`) sends the brief
  (SMTP) and reads your reply (IMAP), exactly as the restaurant does. Reply-ingestion already exists
  (`seo_engine/inbox.py` + `reply_parse.py`).

## What is REUSED as-is (no new keys)
- **`GROQ_API_KEY`** — the LLM (Llama-3.3-70B on Groq) for analysis + interpreting your freeform replies.
- **`HF_TOKEN`** — deploys the dashboard Space.
- **GA4 service account** (`ga4-reader-sa.json`) — the *same* SA reads the AZ property once it's granted access.
- **Engine Gmail** (`WK_ENGINE_EMAIL` + `WK_ENGINE_APP_PASSWORD`) — send + reply-ingest, same account.
- **Built-in `GITHUB_TOKEN`** — commits approved edits to this repo.
- The whole machinery: `ga4.py`, `gsc.py`, the Basic-auth + Docker + HF-sync pattern, and the loop
  (`model.py`, `compose.py`, `notify.py`, `inbox.py`, `reply_parse.py`, `execute.py`, `run.py`).

## What is NEW code we write (I build this — no keys needed)
1. **AZ dashboard app** — a lean GA4-focused Flask app (reuses `ga4.py` + auth + Dockerfile), showing
   traffic, top pages, the section-view funnel, CTA clicks, conversions (`lead_submit`/`call_click`/
   `finder_capture`), sources, drop-off. Groq chat over the data.
2. **A GA4 sensor for the loop** — the restaurant loop measures Clover; the AZ loop measures **GA4**
   (reuse `ga4.py`). Turns GA4 deltas into `finding`s (what's up/down, dead CTAs, drop-offs).
3. **AZ executors** — deterministic edit templates for AZ pages (headline/CTA/order/A-B swaps) writing to
   THIS repo's root site files (not `website-v2/`).
4. **LLM freeform-reply actioner** — the piece the restaurant flagged as *not wired*: when you reply with
   instructions (not just "approve/reject"), Groq interprets intent → a bounded, validated edit → commit.
   Ambiguous → it emails you back to confirm rather than guessing.
5. **AZ config swaps** — owner allowlist (`azoeb52@gmail.com`), site URL, GA4 property id, HF Space name,
   `main`-branch same-repo commit path.

## Guardrails (nothing breaks)
- **Human-in-the-loop:** nothing ships without your emailed approval; only approved items execute;
  unmentioned items roll over (never auto-approve).
- **Fail-closed sender allowlist** on replies (only your email can approve).
- **Validate before commit:** HTML parses, every JSON-LD block `json.loads`-clean, `node --check` on JS —
  reject the edit if anything breaks.
- **Small, revertible commits** (one `git revert` each); full audit trail in the loop's `state/` JSONL.
- **Scope fence:** the engine only edits AZ marketing pages — never `stocks/`, `command/`, or workflows.
- **Cost cap + kill switch** on the LLM; dry-run default; secrets never printed.

## Owner steps — the ONLY genuinely new things (everything else reuses existing keys)

**Step 1 — Give the existing GA4 service account read access to the AZ property (2 min).**
- GA4 → **Admin** (gear) → under *Property*, **Property access management** → **+** → add the service-account
  email (it's the `client_email` in the restaurant's `ga4-reader-sa.json`; I'll paste it to you) → role **Viewer** → Add.
- Then **Admin → Property details** → copy the numeric **Property ID** (looks like `123456789` — this is
  NOT the `G-` measurement id) and send it to me.

**Step 2 — Put the reused secret VALUES where the AZ engine/dashboard run** (I can't copy secret values myself).
- GitHub → this repo → **Settings → Secrets and variables → Actions → New repository secret**, add (same
  values as the restaurant): `HF_TOKEN`, `GROQ_API_KEY`, `GA4_SA_JSON` (paste the full JSON), `GA4_PROPERTY_ID`
  (from Step 1), `WK_ENGINE_EMAIL`, `WK_ENGINE_APP_PASSWORD`, `AUTH_USER`, `AUTH_PASS`.
- In the new **Hugging Face Space** → Settings → Secrets, add the same `GA4_SA_JSON`, `GA4_PROPERTY_ID`,
  `GROQ_API_KEY`, `AUTH_USER`, `AUTH_PASS`. (I'll create the Space wiring; you paste the values.)

**Step 3 — Confirm the approval email address** (default `azoeb52@gmail.com`, already on the restaurant
allowlist). Tell me if you want a different one.

*(Optional, skip for now: Google Places key + Place ID for a reviews panel; Clover — N/A for AZ.)*

## Build order
1. Dashboard (this doc's first deliverable) → deploy to HF, verify it shows GA4 once Step 1–2 done.
2. GA4 sensor + AZ executors + config → the loop MEASURE/ACT retargeted.
3. LLM freeform-reply actioner + the two cron workflows (weekly propose+send, daily read+execute).
4. Dry-run end-to-end, then flip live behind your email approval.
