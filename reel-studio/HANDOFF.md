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

## Cost and voice rule (owner, 2026-10-29)
- Keep reel 01 quality, but under about $1 a reel. Build the cast and restaurant set once and reuse them (kontext edits, not fresh ultra renders). Logic-check every keyframe before generating; re-makes were most of the spend. Animate only 6-8 key shots (Wan 2.2 turbo, $0.10 each); the other beats are a still keyframe with a camera move plus the overlay cards.
- Voice: on-screen narration line for each beat, read by an expressive ElevenLabs v3 voice (Chris, with emotion tags, about $0.10 a reel). Kokoro was rejected as emotionless. Platform text-to-speech can't be switched on when posts go out automatically. His own voice only when he sends a recording.
- No approval needed on voice or narration choices.

## Offer wording (owner, 2026-10-29)
- Never "free for the first two months". Say: "No setup fee, no contract, and for the first two months you only cover what the technology costs to run." No price number in public copy. Older slate lines that say "free" are superseded by this.

## Keep it fresh, hooks and CTAs (owner, 2026-10-29)
Owner: cost cuts must not make reels feel like the same video; keep hooks and CTAs strong.
- Reuse only the world (set, core cast). Every reel brings something new: a new guest character or location, a new card type (check with stamp, printing ticket, split bar), a new camera grammar (close, top-down, wide).
- Rotate the hook format: cold open with a time (01), who-wins question (02), cold open plus question (03), then next: direct address ("Restaurant owners:"), POV, mistake framing, before/after. First second shows the problem on screen, never a wide establishing shot.
- End on a line that loops back into the opening.
- CTA: Comment DEMO on IG/FB/YT/LinkedIn (auto-reply live). TikTok/X: link in bio. Add a send line on IG ("Send this to an owner who..."). Track each reel with ?r=NN on the link.
- Planned: a 25-35s cut of each reel for TikTok and Shorts; rotate a story keyword per reel (needs a new auto-reply each time).
- Hooks never carry numbers we can't back up. Research sources were vendor blogs only (Oct 2026), so treat their % claims as directional.
- Every reel uses a DIFFERENT real order priced from the W&K menu (WokAndKarahiTexas.com website-v2/assets/data/menu.json, base prices; e.g. Chowmein 12.99 + Lari Chowmein 13.99 = 26.98 in reels 01-02, Dum Biryani 17.99 + Naan 3.99 + 2 Mango Lassi 9.98 = 31.96 in reel 03). Never repeat a stakes number.
- Each reel gets its own comment keyword and its own auto-reply (CALL 01, APP 02, TABLE 03). TikTok + YouTube Shorts get a 25-35s short cut (AZ-reels/shorts/cut.py), the other platforms the full reel.
