# `flagship/` — the Wok & Karahi proof layer

**What this folder is:** the distilled, self-contained knowledge that flows from Abbas's own
restaurant — **Wok & Karahi** (Spring, TX), the *test business* — into AZ Restaurant Partners'
**product**. Everything AZ sells was proven there first. This folder is where that proof lives so
the AZ repo (and, later, an AZ chatbot/KB) never has to reach into the restaurant's separate repo
to know what's been built.

**Why it exists:** the two businesses live in two separate repos on purpose
(`abbas-MyPeople/WokAndKarahiTexas.com` = the restaurant; `abbas-MyPeople/AZ` = AZ). Before this
folder, the "proven at the restaurant → productized here" flow was manual — Abbas had to point each
session at the right files or synthesize across repos by hand. This folder + the ledger make that
flow durable and low-effort.

## Contents
| File | What it holds |
|---|---|
| [`CAPABILITY-LEDGER.md`](CAPABILITY-LEDGER.md) | **Start here.** The master table: each restaurant-proven capability → its AZ offering → live status → the gap/next move. The bridge's source of truth. |
| [`capabilities-catalog.md`](capabilities-catalog.md) | The full productized capability catalog + client-onboarding playbook, reconciled against what the AZ site actually markets and prices. |
| [`voice-agent-playbook.md`](voice-agent-playbook.md) | The generalized philosophy + engineering template behind the flagship voice agent — the template AZ brings to every voice engagement. |
| [`case-study-wok-and-karahi.md`](case-study-wok-and-karahi.md) | The flagship case study — the proof artifact the AZ site's own audit named as its #1 missing conversion asset. Grounded in real, verifiable facts; owner-gated where numbers are sensitive. |
| [`SYNC-PROTOCOL.md`](SYNC-PROTOCOL.md) | The ritual that keeps this folder honest: when to update it, who updates it, and how a session in *either* repo should behave. |

## The one rule
**This folder is downstream of the restaurant, upstream of the sales copy.** It is not the place to
invent offerings — a capability earns a row in the ledger only when it's real at the flagship (or is
honestly labeled advisory-only). Marketing copy on the live pages should be able to trace any claim
back to a row here.
