"""Partner share kit for the Houston Holiday Giveaway: one page per partner day at /holiday-giveaway/kit/<slug>/.
Add a partner to partners.json, put its slide*.jpg / story*.mp4 / reel.mp4 in kit/<slug>/, run: python3 build_kit.py
Every page carries the "who's next" chain: the partner sends a ready message to a business they know.
"""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
PHONE = "(408) 393-6716"
RULES = "azrestaurantpartners.com/holiday-giveaway"


def e(s): return html.escape(s, quote=True)


def page(p, files):
    slides = sorted(f for f in files if f.startswith("slide") and f.endswith(".jpg"))
    stories = sorted(f for f in files if f.startswith("story") and f.endswith(".mp4"))
    reel = "reel.mp4" if "reel.mp4" in files else None
    h = p["handle"]
    customer = (f"{p['name']} is giving away {p['prize_plain']} on {p['day_say']} in the Houston Holiday Giveaway. "
                f"To enter: follow @{h} and @azrestaurantpartners on Instagram, then comment on the Day {p['day']} post on "
                f"{p['day_short']}. Tag a friend for a bonus entry. Free to enter. Rules: {RULES}")
    story_day = f"Our day is live! Comment on this post for a chance to win {p['prize_plain']} from {p['name']}."
    nextmsg = (f"Hi! {p['name']} has a day in the Houston Holiday Giveaway: a free prize every day from Dec 1 to Jan 1, "
               f"posted by @azrestaurantpartners on Instagram. You give one prize worth $100 or more, and your business "
               f"gets its own day: a Collab post, a reveal, and new people following you. Nothing else to pay. "
               f"Call or text Abbas at {PHONE} to get a day. Details: {RULES}")
    copy = lambda i, t: (f'<div class="msg"><p id="{i}">{e(t)}</p><button type="button" data-c="{i}">Copy</button></div>')
    sl = "".join(f'<figure><img src="{f}" alt="Day {p["day"]} post, slide {n}" loading="lazy" width="1080" height="1350">'
                 f'<a class="sv" href="{f}" download>Save</a></figure>' for n, f in enumerate(slides, 1))
    st = "".join(f'<figure><video src="{f}" poster="{f[:-4]}.jpg" controls playsinline preload="none"></video>'
                 f'<a class="sv" href="{f}" download>Save Story {n}</a></figure>' for n, f in enumerate(stories, 1))
    rl = (f'<figure class="one"><video src="{reel}" poster="reel.jpg" controls playsinline preload="none"></video>'
          f'<a class="sv" href="{reel}" download>Save the Reel</a></figure>') if reel else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{e(p['name'])}: your giveaway day</title>
