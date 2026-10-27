# Case Study — Wok & Karahi (the flagship)

> **Why this doc exists:** the AZ site's own audit (`research/persona-expansion-and-site-audit.md`)
> names the absence of a **named case study with numbers** as the single biggest conversion gap. This
> is that case study — the raw material to turn into a live page/section. It is written to be **honest
> and defensible**: every claim below is either verifiable today or marked `[OWNER: …]` where it needs
> a real number only Abbas can supply. **Do not guess the bracketed values.**

## The setup (all verifiable)
- **Who:** Wok & Karahi — a halal **Chinese + Indian + Pakistani** fusion restaurant, 3422 FM 2920 Rd
  Unit #120, Spring, TX 77388. Owned by **Abbas Zoeb, an ex-Google software engineer** who runs it as
  AZ's proving ground. "Home of the Crispy Beef."
- **Credibility:** named on **You Had Me At Halal's Top 10 Halal Restaurants of 2024** (unranked list).
  Highest-rated in its category locally.
- **The wedge:** one of the very few halal kitchens serving Chinese *and* Indian/Pakistani under one
  roof — a genuine differentiator most competitors can't match.

## The problem we found on our own restaurant (the "if it's true for us, it's worse for you" hook)
When we turned AZ's methods on our own place, we found exactly what the average independent suffers:
- **The website was invisible to AI.** The old GoDaddy/Wix site returned **HTTP 403 to bots** — so
  ChatGPT, Gemini, Perplexity and Claude literally could not read the menu, hours, or address. In the
  zero-click / AI-answer era, that's being absent from the fastest-growing discovery channel.
- **Discovery lived entirely on Google Business Profile, not the site.** In Jan–Jun 2026 the GBP drove
  **~81,572 profile views** and **7,387 interactions** (directions, menu views, calls) — while the
  website converted **~0 tracked actions**. The front door and the store weren't connected.
- **Margin leaking to third-party apps** at ~30% commission, with no first-party ordering push and no
  clear view of true channel economics.
- **Missed calls = missed orders**, with no way to answer every call or capture after-hours demand.

## What we built (all live or deployed today — this is the proof)
1. **An AI phone agent that actually works.** Answers every call in a locked, human-sounding voice
   (English + Urdu/Hindi), takes orders straight into the Clover POS, sizes catering, upsells like a
   friend, remembers regulars, handles complaints with real empathy and alerts the owners, with no hand-off
   to a person by design. **Live on Fly.io**, 24 integrated tools, gated so it can never place a bad order, and put
   through a 15-scenario QA gate before going live.
2. **A website AI assistants can actually read.** Rebuilt in code as an **AEO-native** site
   (wokandkarahitexas.com): full Restaurant/Menu/FAQ schema, a menu statically rendered so no-JS
   crawlers see every dish, local landing pages, `llms.txt`, and a clean sitemap. The 403 problem is
   gone — the menu is now machine-readable.
3. **A conversational analytics brain.** Ask the POS anything: best/worst sellers, daypart patterns,
   dine-in vs takeout vs delivery vs third-party economics, catering signals — and a reconciliation
   that separates *reported* revenue from *true net* so decisions are made on real margin.
4. **The direct-order push (already running in the real world, 1+ year).** Every order that leaves the
   kitchen carries a **thank-you note, customized by order type**. Third-party-app customers get a card
   that reads *"Paying up to 50% extra?? Order on our website, save big"* — because the apps carry a
   ~30% price markup plus their own fees and delivery, while ordering direct means **delivery within 5
   miles for $7.99, no extra fees, cheaper prices, and more deals.** (Card image on file.) A quiet,
   low-tech machine that converts the app's own customers into direct ones.
5. **Tablet consolidation (live 1+ year).** Third-party delivery orders now flow **straight into the
   Clover POS** and print to the kitchen automatically. Before, staff had to accept each order on a
   separate delivery tablet and **re-type it** into the POS to make a ticket — which, in a rush, meant
   **lost, late, and wrong orders.** That entire manual step is gone.
6. **A review engine that only lets the good ones through (live 1+ year).** Two tracks: a *"Scan me"*
   QR card is brought to the table **when a guest is clearly happy** (and reminded of the experience,
   so they actually scan); if a guest is unhappy, they're handed the **owner's business card** to raise
   it **directly with the owner — before a negative review is ever posted.**

## Rolling out now (in active build — capability, not yet a claimable result)
- **Consent-based SMS loyalty & win-back.** The plumbing is live in the phone agent; the loyalty/
  win-back campaigns are near-complete (one test send done). Present as a capability, not a result.
- **A self-optimizing menu.** An intelligence layer that reads what's selling (Clover), what people
  search for (SEO), timing, and deal performance — then proposes dynamic pricing and deals that write
  back to the menu, **only after the owner approves, with proof and A/B testing.** Early build; the
  direction is real and differentiated.

## The results
> **Timing note:** the rebuilt site went live 2026-06-28 and the phone agent shortly before, so a clean
> "before/after revenue" window on those two doesn't exist yet. The tactics that have run for a year+
> (reviews, thank-you notes, tablet consolidation) already have real results, below.

- **4.6★ across 872 Google reviews** — roughly double the count a year ago (~400), with new reviews
  running five-star since the review system went in. (Flagship's strongest proof point; Google count
  verifiable live.)
- **Tablet consolidation eliminated manual re-entry** and the lost/late/incorrect orders that came with
  it — 1+ year live.
- Website AI-readability: **403-to-bots → fully crawlable** (verifiable now).
- After-hours / missed-call demand captured by the phone agent: `[OWNER: # calls recovered, est. $ once tracked]`
- Direct vs third-party order mix shift from the thank-you-note push: `[OWNER: baseline % → current %]`
- Third-party commission recovered: `[OWNER: $ / month, from the Clover fee model]`

## The one-liner (for the site)
**"We didn't learn this on someone else's restaurant. We built it on our own — an award-winning halal
kitchen in Spring, TX — then packaged what worked so your restaurant gets the enterprise-grade setup
you could never hire for."**

## How to use this
- Turn the "What we built" + "The problem" sections into a live **case study section/page** on the AZ
  site (closes the #1 conversion gap). Lead with the *capabilities that are provably live*; keep the
  bracketed results out until Abbas supplies real numbers.
- Link the AI Phone Agent play to a **real demo** — a recording, a transcript, or the live number —
  which is the strongest possible proof and costs nothing to surface.
- Keep sensitive internal financials (true-net P&L, exact fee dollars) **off the public page** unless
  Abbas explicitly approves; they can power private proposals instead.
