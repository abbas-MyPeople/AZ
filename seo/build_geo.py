#!/usr/bin/env python3
"""Generate the local (city) and service x city pages.

Why a generator rather than 17 hand-written files: the head, schema, nav and
footer have to stay identical to the rest of the site, and they change. The nav
and footer are lifted verbatim out of an existing page at build time, so these
pages can never drift away from the other 42.

Why the content is NOT boilerplate: near-identical city pages are doorway pages,
they get filtered, and they deserve to be. Every city carries its own county,
its own real commercial corridors, its own read on what trades there, and its
own angle. That lives in geo.json, not here.

    python3 seo/build_geo.py          # write the pages
    python3 seo/build_geo.py --check  # report only, write nothing
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent
DATA = json.loads((HERE / "geo.json").read_text())
TEMPLATE_PAGE = REPO / "restaurant-technology-consultant-houston.html"
SITE = "https://azrestaurantpartners.com"

# The one statistic used across these pages, attributed wherever it appears.
CLOSURE_STAT = ("119 restaurants closed across the Houston metro in the first half of 2026 "
                "&mdash; more than any other city in the United States or Canada, with Harris "
                "County leading every county in the country")
CLOSURE_CITE = "https://restaurantdata.com/first-half-2026-restaurant-closure-report/"


def shell() -> tuple[str, str]:
    """(nav, footer) lifted from a live page so they never drift."""
    t = TEMPLATE_PAGE.read_text()
    nav = t[t.index("<header class="): t.index("<main")]
    footer = t[t.index("<footer"):]
    return nav, footer


def head(title: str, desc: str, path: str, schema: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <meta name="theme-color" content="#f4eee2" />
  <link rel="canonical" href="{SITE}/{path}" />
  <meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large" />
  <meta name="geo.region" content="US-TX" />
  <meta name="geo.placename" content="Spring, Texas" />
  <meta property="og:title" content="{title}" />
  <meta property="og:description" content="{desc}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{SITE}/{path}" />
  <meta property="og:image" content="{SITE}/assets/og.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/png" sizes="32x32" href="{SITE}/assets/brand/logo-32.png" />
  <link rel="icon" type="image/png" sizes="192x192" href="{SITE}/assets/brand/logo-192.png" />
  <link rel="apple-touch-icon" sizes="180x180" href="{SITE}/assets/brand/logo-180.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="styles.css" />
  <script type="application/ld+json">
{schema}
  </script>
</head>
"""


def business(area_name: str, url: str, extra: dict | None = None) -> dict:
    """The local entity. Repeated per page on purpose: each page has to stand on
    its own for an assistant that only ever sees that one page."""
    node = {
        "@type": ["ProfessionalService", "LocalBusiness"],
        "@id": f"{SITE}/#organization",
        "name": "AZ Restaurant Partners",
        "url": url,
        "email": "hello@azrestaurantpartners.com",
        "telephone": "+1-408-393-6716",
        "priceRange": "$$",
        "image": f"{SITE}/assets/og.png",
        "logo": f"{SITE}/assets/brand/logo-512.png",
        "address": {"@type": "PostalAddress", "addressLocality": "Spring",
                    "addressRegion": "TX", "postalCode": "77388", "addressCountry": "US"},
        "geo": {"@type": "GeoCoordinates", "latitude": 30.0799, "longitude": -95.4172},
        "areaServed": {"@type": "City", "name": area_name, "addressRegion": "TX"},
        "founder": {"@type": "Person", "name": "Abbas Zoeb", "jobTitle": "Founder & CEO"},
        "knowsAbout": ["restaurant point of sale", "commission-free online ordering",
                       "AI phone answering", "restaurant local SEO", "answer engine optimisation",
                       "restaurant loyalty", "catering sales", "restaurant analytics"],
        "sameAs": ["https://www.linkedin.com/in/abbaszoeb", "https://wokandkarahitexas.com"],
    }
    if extra:
        node.update(extra)
    return node


def faq_node(pairs: list[tuple[str, str]]) -> dict:
    return {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in pairs]}


def crumbs(path: str, name: str) -> dict:
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": "Restaurant tech, Houston",
         "item": f"{SITE}/restaurant-technology-consultant-houston.html"},
        {"@type": "ListItem", "position": 3, "name": name, "item": f"{SITE}/{path}"}]}


CTA = """
    <section class="ctaband">
      <div class="wrap ctaband__inner">
        <div>
          <h2>Bring us your problems.</h2>
          <p>Nothing to prepare. Three months free for founding partners, and you keep whatever we build.</p>
        </div>
        <a class="btn btn--primary" href="index.html#start" data-track="geo_cta" data-track-page="{slug}">Claim a free pilot spot</a>
      </div>
    </section>
"""


