#!/usr/bin/env python3
"""Generate branded 1080x1350 social cards (IG, LinkedIn, FB, Threads, X) from real photos.

Usage: python3 scripts/gen-social-cards.py   ->  writes assets/social/*.jpg

Every number on a card must already be on the live site (index.html) or in
flagship/CAPABILITY-LEDGER.md. Add a card by appending to CARDS below.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "social"
W, H = 1080, 1350

# AZ v2 tokens (index.html :root)
BG, PAPER, INK, MUTED = "#f4efe6", "#fffdf8", "#17130e", "#675e51"
ACCENT, DARK, DARKFG, DARKMUTED = "#c2410c", "#16130f", "#f2ebdf", "#b6ab9b"

FONT_DIR = Path("/usr/share/fonts/opentype/inter")
def font(weight, size):
    name = {"bold": "InterDisplay-Bold.otf", "semi": "InterDisplay-SemiBold.otf",
            "med": "InterDisplay-Medium.otf", "black": "InterDisplay-Black.otf"}[weight]
    p = FONT_DIR / name
    if not p.exists():
        p = FONT_DIR / "InterDisplay-Bold.otf"
    return ImageFont.truetype(str(p), size)

FOOTER = "Abbas Zoeb  ·  AZ Restaurant Partners"


def wrap(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split():
            test = f"{line} {word}".strip()
            if draw.textlength(test, font=fnt) <= max_w:
                line = test
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def fit_text(draw, text, weight, max_w, max_h, start, minimum=40, spacing=1.08):
    size = start
    while size > minimum:
        fnt = font(weight, size)
        lines = wrap(draw, text, fnt, max_w)
        if len(lines) * size * spacing <= max_h and all(draw.textlength(l, font=fnt) <= max_w for l in lines):
            return fnt, lines, size
        size -= 4
    fnt = font(weight, minimum)
    return fnt, wrap(draw, text, fnt, max_w), minimum


def draw_lines(draw, xy, lines, fnt, size, fill, spacing=1.08):
    x, y = xy
    for l in lines:
        draw.text((x, y), l, font=fnt, fill=fill)
        y += int(size * spacing)
    return y


def cover(img, w, h, focus=(0.5, 0.5)):
    img = ImageOps.exif_transpose(img).convert("RGB")
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left = int((img.width - w) * focus[0])
    top = int((img.height - h) * focus[1])
    return img.crop((left, top, left + w, top + h))


def circle(img, d):
    img = cover(img, d, d, (0.5, 0.35))
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, d, d), fill=255)
    out = Image.new("RGBA", (d, d))
    out.paste(img, (0, 0), mask)
    return out


def footer(canvas, draw, dark, head=True):
    fg = DARKMUTED if dark else MUTED
    y = H - 110
    x = 80
    if head:
        av = circle(Image.open(ROOT / "assets/abbas-800.jpg"), 64)
        canvas.paste(av, (x, y - 8), av)
        x += 84
    draw.text((x, y + 6), FOOTER, font=font("med", 30), fill=fg)
    draw.text((W - 80, y + 6), "azrestaurantpartners.com", font=font("med", 26), fill=fg, anchor="ra")


def photo_card(c):
    canvas = Image.new("RGB", (W, H), DARK)
    ph = int(H * c.get("photo_ratio", 0.56))
    canvas.paste(cover(Image.open(ROOT / c["photo"]), W, ph, c.get("focus", (0.5, 0.4))), (0, 0))
    d = ImageDraw.Draw(canvas)
    d.rectangle((0, ph, W, ph + 8), fill=ACCENT)
    y = ph + 56
    d.text((80, y), c["kicker"].upper(), font=font("semi", 30), fill=ACCENT)
    y += 58
    fnt, lines, size = fit_text(d, c["headline"], "bold", W - 160, H - y - 160, 84)
    draw_lines(d, (80, y), lines, fnt, size, DARKFG)
    footer(canvas, d, dark=True, head=False)
    return canvas


def stat_card(c):
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    d.text((80, 110), c["kicker"].upper(), font=font("semi", 32), fill=ACCENT)
    blocks = [fit_text(d, c["stat"], "black", W - 160, 420, 260, minimum=120, spacing=1.0) + (ACCENT, 1.0, 72, 28),
              fit_text(d, c["label"], "bold", W - 160, 330, 76) + (INK, 1.1, 80, 32)]
    if c.get("sub"):
        blocks.append(fit_text(d, c["sub"], "med", W - 160, 260, 40, minimum=28, spacing=1.3) + (MUTED, 1.3, 80, 0))
    total = sum(int(len(b[1]) * b[2] * b[4]) + b[6] for b in blocks)
    y = 170 + max(0, (H - 170 - 190 - total) // 2)
    for fnt, lines, size, fill, sp, x, gap in blocks:
        y = draw_lines(d, (x, y), lines, fnt, size, fill, spacing=sp) + gap
    d.line((80, H - 150, W - 80, H - 150), fill="#e2d9c9", width=2)
    footer(canvas, d, dark=False)
    return canvas


def quote_card(c):
    canvas = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(canvas)
    av = circle(Image.open(ROOT / c.get("photo", "assets/abbas-800.jpg")), 200)
    canvas.paste(av, (80, 110), av)
    d.text((80, 370), "“", font=font("black", 200), fill=ACCENT)
    fnt, lines, size = fit_text(d, c["quote"], "bold", W - 160, 560, 88)
    draw_lines(d, (80, 520), lines, fnt, size, DARKFG)
    footer(canvas, d, dark=True, head=False)
    return canvas


def proof_card(c):
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)
    d.text((80, 100), c["kicker"].upper(), font=font("semi", 32), fill=ACCENT)
    fnt, lines, size = fit_text(d, c["headline"], "bold", W - 160, 300, 76)
    y = draw_lines(d, (80, 160), lines, fnt, size, INK) + 40
    shot = ImageOps.exif_transpose(Image.open(ROOT / c["shot"])).convert("RGB")
    box_w, box_h = W - 160, H - y - 200
    scale = min(box_w / shot.width, box_h / shot.height)
    shot = shot.resize((int(shot.width * scale), int(shot.height * scale)), Image.LANCZOS)
    sx = (W - shot.width) // 2
    d.rounded_rectangle((sx - 3, y - 3, sx + shot.width + 3, y + shot.height + 3), 18, fill="#e2d9c9")
    canvas.paste(shot, (sx, y))
    footer(canvas, d, dark=False)
    return canvas


KINDS = {"photo": photo_card, "stat": stat_card, "quote": quote_card, "proof": proof_card}

CARDS = [
    {"id": "01-fox26-crew", "kind": "photo", "photo": "assets/press/fox26-crew.jpg", "focus": (0.5, 0.2),
     "photo_ratio": 0.62, "kicker": "On FOX 26 Houston · Oct 20, 2026",
     "headline": "Our only server quit. FOX 26 came to see what took over."},
    {"id": "02-fox26-on-air", "kind": "photo", "photo": "assets/press/fox26-on-air-1.jpg", "focus": (0.45, 0.3), "photo_ratio": 0.45,
     "kicker": "Live on FOX 26", "headline": "24 hours from a server to AI. Now every guest orders and pays from their own phone."},
    {"id": "03-fox26-phone", "kind": "photo", "photo": "assets/press/fox26-on-air-2.jpg", "focus": (0.5, 0.45), "photo_ratio": 0.45,
     "kicker": "What you saw on TV", "headline": "That's Haniya. She answers every call and puts the order straight into our register."},
    {"id": "04-stat-9650", "kind": "stat", "kicker": "Our restaurant, October 2026", "stat": "$9,650",
     "label": "a month saved or won back.",
     "sub": "Wok & Karahi, Spring TX. No server, no missed calls, no unpaid tickets. Real numbers, not a demo."},
    {"id": "05-stat-calls", "kind": "stat", "kicker": "The call you never knew you missed", "stat": "1 in 4",
     "label": "calls to our restaurant come in while we're closed.",
     "sub": "Every one of them is answered now. Count the missed calls on your phone tonight."},
    {"id": "06-stat-reviews", "kind": "stat", "kicker": "Reviews, done the smart way", "stat": "400 → 941",
     "label": "Google reviews since we took over. 4.5 stars.",
     "sub": "No paid reviews, no begging. Ask the happy table, hand the unhappy one the owner's card."},
    {"id": "07-stat-selforder", "kind": "stat", "kicker": "August → October", "stat": "17% → 100%",
     "label": "of our own orders are placed by the guest.",
     "sub": "Scan, order, pay. The kitchen only ever sees paid tickets. Dine-and-dash is now impossible."},
    {"id": "08-quote-department", "kind": "quote",
     "quote": "Every chain has a technology department. You have vendors. I want to change that."},
    {"id": "09-quote-enterprise", "kind": "quote", "photo": "assets/press/fox26-on-air-1.jpg",
     "quote": "The tech the big chains use shouldn't be a privilege. Small restaurants deserve it more."},
    {"id": "10-family", "kind": "photo", "photo": "assets/family-413.jpg", "focus": (0.5, 0.75),
     "photo_ratio": 0.6, "kicker": "Why I do this",
     "headline": "I grew up in a restaurant family. Then I became a Google engineer. Now I bring that tech home."},
    {"id": "11-proof-dashboard", "kind": "proof", "shot": "assets/proof/p-dash-today.jpg",
     "kicker": "Building in public", "headline": "Our dashboard knows tonight's rush before we open."},
    {"id": "12-proof-table", "kind": "proof", "shot": "assets/proof/p-table-order.jpg",
     "kicker": "What replaced our server", "headline": "Guests order and pay from their seat. In 7 languages."},
    {"id": "13-proof-haniya", "kind": "proof", "shot": "assets/proof/table-haniya.jpg",
     "kicker": "Meet Haniya", "headline": "Older guests just tap and talk to her."},
    {"id": "14-headshot-intro", "kind": "photo", "photo": "assets/abbas-800.jpg", "focus": (0.5, 0.3),
     "photo_ratio": 0.58, "kicker": "Hi, I'm Abbas",
     "headline": "Ex-Google engineer. Restaurant owner. I bring big-chain tech to the little guy."},
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for c in CARDS:
        img = KINDS[c["kind"]](c)
        img.save(OUT / f"{c['id']}.jpg", quality=88, optimize=True, progressive=True)
        print("wrote", f"assets/social/{c['id']}.jpg")


if __name__ == "__main__":
    main()