<style>
:root{{color-scheme:light dark;--ink:light-dark(oklch(23% .012 60),oklch(94% .01 75));--ink2:light-dark(oklch(45% .01 60),oklch(78% .01 75));
--paper:light-dark(oklch(97% .006 75),oklch(16% .008 70));--surf:light-dark(#fff,oklch(20% .008 70));--rule:light-dark(oklch(88% .008 70),oklch(31% .009 70));
--ticket:light-dark(oklch(53% .15 32),oklch(70% .135 34));--brand:#1c4739}}
:root[data-theme=light]{{color-scheme:light}}:root[data-theme=dark]{{color-scheme:dark}}
*{{box-sizing:border-box;min-width:0}}
body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;overflow-x:clip}}
.w{{max-width:1080px;margin:0 auto;padding:0 24px}}
header{{background:#1a1714;color:#f2ede7;padding:48px 0 40px}}
.kick{{font:600 11px ui-monospace,monospace;letter-spacing:.15em;text-transform:uppercase;color:#e0a07a;margin:0 0 10px}}
h1{{font-size:clamp(2rem,5vw,3.2rem);font-weight:830;letter-spacing:-.04em;line-height:1.03;margin:0 0 12px;text-wrap:balance}}
header p{{color:#c8c0b6;font:19px/1.5 Georgia,"Iowan Old Style",serif;margin:0;max-width:56ch}}
section{{padding:44px 0;border-top:1px solid var(--rule)}}
h2{{font-size:clamp(1.4rem,3vw,2rem);font-weight:790;letter-spacing:-.03em;margin:0 0 6px}}
h2 b{{color:var(--ticket);font-weight:790;margin-right:8px}}
.lede{{color:var(--ink2);font-family:Georgia,serif;margin:0 0 18px;max-width:60ch}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:14px}}
figure{{margin:0;background:var(--surf);border:1px solid var(--rule);border-radius:7px;padding:8px}}
figure img,figure video{{width:100%;height:auto;display:block;border-radius:5px;background:#000}}
.one{{max-width:300px}}
.sv,.msg button{{display:flex;align-items:center;justify-content:center;min-height:44px;margin-top:8px;border-radius:5px;
background:var(--brand);color:#fff;font:600 15px system-ui;text-decoration:none;border:0;cursor:pointer;width:100%}}
.msg{{background:var(--surf);border:1px solid var(--rule);border-radius:7px;padding:16px;max-width:680px}}
.msg p{{margin:0}}.msg button{{width:auto;padding:0 22px}}
ol.steps{{margin:0;padding-left:1.2em;max-width:60ch}}ol.steps li{{margin:4px 0}}
a{{color:inherit}}button:focus-visible,a:focus-visible{{outline:2.5px solid var(--ticket);outline-offset:3px}}
footer{{padding:32px 0 48px;color:var(--ink2);font-size:15px;border-top:1px solid var(--rule)}}
@media(max-width:600px){{.w{{padding:0 16px}}.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
</style></head><body>
<header><div class="w"><p class="kick">1st Annual Houston Holiday Giveaway</p>
<h1>{e(p['name'])}, Day {p['day']} is yours</h1>
<p>{e(p['day_say'])}. {e(p['prize_line'])}. Here is everything to share, ready to go.</p></div></header>
<main>
<section><div class="w"><h2><b>1</b>Accept the Collab</h2>
<p class="lede">The reveal post is live on @azrestaurantpartners with you as a collaborator. Accept it so it shows on your profile and your followers see it too.</p>
<ol class="steps"><li>Open Instagram on the @{e(h)} account.</li><li>Tap the heart (Activity), or the notification from @azrestaurantpartners.</li><li>Open the collaboration request and tap Accept.</li></ol></div></section>
<section><div class="w"><h2><b>2</b>Share these Stories now</h2>
<p class="lede">Save each one and post it to your Story. Tag @azrestaurantpartners.</p><div class="grid">{st}</div></div></section>
<section><div class="w"><h2><b>3</b>Tell your customers</h2>
<p class="lede">Send this to your WhatsApp groups, regulars or text list.</p>{copy("cust", customer)}</div></section>
<section><div class="w"><h2><b>4</b>On {e(p['day_short'])}, share your live post</h2>
<p class="lede">That morning the Day {p['day']} post goes up on @azrestaurantpartners. Reshare it to your Story with this line.</p>{copy("story", story_day)}</div></section>
<section><div class="w"><h2><b>5</b>Who's next?</h2>
<p class="lede">Every day needs a Houston business. If you know one that would love a day, send them this. Or text their name and number to {PHONE} and we'll tell them you sent us.</p>{copy("next", nextmsg)}</div></section>
<section><div class="w"><h2>Your reveal post</h2><p class="lede">Saved here in full size, if you want to post it yourself.</p>
<div class="grid">{sl}</div>{('<div style="margin-top:14px">' + rl + '</div>') if rl else ''}</div></section>
</main>
<footer><div class="w">Questions? Call or text Abbas at {PHONE}. Rules: <a href="https://{RULES}/">{RULES}</a>.<br>AZ Restaurant Partners · Houston, Texas</div></footer>
<script>{{document.querySelectorAll('[data-c]').forEach(b=>b.addEventListener('click',async()=>{{
const t=document.getElementById(b.dataset.c).textContent;try{{await navigator.clipboard.writeText(t);b.textContent='Copied'}}catch(_){{
const r=document.createRange();r.selectNodeContents(document.getElementById(b.dataset.c));const s=getSelection();s.removeAllRanges();s.addRange(r);b.textContent='Selected, now copy'}}
setTimeout(()=>b.textContent='Copy',2500)}}))}}</script>
</body></html>
"""


if __name__ == "__main__":
    for slug, p in json.load(open(os.path.join(HERE, "partners.json"))).items():
        d = os.path.join(HERE, slug)
        files = os.listdir(d)
        with open(os.path.join(d, "index.html"), "w") as f: f.write(page(p, files))
        print("built", slug, len(files), "files")