def city_page(c: dict, nav: str, footer: str) -> tuple[str, str]:
    path = f"restaurant-technology-{c['slug']}-tx.html"
    title = f"Restaurant Technology in {c['name']}, TX &mdash; AZ Restaurant Partners"
    desc = (f"Operator-founded, vendor-neutral restaurant technology for independents in "
            f"{c['name']}, {c['county']}. POS, commission-free ordering, AI phone answering, "
            f"local SEO and AI search. Three months free for founding partners.")
    corridors = ", ".join(c["corridors"])

    faqs = [
        (c["q"], c["a"]),
        (f"Do you actually work with restaurants in {c['name']}?",
         f"Yes. We are based in Spring, TX and {c['name']} is {c['drive']}. Most of the work is "
         f"remote, with on-site visits when they genuinely help — and in {c['county']} that is "
         f"usually around the {c['corridors'][0]} and {c['corridors'][1]} corridors."),
        ("Who owns what you build?",
         "You do. Every account, domain, listing and system is in your name, and if you stop "
         "working with us you keep all of it."),
    ]

    schema = json.dumps({"@context": "https://schema.org", "@graph": [
        business(c["name"], f"{SITE}/{path}"),
        {"@type": "Service", "name": f"Restaurant technology for {c['name']}, TX",
         "serviceType": "Restaurant technology consulting and operations",
         "provider": {"@id": f"{SITE}/#organization"},
         "areaServed": {"@type": "City", "name": c["name"], "addressRegion": "TX"},
         "description": c["angle"]},
        faq_node(faqs), crumbs(path, c["name"])]}, indent=2)

    faq_html = "".join(
        f'\n          <h3>{q}</h3>\n          <p>{a}</p>' for q, a in faqs)
    others = "".join(
        f'<a href="restaurant-technology-{o["slug"]}-tx.html">{o["name"]}</a> '
        for o in DATA["cities"] if o["slug"] != c["slug"])
    services = "".join(
        f'<a href="{s["slug"]}.html">{s["title"]}</a> ' for s in DATA["services"])

    body = ("""<body>
{nav}<main id="top">
    <article class="section guide">
      <div class="wrap">
        <div class="guide__head">
          <p class="guide__crumb"><a href="restaurant-technology-consultant-houston.html">Greater Houston</a> &middot; {c[name]}</p>
          <p class="kicker">Local &amp; operator-founded</p>
          <h1>Restaurant technology in {c[name]}, TX</h1>
          <p class="guide__lead">The technology team an independent restaurant in {c[name]} does
            not have &mdash; and does not need to hire. We find where the money is going, build or
            buy whatever fixes it, and then run it for you.</p>
          <p class="guide__meta">Serving {c[name]}, {c[county]} &middot; based in Spring, TX</p>
        </div>

        <div class="guide__body">
        <h2>What we see in {c[name]}</h2>
        <p>{c[scene]}</p>
        <p>{c[angle]}</p>
        <p>{c[name]} sits in {c[county]}, and the restaurants we work with there trade along
          {corridors}.</p>

        <h2>What we would look at first in {c[name]}</h2>
        <p>{c[first]}</p>

        <div class="guide__callout">
          <p><strong>The market, plainly:</strong> {stat}
            (<a href="{cite}" rel="nofollow noopener" target="_blank">RestaurantData, 2026</a>).
            Rent, labour and food costs are not going back down. What is still winnable is the
            money already leaking out of the operation every week &mdash; and in {c[name]} that
            leak has a particular shape, which is where we start.</p>
        </div>

        <h2>What we take off you</h2>
        <p>Six jobs a chain runs whole departments for, and a {c[name]} owner ends up doing alone.
          We take them off you and keep running them:
          <a href="local-seo-for-restaurants.html">getting found</a>,
          <a href="ai-phone-answering-restaurants.html">winning the order</a>,
          <a href="win-more-catering-orders.html">growing the order</a>,
          <a href="restaurant-loyalty-winback.html">keeping the guest</a>,
          <a href="restaurant-inventory-food-cost.html">keeping the money</a>, and watching all of
          it so a broken thing is found before a guest finds it.</p>
        <p>Our founder engineered at Google, worked on Hard Rock Cafe&rsquo;s first AI agents
          earlier in his career in enterprise software, and owns Wok &amp; Karahi in Spring, Texas.
          We are vendor-neutral and take no commission from any platform, so we will tell you when
          the right move is to spend nothing. <a href="details.html">Full pricing and terms</a>.</p>
        </div>

        <div class="guide__body guide__faq">
          <h2>Questions {c[name]} owners ask</h2>{faq_html}
        </div>

        <div class="guide__next">
          <h2>Nearby</h2>
          <p>{others}</p>
          <h2>By service</h2>
          <p>{services}</p>
          <h2>The engineering</h2>
          <p><a href="investors.html" data-track="tech_behind_geo">What we actually built, in
            engineering detail</a> &mdash; for anyone who wants the technical picture rather
            than the summary.</p>
        </div>
      </div>
{cta}    </article>
  </main>
{footer}""").format(c=c, nav=nav, footer=footer, corridors=corridors,
                             faq_html=faq_html, others=others, services=services,
                             stat=CLOSURE_STAT, cite=CLOSURE_CITE, cta=CTA.format(slug=c["slug"]))
    return path, head(title, desc, path, schema) + body


