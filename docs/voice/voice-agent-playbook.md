<!-- ⚠️ MIGRATED 2026-07-01 → canonical copy now lives in the AZ repo at
     abbas-MyPeople/Abbas : flagship/voice-agent-playbook.md. Kept here for history.
     Edit the AZ-repo copy, not this one. See docs/az-bridge.md. -->

# AZ Restaurant Partners — Voice Agent Playbook

> The distilled philosophy behind building a restaurant phone-ordering voice agent, from the
> highest-level principles down to the nitty-gritty engineering rules. Inferred from the full
> build of the Wok & Karahi agent (every feature, decision, and course-correction), then
> **generalized** — nothing here is Wok-specific. This is the template we bring to every client.
>
> **How to use it:** a client engagement swaps the *data and config* (their POS, their
> best-sellers, their brand voice, their escalation contacts) — the *principles* stay fixed.

---

## 0. The one-line thesis
**A great restaurant voice agent is not "a bot that takes orders." It is the restaurant's best
front-of-house employee — one who sounds human, never gets the menu wrong, remembers regulars,
handles an angry caller with real care, upsells like a friend, protects the business, and quietly
captures everything the owner needs to know.** Every principle below serves that.

---

## 1. High-level philosophy (the "why")

1. **Sound like a person, not an "AI."** The single biggest driver of trust. Skeptics must stay
   comfortable. This is voice + cadence + *word choice* + timing — not just the TTS engine.
2. **Match the voice to the brand and the clientele.** A desi restaurant wants a voice that says
   its dishes and greetings correctly and feels culturally at home; a diner wants warm-American.
   The voice is a brand asset, not a default. **Pick deliberately, lock it once approved.**
3. **Never invent. Ground everything in the client's real data.** Every item, price, promo, hour,
   and recommendation traces to the POS / the restaurant's real numbers. Anti-hallucination is
   non-negotiable — a made-up price or a dish they don't serve is a broken promise on a live call.
4. **Be genuinely smart, from real behavior — not guesses.** Recommend what actually sells. Default
   to what people actually pick. Personalization comes from *behavior and history*, never from
   profiling. (When a client asks for something dubious — e.g. "guess the caller's ethnicity" —
   deliver the *underlying intent*: behavior-based personalization + returning-caller memory +
   language matching. Read intent, not the literal ask.)
5. **Make regulars feel known.** Recognize the caller, greet them by name, offer "the usual." Loyalty
   is built in the first ten seconds of the second call.
6. **In hard moments, care first.** Complaints and angry callers are where reputation is won or lost.
   Genuine acknowledgement before anything else — then understand, capture, and escalate by real
   damage. Never robotic, never defensive.
7. **The agent is a listening post.** Every complaint, question, suggestion, and bit of praise is
   operational gold. Capture it structurally → feeds an FAQ, a review of what customers say, product
   decisions. The phone line becomes a data source.
8. **Protect the business.** Guardrails against spam, pranks, social engineering, and anything the
   agent shouldn't do (payment, PII, refunds, comps, promises). A helpful agent is still a careful one.
9. **Serve the business's actual goals.** Steer to direct/first-party ordering (off the ~30% delivery
   apps), upsell to raise ticket size, route catering to the right human, decline gracefully what the
   channel can't do. Every interaction nudges toward margin and retention.
10. **Human-in-the-loop for taste; automate the rest.** Subjective calls (voice, tone, pronunciation)
    belong to the operator — give them previews/options and iterate. Objective correctness (hours,
    prices, math) belongs to deterministic code.

---

## 2. Mid-level principles (the "what")

### Conversation design
- **Brevity is the whole game.** One short sentence per turn; name two or three things, then ask a
  question back. Never read a long list. A monologue instantly reads as a machine.
- **Natural turn-taking.** Don't cut the caller off — wait for a full thought (smart endpointing +
  a real pause tolerance). Let them interrupt you and stop instantly when they do.
- **No machine narration.** Never say "one moment," "let me check," "processing." Use tools silently
  and just say the answer. Filler is the tell.
- **Genuine expressiveness, in the words.** Warmth, a little personality, emphasis on the tasty word —
  written into the script, because prosody follows punctuation and phrasing.
- **Graceful silence handling.** Don't just hang up on quiet. Check in ("still there?") a couple of
  times, then a warm sign-off ("call back anytime, I'm here 24/7") — then end.

### Ordering
- **Take the whole order first, then clarify.** Don't interrogate item-by-item. Gather everything,
  then resolve the missing required choices in a natural batch.
- **Ask with real options, never echo a guess.** "Beef, chicken, or shrimp?" — not "you want beef,
  right?" And **never re-ask what the caller already said or what the item name already implies.**
- **Batch the global preferences, ask the item-specific ones in context.** Spice is usually one
  choice for the whole order (ask once); protein/style are item-defining (ask when that dish comes up).
- **Lead with the popular pick.** When you must ask, put the best-seller first, and recommend it if
  they're unsure. (Derived from the client's real order data.)
