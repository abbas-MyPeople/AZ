# Restaurant intelligence engine (v1, 2026-11-28)

A living profile of each restaurant, built from public information before we meet the owner. The owner then corrects it in person. Builds on `outreach/ARCHITECTURE.md`, which holds the evidence rules, the 14 research domains and the guardrails. This folder adds what that document did not have: a profile that keeps learning.

## Pieces

| File | Job |
|---|---|
| `discover.py` | Finds independent restaurants across Houston from OpenStreetMap (free, no key). Drops chains and duplicates. Each target keeps its source and the date we saw it. |
| `model.py` | The profile: findings (fact / worked out / our read / a guess), cross-topic patterns, opportunities, and questions only the owner can answer. Enforces the rules: sources and dates on every fact, confidence below 1 and an owner question on every guess, patterns must join two topics, every scenario number labelled with where it came from, no "guaranteed" results, recency weighting (over 12 months = stale). |
| `profiles/<slug>.json` | The base profile, as researched. Never rewritten. |
| `profiles/<slug>.events.jsonl` | Every owner reaction (confirm, challenge, correct, add detail, answer), append-only. The live profile = base + events replayed, so we can always show what we believed before he spoke. A challenged finding halves its confidence and puts any opportunity resting only on it on hold. |
| `render.py` | The phone page: 5 s insight, 30 s proof, 2 min opportunities, 10 min everything by topic with Right / Not quite / Add detail, then the questions only the owner can answer. Noindex. Answers are kept on the phone first, then sent to `ENDPOINT` (the Wok & Karahi server, `voice-agent/src/az_intel.py`, stored in `/data/az_intel_answers.jsonl`). |
| `test_intel.py` | Rules, replay, ripple, page layers, discovery. |

First profile: our own restaurant (`wok-and-karahi-spring`), so every line can be checked by someone who knows the truth.

## What the market does today (researched 2026-11-28)

- Owner.com: free "Restaurant Website Grader" gives an online health score out of 100 (website, local listings, who beats you on Google) and a dollar figure of sales lost, then books a 20-minute demo. Strong funnel, huge sales team (cold calls, texts, social), raised $240M in Aug 2026, now sells AI phone ordering. Weak spots: generic scores, a lost-sales figure with no shown method, and lawsuits from Popmenu and ChowNow alleging its grader marks rivals down (ChowNow case partly survived dismissal, 2026). Sources: owner.com/demo-quiz-grader, restaurantbusinessonline.com (Popmenu suit), news.bgov.com (ChowNow), finviz (funding), owner.com/ai-phone-ordering.
- DoorDash, LocalIQ, HubSpot, WordStream: free website graders. Speed, SEO, mobile. Website only, same report for every restaurant.
- Birdeye, Momos, SevenRooms, Revmo: review sentiment and menu analysis, but only after the restaurant signs up and connects its systems.
- Apify "Restaurant Reservation & Review Audit": $50 per 1,000 automated audits with a pitch angle. Shallow heuristics.

Where they win: scale, polish, one memorable score, a sales team. Where we can beat them: findings specific to one restaurant with dated proof; patterns across reviews, menu, location and community; no made-up money figures (the owner fills the numbers in); the owner corrects us in the room and the profile learns; and a working restaurant (Wok & Karahi) as live proof.

## Next steps

1. Pull the stored answers into `profiles/<slug>.events.jsonl` on a schedule (the endpoint is live; the pull is next).
2. Research collectors that fill a profile automatically: site crawl (`outreach/collect.py`), reviews dated and recency-weighted, menu teardown, Google listing, social, health inspections.
3. Background refresh: re-check each profile's expired evidence on a schedule and flag what changed (new bad review, menu price change, hours cut).
4. Houston-wide run of `discover.py`, then profiles for the shortlist.
