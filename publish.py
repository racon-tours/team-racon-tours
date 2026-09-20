#!/usr/bin/env python3
"""team-racon-tours publisher.

Reads the team-racon-tours Google Sheet (people + links tabs), then:
  1. Generates static profile shells (name/photo/tagline/meta) at /<slug>/index.html
  2. Generates a static hub at /index.html listing all published people
  3. Writes /data/roster.json for client-side fetch of section/link content
  4. Updates /sitemap.xml and /robots.txt (noindex everything)
  5. Deploys to Netlify

Usage:  ./publish.sh   (which calls this script)
"""
import json, os, subprocess, sys, time
from pathlib import Path
from urllib import request

ROOT = Path(__file__).resolve().parent
SHEET_ID_FILE = ROOT / ".sheet_id"
NETLIFY_SITE  = "02e3c1a1-84ed-45d9-80e5-e85374ccd20d"
OP_PATH       = "/opt/homebrew/bin/op"
NETLIFY_PATH  = "/opt/homebrew/bin/netlify"

DEFAULT_FOOTER = ('<a href="https://tourcwe.com/">TourCWE</a> '
                  '&middot; part of Racon&nbsp;Tours')

def op(field):
    return subprocess.check_output(
        [OP_PATH, "item", "get", "Sheets Endpoint", "--vault=RaconTours",
         "--fields", field, "--reveal"]).decode().strip()

def fetch_sheet():
    """Auth'd POST via 1Password (local dev path)."""
    sid = SHEET_ID_FILE.read_text().strip()
    url, secret = op("url"), op("credential")
    def read(tab):
        body = {"secret": secret, "action": "read_range",
                "spreadsheet_id": sid, "range": f"{tab}!A1:Z1000"}
        req = request.Request(url, data=json.dumps(body).encode(),
                              headers={"Content-Type":"application/json"}, method="POST")
        with request.urlopen(req, timeout=30) as r:
            out = json.loads(r.read())
        if not out.get("ok"): raise SystemExit(f"sheet read failed: {out}")
        return out["values"]
    return read("people"), read("links")

# Public read URL (no auth). Points at deployment @5 (owned by
# global.racon.tours). Must match the doGet route in
# sheets-endpoint/Code.gs which is locked to the team-racon-tours sheet.
PUBLIC_FEED = ("https://script.google.com/macros/s/"
               "AKfycbwx109kN4zz3teqMaMVzcbdIxpPFgqov1CJcarECRZr3B8nrspRKCP87U91Y0NgglBjLQ"
               "/exec?action=read_roster")

def fetch_from_public_feed(attempts=4):
    """Public GET via Apps Script — used by CI builds, no secrets needed.

    Apps Script intermittently 404s on its own script.google.com ->
    googleusercontent.com redirect; a bare failure here silently freezes the
    published site, so retry with backoff before giving up.
    """
    last = None
    for i in range(attempts):
        try:
            req = request.Request(PUBLIC_FEED,
                                  headers={"User-Agent": "team-racon-tours-builder/1.0"})
            with request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            if not data.get("ok"):
                raise RuntimeError(f"feed returned ok=false: {data}")
            return data["people"], data["links"]
        except Exception as e:
            last = e
            if i < attempts - 1:
                wait = 5 * (i + 1)
                print(f"  feed attempt {i+1}/{attempts} failed ({e}); retrying in {wait}s")
                time.sleep(wait)
    raise SystemExit(f"public feed read failed after {attempts} attempts: {last}")

def to_dictrows_from_feed(items):
    """Public feed already gives dicts (one per row, headers as keys). Normalize."""
    out = []
    for obj in items or []:
        if not str(obj.get("slug","")).strip(): continue
        # already-normalized published flag from the server side
        p = obj.get("published", True)
        obj["published"] = (p is True or str(p).strip().upper() == "TRUE" or str(p).strip() == "")
        out.append(obj)
    return out