- **Mandatory read-back before commit.** What's read back == what's written to the POS. Get an explicit
  "yes," then place. Never take payment on the call unless the client explicitly wants it (PCI scope).

### Recommendation & upsell
- **Grounded, single, reasoned.** One tasteful add-on, tied to a real reason: pairing ("naan to scoop
  that curry") or popularity ("a lot of people add this"). Channel-aware; back off the instant they
  decline. Never a fabricated discount.
- **Cross-category pairing logic that matches how people actually eat** (carb with a saucy dish, a
  protein entree with a rice/noodle base) — grounded in the client's real attach data.

### Complaints & escalation
- **Acknowledge for real, first** — in the agent's own warm words, matched to the caller's feeling.
- **Understand, then gather** what resolution needs (name, phone, when, what).
- **Log it** — structured, every time, even praise.
- **Triage by inferred damage, not by whether they escalated.** Severe (safety, sickness, a ruined
  large order, threats, fury) → the highest human; normal complaint/feedback → the owner; live/ops →
  the floor. Reassure; never promise a specific outcome.

### Trust & safety
- Honest about being an AI if asked. Halal/dietary/allergy wording discipline. No PII leakage, no
  card numbers, no staff details, no other customers' data. Un-social-engineerable. Spam/prank exit.

---

## 3. Nitty-gritty engineering rules (the "how")

- **Deterministic where correctness matters.** Hours (with breaks/holidays/DST), order state machine,
  modifier validation, money math — computed in code, never left to the model. The LLM *speaks*
  results; it doesn't *derive* them.
- **Push correctness into the tool layer, not the prompt's goodwill.** Examples that recurred:
  auto-fill a required choice the dish name already encodes ("Crispy **Beef**" ⇒ beef; "chicken fried
  rice" ⇒ chicken); accept synonyms the caller will actually say ("vegetable" ⇒ the catalog's "Veg.");
  normalize catalog abbreviations for *speech* ("Veg." → "Vegetable", "pc" → "pieces") while keeping
  the exact name for the POS write. If the model *can* get it wrong, make the server get it right.
- **Ground the menu in the POS catalog, with the real IDs.** Resolve spoken dish → one real item ID or
  ask to disambiguate; refuse non-menu and forbidden items; carry real modifier IDs so the write is exact.
- **Gate irreversible actions and roll out reversibly.** Order writes stay dry-run (log the exact
  payload, write nothing) until verified end-to-end; then double-gate the live write (an env flag AND
  an explicit spoken confirmation). Verify one real write before trusting it.
- **Match infrastructure to the state model.** Per-call state that lives in memory (the cart) demands a
  single worker + single instance, or it splits and the order is lost. (A real bug we caught in dry-run:
  multiple gunicorn workers each held a separate cart.) Threads share memory; processes/machines don't.
- **Persist cross-call memory.** Returning-caller history and the feedback log live on a persistent
  volume as append-only JSON — best-effort, so an IO error never breaks a live call.
- **Test-first / dry-run before every live call.** Simulating the tool chain caught real bugs (the
  cart split above; an empty read-back) before they ever reached a caller. Keep a green tool test suite.
- **Config-as-code, reproducible, secrets out of git.** One script rebuilds the assistant (model,
  prompt, voice, tools, transfer routing) from committed config + env overrides. Secrets live in the
  host's secret store only.
- **Tune turn-taking with real levers, not vibes:** endpointing wait, smart-endpointing, no-punctuation
  timeout, barge-in word threshold, background denoising. Most "bad pickup" is the *browser tester's*
  mic — validate on a real phone line.

---

## 4. The pronunciation lesson (its own section, because it cost the most)
**A single TTS voice only knows one language's pronunciation.** Mixing languages/names in one sentence
(a Chinese greeting + an Urdu word + a Hindi word + a desi name) will be mangled, and *every voice
mangles them differently*, so swapping voices just moves the errors. **Phonetic respelling is
unreliable** — each engine reads it differently ("Nuh-muh-stay" came out "numuste").

The rules that actually work:
1. **Pick a voice that natively says the brand's key words** (the restaurant's name, its signature
   dishes, its greeting) — usually a voice from the matching language/region.
2. **Remove or replace words no available voice can say** (e.g. swap a Chinese "hello" for "Hello").
3. **Only respell as a last resort, and verify by ear** — the operator is the judge; the builder can't
   hear the output.
4. **Lock the voice once approved** and guard it from drift.

---

## 5. What generalizes vs. what's per-client

| Fixed (the template) | Per-client (the config/data) |
|---|---|
| All principles above | POS system + credentials; the real menu + IDs |
| The conversation/ordering/complaint flows | Best-sellers, popular protein/spice defaults (their data) |
| The tool architecture + persistence | Brand voice choice; greeting; agent name |
| Guardrails & safety posture | Escalation contacts + severity routing |
| Deterministic hours/state/validation | Hours, holidays, order types offered, delivery radius/fees |
| Dry-run → gated-live rollout | Whether/when to enable live POS writes & phone payment |

**Bottom line for a new engagement:** stand up the same architecture, point it at the client's POS,
mine their real sales for the smart defaults, choose a brand-fit locked voice, wire their escalation
tree, and roll out dry-run → verified-live. The hard-won philosophy is already paid for; each client
is data + config on top of it.

---

## 6. Expanded build — capabilities & principles the flagship added

The flagship grew well past "take an order." Each of these is a reusable capability + a principle:

- **Returning-caller memory ("your usual?").** Recognize the caller's number, greet by name, offer their
  last order. Loyalty in the first ten seconds of the second call. *Principle: personalization from history,
  never from profiling — when a client asks for something dubious (e.g. "guess ethnicity by voice"), ship the
  ethical, more-accurate version: behavior + history + language-matching.*
- **Reservations.** Take the booking on the call (party size, kids, date/time, high-chair; phone auto from the
  call — never asked), respect the client's real seating limits, persist it AND email the restaurant. *Principle:
  capture the client's real operational constraints (seat counts, table rules) as config.*
- **Complaint + feedback capture → operational intelligence.** Genuine-empathy handling, triage by inferred
  severity, and a structured log of every complaint/suggestion/question/praise (owner-reviewable, an FAQ seed).
  *Principle: the phone line is a listening post; capture everything structurally.*
- **Presence / human-connection layer.** Live weather + day/season/holiday so the agent can be warmly present
  ("perfect chilly night for a hot Karahi") and read the caller's desires/aversions — with appropriate weight,
  never forced. *Principle: be a genuine friend whose intent is to serve and make them smile; guardrail OUT
  hard news/politics/anything somber (brand risk), keep only the safe, warm signals.*
- **Item-knowledge layer.** Rich, grounded talking points per dish (description, spice, dietary, real-sales
  popularity, pairings) so the agent can describe/recommend/answer "what's in it?" *Principle: the agent should
  know each product as well as a great server does — sourced from the client's best copy, not raw POS fields.*
- **Context-aware promotions.** Deals that respond to the moment (e.g. push dine-in lunch specials only during
  the slow weekday-lunch window), explained in full. *Principle: the right offer at the right time, always
  grounded and complete.*
- **Graceful silence handling.** Don't hang up on quiet — check in, then a warm 24/7 sign-off.

### Two engineering principles worth their own line
- **No silent failures.** Never tell a caller "all set" on a failed action. A failed write stays retryable
  (not cached as done); partial failures surface loudly for a human; every best-effort/swallowed error is
  logged and counted (visible at /health + /errors). The agent is told to NEVER falsely confirm.
- **Model tier matches task complexity.** A weak model silently drops rules (filler, unresolved choices).
  For a rich multi-tool flow, use a strong instruction-follower — and prove it with scenario tests.
- **Scenario-gated quality.** A suite of diverse caller states/moods/situations/events (the flagship uses 25)
  is a release gate — it caught a real mis-routing bug that unit tests missed.

---

## 7. The philosophy of coolness (what makes a feature land in reality, not just a demo)

Cool ≠ impressive-on-paper. A feature is cool when a real person — *not* paying attention to the tech —
feels a flicker of being-seen, relief, or delight. This is the difference between what wins demos and what
wins customers, and it's worth naming precisely.

**The one-line definition:** *Cool = it did something a great human would do, that you didn't expect it to
bother with, and it got the weight exactly right — grounded in what's true, delivered with restraint.*

**The five nerves a cool feature hits (at least one):**
1. **Being seen / known** — "your usual, Priya?" The tech is trivial; the payoff is emotional (*they know me*).
2. **Unexpected thoughtfulness** — "perfect chilly night for a hot Karahi." A machine did what only a *caring*
   person would bother with. Cool lives in the gap between "I expected a dumb bot" and "…oh."
3. **Friction removed invisibly** — not asking for a phone number it already has. Feels *inevitable in hindsight.*
4. **Proportional response** — fast-tracking the truly-wronged caller to the boss. Matching the stakes feels like justice.
5. **Integrity you can feel** — never falsely confirming. A system that won't smile and fail you earns trust.

**Reality vs. ideal (the crucial filter):** ideal-cool *impresses in a demo* ("look, it knows the weather!");
real-cool is *felt without being noticed.* **If it has to be explained, it isn't cool.**

**Coolness is fragile — it dies with excess.** Restraint (one light touch, not a weather monologue every call)
is what keeps it cool instead of cringe. Respect the person's attention; never show off.

**The meta-move:** individual cool features **compound into a relationship** — over months the place starts to
*feel like it knows you*. That feeling, not any single feature, is what a competitor can't copy.

**Two audiences for cool:** *caller-cool* (warmth/relief in the moment) and *owner-cool* (turning data the system
already captures into intelligence the owner has never had — e.g. "recovered 4 after-hours calls into ~$180;
6 people asked for a dish you don't carry"). Both are productizable; sell both.

**The test before building anything:** *would a real, distracted person feel something in the moment — without
needing it explained?* If no, it's ideal-cool (skip or cut). If yes, build it, and keep it restrained.