def service_page(s: dict, nav: str, footer: str) -> tuple[str, str]:
    path = f"{s['slug']}.html"
    title = f"{s['title']} &mdash; AZ Restaurant Partners"
    desc = f"{s['intent']} Operator-founded and vendor-neutral, serving independents across Greater Houston. Three months free for founding partners."

    faqs = [
        (f"How quickly can you start?",
         "We take on a small number of founding partners at a time so the work stays hands-on. "
         "If a spot is open we usually start the same week."),
        ("Do you take commission from vendors?",
         "No. We take nothing from any platform or vendor, which is why we can tell you when the "
         "answer is to change nothing and spend nothing."),
        ("What happens if we stop?",
         "You keep everything. Every account and system is in your name from day one."),
    ]

    schema = json.dumps({"@context": "https://schema.org", "@graph": [
        business("Houston", f"{SITE}/{path}"),
        {"@type": "Service", "name": s["title"],
         "serviceType": s["title"], "provider": {"@id": f"{SITE}/#organization"},
         "areaServed": [{"@type": "City", "name": c["name"], "addressRegion": "TX"}
                        for c in DATA["cities"]],
         "description": s["body"],
         "offers": {"@type": "Offer", "price": "0",
                    "priceCurrency": "USD",
                    "description": "Founding partner — first three months free"}},
        faq_node(faqs), crumbs(path, s["title"])]}, indent=2)

    faq_html = "".join(f'\n          <h3>{q}</h3>\n          <p>{a}</p>' for q, a in faqs)
    reading = "".join(f'<a href="{l}">{l.replace("-", " ").replace(".html", "")}</a> '
                      for l in s["links"])
    cities = "".join(f'<a href="restaurant-technology-{c["slug"]}-tx.html">{c["name"]}</a> '
                     for c in DATA["cities"])

    body = f"""<body>
{nav}<main id="top">
    <article class="section guide">
      <div class="wrap">
        <div class="guide__head">
          <p class="guide__crumb"><a href="restaurant-technology-consultant-houston.html">Greater Houston</a> &middot; {s['title']}</p>
          <p class="kicker">Local &amp; operator-founded</p>
          <h1>{s['h1']}</h1>
          <p class="guide__lead">{s['intent']}</p>
          <p class="guide__meta">Greater Houston, TX &middot; based in Spring</p>
        </div>

        <div class="guide__body">
        <p>{s['body']}</p>

        <div class="guide__callout">
          <p><strong>Where this sits:</strong> we do not sell this on its own. It is one of the
            things we run for a restaurant, alongside everything else that runs on technology
            &mdash; because fixing one and ignoring the rest is how owners end up with a dozen
            tools that do not talk.</p>
        </div>

        <h2>Serving Greater Houston</h2>
        <p>We are based in Spring, TX and work with independents across the metro. {CLOSURE_STAT}
          (<a href="{CLOSURE_CITE}" rel="nofollow noopener" target="_blank">RestaurantData, 2026</a>),
          which is the environment every one of these decisions is being made in.</p>
        <p>{cities}</p>

        <h2>What it costs</h2>
        <p>Founding partners pay nothing for three months &mdash; no monthly fee, no setup charge,
          no contract, and you keep whatever we build. After that, $99/month to keep everything
          running, custom work quoted per job.</p>
        </div>

        <div class="guide__body guide__faq">
          <h2>Common questions</h2>{faq_html}
        </div>

        <div class="guide__next">
          <h2>Read further</h2>
          <p>{reading}</p>
          <p><a href="investors.html" data-track="tech_behind_geo">The tech behind it</a> &mdash;
            what we built and how it is run.</p>
        </div>
      </div>
{CTA.format(slug=s['slug'])}    </article>
  </main>
{footer}"""
    return path, head(title, desc, path, schema) + body


def main() -> None:
    check = "--check" in sys.argv
    nav, footer = shell()
    written = []
    for c in DATA["cities"]:
        path, html = city_page(c, nav, footer)
        written.append(path)
        if not check:
            (REPO / path).write_text(html)
    for s in DATA["services"]:
        path, html = service_page(s, nav, footer)
        written.append(path)
        if not check:
            (REPO / path).write_text(html)

    print(f"{'would write' if check else 'wrote'} {len(written)} pages")
    for p in written:
        size = len((REPO / p).read_text()) if (REPO / p).exists() else 0
        print(f"  {p:52} {size:>6} bytes")


if __name__ == "__main__":
    main()