def to_objects(rows):
    """Header row + data rows → list of dicts. Skip rows w/ empty first cell."""
    if not rows or len(rows) < 2: return []
    header = [str(h).strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        if not (r and str(r[0]).strip()): continue
        obj = {}
        for i, h in enumerate(header):
            if not h: continue   # skip trailing empty-header columns
            obj[h] = r[i] if i < len(r) else ""
        # normalize `published`
        p = obj.get("published", "")
        obj["published"] = (p is True or str(p).strip().upper() == "TRUE" or str(p).strip() == "")
        out.append(obj)
    return out

def is_published(o): return o.get("published") is True

# ---------- HTML templates ----------

PROFILE_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>{name} · TourCWE</title>
  <meta name="description" content="{meta_description}">
  <link rel="canonical" href="https://team.racon.tours/{slug}/">
  <meta property="og:type" content="profile">
  <meta property="og:title" content="{name} · TourCWE">
  <meta property="og:description" content="{meta_description}">
  <meta property="og:image" content="https://team.racon.tours/img/{image_filename}">
  <meta property="og:url" content="https://team.racon.tours/{slug}/">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{name} · TourCWE">
  <meta name="twitter:description" content="{meta_description}">
  <meta name="twitter:image" content="https://team.racon.tours/img/{image_filename}">
  <link rel="icon" type="image/svg+xml" href="/assets/logo/favicon.svg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/profile.css?v={cachebust}">
</head>
<body>
<main class="wrap">
  <header class="profile-head">
    <img class="avatar" src="/img/{image_filename}" width="128" height="128" alt="{name}">
    <h1 class="name">{name}</h1>
    <p class="tagline">{tagline}</p>
  </header>

  <div id="link-sections" data-slug="{slug}" aria-live="polite">
    <p class="loading">Loading&hellip;</p>
  </div>

  <footer class="foot">
    <img class="foot__mark" src="/assets/logo/lamp-vector-inverse.svg" alt="" aria-hidden="true">
    <p>{footer_html}</p>
  </footer>
</main>
<script src="/js/profile.js?v={cachebust}" defer></script>
</body>
</html>
"""

HUB_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>Racon Tours · Team</title>
  <meta name="description" content="Guides and team behind Racon Tours.">
  <link rel="icon" type="image/svg+xml" href="/assets/logo/favicon.svg">
  <link rel="icon" type="image/x-icon" href="/favicon.ico">
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Nunito:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="/css/profile.css?v={cachebust}">
</head>
<body>
<main class="wrap">
  <header class="profile-head">
    <img class="avatar" src="/assets/logo/logo-on-cream-disc.svg" width="128" height="128" alt="Racon Tours">
    <h1 class="name">Racon Tours</h1>
    <p class="tagline">The people behind <em>A Taste of Two Cities</em> and Forest Park Picnics.</p>
  </header>

  <h2 class="section-title">Our Team</h2>
{cards}

  <footer class="foot">
    <img class="foot__mark" src="/assets/logo/lamp-vector-inverse.svg" alt="" aria-hidden="true">
    <p><a href="https://tourcwe.com/">TourCWE</a> &middot; <a href="https://forestparkpicnics.com/">Forest Park Picnics</a></p>
  </footer>
</main>
</body>
</html>
"""

CARD_TMPL = """  <a class="link" href="/{slug}/">
    <span class="link__body"><span class="link__title">{name}</span><span class="link__sub">{tagline_plain}</span></span><span class="link__arrow">&#8594;</span>
  </a>"""

import re

def strip_html(s):
    """Crude tag/entity strip for the hub-card subtitle (which is plain text)."""
    s = re.sub(r"<[^>]+>", "", str(s))
    s = (s.replace("&mdash;", "—").replace("&middot;", "·")
           .replace("&nbsp;", " ").replace("&rsquo;", "’")
           .replace("&amp;", "&"))
    return s

# ---------- Build ----------

def build(from_public_feed=False):
    if from_public_feed:
        raw_people, raw_links = fetch_from_public_feed()
        people = [p for p in to_dictrows_from_feed(raw_people) if is_published(p)]
        links  = [l for l in to_dictrows_from_feed(raw_links)  if is_published(l)]
    else:
        people_rows, links_rows = fetch_sheet()
        people = [p for p in to_objects(people_rows) if is_published(p)]
        links  = [l for l in to_objects(links_rows)  if is_published(l)]

    if not people:
        raise SystemExit("no published people in sheet — refusing to build empty site")

    # Slug validation: every links.slug must match a people.slug.
    # Loud error here is much better than silently-broken pages.
    valid_slugs = {p["slug"].strip() for p in people}
    orphans = []
    for i, l in enumerate(links, start=2):  # row 2 = first data row
        s = (l.get("slug") or "").strip()
        if s and s not in valid_slugs:
            orphans.append((i, s, l.get("section",""), l.get("title","")))
    if orphans:
        msg = ["sheet validation FAILED — link rows reference unknown slugs:"]
        msg += [f"  row {r}: slug={s!r}  section={sect!r}  title={t!r}"
                for r, s, sect, t in orphans]
        msg += [f"valid slugs: {sorted(valid_slugs)}"]
        raise SystemExit("\n".join(msg))

    cachebust = time.strftime("%Y-%m-%d")
    by_slug = {p["slug"]: p for p in people}

    # 1. Profile shells
    for p in people:
        slug = p["slug"].strip()
        img  = (p.get("image_filename") or f"{slug}.jpg").strip()
        img_path = ROOT / "img" / img
        if not img_path.exists():
            print(f"  WARN: missing photo for {slug}: img/{img}", file=sys.stderr)

        meta_desc = p.get("meta_description","").strip() or p.get("tagline","")
        meta_desc = strip_html(meta_desc)
        footer = (p.get("footer_html") or "").strip() or DEFAULT_FOOTER

        html = PROFILE_TMPL.format(
            slug=slug,
            name=p["name"],
            tagline=p.get("tagline",""),
            image_filename=img,
            meta_description=meta_desc.replace('"', '&quot;'),
            footer_html=footer,
            cachebust=cachebust,
        )
        out = ROOT / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html)
        print(f"  wrote /{slug}/index.html")

    # 2. Hub
    cards = "\n".join(
        CARD_TMPL.format(slug=p["slug"], name=p["name"],
                         tagline_plain=strip_html(p.get("tagline","")))
        for p in people
    )
    (ROOT / "index.html").write_text(HUB_TMPL.format(cards=cards, cachebust=cachebust))
    print("  wrote /index.html")

    # 3. roster.json
    roster = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "people": [{k: v for k, v in p.items() if k != "published"} for p in people],
        "links":  [{k: v for k, v in l.items() if k != "published"} for l in links],
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "roster.json").write_text(json.dumps(roster, indent=2))
    print(f"  wrote /data/roster.json  ({len(roster['links'])} links across {len(roster['people'])} people)")

    # 4. sitemap + robots (noindex)
    (ROOT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    print("  wrote /robots.txt (full disallow)")
    # No sitemap.xml needed when everything is noindexed; remove if present.
    sm = ROOT / "sitemap.xml"
    if sm.exists(): sm.unlink()

    return people

def deploy():
    token = op("credential")  # piggyback on op; netlify uses its own NETLIFY_AUTH_TOKEN
    netlify_token = subprocess.check_output(
        [OP_PATH, "item", "get", "Netlify PAT", "--vault=RaconTours",
         "--fields", "credential", "--reveal"]).decode().strip()
    env = os.environ.copy()
    env["NETLIFY_AUTH_TOKEN"] = netlify_token
    env["PATH"] = "/opt/homebrew/bin:" + env.get("PATH","")
    r = subprocess.run(
        [NETLIFY_PATH, "deploy", "--prod", "--dir=.",
         f"--site={NETLIFY_SITE}", "--no-build"],
        cwd=str(ROOT), env=env, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        raise SystemExit(f"netlify deploy failed: exit {r.returncode}")

if __name__ == "__main__":
    no_deploy = "--no-deploy" in sys.argv
    from_feed = "--from-public-feed" in sys.argv
    print(f"=== build (source: {'public feed' if from_feed else 'auth POST'}) ===")
    people = build(from_public_feed=from_feed)
    if no_deploy:
        print(f"\n--no-deploy: skipping netlify. {len(people)} people built.")
    else:
        print("\n=== deploy ===")
        deploy()
        print(f"\nDone — {len(people)} profile(s) live at https://team.racon.tours/")
