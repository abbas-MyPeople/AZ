# Sync Protocol — keeping the flagship→AZ bridge alive

> The point of the `flagship/` folder is that Abbas should **never again have to manually explain the
> relationship between the two businesses, or hand-synthesize what the restaurant has proven.** Any
> Claude session in either repo follows this protocol and the bridge stays current on its own.

## The two repos
- **Restaurant (the lab):** `abbas-MyPeople/WokAndKarahiTexas.com` — where capabilities are built and
  proven on Abbas's own restaurant, Wok & Karahi.
- **AZ (the product):** `abbas-MyPeople/AZ` (this repo) — where proven capabilities become named,
  priced offerings sold to other restaurants.

They stay **separate repos** (different deploy targets, different brands). The bridge is
*information*, carried by this folder — not a code dependency.

## Trigger → action

**When something ships or materially changes at the restaurant** (a session working in the Wok repo):
1. Finish the restaurant work as normal.
2. Open `flagship/CAPABILITY-LEDGER.md` (in *this* AZ repo) and update the matching row — status,
   proof location, and the "gap / next move" column. Add a new row if it's a genuinely new capability.
3. If the change is proof-worthy (a new live feature, a real result), note it in
   `case-study-wok-and-karahi.md`.
4. That's it. Don't rewrite AZ marketing copy in the same pass — flag it in the ledger's "next move"
   column and let a focused AZ session act on it.

**When starting AZ product/marketing/scoping work** (a session working in this repo):
1. Read `CAPABILITY-LEDGER.md` first. It tells you what's real vs. aspirational.
2. Any claim you put on a live page must trace to a 🟢/🟡 row (or be honestly labeled advisory).
   Never market a 🔴 capability's *proof* you don't have; never invent a flagship result.
3. When you close a gap (e.g. productize a 🔴 into a named offer), flip its AZ-status in the ledger.

## Who owns what
- **The restaurant repo is authoritative for "what's true"** (live URLs, real numbers, what's deployed).
- **This folder is authoritative for "what we sell and why we can back it."**
- **The live AZ pages are downstream of this folder** — copy reflects the ledger, not the other way around.

## Guardrails (inherited from both businesses)
- **Ground everything in real data.** Numbers come from the restaurant's live site / real POS. Label
  anything inferred. Never fabricate a price, review, cert, or result. (Same principle both repos run on.)
- **Sensitive financials are owner-gated.** Internal restaurant P&L (true-net figures, exact fee dollars)
  may inform strategy but is not published without Abbas's explicit OK. Placeholders in the case study
  marked `[OWNER: …]` must not be guessed.
- **Keep the repos un-entangled.** Don't add a code/build dependency from one repo to the other. The
  bridge is copied knowledge, refreshed deliberately — not a live import.

## Mirror
A short pointer to this protocol lives on the restaurant side at `docs/az-bridge.md`, so a session that
starts in the Wok repo knows the AZ ledger exists and is expected to update it.
