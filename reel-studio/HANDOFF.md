# Reel Studio - handoff (read this first)

Last updated 2026-10-28 from the cloud session. Picks up the AZ social reel work exactly where it stopped.

## What Abbas decided (all approved 2026-10-28)
- AZ reels speak to restaurant owners. Wok & Karahi is the proof ("our own restaurant"), never the subject.
- Every reel is a STORY, not a feature list: one object's journey (a call, an order, a guest, a dollar), a stakes number in the first 8 seconds, a turn, a payoff, a widen, a short close. Hook must stop an owner in 2 seconds.
- Every reel also says WHY WE WIN at that one job, naming competitors and their prices where it adds weight (facts only from AZ's own compare pages, which were checked against vendor pages Oct 2026).
- Production quality bar: physics, logic and reality in every shot (see the reality bible in story-01). Informative and entertaining. The owner's burdens visibly lift off. Easy to understand: one idea per line, one card per idea, max 3 elements per card.
- Abbas voices every AZ reel himself (phone voice memo, 3 takes). Wok & Karahi reels keep Haniya's voice.
- A 3D/illustration artist is commissioned ONCE for a reusable world kit (brief: artist-brief.md). Abbas posts it and sends back 3 quotes. Deliveries land in a Google Drive folder; animation is done in Blender (pip install bpy works).
- Four gates per reel: 1 hook, 2 story (script + shot list, then a timed rough animatic on his voice), 3 three style frames, 4 final cut.
- The 30-day calendar is ON HOLD until reel 01 is made the new way; the 30 stories are re-picked in slate.json.

## State right now
- Reel 01 "The 7:14 Call": gates 1 and 2 approved. Script + shot list + reality bible: story-01-the-714-call.md (also pages/call-714-pack.html).
- Waiting on Abbas: (1) his voice recording of the reel 01 script, (2) artist quotes.
- The 30-story slate with hooks, stakes, turn, close, proof and why-we-win: slate.json (also pages/reel-studio-plan.html).

## Next steps, in order
1. When his voice file arrives: clean it, time every shot to it, build the rough animatic (black-and-white boards, real timing, word-synced captions) and send it for his OK.
2. Set up the comment-keyword auto-reply ("CALL" -> DM the free demo link azrestaurantpartners.com/start/) before reel 01 posts.
3. When the artist kit arrives: 3 style frames for gate 3, then animate reel 01 in Blender.
4. Write scripts for slate stories 2-5 in his voice with the same structure, ready for his next recording session.
5. Connect AZ's Instagram, TikTok, Facebook, LinkedIn for scheduled posting (Wok & Karahi's poster today handles photos only; needs video).

## Lessons from the first attempts (do not repeat)
- 2026-10-28: reel 01 was wrongly rebuilt on the Mac as staged photo cards (the old feed-image method). Owner rejected it. Story reels are an ANIMATED WORLD with characters following one journey, per the reference grammar above. No duplicate labels or tags, captions never repeat a card, nothing overlaps the HUD.
- Real screenshots in reels are unreadable at phone size. Redraw each screen as a teaching card with 2-3 elements.
- Characters drawn from primitives in code look like toys. Production needs the artist's kit.
- On-screen text must equal the voice word for word.
- Never use the haniya-portrait-* art (broken mouth, deleted 2026-10-27). Use haniya-avatar-* or haniya-greet-*.
- Never "Crispy Beef" as the hero dish in reels; use Lari (Street) Style Chowmein / Chowmein.
- No invented numbers; competitor prices only from AZ compare pages; no mention of any sale of the restaurant.

## Files
- slate.json - the 30 stories
- story-01-the-714-call.md - reel 01 script, shots, reality bible
- artist-brief.md - the commission brief
- pages/ - the two pages Abbas reviewed
- engine-v1/ - the first code engine (2D canvas story reels, Kokoro voice, score mixer, Three.js prototype). Reference only; superseded by the Blender + artist-kit pipeline.
