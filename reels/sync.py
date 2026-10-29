"""Keep reels/reels.json in step with the AZ YouTube channel, so every new reel shows on the page
that matches its story without anyone touching the site. Runs from .github/workflows/az-reels-sync.yml."""
import json, re, urllib.request, xml.etree.ElementTree as ET, pathlib

CHANNEL = "UCj-qILzeofW87kiOCZXnVyw"
OUT = pathlib.Path(__file__).with_name("reels.json")
# First rule that matches the title (or description) decides the page. Order matters.
RULES = [
    (r"doordash|uber ?eats|ordering link|commission|the app\b|app\?", "do-restaurants-lose-money-on-doordash.html"),
    (r"walk ?out|table|paid first|did they pay|dine.and.dash", "how-to-stop-dine-and-dash.html"),
    (r"regular|win.?back|loyal|came in every", "restaurant-loyalty-winback.html"),
    (r"chatgpt|\bai assistant|recommended", "get-your-restaurant-recommended-by-ai.html"),
    (r"closed|hours|google says", "how-to-keep-hours-and-menu-accurate-on-google-and-ai-assistants.html"),
    (r"phone|call|ringing|7:14", "ai-phone-answering-restaurants.html"),
]
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015", "m": "http://search.yahoo.com/mrss/"}

def page_for(text):
    t = text.lower()
    return next((p for rx, p in RULES if re.search(rx, t)), None)

def main():
    req = urllib.request.Request(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL}", headers={"User-Agent": "az-reels-sync/1"})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    reels = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS); title = e.findtext("a:title", namespaces=NS) or ""
        desc = e.findtext("m:group/m:description", namespaces=NS) or ""
        reels.append({"id": vid, "title": title, "published": e.findtext("a:published", namespaces=NS),
                      "page": page_for(title) or page_for(desc)})
    reels.sort(key=lambda r: r["published"] or "", reverse=True)
    old = OUT.read_text() if OUT.exists() else ""
    new = json.dumps({"channel": CHANNEL, "reels": reels}, indent=1) + "\n"
    if new != old: OUT.write_text(new)
    print(f"{len(reels)} reels; pages: " + ", ".join(f"{r['id']}->{r['page']}" for r in reels))

if __name__ == "__main__":
    main()
